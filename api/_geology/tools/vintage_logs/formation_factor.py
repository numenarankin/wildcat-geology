"""Tool #99 — formation_factor_field.  Merge target: tools/petrophysics.py.

F = Ro/Rw is one division, so nothing here is about the arithmetic. It is about
the three conditions under which the division is legitimate, each of which
produces a wrong-but-plausible F when violated:

  * Ro is the resistivity of the rock at *100%* water saturation. A deep reading
    in a hydrocarbon interval divided by Rw is dimensionless, plausible, and too
    large. So wetness is a certification the caller must present from an
    enumerated table, not a boolean it can assert.
  * Rw without provenance makes F meaningless exactly as it makes Archie
    meaningless (`archie_sw` gates the same way), and an Rw at the temperature it
    was measured at rather than at formation temperature is roughly a 2x error.
  * A shallow or medium curve reads mud filtrate. In freshwater mud a wet zone
    reads Rxo > Ri > Rt (Asquith #9), so substituting the wrong curve inflates F
    in the exact case the field method is usually run in.

`a` and `m` are never defaulted, in either direction. The catalog's reconcile
note stands: Humble and Archie disagree on the pair, so it is an explicit
argument when consumed and an explicit output when derived.

The local-constant solve is the reason to bother measuring F at all — see the
spec section "Is 'solve for a and m locally' the source's framing?" for how far
the sources actually go, which is: they state the identity a/phi^m = Ro/Rw and
frame the tabulated pairs as a no-local-knowledge fallback, but do not print the
rearrangement. It is therefore labelled derived, and never produced unsolicited.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal

# F = Ro/Rw (Eq. 1.5) and F = a/phi^m (Eq. 1.6), p. 4; zone/curve definitions
# (Rxo flushed, Ri invaded, Rt uninvaded), p. 5-6.
ASQUITH_F = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#8"
# Wet vs hydrocarbon resistivity profiles, p. 13-14, incl. the "Sw much greater
# than 60%" caveat that makes profile evidence insufficient for Ro.
ASQUITH_PROFILES = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9"
# Pad-type flushed-zone devices (MLL, PL, MSFL) and resistivity-derived porosity.
ASQUITH_RXO = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#33"
# The field procedure itself: F established locally from electric logs and water
# analyses, Ro from a deep log after corrections, and F = a/phi^m = Ro/Rw.
EPA_FIELD_F = "12-vintage-logs/epa-environmental-geophysics-electrical-methods#2"

# How an interval may be certified 100% water-saturated. `sw_unity` records
# whether the source supports that evidence establishing Sw = 1.0, which is what
# Ro means -- not merely "this zone looks wet".
WET_EVIDENCE: dict[str, dict[str, object]] = {
    "water_analysis": {
        "sw_unity": True,
        "description": "water sample analysis from this interval (water-producing well)",
        "source": EPA_FIELD_F,
        "caveats": (),
    },
    "dst_water_recovery": {
        "sw_unity": True,
        "description": "drill stem test recovered water and no hydrocarbon from this interval",
        "source": ASQUITH_F,
        "caveats": (),
    },
    "rwa_minimum": {
        "sw_unity": True,
        "description": "lowest Rwa of the compared porous, permeable zones (Asquith Ch. 7 quick-look)",
        "source": ASQUITH_F,
        "caveats": (
            "Rwa method assumes Rw is the same in every zone compared",
            "below about 10% porosity Rwa reads lower than the true Rw, so F is biased",
        ),
    },
    "resistivity_profile_wet": {
        # Asquith #9 closes the wet-profile description with "Both the above
        # examples assume that the water saturation of the uninvaded zone is much
        # greater than 60%". 60% is not 100%: this permits ~40% hydrocarbon,
        # which inflates Ro without limit. Corroboration required.
        "sw_unity": False,
        "description": "wet resistivity profile (Rxo > Ri > Rt in freshwater mud, or all three low in saltwater mud)",
        "source": ASQUITH_PROFILES,
        "caveats": (),
    },
}

# Which curve may supply Ro. Asquith #8 (Rxo flushed / Ri invaded / Rt
# uninvaded), Asquith #33 (MLL, PL, MSFL are flushed-zone pad devices), EPA #2
# (16-in normal investigates only the invaded zone; the 64-in long normal
# investigates the invaded zone *and* the native-water zone).
RESISTIVITY_CURVE_DEPTH: dict[str, str] = {
    "rt": "deep",            # already reduced to true resistivity
    "ild": "deep",           # deep induction
    "lld": "deep",           # deep laterolog
    "n64": "deep",           # 162 cm (64 in) long normal
    "ilm": "medium",         # medium induction
    "lls": "medium",         # shallow laterolog -- invaded zone
    "n32": "medium",         # 81 cm (32 in) normal
    "ri": "medium",
    "sfl": "shallow",
    "msfl": "shallow",
    "mll": "shallow",        # microlaterolog
    "pl": "shallow",         # proximity log
    "microlog": "shallow",
    "n16": "shallow",        # 40 cm (16 in) short normal
    "rxo": "shallow",
}

# Ours, not the source's. EPA #2 names the physical cause of an F below unity --
# "Surface conduction in clay also tends to reduce the resistivity measured" --
# which is the same condition the method is declared invalid for.
F_IMPLAUSIBLE_BELOW = 1.0
# Ours. Tolerance at which the field route and the porosity route are called
# disagreeing. No source states one.
ROUTE_DISAGREEMENT_FRACTION = 0.10
# EPA #2: a bed six times the AM spacing lets the log approach, but not reach,
# Rt; at or below one AM spacing the curve reverses outright.
BED_THICKNESS_AM_MULTIPLE_OK = 6.0


def local_archie_constants(f: float, porosity: float,
                           a: float | None = None, m: float | None = None):
    """Solve the local `a` or `m` from a measured F and a measured porosity.

    From EPA #2's identity `F = a/phi^m = Ro/Rw`: holding one constant fixed,
    the other follows.  m = ln(a/F)/ln(phi);  a = F * phi^m.

    Derived, not published: neither source prints the rearrangement. It is the
    payoff of the field method all the same -- Asquith #8 frames a = 1.0, m = 2.0
    as what to use "where there is no knowledge of the local parameters", and
    this is how that knowledge is obtained.
    """
    if f <= 0:
        raise ValueError("formation factor must be positive")
    if not 0.0 < porosity <= 1.0:
        raise ValueError("porosity must be in (0, 1]")
    if (a is None) == (m is None):
        raise ValueError(
            "supply exactly one of a or m; the other is what gets solved for "
            "(a single wet interval cannot determine both)")
    if porosity == 1.0:
        return Refusal(
            reason="phi = 1.0 makes phi^m constant, so neither a nor m can be solved",
            needed=("a porosity below 1.0",),
            source=EPA_FIELD_F,
        )

    if a is not None:
        if a <= 0:
            raise ValueError("tortuosity factor a must be positive")
        value = math.log(a / f) / math.log(porosity)
        label, held, held_value = "m", "a", a
    else:
        if m <= 0:
            raise ValueError("cementation exponent m must be positive")
        value = f * porosity ** m
        label, held, held_value = "a", "m", m

    flags = []
    if label == "m" and not 1.0 <= value <= 3.0:
        # Asquith Table 1.1 spans m = 1.08 (Pliocene sands) to 2.15 (Humble).
        # The 1.0-3.0 window is ours; the table is the only guide the corpus gives.
        flags.append(
            f"local m = {value:.3f} lies outside Asquith Table 1.1's observed "
            "range (1.08-2.15); bound is ours, not the source's")
    if label == "a" and not 0.5 <= value <= 2.5:
        flags.append(
            f"local a = {value:.3f} lies outside Asquith Table 1.1's observed "
            "range (0.62-2.45); bound is ours, not the source's")

    return Quantity(
        value, "dimensionless",
        f"local {label} from F = a/phi^m with {held} held fixed "
        "(derived from EPA #2 identity; Asquith Eq. 1.6)",
        EPA_FIELD_F,
        inputs={"F": f, "porosity": porosity, held: held_value},
        assumptions={"held_fixed": held, "solved_for": label,
                     "derivation": "rearranged, not printed in the source",
                     "scope": "valid only in the interval/area F was measured in"},
        flags=tuple(flags),
    )


def formation_factor_field(ro_ohmm: float, rw_ohmm: float,
                           rw_source: str | None,
                           rw_at_formation_temperature: bool,
                           wet_evidence: str | None,
                           ro_curve: str | None,
                           ro_invasion_corrected: bool,
                           porosity: float | None = None,
                           a: float | None = None,
                           m: float | None = None,
                           bed_thickness_ft: float | None = None,
                           am_spacing_in: float | None = None,
                           clean_formation: bool | None = None):
    """F = Ro/Rw from an interval certified 100% water-saturated.

    Asquith Eq. 1.5 (`Ro = F x Rw`, p. 4) as rearranged by the EPA field
    procedure: "the long normal curve, or any other resistivity log that provides
    a reasonably correct Rt can be used to calculate Rw from the relationship:
    F = Ro/Rw. Under these conditions, Ro, the resistivity of a rock 100%
    saturated with water, is assumed to approximate Rt, after the appropriate
    corrections have been made."

    Every argument before `porosity` is required and none of them is a default:
    each one gates a way of getting a plausible, wrong F.
    """
    # --- programmer error, not refusals -------------------------------------
    if ro_ohmm <= 0:
        raise ValueError("Ro must be positive (a resistivity is R = rA/L > 0)")
    if rw_ohmm <= 0:
        raise ValueError("Rw must be positive (a resistivity is R = rA/L > 0)")
    if porosity is not None and not 0.0 < porosity <= 1.0:
        raise ValueError("porosity must be in (0, 1]")
    if a is not None and a <= 0:
        raise ValueError("tortuosity factor a must be positive")
    if m is not None and m <= 0:
        raise ValueError("cementation exponent m must be positive")

    # --- R1: Rw provenance ---------------------------------------------------
    if not rw_source:
        return Refusal(
            reason="Rw has no stated provenance; F = Ro/Rw would be meaningless "
                   "and would then propagate into every Sw and porosity in the field",
            needed=("Rw from a water analysis (DST or water-producing well), a "
                    "published catalog, rw_from_sp, rw_pickett, or the Rwa method",),
            source=ASQUITH_F,
        )

    # --- R2: Rw at formation temperature ------------------------------------
    if not rw_at_formation_temperature:
        return Refusal(
            reason="Rw is not declared to be at formation temperature; resistivity "
                   "is strongly temperature-dependent, so Ro and Rw must be at the "
                   "same (formation) temperature before they are divided",
            needed=("Rw corrected to formation temperature "
                    "(resistivity_at_temperature, Arps; Asquith Ch. 1)",),
            source=ASQUITH_F,
        )

    # --- R3/R4: the wet-interval certification ------------------------------
    evidence = WET_EVIDENCE.get(wet_evidence or "")
    if evidence is None:
        return Refusal(
            reason="the interval is not certified 100% water-saturated, so the "
                   "deep reading is not Ro; F computed from a hydrocarbon-bearing "
                   "interval is too high and looks entirely plausible",
            needed=(f"wet_evidence, one of: {', '.join(sorted(WET_EVIDENCE))}",),
            source=EPA_FIELD_F,
        )
    if not evidence["sw_unity"]:
        return Refusal(
            reason=f"{wet_evidence!r} establishes only that water saturation is "
                   "much greater than 60% (Asquith #9), not that it is 100%; up to "
                   "about 40% hydrocarbon would still inflate Ro and therefore F",
            needed=("corroboration by water_analysis, dst_water_recovery or rwa_minimum",),
            source=ASQUITH_PROFILES,
        )

    # --- R5/R6: which curve supplied Ro -------------------------------------
    depth_class = RESISTIVITY_CURVE_DEPTH.get((ro_curve or "").lower())
    if depth_class is None:
        return Refusal(
            reason=f"unknown resistivity curve {ro_curve!r}; cannot establish that "
                   "the reading is a deep one, and a shallow or medium reading is "
                   "not Ro",
            needed=(f"ro_curve, one of: {', '.join(sorted(RESISTIVITY_CURVE_DEPTH))}",),
            source=ASQUITH_F,
        )
    if depth_class != "deep":
        zone = "flushed" if depth_class == "shallow" else "invaded"
        return Refusal(
            reason=f"{ro_curve} is a {depth_class}-reading device: it measures the "
                   f"{zone} zone, which is filled with mud filtrate, not the "
                   "uninvaded zone. In freshwater mud a wet zone reads "
                   "Rxo > Ri > Rt, so this would inflate F",
            needed=("a deep-reading, invasion-corrected resistivity "
                    "(ILD, LLD, 64-in long normal, or Rt)",),
            source=ASQUITH_F,
        )

    # --- R7: corrections ----------------------------------------------------
    if not ro_invasion_corrected:
        return Refusal(
            reason="Ro is not declared invasion/environmentally corrected; EPA #2 "
                   "admits Ro ~= Rt only 'after the appropriate corrections have "
                   "been made' (mud resistivity, bed thickness, borehole diameter, "
                   "mudcake, invasion)",
            needed=("a deep resistivity corrected for borehole, bed thickness and "
                    "invasion (departure_correction, rt_from_long_normal)",),
            source=EPA_FIELD_F,
        )

    # --- R8: lithologies the method is declared invalid for -----------------
    if clean_formation is False:
        return Refusal(
            reason="EPA #2: the method 'does not apply to rocks with a high clay "
                   "content or with randomly distributed solution openings or "
                   "fractures'; surface conduction in clay reduces the measured "
                   "resistivity and F is no longer a rock-geometry constant",
            needed=("a clean, granular interval, or a shaly-sand model "
                    "(shaly_sand_sw) instead of Archie's F",),
            source=EPA_FIELD_F,
        )

    # --- R9: vintage-ES bed thickness ---------------------------------------
    if bed_thickness_ft is not None and am_spacing_in is not None:
        if bed_thickness_ft <= 0 or am_spacing_in <= 0:
            raise ValueError("bed thickness and AM spacing must be positive")
        am_ft = am_spacing_in / 12.0
        if bed_thickness_ft <= am_ft:
            return Refusal(
                reason=f"bed thickness {bed_thickness_ft} ft is at or below the "
                       f"{am_spacing_in}-in AM spacing ({am_ft:.2f} ft); EPA #2: "
                       "'The curve reverses, and the high-resistivity bed actually "
                       "appears to have a lower value than the surrounding "
                       "material' -- the reading is not even qualitatively right",
                needed=("a bed at least six AM spacings thick, or a departure-curve "
                        "correction for bed thickness",),
                source=EPA_FIELD_F,
            )

    # --- the division -------------------------------------------------------
    f = ro_ohmm / rw_ohmm

    flags: list[str] = []
    flags.extend(evidence["caveats"])  # type: ignore[arg-type]

    if ro_curve.lower() == "n64":
        flags.append(
            "Ro from the 64-in long normal: EPA #2 says it investigates the "
            "invaded zone as well as the native-water zone, so it is the weakest "
            "admissible Ro even after correction")
    if bed_thickness_ft is not None and am_spacing_in is not None:
        if bed_thickness_ft < BED_THICKNESS_AM_MULTIPLE_OK * am_spacing_in / 12.0:
            flags.append(
                f"bed thickness {bed_thickness_ft} ft is under {BED_THICKNESS_AM_MULTIPLE_OK:g} "
                f"x AM spacing; EPA #2: the log approaches but does not reach Rt at "
                "6 x AM, so Ro is under-read and F is biased low")
    if clean_formation is None:
        flags.append(
            "clay content / fracturing not declared; EPA #2 declares the method "
            "inapplicable to high-clay, fractured or vuggy rock")
    if f < F_IMPLAUSIBLE_BELOW:
        flags.append(
            f"F = {f:.3f} is below 1.0, i.e. the rock conducts better than the "
            "water in it. Neither source states a bound, so this is a flag and the "
            "bound is ours; EPA #2 names the likely cause -- surface conduction in "
            "clay reducing the measured resistivity")

    assumptions: dict[str, object] = {
        "route": "field",
        "rw_source": rw_source,
        "rw_at_formation_temperature": True,
        "wet_evidence": wet_evidence,
        "wet_evidence_establishes_sw_unity": True,
        "ro_curve_depth_class": depth_class,
        "ro_invasion_corrected": True,
        "field_procedure_source": EPA_FIELD_F,
        "scope": "local: EPA #2 scopes a field F to a limited area",
    }
    if a is not None:
        assumptions["a"] = a
    if m is not None:
        assumptions["m"] = m

    # --- the local-constant solve, and the two-route reconcile --------------
    if porosity is not None:
        if a is not None and m is not None:
            f_phi = a / porosity ** m
            rel = abs(f - f_phi) / f_phi
            assumptions["F_from_porosity_route"] = f_phi
            assumptions["route_relative_difference"] = rel
            if rel > ROUTE_DISAGREEMENT_FRACTION:
                flags.append(
                    f"field route F = {f:.4g} and porosity route F = a/phi^m = "
                    f"{f_phi:.4g} differ by {rel:.1%} (threshold {ROUTE_DISAGREEMENT_FRACTION:.0%} "
                    "is ours). The two routes are independent, so this means the wet "
                    "certification, the porosity, or the assumed a/m is wrong")
        elif a is not None or m is not None:
            solved = local_archie_constants(f, porosity, a=a, m=m)
            if isinstance(solved, Quantity):
                derived = "m" if a is not None else "a"
                assumptions[f"{derived}_local"] = solved.value
                # Also under the canonical key, so the pair travels with F to
                # #100 (which reads `a`/`m` off inputs/assumptions). It is a
                # measured constant, not an assumed one; `derived_constant`
                # records which of the pair was solved rather than declared.
                assumptions[derived] = solved.value
                assumptions["derived_constant"] = derived
                flags.append(
                    f"{derived} = {solved.value:.4g} was derived locally from this "
                    "F and porosity, not declared; it is valid only in the area F "
                    "was measured in")
                flags.extend(solved.flags)
            else:
                flags.append(f"local constant not solved: {solved.reason}")
        else:
            flags.append(
                "porosity supplied but neither a nor m declared, so no local "
                "constant was derived -- that solve is the point of measuring F "
                "in the field rather than assuming a published pair")

    # implied porosity, only when the caller declared both constants
    if a is not None and m is not None:
        phi_implied = (a / f) ** (1.0 / m)
        assumptions["porosity_implied"] = phi_implied
        if not 0.0 < phi_implied <= 1.0:
            flags.append(
                f"F implies porosity {phi_implied:.3f} under the declared a={a}, "
                f"m={m}, which is outside 0-1. Bound is ours; no source states one")

    inputs: dict[str, object] = {"Ro": ro_ohmm, "Rw": rw_ohmm,
                                 "ro_curve": ro_curve, "wet_evidence": wet_evidence}
    if porosity is not None:
        inputs["porosity"] = porosity

    return Quantity(
        f, "dimensionless",
        "F = Ro/Rw (Asquith Eq. 1.5; EPA field procedure)",
        ASQUITH_F,
        inputs=inputs,
        assumptions=assumptions,
        flags=tuple(flags),
    )


def formation_factor_from_porosity(porosity: float, a: float, m: float):
    """F = a/phi^m -- Asquith Eq. 1.6, p. 4. The other route, for the reconcile.

    `a` and `m` are required positional arguments with no defaults. The catalog's
    reconcile note is explicit that Humble (a = 0.62, m = 2.15) and Archie
    (a = 1.0, m = 2.0) disagree and that neither may be defaulted implicitly;
    Asquith #8 offers a = 1.0, m = n = 2.0 only "where there is no knowledge of
    the local parameters", which is a caller's decision, not this tool's.
    """
    if not 0.0 < porosity <= 1.0:
        raise ValueError("porosity must be in (0, 1]")
    if a <= 0:
        raise ValueError("tortuosity factor a must be positive")
    if m <= 0:
        raise ValueError("cementation exponent m must be positive")
    f = a / porosity ** m
    return Quantity(
        f, "dimensionless", "F = a/phi^m (Asquith Eq. 1.6)", ASQUITH_F,
        inputs={"porosity": porosity},
        assumptions={"route": "porosity", "a": a, "m": m,
                     "circularity": "inverting this F back to porosity returns the "
                                    "input; #100 must refuse or flag a porosity-route F"},
    )
