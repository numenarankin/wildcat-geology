"""#103 `cbl_bond_index` — casing amplitude (or attenuation rate) to bond index.

Spec: `specs/103-cbl_bond_index.md`.

Two decisions carry the whole module and neither is obvious from the arithmetic.

**The sign.** Attenuation is `A = (-20/d) log10(measured / free-pipe)`. Cement
attenuates, so `measured < free-pipe`, the log is negative, and only the negative
prefix returns a positive dB/ft. `onepetro-cement-bond-logs-print` p. 8 prints
`+20/TR` and is the outlier; `uspto-10392920` Eqn. 1 rearranges to the negative
form and its published worked check (SA_0=100, SA_a=40, TR=3 -> +2.653 dB/ft) is
reproduced here by `cbl_attenuation`. The sign cancels inside `BI = A_m/A_c` and
does NOT cancel in the dB/ft this module reports as its own output. Do not
"simplify" `ATTENUATION_DB_PREFIX` away because BI is unaffected by it.

**The calibration is consumed, never re-derived.** `tool-catalog.md` #102 requires
that `cbl_bond_index` and `vdl_classify` read the same calibration object. Anchor
fields are looked up through `CALIBRATION_FIELDS` so a naming mismatch with #102
degrades to a `Refusal` naming the missing anchor instead of a silent default.

Supersedes the prototype `attenuation` / `cbl_bond_index` in `tools/cement.py`,
which flagged rather than refused on a bad calibration, took loose amplitudes
rather than a calibration object, and did not expose the free-pipe/spacing checks.
"""
from __future__ import annotations

import math
from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported for the module)

# --- corpus anchors -------------------------------------------------------

DRILLINGMANUAL = "13-cement-integrity/drillingmanual-cement-bond-log"
"""BI = A_m/A_c and A = (-20/d) log(measured/free-pipe), pp. 2-3 (equations
sidecar, vision-transcribed; the .md lost them to image conversion)."""

USPTO_10392920 = "13-cement-integrity/uspto-10392920-cement-attenuation-bond-index"
"""p. 11: 'the bond index (BI) is defined by dividing an attenuation rate in zone
of interest [dB/ft] by an attenuation rate in well cemented zone [dB/ft]'.
Eqn. 1 (p. 12) supplies the attenuation form and settles the sign."""

USPTO_11466558 = "13-cement-integrity/uspto-11466558-cement-bond-index"
"""p. 17: BI = (dB(x) - dB_freePipe)/(dB_100%bond - dB_freePipe) — algebraically
the same equation, and the general form used by the attenuation-input path."""

ONEPETRO = "13-cement-integrity/onepetro-cement-bond-logs-print"
"""'the ratio of measured attenuation to maximum attenuation ... requires
attenuation measurements in zones with 100% bond and in free pipe' (p. 8).
Prints the outlier +20/TR sign; typical TR spacing 3-5 ft."""

# --- constants ------------------------------------------------------------

ATTENUATION_DB_PREFIX = -20.0
"""Numerator of the attenuation prefix, `A = (PREFIX/d) log10(...)`.
Source: DRILLINGMANUAL p. 3, corroborated by USPTO_10392920 Eqn. 1 rearranged.
ONEPETRO p. 8 prints +20; reconcile decided in favour of -20 (see module
docstring and the catalog entry for #103). NEVER inline this."""

ATTENUATION_LOG_BASE = 10
"""dB is a base-10 decade measure; confirmed by USPTO_10392920's Eqn. 1, which
reproduces its published +2.653 dB/ft check only in base 10."""

BOND_INDEX_MIN = 0.0
BOND_INDEX_MAX = 1.0
"""BI is a fraction of casing circumference bonded (USPTO_10392920 p. 11);
1.0 is a perfect bond, <1.0 incomplete (USPTO_11466558 p. 17). Outside this
band the calibration is wrong — refuse, never clamp."""

TR_SPACING_TYPICAL_FT = (3.0, 5.0)
"""'TR spacing typically ranges from 3 to 5 ft' — ONEPETRO. Descriptive, not a
validity limit (USPTO_10392920 works at 7 ft LWD spacing): flag, never refuse."""

SPACING_MATCH_TOL_FT = 0.01
"""Float-noise tolerance when cross-checking `d_ft` against the spacing the
calibration's anchors were established at. House value; no source needed because
it is a float-equality epsilon, not a physical threshold."""

FAST_FORMATION_TRANSIT_US_PER_FT = 57.0
"""Recorded for callers: below this the formation arrival lands in the amplitude
gate and the amplitude curve is unreliable (ONEPETRO). Not checkable from this
tool's arguments — it is `vdl_classify`'s (#106) refusal, not this one's."""

CALIBRATION_FIELDS: dict[str, tuple[str, ...]] = {
    # purpose -> accepted field names, canonical first.
    "free_pipe_amplitude": (
        "free_pipe_amplitude", "amplitude_free_pipe", "free_pipe_amp",
        "free_pipe", "bi0_amplitude",
    ),
    "fully_bonded_amplitude": (
        "fully_bonded_amplitude", "hundred_percent_amplitude", "amplitude_100pct",
        "cemented_amplitude", "full_bond_amplitude", "bi1_amplitude",
    ),
    "free_pipe_attenuation_db_per_ft": (
        "free_pipe_attenuation_db_per_ft", "free_pipe_attenuation",
        "attenuation_free_pipe",
    ),
    "fully_bonded_attenuation_db_per_ft": (
        "fully_bonded_attenuation_db_per_ft", "fully_bonded_attenuation",
        "attenuation_100pct", "cemented_attenuation",
    ),
    "tr_spacing_ft": ("tr_spacing_ft", "d_ft", "spacing_ft", "tr_spacing"),
}
"""The complete set of calibration fields #103 reads. #102 is being written in
parallel; aliases are a bridge until the coordinator pins one spelling. A
calibration spelling an anchor in none of these ways refuses (R3/R4) rather than
falling back to a default."""

CALIBRATION_PROVENANCE_FIELDS = (
    "source", "casing_od_in", "cement_type", "mud_weight_ppg", "casing_weight_lbft",
)
"""Carried through onto the result's `assumptions` so an audit can trace which
anchors produced the number. Never used in the arithmetic."""

_PERMANENT_FLAG = (
    "bond index is the fraction of casing circumference bonded, not a "
    "cement-quality or compressive-strength measure"
)


# --- calibration access ---------------------------------------------------


def _unwrap(value: Any) -> Any:
    """Accept a bare number or a `Quantity` from #102."""
    if isinstance(value, Quantity):
        return value.value
    return value


def _cal_get(calibration: Any, purpose: str) -> tuple[float | None, str | None]:
    """Return (value, field-name-used) for a calibration field, or (None, None).

    Reads dicts, dataclasses and plain objects alike, and looks inside a
    `Quantity.inputs`, because that is the shape #102 actually returns: its
    `Quantity.value` is the characteristic-line span and the two anchors live in
    `.inputs`. Without that last branch this refused a calibration that was
    holding exactly the numbers it asked for -- it failed safe, but by luck
    rather than design, and only when handed #102's own return value directly.
    #106's `_read_field` already had the fallback; this is the two brought into
    line at merge.
    """
    for name in CALIBRATION_FIELDS[purpose]:
        if isinstance(calibration, dict):
            if name in calibration and calibration[name] is not None:
                return _unwrap(calibration[name]), name
            continue
        value = getattr(calibration, name, None)
        if value is not None:
            return _unwrap(value), name
        inputs = getattr(calibration, "inputs", None)
        if isinstance(inputs, dict) and inputs.get(name) is not None:
            return _unwrap(inputs[name]), name
    return None, None


def _cal_provenance(calibration: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in CALIBRATION_PROVENANCE_FIELDS:
        if isinstance(calibration, dict):
            value = calibration.get(name)
        else:
            value = getattr(calibration, name, None)
            if value is None:
                # Same fallback as `_cal_get`: #102 returns a Quantity whose
                # record lives in `.inputs`, so casing/cement/mud provenance is
                # only reachable there. Without this the audit trail was silently
                # empty for exactly the shape the real tool returns.
                inputs = getattr(calibration, "inputs", None)
                if isinstance(inputs, dict):
                    value = inputs.get(name)
        if value is not None:
            out[f"calibration_{name}"] = _unwrap(value)
    return out


def _calibration_unusable(calibration: Any) -> Refusal | None:
    """R1/R2: no calibration at all, or #102 itself declined."""
    if calibration is None:
        return Refusal(
            reason="no CBL calibration supplied; bond index is defined only against "
                   "the free-pipe (BI=0) and 100%-bonded (BI=1) anchors, and the "
                   "source requires both: 'This technique requires attenuation "
                   "measurements in zones with 100% bond and in free pipe'",
            needed=("a cbl_calibration (#102) result for this casing size, cement "
                    "type and TR spacing",),
            source=ONEPETRO,
        )
    if isinstance(calibration, Refusal):
        return Refusal(
            reason=f"cbl_calibration (#102) declined: {calibration.reason}",
            needed=calibration.needed or ("a usable CBL calibration",),
            source=calibration.source or DRILLINGMANUAL,
        )
    return None


def _spacing_refusal(calibration: Any, d_ft: float) -> tuple[Refusal | None, list[str], float | None]:
    """R6 plus the spacing flags. Returns (refusal, flags, calibration spacing)."""
    flags: list[str] = []
    cal_d, _ = _cal_get(calibration, "tr_spacing_ft")
    if cal_d is None:
        flags.append(
            f"calibration does not record the T-R spacing its anchors were "
            f"established at; comparability with d_ft = {d_ft:g} ft is unverified"
        )
    elif abs(float(cal_d) - d_ft) > SPACING_MATCH_TOL_FT:
        return (
            Refusal(
                reason=f"calibration anchors were established at a T-R spacing of "
                       f"{float(cal_d):g} ft but the measurement is at {d_ft:g} ft; "
                       "amplitudes recorded at different spacings are not comparable "
                       "quantities and their ratio is not a bond index",
                needed=(f"a calibration established at {d_ft:g} ft, or the amplitude "
                        "measured at the calibration's spacing",),
                source=USPTO_10392920,
            ),
            flags,
            float(cal_d),
        )
    low, high = TR_SPACING_TYPICAL_FT
    if d_ft < low or d_ft > high:
        flags.append(
            f"T-R spacing {d_ft:g} ft is outside the {low:g}-{high:g} ft typical range; "
            "the equation is not restricted to that range, but confirm the "
            "calibration was run on the same tool"
        )
    return None, flags, (float(cal_d) if cal_d is not None else None)


# --- the attenuation primitive -------------------------------------------


def cbl_attenuation(amplitude: float, free_pipe_amplitude: float, d_ft: float):
    """Casing-mode attenuation in dB/ft. **Positive for attenuating cement.**

    `A = (-20/d) log10(measured amplitude / free-pipe amplitude)`
    — DRILLINGMANUAL p. 3.

    Exposed as its own tool because dB/ft is a reported CBL output and because
    this is where the sign matters. It cancels in `cbl_bond_index`; it does not
    cancel here.

    Raises `ValueError` on impossible arguments (non-positive spacing, negative
    amplitude); returns a `Refusal` for conditions a real log produces.
    """
    if d_ft is None:
        return Refusal(
            reason="transmitter-receiver spacing is not recorded; attenuation is "
                   "(-20/d)·log10(measured/free-pipe) and d is an input, not a "
                   "tool constant",
            needed=("the tool's T-R spacing in feet, from the log header or the "
                    "service-company tool sheet",),
            source=DRILLINGMANUAL,
        )
    if d_ft <= 0:
        raise ValueError(f"transmitter-receiver spacing must be positive, got {d_ft}")
    if amplitude < 0 or free_pipe_amplitude < 0:
        raise ValueError("amplitudes cannot be negative")
    if free_pipe_amplitude == 0:
        return Refusal(
            reason="free-pipe amplitude is zero; it is the denominator of the "
                   "attenuation ratio and the BI=0 anchor",
            needed=("a non-zero free-pipe amplitude from cbl_calibration (#102)",),
            source=DRILLINGMANUAL,
        )
    if amplitude == 0:
        return Refusal(
            reason="measured amplitude is zero: log10(0) is undefined, and a zero "
                   "casing amplitude is at or below the noise floor, where "
                   "'quantitative cement evaluation may be affected by noise and "
                   "invalid'",
            needed=("a casing amplitude above the tool's noise level",),
            source=USPTO_10392920,
        )
    if amplitude > free_pipe_amplitude:
        return Refusal(
            reason=f"measured amplitude {amplitude:g} exceeds the free-pipe anchor "
                   f"{free_pipe_amplitude:g}; nothing behind the casing is less "
                   "attenuating than free pipe, so either the free-pipe anchor is "
                   "wrong for this mud/casing or the formation arrival is inside "
                   "the amplitude gate",
            needed=("a free-pipe anchor established in this well's mud and casing, "
                    "or confirmation that the interval is not a fast formation "
                    f"(transit time < {FAST_FORMATION_TRANSIT_US_PER_FT:g} us/ft)",),
            source=DRILLINGMANUAL,
        )

    ratio = amplitude / free_pipe_amplitude
    att = (ATTENUATION_DB_PREFIX / d_ft) * math.log(ratio, ATTENUATION_LOG_BASE)
    att = att + 0.0 if att else 0.0  # free pipe gives -0.0; report it as 0.0
    return Quantity(
        att, "dB/ft",
        "attenuation A = (-20/d)·log10(measured/free-pipe)", DRILLINGMANUAL,
        inputs={"amplitude": amplitude, "free_pipe_amplitude": free_pipe_amplitude,
                "d_ft": d_ft, "amplitude_ratio": ratio},
        assumptions={"log_base": ATTENUATION_LOG_BASE,
                     "attenuation_prefix": ATTENUATION_DB_PREFIX,
                     "sign_convention": "negative prefix; OnePetro's +20/TR is the "
                                        "outlier and returns a negative dB/ft for "
                                        "attenuating cement",
                     "corroborated_by": USPTO_10392920},
        flags=("positive dB/ft means the interval attenuates; the sign is "
               "load-bearing here and cancels only inside the bond-index ratio",),
    )


# --- the tool -------------------------------------------------------------


def _bond_index_result(bi: float, *, inputs: dict[str, Any], assumptions: dict[str, Any],
                       flags: list[str], method: str, source: str):
    """Shared tail: the out-of-range refusal, then the Quantity."""
    if not bi:
        bi = 0.0  # a free-pipe reading produces -0.0; report it as 0.0
    if bi < BOND_INDEX_MIN or bi > BOND_INDEX_MAX:
        return Refusal(
            reason=f"bond index computes to {bi:.6f}, outside {BOND_INDEX_MIN:g}-"
                   f"{BOND_INDEX_MAX:g}. BI is the fraction of casing circumference "
                   "bonded, so this is not a better- or worse-than-possible bond: "
                   "the calibration anchors are wrong. Refused rather than clamped, "
                   "because a clamped 1.0 would certify isolation off a calibration "
                   "already known to be bad",
            needed=("a 100%-bonded anchor picked in a genuinely fully cemented "
                    "interval, and a free-pipe anchor from this well",),
            source=source,
        )
    if bi == BOND_INDEX_MIN:
        flags.append("free pipe: measured attenuation equals the free-pipe anchor "
                     "(BI = 0)")
    return Quantity(
        bi, "fraction", method, source,
        inputs=inputs, assumptions=assumptions,
        flags=tuple([_PERMANENT_FLAG, *flags]),
    )


def cbl_bond_index(measured_amplitude: float, calibration: Any, d_ft: float):
    """Bond index from a casing amplitude and a `cbl_calibration` (#102) result.

    `BI = A_m / A_c`, with
    `A_m = (-20/d) log10(measured / free-pipe)` and
    `A_c = (-20/d) log10(100%-cemented / free-pipe)`  — DRILLINGMANUAL pp. 2-3.

    `d_ft` is required and has no default: a 3 ft and a 5 ft tool do not give the
    same attenuation from the same amplitudes. It cancels in the ratio; requiring
    it is what lets the calibration's own spacing be cross-checked, which is the
    error that actually happens. Pass `d_ft=None` to say the spacing is unrecorded
    — that returns a `Refusal`. Omitting the argument is a `TypeError`.

    Returns a `Quantity` (fraction, 0-1) or a `Refusal`.
    """
    unusable = _calibration_unusable(calibration)
    if unusable is not None:
        return unusable

    if d_ft is None:
        return Refusal(
            reason="transmitter-receiver spacing was not supplied; the source states "
                   "d as an input to the attenuation ('d = distance between the "
                   "transmitter and receiver on the tool'), and a 3 ft and a 5 ft "
                   "tool do not give the same attenuation from the same amplitudes",
            needed=("the tool's T-R spacing in feet, from the log header or the "
                    "service-company tool sheet",),
            source=DRILLINGMANUAL,
        )
    if d_ft <= 0:
        raise ValueError(f"transmitter-receiver spacing must be positive, got {d_ft}")

    measured_amplitude = _unwrap(measured_amplitude)
    if measured_amplitude < 0:
        raise ValueError(f"amplitude cannot be negative, got {measured_amplitude}")

    free_pipe, free_pipe_field = _cal_get(calibration, "free_pipe_amplitude")
    bonded, bonded_field = _cal_get(calibration, "fully_bonded_amplitude")

    if bonded is None:
        # R3 first: the BI=1 anchor is the one operators most often lack.
        return Refusal(
            reason="calibration carries no 100%-bonded (BI=1) amplitude anchor; it "
                   "is the denominator of the bond index. Interpretation 'requires "
                   "correct knowledge of the amplitude of 100% cemented sheath and "
                   "of free pipe'",
            needed=(f"one of {CALIBRATION_FIELDS['fully_bonded_amplitude']} on the "
                    "cbl_calibration result",),
            source=DRILLINGMANUAL,
        )
    if free_pipe is None:
        return Refusal(
            reason="calibration carries no free-pipe (BI=0) amplitude anchor; it is "
                   "the reference both attenuations are measured against",
            needed=(f"one of {CALIBRATION_FIELDS['free_pipe_amplitude']} on the "
                    "cbl_calibration result",),
            source=DRILLINGMANUAL,
        )

    free_pipe = float(free_pipe)
    bonded = float(bonded)
    if free_pipe <= 0 or bonded <= 0:
        return Refusal(
            reason=f"calibration amplitudes must be positive; got free pipe "
                   f"{free_pipe:g}, 100%-bonded {bonded:g}",
            needed=("a re-run of cbl_calibration (#102) against real anchor "
                    "intervals",),
            source=DRILLINGMANUAL,
        )
    if bonded >= free_pipe:
        return Refusal(
            reason=f"100%-bonded anchor {bonded:g} is not below the free-pipe anchor "
                   f"{free_pipe:g}; a fully cemented sheath must attenuate more than "
                   "free pipe, so this calibration gives a zero or negative "
                   "denominator (A_c <= 0)",
            needed=("a 100%-bonded amplitude picked in a genuinely fully cemented "
                    "interval, below the free-pipe amplitude",),
            source=DRILLINGMANUAL,
        )

    spacing_refusal, flags, cal_spacing = _spacing_refusal(calibration, d_ft)
    if spacing_refusal is not None:
        return spacing_refusal

    a_m = cbl_attenuation(measured_amplitude, free_pipe, d_ft)
    if isinstance(a_m, Refusal):
        return a_m
    a_c = cbl_attenuation(bonded, free_pipe, d_ft)
    if isinstance(a_c, Refusal):
        return a_c

    bi = a_m.value / a_c.value

    assumptions = {
        "log_base": ATTENUATION_LOG_BASE,
        "attenuation_prefix": ATTENUATION_DB_PREFIX,
        "sign_convention": "negative prefix (DRILLINGMANUAL, USPTO 10392920); "
                           "cancels inside this ratio, not in a reported dB/ft",
        "bond_index_is_circumferential_fraction": True,
        "corroborated_by": (USPTO_10392920, USPTO_11466558),
        "calibration_fields_read": {"free_pipe": free_pipe_field,
                                    "fully_bonded": bonded_field},
        "calibration_tr_spacing_ft": cal_spacing,
    }
    assumptions.update(_cal_provenance(calibration))

    return _bond_index_result(
        bi,
        inputs={"measured_amplitude": measured_amplitude,
                "free_pipe_amplitude": free_pipe,
                "fully_bonded_amplitude": bonded,
                "d_ft": d_ft,
                "A_m_db_per_ft": a_m.value,
                "A_c_db_per_ft": a_c.value},
        assumptions=assumptions,
        flags=flags,
        method="bond index BI = A_m/A_c from casing amplitudes",
        source=DRILLINGMANUAL,
    )


def cbl_bond_index_from_attenuation(measured_attenuation_db_per_ft: float,
                                    calibration: Any,
                                    d_ft: float | None = None):
    """Bond index when the tool logs an attenuation (dB/ft) curve directly.

    `BI = (A_m - A_freepipe) / (A_100%bond - A_freepipe)` — USPTO_11466558 p. 17,
    the general form. Where the calibration reports no free-pipe attenuation the
    rates are taken as already referenced to free pipe (`A_freepipe = 0`), which
    reduces it to the drilling manual's `A_m/A_c`; that assumption is flagged.

    `d_ft` is optional here — a dB/**ft** rate is already spacing-normalised — and
    is used only to cross-check the calibration's spacing.
    """
    unusable = _calibration_unusable(calibration)
    if unusable is not None:
        return unusable

    measured = float(_unwrap(measured_attenuation_db_per_ft))

    bonded_att, bonded_field = _cal_get(calibration, "fully_bonded_attenuation_db_per_ft")
    if bonded_att is None:
        return Refusal(
            reason="calibration carries no 100%-bonded attenuation rate; BI is 'an "
                   "attenuation rate in zone of interest [dB/ft]' divided by 'an "
                   "attenuation rate in well cemented zone [dB/ft]' and the "
                   "denominator is missing",
            needed=(f"one of {CALIBRATION_FIELDS['fully_bonded_attenuation_db_per_ft']} "
                    "on the cbl_calibration result",),
            source=USPTO_10392920,
        )
    bonded_att = float(bonded_att)

    flags: list[str] = []
    free_att, _ = _cal_get(calibration, "free_pipe_attenuation_db_per_ft")
    if free_att is None:
        free_att = 0.0
        flags.append("free-pipe attenuation taken as 0 dB/ft, i.e. the attenuation "
                     "rates are assumed already referenced to free pipe")
    else:
        free_att = float(free_att)

    if d_ft is not None:
        if d_ft <= 0:
            raise ValueError(f"transmitter-receiver spacing must be positive, got {d_ft}")
        spacing_refusal, spacing_flags, cal_spacing = _spacing_refusal(calibration, d_ft)
        if spacing_refusal is not None:
            return spacing_refusal
        flags.extend(spacing_flags)
    else:
        cal_spacing, _ = _cal_get(calibration, "tr_spacing_ft")

    denominator = bonded_att - free_att
    if denominator == 0:
        return Refusal(
            reason=f"100%-bonded attenuation {bonded_att:g} dB/ft equals the "
                   f"free-pipe attenuation {free_att:g} dB/ft; the calibration has "
                   "no dynamic range and the bond index is undefined",
            needed=("distinct free-pipe and 100%-bonded attenuation anchors",),
            source=USPTO_11466558,
        )
    if denominator < 0:
        return Refusal(
            reason=f"100%-bonded attenuation {bonded_att:g} dB/ft is below the "
                   f"free-pipe attenuation {free_att:g} dB/ft; a fully cemented "
                   "sheath must attenuate more than free pipe",
            needed=("anchors picked in a genuinely free-pipe and a genuinely "
                    "fully-cemented interval",),
            source=USPTO_11466558,
        )

    bi = (measured - free_att) / denominator

    assumptions = {
        "form": "BI = (A_m - A_freepipe)/(A_100%bond - A_freepipe)",
        "free_pipe_attenuation_db_per_ft": free_att,
        "bond_index_is_circumferential_fraction": True,
        "corroborated_by": (DRILLINGMANUAL, USPTO_10392920),
        "calibration_fields_read": {"fully_bonded_attenuation": bonded_field},
        "calibration_tr_spacing_ft": (float(cal_spacing) if cal_spacing is not None else None),
    }
    assumptions.update(_cal_provenance(calibration))

    return _bond_index_result(
        bi,
        inputs={"A_m_db_per_ft": measured,
                "A_c_db_per_ft": bonded_att,
                "A_freepipe_db_per_ft": free_att,
                "d_ft": d_ft},
        assumptions=assumptions,
        flags=flags,
        method="bond index from attenuation rates (dB-difference form)",
        source=USPTO_11466558,
    )
