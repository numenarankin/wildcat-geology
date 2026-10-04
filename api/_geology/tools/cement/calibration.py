"""CBL calibration — the two anchors every bond index is measured against.

Tool #102 (group K, §15). Spec: `specs/102-cbl_calibration.md`.

Why this is a tool and not a constant. US 11,466,558 B2 Eq. 16 writes the bond
index as an affine function of a dB-domain quantity between two anchors:

    BI = (dB(x) - dB_freePipe) / (dB_100%bond - dB_freePipe)

Both anchors are properties of *this* well, not of the method: the drilling
manual says the free-pipe and 100%-cemented amplitudes "are a function of
drilling mud, cement acoustic properties, casing size and thickness". So the
anchors have to be established once, with their provenance, and read by both
`cbl_bond_index` (#103) and `vdl_classify` (#106). Two bond indices computed
against different anchors are each internally consistent and at least one is
wrong, with nothing on the log to show it.

The honest part. A free-pipe reading is usually obtainable above the top of
cement; a true 100%-bond amplitude frequently is not. This tool therefore
refuses rather than defaulting a missing anchor, and offers
`cbl_free_pipe_reference` as an explicitly *partial* record that downstream
tools detect through `inputs["complete"] is False`.

The record shape (`Quantity.inputs`) is the interface #103 and #106 consume; it
is documented in `CALIBRATION_KEYS` below and in the spec's "calibration record"
table. `Quantity.value` is the characteristic-line span in dB/ft, which is the
denominator of Eq. 16 - i.e. `A_c` in the drilling manual's `BI = A_m / A_c`.
"""
from __future__ import annotations

import math
from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

SOURCE_PATENT_BI = (
    "13-cement-integrity/uspto-11466558-cement-bond-index#5"
)  # Eq. 16, the characteristic line; equations sidecar PDF p. 17
SOURCE_PATENT_FREECASING = (
    "13-cement-integrity/uspto-11466558-cement-bond-index#4"
)  # free-casing information obtained by calibration logging in a free casing zone
SOURCE_MANUAL = (
    "13-cement-integrity/drillingmanual-cement-bond-log#0"
)  # A_m / A_c, the TR spacing d, and the "requires correct knowledge" caveat
SOURCE_PATENT_ATTN = (
    "13-cement-integrity/uspto-10392920-cement-attenuation-bond-index#5"
)  # characteristic line per TR spacing; free pipe BI=0 / full bond BI=1
SOURCE_SPE_DECK = (
    "13-cement-integrity/spe-back-to-basics-bond-log-theory#0"
)  # free-pipe amplitude vs casing size chart (image only); lightweight cement
SOURCE_PETROWIKI = (
    "13-cement-integrity/petrowiki-cement-bond-logs#1"
)  # foamed/exotic cements: consult the logging service company

SOURCE = f"{SOURCE_PATENT_BI}; {SOURCE_MANUAL}"

METHOD = (
    "cbl_calibration: characteristic-line anchors, free pipe BI=0 and 100% bond "
    "BI=1 (US 11,466,558 B2 Eq. 16); span as attenuation A_c = (-20/d)"
    "log10(A_100/A_freepipe) (drillingmanual CBL, p. 3)"
)

# --------------------------------------------------------------------------
# Constants and tables
# --------------------------------------------------------------------------

#: dB conversion factor in `A = (-20/d) log10(ratio)`.
#: drillingmanual-cement-bond-log, PDF p. 3 (equations sidecar). The sign is the
#: reconciled one: cement attenuates, so A_c comes out positive. OnePetro prints
#: `+20/TR` and is the outlier - see the reconcile note in
#: uspto-10392920-cement-attenuation-bond-index.equations.md.
_DB_FACTOR = -20.0

#: Patent endpoints, pinned. uspto-11466558 #5: "A BI value of 1.0 represents a
#: perfect cement-bond"; a free-pipe response is BI = 0 (uspto-10392920 #5:
#: "free pipe (Bond index=0) and full bond (Bond index=1)").
BI_FREE_PIPE = 0.0
BI_FULL_BOND = 1.0

#: Where an anchor came from -> (is it measured in this well?, source).
#: Only kinds the corpus actually names are allowed; anything else is a
#: programmer error, because a provenance the tool cannot reason about is worse
#: than none.
ANCHOR_PROVENANCE: dict[str, tuple[bool, str]] = {
    "measured_free_pipe_this_well": (
        True,
        f"{SOURCE_PATENT_FREECASING}: 'The free-casing information may be "
        f"obtained by a calibration logging and processing in a free casing zone.'",
    ),
    "measured_bonded_this_well": (
        True,
        f"{SOURCE_PATENT_ATTN}: amplitude normalization at 'a depth for amplitude "
        f"normalization derived from the data'; {SOURCE_PATENT_FREECASING}: tool "
        f"waves 'extracted from the well-bonded zone'.",
    ),
    "service_company": (
        False,
        f"{SOURCE_PETROWIKI}: 'users are advised to consult with the logging "
        f"service company regarding the appropriate calibrations.'",
    ),
    "declared_by_caller": (
        False,
        f"{SOURCE_PATENT_ATTN}, claim 3: 'defining a free-pipe amplitude based on "
        f"an amplitude of an acoustic signal propagating through a casing without "
        f"cement attached to the casing, when the depth for amplitude "
        f"normalization is not derived from the measured waveform data.'",
    ),
    "corpus_chart": (
        False,
        f"{SOURCE_SPE_DECK}: 'Amplitude Signals vs. Pipe Size of \"free\" pipe / "
        f"3 ft Amplitude vs. Casing Size' - present in the corpus only as "
        f"img-9.jpeg / img-10.jpeg, with no OCR'd values.",
    ),
}

#: Free-pipe amplitude by casing size. **Empty by construction.**
#: The only such chart in the corpus (SOURCE_SPE_DECK, PDF p. 9) is an
#: un-OCR'd figure, and neither cited source prints a numeric free-pipe or
#: 100%-bonded amplitude for any casing / mud / cement combination. Populating
#: this from a figure read by eye is exactly the invention this build forbids,
#: so every chart lookup refuses instead.
FREE_PIPE_AMPLITUDE_CHART: dict[tuple[float, float], float] = {}

#: Cements whose 100%-bond anchor cannot be taken from a chart or a declaration.
#: drillingmanual-cement-bond-log #0: "low density, low compressive strength
#: cement such as foamed cement, cement with sponge-like microspheres, cement
#: containing hydrogen for control of annulus flux, or any cement containing gas
#: percolation ... the acoustic impedance of the lightweight cement is slightly
#: more than that of the drilling mud."
#: petrowiki-cement-bond-logs #1: "in foamed cements or when exotic additives are
#: used, these calibrations can be inaccurate."
#: spe-back-to-basics-bond-log-theory #0 (PDF p. 24), lightweight cement:
#: "3ft amplitudes may range between 5-10 mV (depending on density)" - i.e. the
#: pipe still rings under *perfect* bonding.
ACOUSTICALLY_CHALLENGING_CEMENT_KEYWORDS: tuple[str, ...] = (
    "foam",
    "lightweight",
    "light weight",
    "light-weight",
    "microsphere",
    "low density",
    "low-density",
    "gas percolation",
)

#: Minimum cement sheath thickness for a valid acoustic evaluation, inches.
#: drillingmanual-cement-bond-log #0: "a cement sheath less than 3/4 in. will not
#: provide complete attenuation for the acoustic signal and hence will not give
#: correct cement evaluation." SOURCED - the one numeric threshold the cited
#: sources print.
MIN_CEMENT_SHEATH_IN = 0.75

#: Relative tolerance when the caller supplies both amplitudes and an
#: attenuation for the same anchor. Not a source constant: a reconcile guard.
_ANCHOR_AGREEMENT_RTOL = 0.01

#: The keys `cbl_bond_index` (#103) and `vdl_classify` (#106) may rely on.
CALIBRATION_KEYS: tuple[str, ...] = (
    "calibration_kind",
    "complete",
    "tr_spacing_ft",
    "amplitude_unit",
    "free_pipe_amplitude",
    "bonded_amplitude",
    "free_pipe_attenuation_db_ft",
    "bonded_attenuation_db_ft",
    "span_db_ft",
    "free_pipe_provenance",
    "bonded_provenance",
    "casing_od_in",
    "casing_weight_lb_ft",
    "cement_type",
    "mud_weight_ppg",
    "mud_type",
    "bi_at_free_pipe",
    "bi_at_full_bond",
)

CALIBRATION_KIND = "cbl_characteristic_line"

#: Alias -> canonical key. The record is emitted with both spellings so the two
#: consumers written in parallel can read it unchanged: #106 looks for
#: `bonded_amplitude` and descends into `Quantity.inputs`; #103 looks for
#: `fully_bonded_amplitude` / `fully_bonded_attenuation_db_per_ft` and reads a
#: plain mapping (pass it `calibration.inputs`). Aliases are *derived* in
#: `_record`, never set independently, so the two spellings cannot diverge.
CALIBRATION_ALIASES: dict[str, str] = {
    "fully_bonded_amplitude": "bonded_amplitude",
    "bonded_amplitude_mv": "bonded_amplitude",
    "free_pipe_amplitude_mv": "free_pipe_amplitude",
    "fully_bonded_attenuation_db_per_ft": "bonded_attenuation_db_ft",
    "free_pipe_attenuation_db_per_ft": "free_pipe_attenuation_db_ft",
    "casing_weight_lbft": "casing_weight_lb_ft",
}


# --------------------------------------------------------------------------
# Internals
# --------------------------------------------------------------------------


def _check_amplitude(name: str, value: float | None) -> None:
    """Amplitudes that cannot exist are programmer error, not a refusal."""
    if value is None:
        return
    v = float(value)
    if not math.isfinite(v) or v <= 0.0:
        raise ValueError(
            f"{name} must be a finite positive amplitude (got {value!r}); "
            "the attenuation form takes log10 of an amplitude ratio"
        )


def _check_provenance(name: str, value: str | None) -> None:
    if value is None:
        return
    if value not in ANCHOR_PROVENANCE:
        raise ValueError(
            f"{name}={value!r} is not a known anchor provenance; "
            f"expected one of {sorted(ANCHOR_PROVENANCE)}"
        )


def _attenuation_db_ft(amplitude: float, free_pipe_amplitude: float, tr_ft: float) -> float:
    """A = (-20/d) log10(amplitude / free-pipe amplitude), dB/ft.

    drillingmanual-cement-bond-log, PDF p. 3 (equations sidecar).
    """
    return (_DB_FACTOR / tr_ft) * math.log10(amplitude / free_pipe_amplitude)


def _cement_is_challenging(cement_type: str | None) -> bool:
    if not cement_type:
        return False
    lowered = cement_type.lower()
    return any(k in lowered for k in ACOUSTICALLY_CHALLENGING_CEMENT_KEYWORDS)


def _record(
    *,
    complete: bool,
    tr_spacing_ft: float | None,
    amplitude_unit: str,
    free_pipe_amplitude: float | None,
    bonded_amplitude: float | None,
    free_pipe_attenuation_db_ft: float,
    bonded_attenuation_db_ft: float | None,
    span_db_ft: float | None,
    free_pipe_provenance: str | None,
    bonded_provenance: str | None,
    casing_od_in: float | None,
    casing_weight_lb_ft: float | None,
    cement_type: str | None,
    mud_weight_ppg: float | None,
    mud_type: str | None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "calibration_kind": CALIBRATION_KIND,
        "complete": complete,
        "tr_spacing_ft": tr_spacing_ft,
        "amplitude_unit": amplitude_unit,
        "free_pipe_amplitude": free_pipe_amplitude,
        "bonded_amplitude": bonded_amplitude,
        "free_pipe_attenuation_db_ft": free_pipe_attenuation_db_ft,
        "bonded_attenuation_db_ft": bonded_attenuation_db_ft,
        "span_db_ft": span_db_ft,
        "free_pipe_provenance": free_pipe_provenance,
        "bonded_provenance": bonded_provenance,
        "casing_od_in": casing_od_in,
        "casing_weight_lb_ft": casing_weight_lb_ft,
        "cement_type": cement_type,
        "mud_weight_ppg": mud_weight_ppg,
        "mud_type": mud_type,
        "bi_at_free_pipe": BI_FREE_PIPE,
        "bi_at_full_bond": BI_FULL_BOND,
    }
    for alias, canonical in CALIBRATION_ALIASES.items():
        record[alias] = record[canonical]
    return record


def _tr_refusal() -> Refusal:
    return Refusal(
        reason=(
            "CBL calibration requires the transmitter-receiver spacing the log was "
            "run with: attenuation is (-20/d)log10(amplitude ratio), so a 3 ft and "
            "a 5 ft tool do not give the same attenuation from the same "
            "amplitudes, and uspto-10392920 builds a different characteristic line "
            "for each TR spacing."
        ),
        needed=("tr_spacing_ft",),
        source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_ATTN}",
    )


def _chart_refusal(which: str) -> Refusal:
    return Refusal(
        reason=(
            f"{which} anchor was requested from a chart, but the corpus prints no "
            "numeric free-pipe or 100%-bonded amplitude for any casing / mud / "
            "cement combination. The one chart that would supply them "
            "('Amplitude Signals vs. Pipe Size of \"free\" pipe / 3 ft Amplitude "
            "vs. Casing Size') exists in the corpus only as an un-OCR'd figure "
            "(img-9.jpeg, img-10.jpeg), so FREE_PIPE_AMPLITUDE_CHART is empty by "
            "construction and no set of conditions is covered."
        ),
        needed=(
            "the anchor measured on this log",
            "or the service-company chart value with the casing, mud and cement "
            "it applies to",
        ),
        source=SOURCE_SPE_DECK,
    )


def _provenance_refusal(which: str, arg: str) -> Refusal:
    return Refusal(
        reason=(
            f"{which} anchor was supplied without its provenance. An anchor whose "
            "origin is unknown cannot be audited, and 'measured in a free-pipe "
            "interval on this log' versus 'declared by the caller' is precisely "
            "what the operator has to see before trusting a bond index."
        ),
        needed=(arg, f"one of {sorted(ANCHOR_PROVENANCE)}"),
        source=SOURCE_MANUAL,
    )


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------


def cbl_calibration(
    *,
    tr_spacing_ft: float | None = None,
    free_pipe_amplitude_mv: float | None = None,
    bonded_amplitude_mv: float | None = None,
    free_pipe_attenuation_db_ft: float | None = None,
    bonded_attenuation_db_ft: float | None = None,
    free_pipe_provenance: str | None = None,
    bonded_provenance: str | None = None,
    anchor_tr_spacing_ft: float | None = None,
    casing_od_in: float | None = None,
    casing_weight_lb_ft: float | None = None,
    cement_type: str | None = None,
    mud_weight_ppg: float | None = None,
    mud_type: str | None = None,
    cement_sheath_thickness_in: float | None = None,
    amplitude_unit: str = "mV",
) -> Quantity | Refusal:
    """Establish the BI = 0 and BI = 1 anchors for one logged interval.

    Returns a `Quantity` whose value is the characteristic-line span in dB/ft -
    the denominator of Eq. 16, equal to the drilling manual's `A_c` - carrying
    the full calibration record in `.inputs` (see `CALIBRATION_KEYS`). Returns a
    `Refusal` whenever an anchor is missing, unprovenanced, inverted, or
    transferred without the conditions it applies to.

    Amplitudes may be in any consistent unit; only their ratio enters the
    arithmetic. `amplitude_unit` labels it, and downstream measurements must be
    in the same unit. The patent notes the raw data "is often unitless" and that
    free-casing data is what normalises it (uspto-11466558 #4).
    """
    # ---- programmer errors first -----------------------------------------
    _check_amplitude("free_pipe_amplitude_mv", free_pipe_amplitude_mv)
    _check_amplitude("bonded_amplitude_mv", bonded_amplitude_mv)
    _check_provenance("free_pipe_provenance", free_pipe_provenance)
    _check_provenance("bonded_provenance", bonded_provenance)
    for name, spacing in (
        ("tr_spacing_ft", tr_spacing_ft),
        ("anchor_tr_spacing_ft", anchor_tr_spacing_ft),
    ):
        if spacing is not None:
            if not math.isfinite(float(spacing)) or float(spacing) <= 0.0:
                raise ValueError(f"{name} must be a finite positive length in feet")

    # ---- refusals, in the spec's order -----------------------------------
    if tr_spacing_ft is None:
        return _tr_refusal()
    tr_ft = float(tr_spacing_ft)

    has_free_pipe = (
        free_pipe_amplitude_mv is not None or free_pipe_attenuation_db_ft is not None
    )
    has_bonded = (
        bonded_amplitude_mv is not None or bonded_attenuation_db_ft is not None
    )

    if has_free_pipe and free_pipe_provenance is None:
        return _provenance_refusal("The free-pipe (BI = 0)", "free_pipe_provenance")
    if has_bonded and bonded_provenance is None:
        return _provenance_refusal("The 100%-bonded (BI = 1)", "bonded_provenance")

    if free_pipe_provenance == "corpus_chart" and free_pipe_amplitude_mv is None:
        return _chart_refusal("The free-pipe (BI = 0)")
    if bonded_provenance == "corpus_chart" and bonded_amplitude_mv is None:
        return _chart_refusal("The 100%-bonded (BI = 1)")

    if not has_free_pipe:
        return Refusal(
            reason=(
                "No free-pipe (BI = 0) anchor. CBL interpretation 'requires correct "
                "knowledge of the amplitude of 100% cemented sheath and of free "
                "pipe', and the free-pipe amplitude is what normalises an "
                "otherwise unitless amplitude log; the corpus supplies no default "
                "for any casing, mud or cement."
            ),
            needed=(
                "free_pipe_amplitude_mv with free_pipe_provenance",
                "or free_pipe_attenuation_db_ft with free_pipe_provenance",
                "normally read from an uncemented interval above the top of cement "
                "on this log",
            ),
            source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_FREECASING}",
        )

    if not has_bonded:
        return Refusal(
            reason=(
                "No 100%-bonded (BI = 1) anchor. This is the anchor that is usually "
                "unavailable: it depends on the drilling mud, the cement acoustic "
                "properties, and the casing size and thickness, and it needs a "
                "genuinely fully-bonded interval on this log. A bond index computed "
                "against a guessed 100%-bond amplitude is wrong by an unbounded "
                "amount and looks entirely normal, so no value is defaulted. For an "
                "attenuation log or a free-pipe call without a bond index, use "
                "cbl_free_pipe_reference(), which returns an explicitly partial "
                "calibration."
            ),
            needed=(
                "bonded_amplitude_mv with bonded_provenance",
                "or bonded_attenuation_db_ft with bonded_provenance",
                "a fully-bonded interval on this log, or the service company's "
                "100%-bond amplitude for this casing, mud and cement",
            ),
            source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_BI}",
        )

    if anchor_tr_spacing_ft is not None and not math.isclose(
        float(anchor_tr_spacing_ft), tr_ft, rel_tol=1e-9, abs_tol=1e-12
    ):
        return Refusal(
            reason=(
                f"Anchors were measured at a TR spacing of {float(anchor_tr_spacing_ft)} "
                f"ft but the log was run at {tr_ft} ft. uspto-10392920 builds a "
                "separate characteristic line per TR spacing and converts between "
                "them with 'the product of attenuation rate (in dB/ft) of given "
                "cement bond conditions and the extra spacing' - a per-bond-"
                "condition attenuation rate the corpus tabulates nowhere, so the "
                "conversion is not performed here rather than invented."
            ),
            needed=(
                "anchors measured at tr_spacing_ft",
                "or the attenuation rate in dB/ft for free pipe and for 100% bond "
                "under these conditions",
            ),
            source=SOURCE_PATENT_ATTN,
        )

    if (
        cement_sheath_thickness_in is not None
        and float(cement_sheath_thickness_in) < MIN_CEMENT_SHEATH_IN
    ):
        return Refusal(
            reason=(
                f"Cement sheath {float(cement_sheath_thickness_in)} in is thinner "
                f"than {MIN_CEMENT_SHEATH_IN} in: 'a cement sheath less than 3/4 in. "
                "will not provide complete attenuation for the acoustic signal and "
                "hence will not give correct cement evaluation'. The 100%-bond "
                "anchor cannot be established in a sheath that never reaches full "
                "attenuation."
            ),
            needed=(
                "a hole/casing geometry giving at least 0.75 in of annular cement",
                "or an ultrasonic evaluation instead of a bond index",
            ),
            source=SOURCE_MANUAL,
        )

    free_measured = ANCHOR_PROVENANCE[free_pipe_provenance][0]
    bonded_measured = ANCHOR_PROVENANCE[bonded_provenance][0]

    if not (free_measured and bonded_measured):
        missing = [
            arg
            for arg, val in (
                ("casing_od_in", casing_od_in),
                ("casing_weight_lb_ft", casing_weight_lb_ft),
                ("cement_type", cement_type),
                ("mud_weight_ppg or mud_type", mud_weight_ppg or mud_type),
            )
            if val is None
        ]
        if missing:
            return Refusal(
                reason=(
                    "An anchor that was not measured in this well was supplied "
                    f"({free_pipe_provenance!r} / {bonded_provenance!r}) without the "
                    "conditions it applies to. The free-pipe and 100%-cemented "
                    "amplitudes 'are a function of drilling mud, cement acoustic "
                    "properties, casing size and thickness', so a transferred "
                    "anchor is meaningless unless those are stated and checked "
                    "against the string actually run."
                ),
                needed=tuple(missing),
                source=SOURCE_MANUAL,
            )

    if _cement_is_challenging(cement_type) and not (
        bonded_measured or bonded_provenance == "service_company"
    ):
        return Refusal(
            reason=(
                f"cement_type={cement_type!r} is acoustically challenging (foamed, "
                "lightweight, microsphere or gas-bearing): 'the acoustic impedance "
                "of the lightweight cement is slightly more than that of the "
                "drilling mud', 3 ft amplitudes may still read 5-10 mV under "
                "perfect bonding, and 'in foamed cements or when exotic additives "
                "are used, these calibrations can be inaccurate'. A declared or "
                "charted 100%-bond anchor cannot stand here."
            ),
            needed=(
                "a 100%-bond anchor measured in this well "
                "(bonded_provenance='measured_bonded_this_well')",
                "or the logging service company's calibration for this cement "
                "(bonded_provenance='service_company')",
            ),
            source=f"{SOURCE_MANUAL}; {SOURCE_PETROWIKI}; {SOURCE_SPE_DECK}",
        )

    # ---- the arithmetic ---------------------------------------------------
    free_atten = (
        0.0 if free_pipe_attenuation_db_ft is None else float(free_pipe_attenuation_db_ft)
    )

    bonded_atten_from_amp: float | None = None
    if bonded_amplitude_mv is not None and free_pipe_amplitude_mv is not None:
        bonded_atten_from_amp = free_atten + _attenuation_db_ft(
            float(bonded_amplitude_mv), float(free_pipe_amplitude_mv), tr_ft
        )
    elif bonded_amplitude_mv is not None and free_pipe_amplitude_mv is None:
        return Refusal(
            reason=(
                "A 100%-bonded amplitude was supplied but the free-pipe anchor was "
                "given only as an attenuation. The amplitude-domain anchor pair must "
                "be complete: A_c is (-20/d)log10(bonded amplitude / free-pipe "
                "amplitude), and there is no free-pipe amplitude to divide by."
            ),
            needed=("free_pipe_amplitude_mv",),
            source=SOURCE_MANUAL,
        )

    bonded_atten_given = (
        None if bonded_attenuation_db_ft is None else float(bonded_attenuation_db_ft)
    )

    if bonded_atten_from_amp is not None and bonded_atten_given is not None:
        if not math.isclose(
            bonded_atten_from_amp,
            bonded_atten_given,
            rel_tol=_ANCHOR_AGREEMENT_RTOL,
            abs_tol=1e-9,
        ):
            return Refusal(
                reason=(
                    "The two independent derivations of the 100%-bond anchor "
                    f"disagree: {bonded_atten_from_amp:.6g} dB/ft from the supplied "
                    f"amplitudes at TR = {tr_ft} ft versus "
                    f"{bonded_atten_given:.6g} dB/ft supplied directly. One "
                    "calibration cannot hold two values; the tool will not pick "
                    "one silently."
                ),
                needed=(
                    "amplitudes and attenuation that reconcile at this TR spacing",
                    "or only one of the two",
                ),
                source=SOURCE_MANUAL,
            )

    bonded_atten = (
        bonded_atten_from_amp if bonded_atten_from_amp is not None else bonded_atten_given
    )
    assert bonded_atten is not None  # guaranteed by the has_bonded check above

    span = bonded_atten - free_atten

    if span <= 0.0:
        if free_pipe_amplitude_mv is not None and bonded_amplitude_mv is not None:
            detail = (
                f"free-pipe amplitude {float(free_pipe_amplitude_mv)} "
                f"{amplitude_unit} is not above the 100%-bonded amplitude "
                f"{float(bonded_amplitude_mv)} {amplitude_unit}"
            )
        else:
            detail = (
                f"the 100%-bond attenuation {bonded_atten:.6g} dB/ft is not above "
                f"the free-pipe attenuation {free_atten:.6g} dB/ft"
            )
        return Refusal(
            reason=(
                "Inverted or degenerate calibration: " + detail + ". Physically the "
                "free pipe rings loudest - 'a low amplitude indicates cement, and a "
                "high amplitude indicates free pipe' - so the span dB_100%bond - "
                "dB_freePipe must be strictly positive; here it is "
                f"{span:.6g} dB/ft, which would make Eq. 16 negative or "
                "undefined. Usual causes: a mis-picked free-pipe interval, a "
                "microannulus reading like free pipe in cemented casing, a fast "
                "formation arrival inside the amplitude gate, or a gain change "
                "between passes."
            ),
            needed=(
                "a free-pipe anchor read in genuinely uncemented casing",
                "a 100%-bond anchor read in a genuinely fully-bonded interval",
                "both at the same tool gain and TR spacing",
            ),
            source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_BI}",
        )

    flags: list[str] = []
    if not bonded_measured:
        flags.append("bonded_anchor_not_measured")
    if not free_measured:
        flags.append("free_pipe_anchor_not_measured")
    if _cement_is_challenging(cement_type):
        flags.append("cement_acoustically_challenging")
    if amplitude_unit != "mV":
        flags.append(f"amplitude_unit_{amplitude_unit}")
    if free_atten != 0.0:
        flags.append("absolute_attenuation_parameterisation")
    if any(
        v is None
        for v in (casing_od_in, casing_weight_lb_ft, cement_type, mud_weight_ppg or mud_type)
    ):
        flags.append("conditions_incomplete")

    return Quantity(
        value=span,
        unit="dB/ft",
        method=METHOD,
        source=SOURCE,
        inputs=_record(
            complete=True,
            tr_spacing_ft=tr_ft,
            amplitude_unit=amplitude_unit,
            free_pipe_amplitude=(
                None if free_pipe_amplitude_mv is None else float(free_pipe_amplitude_mv)
            ),
            bonded_amplitude=(
                None if bonded_amplitude_mv is None else float(bonded_amplitude_mv)
            ),
            free_pipe_attenuation_db_ft=free_atten,
            bonded_attenuation_db_ft=bonded_atten,
            span_db_ft=span,
            free_pipe_provenance=free_pipe_provenance,
            bonded_provenance=bonded_provenance,
            casing_od_in=casing_od_in,
            casing_weight_lb_ft=casing_weight_lb_ft,
            cement_type=cement_type,
            mud_weight_ppg=mud_weight_ppg,
            mud_type=mud_type,
        ),
        assumptions={
            "characteristic_line": (
                "linear in dB between the anchors: BI = (dB(x) - dB_freePipe) / "
                "(dB_100%bond - dB_freePipe), US 11,466,558 B2 Eq. 16. Not linear "
                "in raw amplitude."
            ),
            "free_pipe_attenuation_reference": (
                "attenuation referenced to free pipe (0 dB/ft) unless the caller "
                "supplies an absolute free-pipe attenuation; this parameterisation "
                "is what makes the drilling manual's BI = A_m/A_c identical to "
                "Eq. 16"
            ),
            "sign": (
                "A = (-20/d)log10(amplitude ratio); cement attenuates so A_c > 0 "
                "(reconciled against OnePetro's +20/TR)"
            ),
            "anchor_provenance": {
                "free_pipe": ANCHOR_PROVENANCE[free_pipe_provenance][1],
                "bonded": ANCHOR_PROVENANCE[bonded_provenance][1],
            },
        },
        flags=tuple(flags),
    )


def cbl_free_pipe_reference(
    *,
    tr_spacing_ft: float | None = None,
    free_pipe_amplitude_mv: float | None = None,
    free_pipe_provenance: str | None = None,
    free_pipe_attenuation_db_ft: float | None = None,
    casing_od_in: float | None = None,
    casing_weight_lb_ft: float | None = None,
    cement_type: str | None = None,
    mud_weight_ppg: float | None = None,
    mud_type: str | None = None,
    amplitude_unit: str = "mV",
) -> Quantity | Refusal:
    """The BI = 0 anchor alone: an explicitly **partial** calibration.

    Enough to compute an attenuation log (`A_m = (-20/d)log10(measured /
    free-pipe)`) and to recognise a free-pipe response. **Not** enough for a bond
    index: `inputs["complete"]` is False and the result is flagged
    `bond_index_unavailable`, which #103 and #106 must check before dividing by a
    span that does not exist.
    """
    _check_amplitude("free_pipe_amplitude_mv", free_pipe_amplitude_mv)
    _check_provenance("free_pipe_provenance", free_pipe_provenance)
    if tr_spacing_ft is not None and (
        not math.isfinite(float(tr_spacing_ft)) or float(tr_spacing_ft) <= 0.0
    ):
        raise ValueError("tr_spacing_ft must be a finite positive length in feet")

    if tr_spacing_ft is None:
        return _tr_refusal()
    if free_pipe_amplitude_mv is None:
        return Refusal(
            reason=(
                "No free-pipe (BI = 0) amplitude. It must be read from an "
                "uncemented interval on this log or declared with its conditions; "
                "the corpus supplies no default for any casing, mud or cement."
            ),
            needed=("free_pipe_amplitude_mv", "free_pipe_provenance"),
            source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_FREECASING}",
        )
    if free_pipe_provenance is None:
        return _provenance_refusal("The free-pipe (BI = 0)", "free_pipe_provenance")
    if free_pipe_provenance == "corpus_chart":
        return _chart_refusal("The free-pipe (BI = 0)")

    flags = ["partial_calibration", "bond_index_unavailable"]
    if not ANCHOR_PROVENANCE[free_pipe_provenance][0]:
        flags.append("free_pipe_anchor_not_measured")

    return Quantity(
        value=float(free_pipe_amplitude_mv),
        unit=amplitude_unit,
        method=(
            "cbl_free_pipe_reference: BI = 0 anchor only; attenuation reference for "
            "A_m = (-20/d)log10(measured / free-pipe), no 100%-bond anchor"
        ),
        source=f"{SOURCE_MANUAL}; {SOURCE_PATENT_FREECASING}",
        inputs=_record(
            complete=False,
            tr_spacing_ft=float(tr_spacing_ft),
            amplitude_unit=amplitude_unit,
            free_pipe_amplitude=float(free_pipe_amplitude_mv),
            bonded_amplitude=None,
            free_pipe_attenuation_db_ft=(
                0.0
                if free_pipe_attenuation_db_ft is None
                else float(free_pipe_attenuation_db_ft)
            ),
            bonded_attenuation_db_ft=None,
            span_db_ft=None,
            free_pipe_provenance=free_pipe_provenance,
            bonded_provenance=None,
            casing_od_in=casing_od_in,
            casing_weight_lb_ft=casing_weight_lb_ft,
            cement_type=cement_type,
            mud_weight_ppg=mud_weight_ppg,
            mud_type=mud_type,
        ),
        assumptions={
            "completeness": (
                "no 100%-bond anchor: bond index is unavailable, attenuation is not"
            ),
            "anchor_provenance": {
                "free_pipe": ANCHOR_PROVENANCE[free_pipe_provenance][1]
            },
        },
        flags=tuple(flags),
    )


def cbl_characteristic_line(
    calibration: Quantity | Refusal,
    bond_index: float,
) -> Quantity | Refusal:
    """Eq. 16 inverted: the dB/ft attenuation a given bond index sits at.

    `dB(BI) = dB_freePipe + BI * (dB_100%bond - dB_freePipe)`. Provided so the
    patent's endpoints can be asserted directly: BI = 0 returns the free-pipe
    anchor, BI = 1 returns the 100%-bond anchor. Mapping a *measurement* to a
    bond index is `cbl_bond_index` (#103), not this.
    """
    if isinstance(calibration, Refusal):
        return calibration
    bi = float(bond_index)
    if not math.isfinite(bi) or bi < BI_FREE_PIPE or bi > BI_FULL_BOND:
        raise ValueError(
            "bond_index must lie on [0, 1]; the characteristic line is only "
            "defined between the free-pipe and 100%-bond anchors"
        )
    record = calibration.inputs
    if record.get("calibration_kind") != CALIBRATION_KIND:
        raise ValueError("calibration is not a cbl_characteristic_line record")
    if not record.get("complete"):
        return Refusal(
            reason=(
                "Partial calibration: the 100%-bond (BI = 1) anchor is missing, so "
                "the characteristic line has no far end and no bond index can be "
                "placed on it."
            ),
            needed=("a complete cbl_calibration",),
            source=SOURCE_PATENT_BI,
        )
    free_atten = float(record["free_pipe_attenuation_db_ft"])
    span = float(record["span_db_ft"])
    return Quantity(
        value=free_atten + bi * span,
        unit="dB/ft",
        method=(
            "cbl_characteristic_line: dB(BI) = dB_freePipe + BI(dB_100%bond - "
            "dB_freePipe), US 11,466,558 B2 Eq. 16 inverted"
        ),
        source=SOURCE_PATENT_BI,
        inputs={
            "bond_index": bi,
            "free_pipe_attenuation_db_ft": free_atten,
            "span_db_ft": span,
            "tr_spacing_ft": record["tr_spacing_ft"],
        },
        assumptions={
            "characteristic_line": "linear in dB between the two anchors (Eq. 16)"
        },
        flags=calibration.flags,
    )
