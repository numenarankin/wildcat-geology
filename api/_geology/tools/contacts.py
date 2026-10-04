"""Fluid contacts: projection, standoff and column height (#21, #22, #23).

Staging file for merge into `tools/contacts.py`. Three tools that share one
subject — where a fluid contact is, how far a perforation sits from it, and how
much rock stands above it — and therefore share one datum gate and one
uncertainty algebra.

**Everything here is subsea true vertical depth, and that is enforced rather
than documented.** `_normalise_depth` accepts a `subsea_convert` (#18)
`Quantity` (unit `"ft SS"`) or a pick mapping in the shape `structural_dip`
(#20) already takes, and it **refuses a bare float**: a naked number carries no
datum, and every one of these tools is a difference of two depths, so a datum
error survives the subtraction only when both depths came through the same one.
Measured depth, an unresolved datum and two depths on different references each
refuse in `structural_dip`'s own words, naming `datum_resolve` (#15),
`md_to_tvd` (#17), `subsea_convert` (#18) and `datum_reconcile` (#16). The sign
convention — negative below sea level — is `subsea_convert`'s and is not
restated: it is read off the values it produced.

The three non-obvious decisions:

**#21 projects flat, and refuses to tilt unless told to twice.** Tearpock p. 761
states "the oil/water contact is a horizontal surface" and then *drops the
bed-dip term from a published equation* because of it, working the arithmetic
both ways on the page. No tilted-contact construction exists anywhere in this
corpus. But the catalog requires the flat assumption be explicit *and
overridable*, so a dip is honoured only when `tilt_construction` is passed the
literal token `"caller-supplied-unsourced"`. Then the result carries the flat
answer beside it, `UNSOURCED-CALLER-SUPPLIED-TILT` as its first flag, and a
sentinel `source` a provenance audit cannot mistake for a citation. A dip passed
without the token is a `Refusal`, and a dip that is a `structural_dip` result
flagged `apparent_dip` is refused outright — tilting a contact by the apparent
*bed* dip is the exact error p. 761 refutes.

**#22 is the completion-sense standoff, and it never grades.** "Standoff" is
gun-to-casing clearance in inches in the perforating literature; an automated
matcher put that homonym on this tool. This is perforation-to-contact vertical
distance in feet — Ahmed's `D_t` and `D_b` (Eqs. 9-7/9-8), which
`perf_length_optimize` (#50) already computes and `perf_standoff_check` (#58)
already checks. So it returns those two under those names and must agree with
both; `RECONCILE` records the identities and the sign reversal between #58's
downward depths and this module's subsea elevations. It returns a `Range`, not a
`Quantity`, because the contact is normally an inference from #21 and a crisp
number is something an operator perforates against. Whether the standoff is
*enough* is #58's question and the corpus supplies no threshold, so asking this
tool for a verdict raises rather than answers.

**#23 returns gross, and says so in the unit.** Tearpock p. 744 computes the
gross interval and then multiplies it by net/gross to *get* pay. A gross column
consumed as pay overstates reserves by that ratio — a factor of two in his own
example — so the unit string is `"ft gross"`, the first flag is always
`GROSS-COLUMN-NOT-NET-PAY`, and any cutoff or net/gross keyword raises naming
`net_pay_cutoffs` (#39). Top of porosity is an input, not an inference: picking
it is a petrophysical decision with its own cutoff, and a curve in that argument
raises. A negative column is returned flagged, not clipped, following
`density_porosity`'s treatment of negative porosity — "18 ft into the water leg"
and "right at the contact" lead to different completions.

Uncertainty is **interval arithmetic added linearly, never in quadrature**. No
source states a probability model, and `perf_standoff_check` already treats the
same quantity as an interval (`h_interval = column_h +/- 2u`). Two tools using
two different error algebras on one number is the reconcile failure this build
exists to catch.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field as dc_field
from typing import Any

from .result import Quantity, Range, Refusal
from .geometry import normalize_reference, offset_bearing, offset_distance

# --------------------------------------------------------------------------- #
# Corpus anchors
# --------------------------------------------------------------------------- #

_TEARPOCK = "06-fort-worth-basin/tearpock-bischke-applied-subsurface-geological-mapping"

#: Chap. 14, p. 761. THE flat-contact statement, and the anchor `tool-verification.md`
#: corrected to (it is #234, not #227).
TEARPOCK_FLAT_CONTACT = f"{_TEARPOCK}#234"

#: Chap. 14, pp. 731-737. The Wharton method: one contact elevation per reservoir,
#: traced across the structure maps. Projection by constant subsea elevation.
TEARPOCK_CONSTANT_ELEVATION = f"{_TEARPOCK}#227"

#: Chap. 14, p. 744. Gross interval = top of porosity - water level, worked at
#: -8310 / -8350 -> 40 ft, then multiplied by net/gross to reach net pay.
TEARPOCK_COLUMN = f"{_TEARPOCK}#229"

#: Chap. 4, p. 61. SSTVD, the datum vocabulary. Shared with #15/#18/#20.
TEARPOCK_DATUM = f"{_TEARPOCK}#24"

#: Chap. 3, Fig. 3-12. Fixes the direction of the number line (-9748 "adjusted
#: upward 10 ft" becomes -9738), and is also the multi-well contact-disagreement
#: case this module deliberately does not handle (spec 21, open question 1).
TEARPOCK_SIGN = f"{_TEARPOCK}#23"

#: Ahmed Ch. 9, pp. 583-584. Eqs. 9-7 / 9-8 define D_t and D_b. Reached through
#: specs 50 and 58; #22 reports these, it does not redefine them.
AHMED_CHIERICI_DEFS = "00-reference/ahmed-reservoir-engineering-handbook#120"

#: Sentinels. Not anchors — the absence of one, said out loud, so that
#: `provenance_audit` (#67) cannot read an unsourced construction as a cited one.
NO_SOURCE_TILT = "no-corpus-source:tilted-fluid-contact"
NO_SOURCE_STANDOFF = "no-corpus-source:standoff_compute"

#: The quotes the decisions rest on, kept next to the anchors so a reviewer does
#: not have to re-open the corpus to check that the tool does what the page says.
QUOTES: dict[str, str] = {
    TEARPOCK_FLAT_CONTACT: (
        "p. 761: 'A review of Fig. 14-30 shows that the oil/water contact is a "
        "horizontal surface. Therefore, we do not have to consider any bed dip "
        "correction factor... No bed dip affects the TVT of the net oil sand, "
        "since the oil/water contact is a horizontal surface'. And the italicised "
        "conclusion: 'Wherever the penetration point of a well at the top of a "
        "reservoir is above a fluid contact (in the wedge)... the dip of the beds "
        "can be considered zero'. The contact is flat even where the beds dip 20 deg."
    ),
    TEARPOCK_CONSTANT_ELEVATION: (
        "p. 732, the Wharton method's data list: '5. depth or elevation of all "
        "fluid contacts (oil/water, gas/water, oil/gas)' -- one elevation per "
        "contact -- and the construction that traces that one elevation across "
        "both the top-of-porosity and base-of-porosity structure maps."
    ),
    TEARPOCK_COLUMN: (
        "p. 744: 'calculate the gross interval thickness above the water level as "
        "the difference in depth between the top of porosity and the water level. "
        "Multiply this calculated gross interval by the net/gross ratio to "
        "estimate the net sand above the water level, which is equal to net pay'. "
        "Worked: contact -8350 ft, top of porosity -8310 ft, gross = 40 ft; "
        "net/gross 0.50 -> net pay 20 ft."
    ),
    AHMED_CHIERICI_DEFS: (
        "pp. 583-584, Eqs. 9-7 and 9-8: 'D_t is the distance from the original GOC "
        "to the top of perforations, ft'; 'D_b = distance from the original WOC to "
        "the bottom of the perforations, ft'."
    ),
}

# --------------------------------------------------------------------------- #
# Conventions. Tabled, echoed onto every result, never inline.
# --------------------------------------------------------------------------- #

#: The unit string `subsea_convert` (#18) emits. Deliberately not plain "ft", so a
#: consumer cannot mix a subsea elevation with a depth without noticing. Matched
#: exactly (after strip) rather than parsed.
SUBSEA_UNIT = "ft SS"

#: The `depth_basis` label `structural_dip` (#20) requires. Same constant name,
#: same value, same refusal.
REQUIRED_DEPTH_BASIS = "SSTVD"

#: #23's unit. The same device as "ft SS": a net-pay consumer has to read the
#: string to add this to anything.
GROSS_UNIT = "ft gross"

CONVENTIONS: dict[str, str] = {
    "depth_basis": (
        "subsea true vertical depth only. Measured depth carries hole deviation "
        "and TVD carries each well's own elevation, so neither is comparable "
        "between wells or against a mapped contact. md_to_tvd (#17) then "
        "subsea_convert (#18)."
    ),
    "depth_sign": (
        "subsea elevation, POSITIVE UPWARD, sea level = 0 -- exactly what "
        "subsea_convert returns (-9738 ft for a contact 9738 ft below sea level, "
        "tearpock#23). The shallower depth is the GREATER value."
    ),
    "contact_geometry": (
        "a fluid contact is a horizontal surface (tearpock#234, p. 761), so it "
        "projects at constant subsea elevation and its projection does not depend "
        "on distance, bearing or bed dip."
    ),
    "standoff_sense": (
        "D_t and D_b are POSITIVE when the perforations lie inside the column, "
        "NEGATIVE when they are past the contact (in the gas cap or the aquifer). "
        "Never clipped, never absolute-valued."
    ),
    "column_sense": (
        "gross column is POSITIVE when the top of porosity is above the contact "
        "and NEGATIVE when it is below it (wet). Never clipped."
    ),
    "uncertainty": (
        "interval arithmetic, half-widths added LINEARLY, not in quadrature. No "
        "source states a probability model and these are not confidence bounds. "
        "perf_standoff_check (#58) treats the same quantity the same way."
    ),
}

#: Which tool answers which question. #22 exists in the middle of these three and
#: must never offer a second answer to either neighbour's question.
RECONCILE: dict[str, str] = {
    "perf_length_optimize (#50)": (
        "where the perforations SHOULD go -- the Chierici-Ciucci optimum. Already "
        "implemented in tools/perforation.py; it emits D_t and D_b on its inputs."
    ),
    "standoff_compute (#22)": (
        "how far THESE perforations are from the contact. The measurement. Same "
        "D_t and D_b, same definitions (Ahmed Eqs. 9-7/9-8), carried with their "
        "uncertainty."
    ),
    "perf_standoff_check (#58)": (
        "whether that is far ENOUGH -- the Chierici validity bands. Already "
        "implemented. Its Quantity.value is the governing standoff and its "
        "inputs['governing_standoff_range_ft'] is the band this tool returns."
    ),
    "sign reversal": (
        "#58 works in depths increasing DOWNWARD: D_t = perf_top - goc, "
        "D_b = woc - perf_base. This module works in subsea elevation increasing "
        "UPWARD: D_t = goc - perf_top, D_b = perf_base - woc. Both give the same "
        "signed number; the subtraction reverses and a flipped D_t is invisible "
        "downstream."
    ),
    "net_pay_cutoffs (#39)": (
        "net pay. column_height (#23) returns the GROSS interval; net pay is that "
        "times the net/gross ratio (tearpock#229 p. 744). #23 will not apply a "
        "cutoff and raises if handed one."
    ),
}

#: The acknowledgement token that enables #21's unsourced tilt path. A literal
#: string rather than a boolean so that enabling it cannot be a typo or a
#: truthy default, and so it reads as an admission at the call site.
TILT_ACKNOWLEDGEMENT = "caller-supplied-unsourced"

#: Definitional ranges, not thresholds this build chose.
DIP_RANGE_DEG = (0.0, 90.0)          # 90 excluded: a vertical "contact" is not one
AZIMUTH_RANGE_DEG = (0.0, 360.0)     # same convention as md_to_tvd's

FLAG_NOTES: dict[str, str] = {
    "flat-contact-assumption": (
        "The contact was projected at CONSTANT SUBSEA ELEVATION because "
        "tearpock#234 p. 761 states a fluid contact is a horizontal surface. This "
        "is the assumption, it is sourced, and it is overridable via "
        f"tilt_construction={TILT_ACKNOWLEDGEMENT!r} -- which produces an "
        "UNSOURCED number."
    ),
    "projection-not-measurement": (
        "This contact was not observed at the target. It is an inference from "
        "another location under the flat-surface assumption, and its uncertainty "
        "is the caller's pick uncertainty plus an unquantified allowance for the "
        "assumption itself, which the corpus does not state."
    ),
    "contact-uncertainty-not-stated": (
        "No pick_uncertainty_ft was supplied, so this contact carries no "
        "uncertainty. standoff_compute (#22) will refuse on it: the catalog "
        "requires a standoff be carried with its uncertainty range."
    ),
    "same-reservoir-not-declared": (
        "The caller did not declare same_reservoir. One contact elevation belongs "
        "to one pressure-connected reservoir; tearpock#227 notes an edge-water "
        "reservoir may be 'cut by one or more faults', and a fault-separated "
        "compartment has its own contact at its own elevation."
    ),
    "UNSOURCED-CALLER-SUPPLIED-TILT": (
        "THE CONTACT WAS TILTED BY A CONSTRUCTION NO CORPUS SOURCE PUBLISHES. The "
        "only statement in this corpus about the attitude of a fluid contact is "
        "that it is horizontal (tearpock#234). The dip and its azimuth are the "
        "caller's, the plane geometry is arithmetic and not a correlation, and "
        "the flat answer is on inputs['flat_contact_sstvd_ft'] so the size of the "
        "override is visible. Do not present this number as sourced."
    ),
    "zero-dip-supplied-flat-projection-used": (
        "A contact dip of zero was supplied, which is the sourced flat projection. "
        "No override was applied and no acknowledgement was required."
    ),
    "tilt-acknowledgement-without-a-dip": (
        "tilt_construction was supplied but no contact dip was. The sourced flat "
        "projection was used."
    ),
    "grid-bearing-versus-contact-dip-azimuth": (
        "The bearing to the target came from offset_bearing (#19) and may be a "
        "GRID bearing, while the contact dip azimuth is whatever the caller "
        "measured it against. offset_bearing's own flags state which; the "
        "difference is not corrected here."
    ),
    "GROSS-COLUMN-NOT-NET-PAY": (
        "This is the GROSS interval from the top of porosity to the contact "
        "(tearpock#229 p. 744). It is NOT net pay, NOT net reservoir and NOT the "
        "producible interval. Net pay = this x net/gross; in the source's own "
        "worked example that is 0.50 x 40 ft = 20 ft, half this number. "
        "net_pay_cutoffs (#39) owns pay."
    ),
    "top-of-porosity-is-a-caller-pick": (
        "The top of porosity was supplied, not derived. Picking it is a "
        "petrophysical decision with its own porosity cutoff; this tool neither "
        "applies one nor checks the one that was used."
    ),
    "wet-or-inverted-column": (
        "The top of porosity is at or below the contact, so the gross column is "
        "zero or negative: this point is in the water leg. Returned rather than "
        "clipped, as density_porosity returns negative porosity rather than "
        "hiding an anhydrite signal. It is Tearpock's zero line (#227) and "
        "everything down-dip of it."
    ),
    "contact-is-a-projection-not-a-measurement": (
        "The contact came from contact_project (#21) and was inferred, not "
        "observed at this location."
    ),
    "contact-below-base-of-porosity-full-thickness-area": (
        "The contact lies below the base of porosity, so this point is in "
        "tearpock#227's FULL THICKNESS AREA, where the reservoir is hydrocarbon "
        "filled from top to base of porosity and the hydrocarbon interval is "
        "capped by the base, not by the contact. The top-to-base interval is on "
        "inputs['top_to_base_of_porosity_ft']. The value is NOT clamped: #229's "
        "equation is printed without a base term and clamping it would be an "
        "unsourced modification."
    ),
    "column-uncertainty-not-stated": (
        "Neither depth carried an uncertainty, so no range accompanies this "
        "column."
    ),
    "point-perforation": (
        "No perf_base was supplied, so the standoff was measured from a single "
        "depth to both contacts. The perforated length is zero, which is not a "
        "completion; supply perf_base for the interval geometry Ahmed's Eqs. "
        "9-7/9-8 assume."
    ),
    "perforations-past-a-contact": (
        "At least one standoff is negative: the perforations lie beyond that "
        "contact, in the gas cap or in the aquifer. Returned signed and not "
        "clipped, because that is the finding."
    ),
    "standoff-is-not-graded": (
        "This tool does not say whether the standoff is enough. The corpus states "
        "no minimum standoff anywhere; Ahmed's 0.07-0.9 delta bands are the "
        "validity limits of the Chierici graphical correlation, not a safety "
        "margin, and applying them needs h, k_h, k_v and r_e. "
        "perf_standoff_check (#58) owns the verdict."
    ),
}

# --------------------------------------------------------------------------- #
# The datum gate. One implementation for all three tools, in structural_dip's
# vocabulary, so an operator sees one wording across the structural spine.
# --------------------------------------------------------------------------- #

_PICK_FIELDS = ("sstvd_ft", "depth_basis", "datum_resolved", "depth_reference")

_UNCERTAINTY_KEYS = ("uncertainty_ft", "pick_uncertainty_ft", "contact_uncertainty_ft")


@dataclass(frozen=True)
class _Depth:
    """One depth that has passed the datum gate."""

    sstvd_ft: float
    label: str
    reference: str | None           # normalised key (KB / GL / DF / TKB / ...)
    reference_raw: str
    provenance: str
    uncertainty_ft: float | None = None
    contact_type: str = ""
    inherited_flags: tuple[str, ...] = ()
    inherited_assumptions: dict[str, Any] = dc_field(default_factory=dict)


def _refuse_not_subsea(label: str, detail: str) -> Refusal:
    """The one refusal every tool in this module shares. Wording tracks #20."""
    return Refusal(
        reason=(
            f"{label}: {detail}. These tools compute on subsea true vertical "
            "depths. Measured depth carries hole deviation and TVD carries the "
            "well's own elevation, so neither is comparable between wells or "
            "against a mapped fluid contact"
        ),
        needed=(
            "md_to_tvd (#17) to convert measured depth to TVD",
            "subsea_convert (#18) to hang TVD on sea level",
            f'a subsea_convert Quantity (unit "{SUBSEA_UNIT}"), or a mapping with '
            f'{", ".join(_PICK_FIELDS)} and depth_basis == "{REQUIRED_DEPTH_BASIS}"',
        ),
        source=TEARPOCK_DATUM,
    )


def _propagate(refusal: Refusal, label: str) -> Refusal:
    return Refusal(
        reason=f"{label} is unavailable upstream: {refusal.reason}",
        needed=tuple(refusal.needed),
        source=refusal.source or TEARPOCK_DATUM,
    )


def _finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    out = float(value)
    return out if math.isfinite(out) else None


def _first(container: Mapping[str, Any] | None, keys: Sequence[str]) -> Any:
    if not isinstance(container, Mapping):
        return None
    for key in keys:
        if key in container and container[key] is not None:
            return container[key]
    return None


def _normalise_depth(value: Any, label: str) -> _Depth | Refusal:
    """Accept a #18/#21 `Quantity`, a pick mapping, or a `Refusal`. Nothing else.

    A bare float refuses. That is the whole gate: every tool here is a difference
    of two depths, so a datum error cancels only when both depths came through
    the same datum, and a naked number cannot say whether it did.
    """
    if isinstance(value, Refusal):
        return _propagate(value, label)

    if isinstance(value, Range):
        return Refusal(
            reason=(
                f"{label} was given as a Range ({value.low:g} to {value.high:g} "
                f"{value.unit}); a band is not a depth. Pass the depth and state "
                "its uncertainty in the uncertainty argument, which is where these "
                "tools carry it"
            ),
            needed=(f"a single subsea depth for {label}",
                    "its uncertainty as the matching *_uncertainty_ft argument"),
            source=TEARPOCK_DATUM,
        )

    if isinstance(value, Quantity):
        unit = str(value.unit or "").strip()
        if unit != SUBSEA_UNIT:
            return _refuse_not_subsea(
                label,
                f'was given a Quantity in "{unit}", not "{SUBSEA_UNIT}"',
            )
        sstvd = _finite(value.value)
        if sstvd is None:
            return _refuse_not_subsea(label, f"elevation {value.value!r} is not finite")
        resolved = _first(value.inputs, ("datum_resolved",))
        if resolved is not None and not resolved:
            return Refusal(
                reason=(f"{label} carries datum_resolved=False; subsea depth is the "
                        "gate everything structural depends on, and an unresolved "
                        "datum makes this arithmetic on two different zeros"),
                needed=("datum_resolve (#15): KB, GL, DF or TKB elevation and which "
                        "reference the depths are hung on",),
                source=TEARPOCK_DATUM,
            )
        raw = _first(value.inputs, ("reference", "depth_reference"))
        return _Depth(
            sstvd_ft=sstvd,
            label=label,
            reference=normalize_reference(raw),
            reference_raw="" if raw is None else str(raw),
            provenance=f"{value.method} [{value.source}]",
            uncertainty_ft=_finite(_first(value.inputs, _UNCERTAINTY_KEYS)),
            contact_type=str(_first(value.inputs, ("contact_type",)) or ""),
            inherited_flags=tuple(value.flags),
            inherited_assumptions=dict(value.assumptions),
        )

    if isinstance(value, Mapping):
        missing = [f for f in _PICK_FIELDS if f not in value]
        if missing:
            return Refusal(
                reason=(f"{label} is missing {', '.join(missing)}; a depth cannot be "
                        "used structurally until it says what it is measured from "
                        "and whether that was resolved"),
                needed=tuple(missing),
                source=TEARPOCK_DATUM,
            )
        basis = str(value["depth_basis"]).strip().upper()
        if basis != REQUIRED_DEPTH_BASIS.upper():
            return _refuse_not_subsea(label, f"depth_basis is {value['depth_basis']!r}")
        if not value["datum_resolved"]:
            return Refusal(
                reason=(f"{label} has datum_resolved=False; subsea depth is the gate "
                        "everything structural depends on, and an unresolved datum "
                        "makes this arithmetic on two different zeros"),
                needed=("datum_resolve (#15): KB, GL, DF or TKB elevation and which "
                        "reference the depths are hung on",),
                source=TEARPOCK_DATUM,
            )
        sstvd = _finite(value["sstvd_ft"])
        if sstvd is None:
            return _refuse_not_subsea(
                label, f"sstvd_ft {value['sstvd_ft']!r} is not a finite number")
        raw = value["depth_reference"]
        return _Depth(
            sstvd_ft=sstvd,
            label=label,
            reference=normalize_reference(raw),
            reference_raw="" if raw is None else str(raw),
            provenance=str(value.get("provenance") or "caller-supplied pick mapping"),
            uncertainty_ft=_finite(_first(value, _UNCERTAINTY_KEYS)),
            contact_type=str(value.get("contact_type") or ""),
        )

    if isinstance(value, bool) or isinstance(value, (int, float)):
        return _refuse_not_subsea(
            label,
            f"was given the bare number {value!r}, which carries no datum. It will "
            "not be assumed to be subsea: a wrong datum survives the subtraction "
            "these tools do and the answer looks right",
        )

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        raise ValueError(
            f"{label} must be a single pick, not a curve or a list of depths "
            f"(got {type(value).__name__} of length {len(value)}). Picking a depth "
            "from a curve is a petrophysical decision with its own cutoff and "
            "belongs to the caller; net_pay_cutoffs (#39) owns cutoffs."
        )

    raise TypeError(
        f"{label} must be a subsea_convert (#18) Quantity, a pick mapping with "
        f"{_PICK_FIELDS}, or a Refusal; got {type(value).__name__}"
    )


def _one_reference(depths: Sequence[_Depth]) -> Refusal | None:
    """Refuse two depths hung on different references. `structural_dip`'s gate."""
    seen: dict[str, list[str]] = {}
    for d in depths:
        key = d.reference or f"unrecognised:{d.reference_raw}"
        seen.setdefault(key, []).append(d.label)
    if len(seen) <= 1:
        return None
    detail = "; ".join(f"{', '.join(labels)} on {key}" for key, labels in sorted(seen.items()))
    return Refusal(
        reason=(
            f"the depths are hung on different references ({detail}); a KB-versus-GL "
            "mix is a constant elevation offset that reads here as structure. On "
            "sky-heighten-1 (EKB 1139.5, EGL 1129.0) that mix is 10.5 ft, a quarter "
            "of Tearpock's 40 ft worked column"
        ),
        needed=("datum_reconcile (#16) to confirm one reference and return the "
                "correction if there is not",),
        source=TEARPOCK_DATUM,
    )


def _check_uncertainty(name: str, value: Any) -> float | None:
    """Validate an uncertainty argument. Negative is programmer error."""
    if value is None:
        return None
    number = _finite(value)
    if number is None:
        raise ValueError(f"{name} must be a finite number of feet; got {value!r}")
    if number < 0:
        raise ValueError(f"{name} must not be negative; got {number!r}")
    return number


def _reject(kwargs: Mapping[str, Any], table: Mapping[str, str], tool: str) -> None:
    """Raise on a keyword that asks this tool to be a different tool."""
    if not kwargs:
        return
    for name in sorted(kwargs):
        for pattern, message in table.items():
            if pattern in name.lower():
                raise ValueError(f"{tool} does not accept {name!r}: {message}")
    raise ValueError(
        f"{tool} got unexpected keyword argument(s) {', '.join(sorted(kwargs))}")


# --------------------------------------------------------------------------- #
# 21_contact_project
# Project a fluid contact to another location. Flat, because the source says so.
# --------------------------------------------------------------------------- #


def _dip_value(supplied: Any) -> float | Refusal | None:
    """Read a contact dip. Refuses an apparent bed dip; raises on nonsense."""
    if supplied is None:
        return None
    if isinstance(supplied, Refusal):
        return _propagate(supplied, "contact_dip_deg")
    if isinstance(supplied, Quantity):
        if "apparent_dip" in supplied.flags:
            return Refusal(
                reason=(
                    "the contact dip supplied is an APPARENT dip from structural_dip "
                    f"(#20): {supplied.value:g} deg along one bearing. That is a "
                    "lower bound on the dip of the BEDS, and tearpock#234 p. 761 is "
                    "explicit that bed dip does not apply to a fluid contact -- 'No "
                    "bed dip affects the TVT of the net oil sand, since the "
                    "oil/water contact is a horizontal surface'. Tilting a contact "
                    "by an apparent bed dip is wrong twice over"
                ),
                needed=("a measured attitude of the CONTACT itself, not of the beds",
                        "or omit the dip and take the sourced flat projection",),
                source=TEARPOCK_FLAT_CONTACT,
            )
        number = _finite(supplied.value)
        if number is None:
            raise ValueError(f"contact_dip_deg Quantity value {supplied.value!r} is not finite")
        return number
    number = _finite(supplied)
    if number is None:
        raise ValueError(
            f"contact_dip_deg must be a number of degrees or a Quantity; got {supplied!r}")
    return number


def contact_project(
    observed_contact: Any,
    *,
    contact_type: str,
    observed_at: str = "",
    target_well: str = "",
    same_reservoir: bool | None = None,
    pick_uncertainty_ft: float | None = None,
    reference_location: Any = None,
    target_location: Any = None,
    contact_dip_deg: Any = None,
    contact_dip_azimuth_deg: float | None = None,
    tilt_construction: str | None = None,
) -> Quantity | Refusal:
    """Project a fluid contact from one wellbore to another (#21).

    A fluid contact is a horizontal surface (tearpock#234, p. 761), so the
    projection is at **constant subsea elevation** and the returned value equals
    the observed one. The tool's work is the datum gate, making the flat
    assumption visible on the result, and refusing to tilt.

    `observed_contact` is a `subsea_convert` (#18) `Quantity`, a pick mapping
    (`sstvd_ft` / `depth_basis` / `datum_resolved` / `depth_reference`), or a
    `Refusal`. A bare float refuses.

    A `contact_dip_deg` is honoured only alongside
    ``tilt_construction="caller-supplied-unsourced"``; without it the tool
    refuses, because no tilted-contact construction exists in this corpus. With
    it, the result is flagged UNSOURCED, carries the flat answer beside it, and
    its `source` is a sentinel rather than an anchor.

    Returns a `Quantity` in `"ft SS"`, or a `Refusal`.
    """
    label = f"the contact observed at {observed_at}" if observed_at else "the observed contact"

    if not isinstance(contact_type, str) or not contact_type.strip():
        return Refusal(
            reason=("the contact was not named; a GOC and a WOC bound the column from "
                    "opposite ends and mislabelling one inverts every standoff "
                    "computed from it"),
            needed=('contact_type, e.g. "OWC", "GWC" or "GOC"',),
            source=TEARPOCK_CONSTANT_ELEVATION,
        )

    depth = _normalise_depth(observed_contact, label)
    if isinstance(depth, Refusal):
        return depth

    if same_reservoir is False:
        return Refusal(
            reason=(
                f"{observed_at or 'the observing well'} and "
                f"{target_well or 'the target'} are declared NOT to share a "
                "reservoir. One contact elevation belongs to one pressure-connected "
                "reservoir; tearpock#227 notes an edge-water reservoir may be 'cut "
                "by one or more faults', and a fault-separated compartment has its "
                "own contact at its own elevation. Projecting across the fault "
                "would report the other compartment's contact as this one's"
            ),
            needed=("a contact observed in the target's own compartment",
                    "or pressure_system_compare (#45) evidence that the two are "
                    "connected, then same_reservoir=True",),
            source=TEARPOCK_CONSTANT_ELEVATION,
        )

    uncertainty = _check_uncertainty("pick_uncertainty_ft", pick_uncertainty_ft)
    if uncertainty is None:
        uncertainty = depth.uncertainty_ft

    dip = _dip_value(contact_dip_deg)
    if isinstance(dip, Refusal):
        return dip

    flags: list[str] = []
    inputs: dict[str, Any] = {
        "observed_contact_sstvd_ft": depth.sstvd_ft,
        "contact_type": contact_type.strip(),
        "observed_at": observed_at,
        "target_well": target_well,
        "reference": depth.reference,
        "depth_reference": depth.reference,
        "depth_reference_as_stated": depth.reference_raw,
        "datum_resolved": True,
        "uncertainty_ft": uncertainty,
        "observed_contact_provenance": depth.provenance,
    }
    assumptions: dict[str, Any] = {
        "depth_basis": REQUIRED_DEPTH_BASIS,
        "sign": "negative below sea level",
        "same_reservoir": same_reservoir,
        "flat_contact_is_overridable": (
            f"yes, with tilt_construction={TILT_ACKNOWLEDGEMENT!r} -- which returns "
            "an UNSOURCED number"),
        "conventions": dict(CONVENTIONS),
        "corroborating_source": TEARPOCK_CONSTANT_ELEVATION,
        "source_quote": QUOTES[TEARPOCK_FLAT_CONTACT],
    }

    tilt_requested = dip is not None and dip != 0.0

    # --- the sourced flat projection ---------------------------------------
    if not tilt_requested:
        if dip == 0.0:
            flags.append("zero-dip-supplied-flat-projection-used")
        if tilt_construction is not None and dip is None:
            flags.append("tilt-acknowledgement-without-a-dip")
        flags.append("flat-contact-assumption")
        flags.append("projection-not-measurement")
        if uncertainty is None:
            flags.append("contact-uncertainty-not-stated")
        if same_reservoir is None:
            flags.append("same-reservoir-not-declared")

        # Distance is recorded when it is available and is NOT used. That it does
        # not enter the answer is the sourced behaviour, and having the number on
        # the result makes that checkable rather than assertable.
        if reference_location is not None and target_location is not None:
            distance = offset_distance(reference_location, target_location, distance_unit="ft")
            inputs["run_ft"] = distance.value if isinstance(distance, Quantity) else None
            inputs["run_unavailable_because"] = (
                distance.reason if isinstance(distance, Refusal) else None)
        inputs["projection_changed_the_elevation_by_ft"] = 0.0

        assumptions["contact_geometry"] = "horizontal surface (tearpock#234, p. 761)"
        assumptions["projection_rule"] = (
            "constant subsea elevation; independent of distance, bearing and bed dip")
        assumptions["flag_notes"] = {f: FLAG_NOTES[f] for f in flags}
        return Quantity(
            depth.sstvd_ft, SUBSEA_UNIT,
            "fluid contact projected at constant subsea elevation -- a fluid contact "
            "is a horizontal surface (Tearpock p. 761), so no bed-dip correction "
            "applies and the projected elevation equals the observed one",
            TEARPOCK_FLAT_CONTACT,
            inputs=inputs, assumptions=assumptions, flags=tuple(flags),
        )

    # --- the override ------------------------------------------------------
    if tilt_construction != TILT_ACKNOWLEDGEMENT:
        return Refusal(
            reason=(
                f"a contact dip of {dip:g} deg was supplied, but NO TILTED-CONTACT "
                "CONSTRUCTION EXISTS IN THIS CORPUS. The only statement it makes "
                "about the attitude of a fluid contact is that it is a HORIZONTAL "
                "SURFACE (tearpock#234, p. 761), and Tearpock drops the bed-dip term "
                "from a published equation because of it -- 115 ft x cos 30 deg = "
                "100 ft of oil, with the 20 deg bed dip deliberately ignored. "
                "Projecting at a dip anyway would return a precise, unsourced number "
                "that looks exactly like the sourced one"
            ),
            needed=(
                "omit the dip and take the sourced flat projection (tearpock#234)",
                "or a corpus source publishing a tilted / hydrodynamic fluid-contact "
                "construction",
                f"or, to proceed on your own authority, "
                f"tilt_construction={TILT_ACKNOWLEDGEMENT!r} -- the result is then "
                "flagged UNSOURCED and carries the flat answer beside it",
            ),
            source=TEARPOCK_FLAT_CONTACT,
        )

    lo, hi = DIP_RANGE_DEG
    if not lo <= dip < hi:
        return Refusal(
            reason=(f"contact dip {dip:g} deg is outside {lo:g}-{hi:g} deg; that is "
                    "not a dip, and at 90 deg the surface is vertical and projects "
                    "nowhere"),
            needed=(f"a dip in [{lo:g}, {hi:g}) degrees from horizontal",),
            source=NO_SOURCE_TILT,
        )

    azimuth = _finite(contact_dip_azimuth_deg)
    if azimuth is None:
        return Refusal(
            reason=("a contact dip was supplied without contact_dip_azimuth_deg, so "
                    "there is no down-dip direction and the projection is undefined. "
                    "This is the CONTACT's azimuth and is never taken from the beds"),
            needed=("contact_dip_azimuth_deg: the down-dip azimuth of the contact "
                    "surface, degrees clockwise from north",),
            source=NO_SOURCE_TILT,
        )
    lo, hi = AZIMUTH_RANGE_DEG
    if not lo <= azimuth <= hi:
        return Refusal(
            reason=(f"contact dip azimuth {azimuth:g} deg is outside {lo:g}-{hi:g}; an "
                    "azimuth written on a -180/+180 convention must be normalised by "
                    "the caller, visibly, not silently here"),
            needed=("a dip azimuth as a compass bearing, 0-360 deg",),
            source=NO_SOURCE_TILT,
        )

    if reference_location is None or target_location is None:
        return Refusal(
            reason=("a tilted projection needs the horizontal separation between the "
                    "observing well and the target, and one or both locations were "
                    "not supplied. The flat projection needs neither, which is the "
                    "point of it"),
            needed=("reference_location and target_location for offset_geometry (#19)",
                    "or omit the dip and take the sourced flat projection",),
            source=NO_SOURCE_TILT,
        )

    distance = offset_distance(reference_location, target_location, distance_unit="ft")
    if isinstance(distance, Refusal):
        return _propagate(distance, "the separation between the two locations")
    bearing = offset_bearing(reference_location, target_location)
    if isinstance(bearing, Refusal):
        return _propagate(bearing, "the bearing to the target")

    run_ft = float(distance.value)
    bearing_deg = float(bearing.value)
    # The component of the separation that lies down-dip. A target along strike
    # has none, and its contact is at the observed elevation whatever the dip.
    run_along_dip_ft = run_ft * math.cos(math.radians(bearing_deg - azimuth))
    delta_ft = -(run_along_dip_ft * math.tan(math.radians(dip)))
    projected = depth.sstvd_ft + delta_ft

    flags.append("UNSOURCED-CALLER-SUPPLIED-TILT")
    flags.append("projection-not-measurement")
    flags.append("grid-bearing-versus-contact-dip-azimuth")
    if uncertainty is None:
        flags.append("contact-uncertainty-not-stated")
    if same_reservoir is None:
        flags.append("same-reservoir-not-declared")

    inputs.update({
        "flat_contact_sstvd_ft": depth.sstvd_ft,
        "run_ft": run_ft,
        "bearing_deg": bearing_deg,
        "dip_deg": dip,
        "dip_azimuth_deg": azimuth,
        "run_along_dip_ft": run_along_dip_ft,
        "delta_ft": delta_ft,
        "projection_changed_the_elevation_by_ft": delta_ft,
        "distance_provenance": f"{distance.method} [{distance.source}]",
        "bearing_provenance": f"{bearing.method} [{bearing.source}]",
        "bearing_flags": tuple(bearing.flags),
    })
    assumptions.update({
        "contact_geometry": (
            f"CALLER-SUPPLIED PLANE: {dip:g} deg dipping toward {azimuth:g} deg. "
            "UNSOURCED -- the corpus says a fluid contact is horizontal"),
        "projection_rule": (
            "delta = -(run x cos(bearing - dip_azimuth) x tan(dip)); the geometry of "
            "a plane through the observed point, which is arithmetic and not a "
            "corpus correlation. What is unsourced is the claim that a fluid "
            "contact has an attitude at all"),
        "flat_answer_would_have_been_ft_ss": depth.sstvd_ft,
        "override_cost_ft": delta_ft,
    })
    assumptions["flag_notes"] = {f: FLAG_NOTES[f] for f in flags}

    return Quantity(
        projected, SUBSEA_UNIT,
        f"CALLER-SUPPLIED TILTED projection: contact carried {delta_ft:+.4f} ft from "
        f"the observed {depth.sstvd_ft:g} ft SS on a {dip:g} deg plane dipping toward "
        f"{azimuth:g} deg. NO CORPUS SOURCE PUBLISHES A TILTED FLUID CONTACT; the "
        f"sourced flat answer is {depth.sstvd_ft:g} ft SS",
        NO_SOURCE_TILT,
        inputs=inputs, assumptions=assumptions, flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# 22_standoff_compute
# Perforation-to-contact vertical distance. Ahmed's D_t and D_b, with their band.
# --------------------------------------------------------------------------- #

_STANDOFF_REJECT: dict[str, str] = {
    "threshold": ("this tool does not grade a standoff. The corpus states no minimum "
                  "standoff anywhere; perf_standoff_check (#58) owns the verdict and "
                  "checks Ahmed's delta bands, which need h, k_h, k_v and r_e"),
    "min_standoff": ("this tool does not grade a standoff -- perf_standoff_check "
                     "(#58) does"),
    "grade": "perf_standoff_check (#58) owns the verdict; this tool measures",
    "verdict": "perf_standoff_check (#58) owns the verdict; this tool measures",
    "pass": "perf_standoff_check (#58) owns the verdict; this tool measures",
    "optim": ("where the perforations SHOULD go is perf_length_optimize (#50), the "
              "Chierici-Ciucci optimum; this tool measures where they ARE"),
    "chart": "chart readings belong to perf_length_optimize (#50)",
    "h_p": ("the perforated length is derived here from perf_top and perf_base; "
            "perf_length_optimize (#50) is the tool that chooses one"),
}

# The two contacts Ahmed's Eqs. 9-7 / 9-8 actually name, per slot. Anything else
# in a slot -- a gas-water contact above all, which this basin has and which the
# spec's Inputs table admits into EITHER slot -- is Ahmed's geometry measured to a
# contact his system does not contain, and says so rather than being renamed.
_AHMED_SLOT_CONTACTS: dict[str, tuple[frozenset[str], str, str, str]] = {
    "goc": (frozenset({"GOC", "GASOIL", "GAS-OIL", "GAS/OIL"}),
            "D_t", "9-7", "original GOC to the top of perforations"),
    "woc": (frozenset({"WOC", "OWC", "WATEROIL", "WATER-OIL", "WATER/OIL",
                       "OILWATER", "OIL-WATER", "OIL/WATER"}),
            "D_b", "9-8", "original WOC to the bottom of the perforations"),
}


def standoff_compute(
    perf_top: Any,
    perf_base: Any = None,
    *,
    goc: Any = None,
    woc: Any = None,
    contact_uncertainty_ft: float | None = None,
    perf_depth_uncertainty_ft: float = 0.0,
    **unsupported: Any,
) -> Range | Refusal:
    """Vertical distance from a proposed perforation to a fluid contact (#22).

    **The completion-sense standoff, in feet** -- Ahmed's `D_t` (GOC to top of
    perforations) and `D_b` (base of perforations to WOC), Eqs. 9-7/9-8, the same
    quantity `perf_length_optimize` (#50) computes and `perf_standoff_check` (#58)
    checks. NOT the perforating literature's gun-to-casing clearance, which is a
    sub-inch mechanical homonym and is a different physical quantity.

    Returns a **`Range`**, because the contact is normally a projection from
    `contact_project` (#21) rather than an observation, and the catalog requires
    the standoff be carried with its uncertainty. The point value is
    `members["standoff_ft"]`. `contact_uncertainty_ft` has no default: it is read
    off a #21 result when that carries one, and refused when neither supplies it.
    An explicit `0.0` is accepted and gives a zero-width band.

    It does **not** say whether the standoff is enough -- no source states a
    minimum, and `perf_standoff_check` (#58) owns that question.
    """
    _reject(unsupported, _STANDOFF_REJECT, "standoff_compute (#22)")

    u_perf = _check_uncertainty("perf_depth_uncertainty_ft", perf_depth_uncertainty_ft) or 0.0
    u_contact_arg = _check_uncertainty("contact_uncertainty_ft", contact_uncertainty_ft)

    top = _normalise_depth(perf_top, "the top of the proposed perforations")
    if isinstance(top, Refusal):
        return top
    if perf_base is None:
        base = top
        point_perforation = True
    else:
        base = _normalise_depth(perf_base, "the base of the proposed perforations")
        if isinstance(base, Refusal):
            return base
        point_perforation = False

    contacts: dict[str, _Depth] = {}
    for name, supplied in (("goc", goc), ("woc", woc)):
        if supplied is None:
            continue
        got = _normalise_depth(supplied, f"the {name.upper()}")
        if isinstance(got, Refusal):
            return got
        contacts[name] = got

    if not contacts:
        return Refusal(
            reason=("no fluid contact supplied, so there is nothing to stand off from. "
                    "This tool measures the vertical distance from a perforation to a "
                    "projected or observed contact"),
            needed=("goc and/or woc, from contact_project (#21)",),
            source=AHMED_CHIERICI_DEFS,
        )

    records = [top] + ([] if point_perforation else [base]) + list(contacts.values())
    clash = _one_reference(records)
    if clash is not None:
        return clash

    if top.sstvd_ft < base.sstvd_ft:
        raise ValueError(
            f"perf_top ({top.sstvd_ft:g} ft SS) is below perf_base "
            f"({base.sstvd_ft:g} ft SS). Subsea elevation is POSITIVE UPWARD, so the "
            "top of an interval is the GREATER value; these look reversed, or a raw "
            "TVD was passed as a subsea elevation"
        )

    goc_d = contacts.get("goc")
    woc_d = contacts.get("woc")
    if goc_d is not None and woc_d is not None and goc_d.sstvd_ft <= woc_d.sstvd_ft:
        return Refusal(
            reason=(f"the contacts are not ordered gas above water (GOC "
                    f"{goc_d.sstvd_ft:g} ft SS, WOC {woc_d.sstvd_ft:g} ft SS); on the "
                    "positive-upward convention the GOC must be the greater value, "
                    "and the oil column between them is undefined as given"),
            needed=("a GOC above the WOC in subsea elevation",
                    "or contact_project (#21) re-run with the contacts not swapped",),
            source=AHMED_CHIERICI_DEFS,
        )

    # The uncertainty. Caller's argument wins; otherwise it comes off the #21
    # results, taking the widest when the two contacts disagree, because taking
    # the narrower would be choosing the more flattering of two stated facts.
    stated = [d.uncertainty_ft for d in contacts.values() if d.uncertainty_ft is not None]
    if u_contact_arg is not None:
        u_contact = u_contact_arg
        u_origin = "caller-supplied contact_uncertainty_ft"
    elif len(stated) == len(contacts):
        u_contact = max(stated)
        u_origin = "read from the contact_project (#21) results (widest of them)"
    else:
        return Refusal(
            reason=(
                "the contact carries no uncertainty and none was supplied. A contact "
                "from contact_project (#21) is an INFERENCE -- projected from another "
                "wellbore on the flat-surface assumption -- and tool-catalog.md "
                "specifies this standoff as 'carried with its uncertainty range'. A "
                "crisp number here is one an operator perforates against"
            ),
            needed=("contact_uncertainty_ft, in ft",
                    "or a contact_project (#21) result carrying pick_uncertainty_ft",
                    "or an explicit contact_uncertainty_ft=0.0 to state that the "
                    "contact was logged in this wellbore",),
            source=NO_SOURCE_STANDOFF,
        )

    d_t = None if goc_d is None else goc_d.sstvd_ft - top.sstvd_ft
    d_b = None if woc_d is None else base.sstvd_ft - woc_d.sstvd_ft
    available = [v for v in (d_t, d_b) if v is not None]
    standoff = min(available)
    governing_slot = "goc" if standoff == d_t else "woc"
    governing = "D_t (gas side, GOC to the top of perforations)" if standoff == d_t else \
                "D_b (water side, base of perforations to WOC)"

    # The contact's declared NAME travels onto the result. contact_project (#21)
    # refuses an unnamed contact because "mislabelling one inverts every standoff
    # computed from it", and column_height (#23) already carries the label onto
    # its own result. The slot cannot stand in for the name: this spec's Inputs
    # table admits a gas-water contact into either slot, so a GWC reported under
    # the slot's wording alone would read to the caller as an oil-water contact.
    declared = {slot: contacts[slot].contact_type.strip()
                for slot in ("goc", "woc")
                if slot in contacts and contacts[slot].contact_type.strip()}
    off_model = {slot: name for slot, name in declared.items()
                 if name.upper().replace(" ", "") not in _AHMED_SLOT_CONTACTS[slot][0]}
    if governing_slot in declared:
        governing += f", the contact the caller declared a {declared[governing_slot]}"

    half_width = u_contact + u_perf
    perf_length = top.sstvd_ft - base.sstvd_ft

    members: dict[str, float] = {
        "standoff_ft": standoff,
        "uncertainty_ft": half_width,
        "contact_uncertainty_ft": u_contact,
        "perf_depth_uncertainty_ft": u_perf,
        "perf_top_sstvd_ft": top.sstvd_ft,
        "perf_base_sstvd_ft": base.sstvd_ft,
        "perf_length_ft": perf_length,
    }
    if d_t is not None:
        members["d_t_ft"] = d_t
        members["goc_sstvd_ft"] = goc_d.sstvd_ft
    if d_b is not None:
        members["d_b_ft"] = d_b
        members["woc_sstvd_ft"] = woc_d.sstvd_ft
    if d_t is not None and d_b is not None:
        members["column_height_ft"] = goc_d.sstvd_ft - woc_d.sstvd_ft

    # `Range` carries no flags field, so every caveat that would have been a flag
    # is written into `method`. Losing them silently is not an option: the
    # projection caveat and the no-grading caveat are the whole point of the tool.
    notes = [
        f"governing side: {governing}",
        "D_t = GOC - perf_top and D_b = perf_base - WOC in SUBSEA elevation "
        "(positive upward); perf_standoff_check (#58) computes the same two "
        "quantities from depths increasing downward and must agree",
        f"uncertainty half-width {half_width:g} ft = contact {u_contact:g} ft + "
        f"perforation {u_perf:g} ft, added LINEARLY as an interval, not in "
        "quadrature; these are interval endpoints, not confidence bounds",
        FLAG_NOTES["standoff-is-not-graded"],
    ]
    if declared:
        notes.append("declared contact types, as the caller or contact_project (#21) "
                     "named them: " + "; ".join(f"{slot} = {name}"
                                                for slot, name in declared.items()))
    for slot, name in off_model.items():
        symbol, equation, definition = _AHMED_SLOT_CONTACTS[slot][1:]
        notes.append(
            f"the {slot} argument was given a {name}, and Ahmed Eq. {equation} defines "
            f"{symbol} as the distance from the {definition}. The vertical distance "
            f"reported here is that geometry measured to a contact the source does not "
            f"model -- a gas-water contact has no oil column, so any column height "
            f"reported here is NOT Ahmed's oil pay thickness h and this {symbol} must "
            f"not be turned "
            f"into a Chierici ratio: chierici_critical_rate (#47) refuses a gas-water "
            f"system outright ('no gas-water ... form of this correlation is published'). "
            f"The distance is real and is reported under the caller's name for the "
            f"contact, not renamed a {slot.upper()}")
    if point_perforation:
        notes.append(FLAG_NOTES["point-perforation"])
    if standoff < 0:
        notes.append(FLAG_NOTES["perforations-past-a-contact"])
    if any("projection-not-measurement" in d.inherited_flags for d in contacts.values()):
        notes.append(FLAG_NOTES["projection-not-measurement"])
    if any("UNSOURCED-CALLER-SUPPLIED-TILT" in d.inherited_flags for d in contacts.values()):
        notes.append(
            "AT LEAST ONE CONTACT WAS TILTED BY AN UNSOURCED CALLER-SUPPLIED "
            "CONSTRUCTION (contact_project #21). This standoff inherits that.")
    if u_contact == 0.0:
        notes.append(
            "the contact was stated with ZERO uncertainty, so this band has zero "
            "width. That is the caller's assertion that the contact was observed "
            "here, not a default")
    if d_t is None:
        notes.append("no GOC supplied: the gas side was not evaluated, which is not "
                     "evidence that there is no gas cap")
    if d_b is None:
        notes.append("no WOC supplied: the water side was not evaluated")
    notes.append(f"contact definitions: {QUOTES[AHMED_CHIERICI_DEFS]}")
    notes.append("uncertainty origin: " + u_origin)

    return Range(
        standoff - half_width,
        standoff + half_width,
        "ft",
        "perforation-to-contact vertical standoff, Ahmed's D_t / D_b (Eqs. 9-7, 9-8) "
        "on subsea elevations, reported as the band its contact uncertainty implies. "
        "NOT gun-to-casing mechanical standoff. " + " || ".join(notes),
        NO_SOURCE_STANDOFF,
        members=members,
    )


# --------------------------------------------------------------------------- #
# 23_column_height
# Top of porosity to contact. GROSS. Not net pay, and it will not compute net pay.
# --------------------------------------------------------------------------- #

_COLUMN_REJECT: dict[str, str] = {
    "cutoff": ("this tool returns the GROSS interval and never applies a cutoff. "
               "net_pay_cutoffs (#39) owns cutoffs; tearpock#229 p. 744 reaches net "
               "pay as gross x net/gross, which is #39's arithmetic, not this one's"),
    "net_gross": ("net pay = gross column x net/gross (tearpock#229 p. 744). This "
                  "tool returns the GROSS column only; applying the ratio here "
                  "would emit a pay figure under a gross tool's provenance. "
                  "net_pay_cutoffs (#39)"),
    "net/gross": "see net_gross: net_pay_cutoffs (#39) owns pay",
    "vsh": "a shale-volume cutoff belongs to net_pay_cutoffs (#39)",
    "sw": "a water-saturation cutoff belongs to net_pay_cutoffs (#39)",
    "phi": "a porosity cutoff belongs to net_pay_cutoffs (#39)",
    "porosity_curve": ("the top of porosity is a PICK, not a curve. Picking it is a "
                       "petrophysical decision with its own cutoff and belongs to "
                       "the caller"),
    "net_pay": "net_pay_cutoffs (#39) owns net pay; this tool returns gross column",
    "pay": "net_pay_cutoffs (#39) owns net pay; this tool returns gross column",
}


def column_height(
    top_of_porosity: Any,
    contact: Any,
    *,
    contact_type: str = "",
    top_of_porosity_uncertainty_ft: float | None = None,
    contact_uncertainty_ft: float | None = None,
    top_of_porosity_source: str = "",
    base_of_porosity: Any = None,
    **unsupported: Any,
) -> Quantity | Refusal:
    """Gross hydrocarbon column, top of porosity to fluid contact (#23).

    Tearpock p. 744: "calculate the gross interval thickness above the water level
    as the difference in depth between the top of porosity and the water level".
    His worked example -- top of porosity -8310 ft, gas/water contact -8350 ft --
    gives 40 ft, and his very next line multiplies it by a net/gross of 0.50 to
    reach 20 ft of net pay.

    **This returns the 40, and it is not the 20.** The unit is `"ft gross"`, the
    first flag is always `GROSS-COLUMN-NOT-NET-PAY`, and any cutoff or net/gross
    keyword raises naming `net_pay_cutoffs` (#39).

    The top of porosity is an **input**: picking it is a petrophysical decision
    with its own porosity cutoff, so a curve in that argument raises. A negative
    or zero column -- the top of porosity at or below the contact, i.e. wet -- is
    returned flagged rather than clipped.

    `base_of_porosity` is optional and is used **only to flag** Tearpock's
    full-thickness case; it never changes the value.
    """
    _reject(unsupported, _COLUMN_REJECT, "column_height (#23)")

    u_top = _check_uncertainty("top_of_porosity_uncertainty_ft", top_of_porosity_uncertainty_ft)
    u_contact = _check_uncertainty("contact_uncertainty_ft", contact_uncertainty_ft)

    top = _normalise_depth(top_of_porosity, "the top of porosity")
    if isinstance(top, Refusal):
        return top
    contact_d = _normalise_depth(contact, "the fluid contact")
    if isinstance(contact_d, Refusal):
        return contact_d

    records = [top, contact_d]
    base_d: _Depth | None = None
    if base_of_porosity is not None:
        base_d = _normalise_depth(base_of_porosity, "the base of porosity")
        if isinstance(base_d, Refusal):
            return base_d
        records.append(base_d)

    clash = _one_reference(records)
    if clash is not None:
        return clash

    if u_top is None:
        u_top = top.uncertainty_ft
    if u_contact is None:
        u_contact = contact_d.uncertainty_ft

    gross = top.sstvd_ft - contact_d.sstvd_ft
    label = (contact_type or contact_d.contact_type or "").strip()

    flags: list[str] = ["GROSS-COLUMN-NOT-NET-PAY", "top-of-porosity-is-a-caller-pick"]
    if gross <= 0:
        flags.append("wet-or-inverted-column")
    if "projection-not-measurement" in contact_d.inherited_flags:
        flags.append("contact-is-a-projection-not-a-measurement")

    inputs: dict[str, Any] = {
        "top_of_porosity_sstvd_ft": top.sstvd_ft,
        "contact_sstvd_ft": contact_d.sstvd_ft,
        "contact_type": label,
        "reference": top.reference,
        "depth_reference": top.reference,
        "depth_reference_as_stated": top.reference_raw,
        "datum_resolved": True,
        "top_of_porosity_source": top_of_porosity_source,
        "top_of_porosity_provenance": top.provenance,
        "contact_provenance": contact_d.provenance,
        "top_of_porosity_uncertainty_ft": u_top,
        "contact_uncertainty_ft": u_contact,
    }

    if u_top is None and u_contact is None:
        flags.append("column-uncertainty-not-stated")
        inputs["uncertainty_ft"] = None
        inputs["column_range_ft"] = None
    else:
        half_width = (u_top or 0.0) + (u_contact or 0.0)
        inputs["uncertainty_ft"] = half_width
        inputs["column_range_ft"] = (gross - half_width, gross + half_width)

    if base_d is not None:
        inputs["base_of_porosity_sstvd_ft"] = base_d.sstvd_ft
        inputs["top_to_base_of_porosity_ft"] = top.sstvd_ft - base_d.sstvd_ft
        if contact_d.sstvd_ft < base_d.sstvd_ft:
            flags.append("contact-below-base-of-porosity-full-thickness-area")

    assumptions: dict[str, Any] = {
        "is_net_pay": False,
        "net_gross_applied": None,
        "net_pay_route": (
            "net pay = this gross column x net/gross (tearpock#229 p. 744: "
            "'(0.50)(40 ft) = 20 ft net sand above the water level'). "
            "net_pay_cutoffs (#39) owns it; this tool will not"),
        "depth_basis": REQUIRED_DEPTH_BASIS,
        "sign": "negative below sea level",
        "contact_geometry": contact_d.inherited_assumptions.get(
            "contact_geometry", "not stated by the supplied contact"),
        "uncertainty_algebra": CONVENTIONS["uncertainty"],
        "conventions": dict(CONVENTIONS),
        "corroborating_sources": (TEARPOCK_CONSTANT_ELEVATION, TEARPOCK_FLAT_CONTACT),
        "source_quote": QUOTES[TEARPOCK_COLUMN],
        "flag_notes": {f: FLAG_NOTES[f] for f in flags},
    }

    return Quantity(
        gross, GROSS_UNIT,
        "gross hydrocarbon column, top of porosity to fluid contact (Tearpock "
        "p. 744: 'the difference in depth between the top of porosity and the water "
        "level'). GROSS interval -- NOT net pay, NOT net reservoir, NOT the "
        "producible interval. Net pay is this times the net/gross ratio "
        "(net_pay_cutoffs #39)",
        TEARPOCK_COLUMN,
        inputs=inputs, assumptions=assumptions, flags=tuple(flags),
    )
