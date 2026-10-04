"""Rock and fluid properties. Group N.

This module exists to close two breaks in the catalog rather than to add answers.
`coning_critical_rate` requires `k_h_md` and `k_v_md`, `coning_breakthrough_time`
requires those plus `k_rw_sor` and `k_ro_swc`, and `perf_length_optimize` requires
three permeabilities. Nothing produced any of them, so those tools either refused
or ran on a number the model supplied. Separately, `standoff_compute` returned a
distance with no consequence attached, because nothing said what saturation to
expect at a height above the contact.

Four decisions here are not obvious from the equations.

**Three permeability correlations, side by side, never averaged.** Asquith #48
prints Wyllie-Rose, Timur and Coates-Dumanoir as alternatives, and they disagree
by a factor of several on identical input. `permeability_estimate` returns the
spread across whichever could answer, the way `shaly_sand_sw` presents three
saturation models instead of picking one. The gate they all share is printed at
the top of that same page and is absolute: "Log-derived permeability formulas are
only valid for estimating permeability in formations at irreducible water
saturation (Schlumberger, 1977)." That is a declaration the caller has to make,
and without it every leg refuses. Wyllie-Rose has a second, narrower limit: two
constants are published, 250 for medium-gravity oils and 79 for dry gas, and
nothing in between, so a condensate or a heavy oil is a refusal and not an
interpolation.

**`kv_kh_ratio` will not guess from lithology.** The corpus defines F_k = k_v/k_h
(Ahmed Eq. 10-29) and gives two sourced ways to compute it from layer data:
Eq. 4-50, the thickness-weighted arithmetic average, which is the parallel-beds
case and therefore k_h, and Eq. 4-52, the harmonic average, which is the
series-beds case and therefore k_v. What it does NOT contain anywhere is a table
of typical k_v/k_h by rock type or bedding style. The only ratios printed are
single case values inside worked examples. A lookup table of "shale-laminated
sand: 0.01" would be this tool inventing a correlation, so asking for one is a
refusal that says where the number would have to come from instead.

**FWL and the WOC are different depths and the pair enforces it.** Ahmed Eq. 4-35
is FWL = WOC + 144 p_d / delta-rho, which on his own Example 4-5 puts the free
water level 10.5 feet BELOW the contact the logs pick. Substituting one for the
other is the specific error `free_water_level` and `saturation_height` exist to
prevent, which is why the first refuses without an entry pressure and the second
refuses without a free water level. Neither will accept the other's depth as a
stand-in.

**Brooks-Corey is not in this corpus and is not implemented.** `saturation_height`
offers Ahmed's two sourced routes instead: Eq. 5-24 inverted, which is the same
power-law shape fitted to endpoints, and the Leverett J-function (Eq. 4-36) run
over a supplied laboratory capillary-pressure curve. Note what Eq. 5-24 does at
the free water level: it returns S_w = 1 - S_orw there, not 1.0, because it is
the capillary-pressure companion of the relative-permeability pair and shares
their saturation window. That is a real property of the equation and is flagged
on every result rather than being clamped away.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

from .result import Quantity, Range, Refusal

# --------------------------------------------------------------------------
# Corpus anchors
# --------------------------------------------------------------------------

#: Asquith Chapter 7, "PERMEABILITY FROM LOGS", pp. 124-125. Wyllie and Rose
#: Eqs. 7.30/7.31, Timur Eq. 7.32, Coates and Dumanoir Eqs. 7.33-7.35, and the
#: irreducible-water-saturation gate they all sit under.
ASQUITH_PERMEABILITY = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#48"
#: Ahmed Eqs. 4-50 (weighted average, parallel beds) and 4-52 (harmonic average,
#: series beds), with Examples 4-11 and 4-12.
AHMED_PERM_AVERAGING = "00-reference/ahmed-reservoir-engineering-handbook#53"
#: Ahmed Eq. 10-29, F_k = k_v/k_h, and the k_h/k_v core-plug definition.
AHMED_FK = "00-reference/ahmed-reservoir-engineering-handbook#138"
#: Ahmed Eqs. 5-4/5-5/5-6, the Wyllie-Gardner drainage tables by formation type,
#: plus Pirson and Example 5-1.
AHMED_WYLLIE_GARDNER = "00-reference/ahmed-reservoir-engineering-handbook#63"
#: Ahmed Eqs. 5-22/5-23 (oil-water relative permeability from endpoints), 5-24
#: (the matching capillary pressure) and Example 5-5.
AHMED_RELPERM = "00-reference/ahmed-reservoir-engineering-handbook#64"
#: Ahmed Eqs. 14-11, 14-19 and 14-22, the Leverett fractional flow equation.
AHMED_FRACTIONAL_FLOW = "00-reference/ahmed-reservoir-engineering-handbook#182"
#: Ahmed Eqs. 4-30/4-32, capillary pressure from interfacial tension and pore
#: radius.
AHMED_CAPILLARY = "00-reference/ahmed-reservoir-engineering-handbook#45"
#: Ahmed Eq. 4-34 (h = 144 p_c / delta-rho), Eq. 4-35 (FWL from the WOC), and the
#: transition-zone / WOC / FWL definitions.
AHMED_FWL = "00-reference/ahmed-reservoir-engineering-handbook#48"
#: Example 4-5 worked: FWL = 5023 + 144(1.5)/20.6 = 5033.5 ft.
AHMED_FWL_EXAMPLE = "00-reference/ahmed-reservoir-engineering-handbook#49"
#: Ahmed Eq. 4-36 (Leverett J), the lab-to-reservoir conversion and Eq. 4-37,
#: with Example 4-7.
AHMED_LEVERETT = "00-reference/ahmed-reservoir-engineering-handbook#50"

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

#: Asquith Eq. 7.30 / 7.31. Two constants are published and nothing between them.
WYLLIE_ROSE_CONSTANTS: dict[str, float] = {
    "medium_gravity_oil": 250.0,
    "dry_gas": 79.0,
}
TIMUR_CONSTANT = 93.0          # Asquith Eq. 7.32
TIMUR_EXPONENT = 2.2           # Asquith Eq. 7.32
#: Coates and Dumanoir Eq. 7.33, C = 23 + 465 rho_h - 188 rho_h^2.
COATES_C = (23.0, 465.0, -188.0)
COATES_W_OFFSET = 3.75         # Asquith Eq. 7.34
COATES_W_SHIFT = 2.2           # Asquith Eq. 7.34
COATES_W_DIVISOR = 2.0         # Asquith Eq. 7.34

#: Asquith #48, the sentence every leg sits under.
IRREDUCIBLE_GATE = (
    "\"Log-derived permeability formulas are only valid for estimating permeability "
    "in formations at irreducible water saturation (Schlumberger, 1977).\" "
    "Asquith #48 p. 124. Constancy of bulk volume water (BVW = S_w x phi) over the "
    "interval is the test; where BVW is not constant the estimates are, in his "
    "words, suspect."
)

#: Ahmed Eqs. 5-4/5-6, drainage oil-water relative permeability by formation type.
#: k_ro and k_rw are functions of S_w* = (S_w - S_wc)/(1 - S_wc) alone, which is
#: what makes this the one route that needs no measured endpoints.
WYLLIE_GARDNER_FORMATIONS = (
    "unconsolidated_well_sorted",
    "unconsolidated_poorly_sorted",
    "cemented_sandstone",
)

#: Ahmed Eq. 4-34, p_c psi to height in feet with delta-rho in lb/ft3.
PSI_FT_PER_LB_FT3 = 144.0
#: Ahmed Eq. 4-36, J(S_w) = 0.21645 (p_c/sigma) sqrt(k/phi).
LEVERETT_COEFF = 0.21645

_SATURATION_HEIGHT_METHODS = ("analytical", "leverett_j")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _positive(name: str, value: Any) -> float:
    if not _finite(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}")
    return float(value)


def _fraction(name: str, value: Any) -> float:
    if not _finite(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} must be a fraction in [0, 1], got {value!r}; a percentage here "
            "changes the answer by orders of magnitude with no other symptom")
    return float(value)


def _missing(**kwargs: Any) -> tuple[str, ...]:
    return tuple(name for name, value in kwargs.items() if value is None)


# --------------------------------------------------------------------------
# N1 - permeability_estimate
# --------------------------------------------------------------------------

def _wyllie_rose(phi: float, sw_irr: float,
                 hydrocarbon: str | None) -> Quantity | Refusal:
    """Asquith Eqs. 7.30 (medium-gravity oils) and 7.31 (dry gas)."""
    if hydrocarbon is None:
        return Refusal(
            reason=("Wyllie-Rose publishes one constant per hydrocarbon type, 250 for "
                    "medium-gravity oils (Eq. 7.30) and 79 for dry gas (Eq. 7.31), and "
                    "the two differ by a factor of 10 in k. Which one applies is not "
                    "derivable from phi and S_wirr"),
            needed=(f"hydrocarbon, one of {sorted(WYLLIE_ROSE_CONSTANTS)}",),
            source=ASQUITH_PERMEABILITY)
    constant = WYLLIE_ROSE_CONSTANTS.get(hydrocarbon)
    if constant is None:
        return Refusal(
            reason=(f"Wyllie-Rose publishes no constant for {hydrocarbon!r}. Asquith #48 "
                    "prints exactly two, 250 for medium-gravity oils and 79 for dry gas. "
                    "Interpolating between them for a condensate or a heavy oil would be "
                    "an invented correlation"),
            needed=(f"a fluid Asquith tabulates: {sorted(WYLLIE_ROSE_CONSTANTS)}",),
            source=ASQUITH_PERMEABILITY)
    k = (constant * phi ** 3 / sw_irr) ** 2
    eq = "7.30" if hydrocarbon == "medium_gravity_oil" else "7.31"
    return Quantity(
        k, "md", f"Wyllie and Rose (1950), Asquith Eq. {eq}", ASQUITH_PERMEABILITY,
        inputs={"phi": phi, "sw_irr": sw_irr, "hydrocarbon": hydrocarbon},
        assumptions={"constant": constant, "at_irreducible_water_saturation": True})


def _timur(phi: float, sw_irr: float) -> Quantity:
    """Asquith Eq. 7.32, K = (93 phi^2.2 / S_wirr)^2."""
    k = (TIMUR_CONSTANT * phi ** TIMUR_EXPONENT / sw_irr) ** 2
    return Quantity(
        k, "md", "Timur (1968), Asquith Eq. 7.32", ASQUITH_PERMEABILITY,
        inputs={"phi": phi, "sw_irr": sw_irr},
        assumptions={"constant": TIMUR_CONSTANT, "exponent": TIMUR_EXPONENT,
                     "at_irreducible_water_saturation": True,
                     "hydrocarbon_type": "not a term in Eq. 7.32; Timur publishes one "
                                         "constant for oil and gas alike"})


def _coates_dumanoir(phi: float, rho_h_g_cc: float | None, rw: float | None,
                     r_irr: float | None) -> Quantity | Refusal:
    """Asquith Eqs. 7.33-7.35."""
    need = _missing(rho_h_g_cc=rho_h_g_cc, rw=rw, r_irr=r_irr)
    if need:
        return Refusal(
            reason=("Coates and Dumanoir (1973) is the one of the three that carries "
                    "hydrocarbon density explicitly instead of hiding it in a constant, "
                    f"so it needs {', '.join(need)} (Eqs. 7.33-7.35)"),
            needed=need, source=ASQUITH_PERMEABILITY)
    c0, c1, c2 = COATES_C
    c = c0 + c1 * rho_h_g_cc + c2 * rho_h_g_cc ** 2                      # Eq. 7.33
    ratio = rw / r_irr
    inner = (COATES_W_OFFSET - phi) + ((math.log10(ratio) + COATES_W_SHIFT) ** 2
                                       / COATES_W_DIVISOR)               # Eq. 7.34
    if inner <= 0:
        return Refusal(
            reason=(f"Eq. 7.34's radicand is {inner:.4g}; W is the square root of it and "
                    "is undefined here"),
            needed=("a porosity and an R_w/R_irr inside the range Eq. 7.34 is defined on",),
            source=ASQUITH_PERMEABILITY)
    w = math.sqrt(inner)
    k = (c * phi ** (2.0 * w) / (w ** 4 * ratio)) ** 2                    # Eq. 7.35
    return Quantity(
        k, "md", "Coates and Dumanoir (1973), Asquith Eqs. 7.33-7.35",
        ASQUITH_PERMEABILITY,
        inputs={"phi": phi, "rho_h_g_cc": rho_h_g_cc, "rw": rw, "r_irr": r_irr,
                "C": c, "W": w, "rw_over_rirr": ratio},
        assumptions={"at_irreducible_water_saturation": True,
                     "log_base": "base 10; Asquith Eq. 7.34 prints 'log' unqualified and "
                                 "the log-analysis convention is base 10. A natural log "
                                 "here changes W and therefore the exponent on phi"},
        flags=("Eq. 7.34's logarithm is printed unqualified in the corpus; base 10 is "
               "assumed, see assumptions.log_base",))


def permeability_estimate(phi: float, sw_irr: float, *,
                          at_irreducible: bool | None = None,
                          hydrocarbon: str | None = None,
                          rho_h_g_cc: float | None = None,
                          rw: float | None = None,
                          r_irr: float | None = None) -> Range | Refusal:
    """Timur, Wyllie-Rose and Coates-Dumanoir side by side. Asquith #48.

    Returns the spread across whichever correlations could answer, with every
    leg's own value in `members`. It does not pick one and does not average them:
    they were fitted from different data and disagree materially on identical
    input, which is information the caller needs.

    `at_irreducible` has no default. All three formulas are published as valid
    only at irreducible water saturation, and whether an interval is there is a
    BVW-constancy reading, not something derivable from phi and S_w.

    Args:
        phi: porosity, v/v.
        sw_irr: water saturation of a zone AT irreducible saturation, v/v.
        at_irreducible: the caller's declaration that the interval is at
            irreducible water saturation. Required.
        hydrocarbon: "medium_gravity_oil" or "dry_gas", for Wyllie-Rose only.
        rho_h_g_cc: hydrocarbon density, g/cm3, for Coates-Dumanoir only.
        rw: formation water resistivity at formation temperature, ohm-m.
        r_irr: deep resistivity from the zone at irreducible saturation, ohm-m.
    """
    _fraction("phi", phi)
    _fraction("sw_irr", sw_irr)
    if phi <= 0:
        raise ValueError("porosity must be positive for a permeability estimate")
    if sw_irr <= 0:
        raise ValueError("sw_irr must be positive; every correlation divides by it")

    if at_irreducible is not True:
        stance = ("was not declared" if at_irreducible is None
                  else "was declared FALSE by the caller")
        return Refusal(
            reason=(f"irreducible water saturation {stance}, and all three log-derived "
                    f"permeability formulas are published only for that case. "
                    + IRREDUCIBLE_GATE),
            needed=("at_irreducible=True, established from constant bulk volume water "
                    "over the interval (bulk_volume_water, or BVW = S_w x phi read off "
                    "the log)",),
            source=ASQUITH_PERMEABILITY)

    legs: dict[str, Quantity | Refusal] = {
        "timur": _timur(phi, sw_irr),
        "wyllie_rose": _wyllie_rose(phi, sw_irr, hydrocarbon),
        "coates_dumanoir": _coates_dumanoir(phi, rho_h_g_cc, rw, r_irr),
    }
    members = {name: leg.value for name, leg in legs.items() if isinstance(leg, Quantity)}
    excluded = {name: leg.reason for name, leg in legs.items() if isinstance(leg, Refusal)}

    if not members:
        return Refusal(
            reason=" | ".join(f"{name}: {why}" for name, why in excluded.items()),
            needed=tuple(dict.fromkeys(
                need for leg in legs.values()
                if isinstance(leg, Refusal) for need in leg.needed)),
            source=ASQUITH_PERMEABILITY)

    flags: tuple[str, ...] = (
        "log-derived permeability is a comparison number, not an absolute one: Asquith "
        "#48 says to compare it against nearby producers in the same formation",)
    if excluded:
        flags += tuple(f"excluded, {name}: {why}" for name, why in excluded.items())
    if len(members) == 1:
        flags += ("one correlation answered, so the spread is degenerate and hides the "
                  "disagreement this tool exists to show",)

    return Range(
        min(members.values()), max(members.values()), "md",
        "spread of log-derived permeability correlations at irreducible water "
        f"saturation ({', '.join(sorted(members))}), Asquith #48",
        ASQUITH_PERMEABILITY, members=members,
        inputs={"phi": phi, "sw_irr": sw_irr, "hydrocarbon": hydrocarbon,
                "rho_h_g_cc": rho_h_g_cc, "rw": rw, "r_irr": r_irr},
        assumptions={"at_irreducible_water_saturation": True,
                     "correlations": sorted(members),
                     "excluded": sorted(excluded),
                     "never_averaged": "the legs were fitted from different data; the "
                                       "band is their disagreement, not an error bar"},
        flags=flags)


# --------------------------------------------------------------------------
# N2 - kv_kh_ratio
# --------------------------------------------------------------------------

def kv_kh_ratio(k_v_md: float | None = None, k_h_md: float | None = None, *,
                layer_k_md: Sequence[float] | None = None,
                layer_thickness_ft: Sequence[float] | None = None,
                lithology: str | None = None,
                bedding: str | None = None) -> Quantity | Refusal:
    """F_k = k_v/k_h. Ahmed Eq. 10-29, from measurements or from layer data.

    Two sourced routes, and one refusal that matters more than either.

    Measured: pass `k_v_md` and `k_h_md`, which Ahmed #51 defines as core plugs cut
    perpendicular and parallel to bedding. The ratio is then Eq. 10-29 outright.

    Layered: pass `layer_k_md` and `layer_thickness_ft`. Flow along the bedding is
    the parallel-beds case, so k_h is the thickness-weighted arithmetic average
    (Ahmed Eq. 4-50); flow across it is the series-beds case, so k_v is the
    harmonic average (Eq. 4-52). The ratio of the two is the anisotropy the
    layering itself implies, and a single thin tight streak drives it, which is
    the physical point.

    Refused: an estimate from `lithology` or `bedding` alone. This corpus defines
    F_k and prints no table of typical values by rock type or bedding style, only
    single case values inside worked examples. Returning one would be this tool
    publishing a correlation rather than citing one, and every coning rate
    downstream would inherit it invisibly.
    """
    measured = k_v_md is not None and k_h_md is not None
    layered = layer_k_md is not None and layer_thickness_ft is not None

    if measured and layered:
        raise ValueError(
            "supply either measured (k_v_md, k_h_md) or layer data, not both; two "
            "anisotropies that disagree would be silently reconciled")

    if measured:
        _positive("k_v_md", k_v_md)
        _positive("k_h_md", k_h_md)
        ratio = k_v_md / k_h_md
        flags = () if ratio <= 1.0 else (
            "k_v exceeds k_h, which is unusual: routine core analysis cuts plugs "
            "parallel to bedding for k_h and perpendicular for k_v (Ahmed #51), so a "
            "ratio above 1 is worth checking against the plug orientations",)
        return Quantity(
            ratio, "fraction", "F_k = k_v/k_h from measured permeabilities "
            "(Ahmed Eq. 10-29)", AHMED_FK,
            inputs={"k_v_md": k_v_md, "k_h_md": k_h_md},
            assumptions={"route": "measured core plugs",
                         "plug_orientation": "k_h parallel to bedding, k_v perpendicular "
                                             "(Ahmed #51)"},
            flags=flags)

    if layered:
        if len(layer_k_md) != len(layer_thickness_ft):
            raise ValueError(
                f"layer_k_md has {len(layer_k_md)} entries and layer_thickness_ft has "
                f"{len(layer_thickness_ft)}")
        if len(layer_k_md) < 2:
            return Refusal(
                reason=("one layer is isotropic by construction: Eqs. 4-50 and 4-52 both "
                        "return that layer's own permeability and the ratio is 1.0, which "
                        "says nothing about the rock"),
                needed=("at least two layers with different permeabilities",),
                source=AHMED_PERM_AVERAGING)
        ks = [_positive("layer_k_md", k) for k in layer_k_md]
        hs = [_positive("layer_thickness_ft", h) for h in layer_thickness_ft]
        total = sum(hs)
        k_h = sum(k * h for k, h in zip(ks, hs)) / total                  # Eq. 4-50
        k_v = total / sum(h / k for k, h in zip(ks, hs))                  # Eq. 4-52
        ratio = k_v / k_h
        return Quantity(
            ratio, "fraction",
            "F_k = k_v/k_h with k_h the thickness-weighted average of the layers "
            "(Ahmed Eq. 4-50, parallel beds) and k_v their harmonic average "
            "(Eq. 4-52, series beds)", f"{AHMED_FK}; {AHMED_PERM_AVERAGING}",
            inputs={"layers": len(ks), "k_h_md": k_h, "k_v_md": k_v,
                    "gross_ft": total, "layer_k_md": list(ks),
                    "layer_thickness_ft": list(hs)},
            assumptions={"route": "layer averaging",
                         "k_h_equation": "Ahmed Eq. 4-50, arithmetic, thickness weighted",
                         "k_v_equation": "Ahmed Eq. 4-52, harmonic",
                         "no_cross_flow": "Eq. 4-50 is derived for beds with no cross "
                                          "flow between them (Ahmed #53)",
                         "scale": "this is the anisotropy the LAYERING implies; it does "
                                  "not include anisotropy inside a single layer"})

    return Refusal(
        reason=(
            "k_v/k_h cannot be estimated from lithology or bedding description in this "
            "corpus. Ahmed defines F_k = k_v/k_h (Eq. 10-29) and #51 defines the two "
            "plug orientations behind it, but no table of typical ratios by rock type "
            "or bedding style is published anywhere here. The only ratios printed are "
            "single case values inside worked examples, which are those reservoirs, not "
            "a correlation. Returning a number from "
            + (f"lithology={lithology!r} " if lithology else "")
            + (f"bedding={bedding!r} " if bedding else "")
            + "would put an invented anisotropy into every coning rate downstream."),
        needed=("k_v_md and k_h_md from oriented core plugs (Ahmed #51)",
                "or layer_k_md and layer_thickness_ft, which give k_h by Eq. 4-50 and "
                "k_v by Eq. 4-52",
                "or a vertical interference or pulse test"),
        source=AHMED_FK)


# --------------------------------------------------------------------------
# N3 - relative_permeability
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RelativePermeabilityPair:
    """What #N3 returns: the pair at the requested S_w and the two endpoints.

    `k_ro_swc` and `k_rw_sor` are named for the arguments
    `coning_breakthrough_time` takes, because supplying them is the reason this
    tool exists. `mobility_ratio_input` restates Ahmed Eq. 9-24's grouping so the
    caller can see exactly what the coning tool will build from them.
    """

    k_ro: Quantity
    k_rw: Quantity
    k_ro_swc: Quantity
    k_rw_sor: Quantity
    mobility_ratio_input: dict[str, float] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()


def _sw_star(sw: float, swc: float) -> float:
    """Ahmed Eq. 5-2, S_w* = (S_w - S_wc)/(1 - S_wc)."""
    return (sw - swc) / (1.0 - swc)


def _wyllie_gardner_pair(sw_star: float, formation: str) -> tuple[float, float]:
    """Ahmed Eqs. 5-4/5-5/5-6, drainage oil-water, by formation type."""
    if formation == "unconsolidated_well_sorted":                        # Eq. 5-4
        return (1.0 - sw_star) ** 3, sw_star ** 3
    if formation == "unconsolidated_poorly_sorted":                      # Eq. 5-5
        return ((1.0 - sw_star) ** 2 * (1.0 - sw_star ** 1.5),
                sw_star ** 3.5)
    return ((1.0 - sw_star) ** 2 * (1.0 - sw_star ** 2), sw_star ** 4)   # Eq. 5-6


def relative_permeability(sw: float, swc: float, sor: float, *,
                          model: str = "analytical",
                          k_ro_swc: float | None = None,
                          k_rw_sor: float | None = None,
                          n_o: float = 1.0, n_w: float = 1.0,
                          formation: str | None = None
                          ) -> RelativePermeabilityPair | Refusal:
    """Oil-water relative permeability, and the two endpoints coning needs.

    Two models, and the choice is about what the caller has.

    `model="analytical"` is Ahmed Eqs. 5-22 and 5-23, the endpoint power law:

        k_ro = (k_ro)_Swc [(1 - S_w - S_orw)/(1 - S_wc - S_orw)]^n_o
        k_rw = (k_rw)_Sorw [(S_w - S_wc)/(1 - S_wc - S_orw)]^n_w

    It needs measured endpoints and exponents and refuses without them, since the
    corpus prints no way to invent an endpoint.

    `model="wyllie_gardner"` is Ahmed Eqs. 5-4/5-5/5-6, keyed by formation type.
    Those are functions of S_w* alone, so they need NO measured endpoints, which
    makes this the route that actually unblocks `coning_breakthrough_time` on a
    stripper well with no special core analysis. It is a drainage correlation and
    says so on the result.

    The `k_ro_swc` and `k_rw_sor` on the result are the endpoint values under the
    model that ran, which is what `coning_breakthrough_time(k_rw_sor=...,
    k_ro_swc=...)` takes.
    """
    if model not in ("analytical", "wyllie_gardner"):
        raise ValueError(
            f"model must be 'analytical' or 'wyllie_gardner', got {model!r}")
    _fraction("sw", sw)
    _fraction("swc", swc)
    _fraction("sor", sor)
    if swc + sor >= 1.0:
        raise ValueError(
            f"S_wc + S_or = {swc + sor:g}: there is no mobile saturation window left, and "
            "every normalised saturation divides by (1 - S_wc - S_orw)")
    if not swc <= sw <= 1.0 - sor:
        return Refusal(
            reason=(f"S_w = {sw:g} is outside the mobile window [{swc:g}, {1.0 - sor:g}]. "
                    "Ahmed's Eqs. 5-22/5-23 are defined between the endpoints; outside "
                    "them a relative permeability comes out negative or above one"),
            needed=("a water saturation between S_wc and 1 - S_orw",),
            source=AHMED_RELPERM)

    if model == "analytical":
        need = _missing(k_ro_swc=k_ro_swc, k_rw_sor=k_rw_sor)
        if need:
            return Refusal(
                reason=("Ahmed Eqs. 5-22/5-23 are anchored on measured endpoints and the "
                        f"corpus prints no way to invent one, so this route needs "
                        f"{', '.join(need)}. Use model='wyllie_gardner' (Eqs. 5-4/5-6) "
                        "for a correlation that needs only S_wc and a formation type"),
                needed=need, source=AHMED_RELPERM)
        _fraction("k_ro_swc", k_ro_swc)
        _fraction("k_rw_sor", k_rw_sor)
        _positive("n_o", n_o)
        _positive("n_w", n_w)
        window = 1.0 - swc - sor
        kro = k_ro_swc * ((1.0 - sw - sor) / window) ** n_o               # Eq. 5-22
        krw = k_rw_sor * ((sw - swc) / window) ** n_w                     # Eq. 5-23
        end_ro, end_rw = k_ro_swc, k_rw_sor
        method_ro = "Ahmed Eq. 5-22, oil-water analytical form"
        method_rw = "Ahmed Eq. 5-23, oil-water analytical form"
        source = AHMED_RELPERM
        assumptions: dict[str, Any] = {
            "model": "analytical endpoint power law (Ahmed Eqs. 5-22/5-23)",
            "n_o": n_o, "n_w": n_w,
            "exponent_fit": "Ahmed #64: the exponents are 'usually determined by the "
                            "least-squares method to match the experimental or field "
                            "relative permeability' data. Unity is not a published "
                            "default, it is the neutral value",
        }
        flags: tuple[str, ...] = ()
        if n_o == 1.0 and n_w == 1.0:
            flags += ("n_o and n_w left at 1.0, which makes both curves straight lines; "
                      "Ahmed's Example 5-5 works 0.9 and 1.5 on a real pair",)
    else:
        if formation not in WYLLIE_GARDNER_FORMATIONS:
            return Refusal(
                reason=(f"Wyllie-Gardner is tabulated per formation type and "
                        f"{formation!r} is not one of them. Ahmed #63 prints three rows: "
                        f"{', '.join(WYLLIE_GARDNER_FORMATIONS)}"),
                needed=(f"formation, one of {list(WYLLIE_GARDNER_FORMATIONS)}",),
                source=AHMED_WYLLIE_GARDNER)
        kro, krw = _wyllie_gardner_pair(_sw_star(sw, swc), formation)
        end_ro, _ = _wyllie_gardner_pair(0.0, formation)                  # at S_wc
        _, end_rw = _wyllie_gardner_pair(_sw_star(1.0 - sor, swc), formation)
        method_ro = f"Wyllie and Gardner drainage k_ro, {formation} (Ahmed #63)"
        method_rw = f"Wyllie and Gardner drainage k_rw, {formation} (Ahmed #63)"
        source = AHMED_WYLLIE_GARDNER
        assumptions = {
            "model": "Wyllie and Gardner drainage tables (Ahmed Eqs. 5-4/5-5/5-6)",
            "formation": formation,
            "sw_star": "Ahmed Eq. 5-2, (S_w - S_wc)/(1 - S_wc). Note this normalises on "
                       "S_wc only, so S_w* reaches 1 at S_w = 1 and NOT at 1 - S_orw",
        }
        flags = ("a drainage correlation: Ahmed #63 tabulates these under 'Drainage "
                 "Oil-Water Relative Permeabilities'. Water encroaching into an oil "
                 "column is imbibition, so these curves are the wrong branch of the "
                 "hysteresis loop for a rising contact",)

    common_inputs = {"sw": sw, "swc": swc, "sor": sor, "model": model}
    return RelativePermeabilityPair(
        k_ro=Quantity(kro, "fraction", method_ro, source,
                      inputs=common_inputs, assumptions=assumptions),
        k_rw=Quantity(krw, "fraction", method_rw, source,
                      inputs=common_inputs, assumptions=assumptions),
        k_ro_swc=Quantity(end_ro, "fraction",
                          method_ro + ", evaluated at S_wc", source,
                          inputs={"swc": swc}, assumptions=assumptions),
        k_rw_sor=Quantity(end_rw, "fraction",
                          method_rw + ", evaluated at 1 - S_or", source,
                          inputs={"sor": sor, "swc": swc}, assumptions=assumptions),
        mobility_ratio_input={"k_rw_sor": end_rw, "k_ro_swc": end_ro},
        assumptions={**assumptions,
                     "downstream": "k_ro_swc and k_rw_sor are the arguments "
                                   "coning_breakthrough_time builds M from "
                                   "(Ahmed Eq. 9-24, M = (k_rw_sor/k_ro_swc)(mu_o/mu_w))"},
        flags=flags)


# --------------------------------------------------------------------------
# N4 - fractional_flow
# --------------------------------------------------------------------------

def fractional_flow(k_ro: float, k_rw: float, mu_o_cp: float,
                    mu_w_cp: float) -> Quantity | Refusal:
    """Water cut against saturation. Ahmed Eq. 14-19 with Eq. 14-22's neglects.

        f_w = 1 / (1 + (k_ro/k_rw)(mu_w/mu_o))

    Ahmed's full Eq. 14-19 carries a capillary-pressure gradient and a gravity
    term in the numerator. Both are dropped here, and the reason is his: "The
    effect of capillary pressure is usually neglected because the capillary
    pressure gradient is generally small" (#182), which reduces Eq. 14-19 to
    Eq. 14-22; and Eq. 14-22's remaining term carries sin(alpha), which vanishes
    for a horizontal system. This tool implements the horizontal, capillarity-free
    case and says so, rather than taking a dip angle and an injection rate it
    cannot check.

    At S_wc the water rate is zero so f_w is 0, and at S_or the oil rate is zero
    so f_w is 1 (#182). Feed it the pair from `relative_permeability`.
    """
    _positive("mu_o_cp", mu_o_cp)
    _positive("mu_w_cp", mu_w_cp)
    _fraction("k_ro", k_ro)
    _fraction("k_rw", k_rw)

    if k_rw <= 0.0:
        return Quantity(
            0.0, "bbl/bbl",
            "water cut at k_rw = 0 (Ahmed #182: at irreducible water saturation the "
            "water flow rate is zero and the water cut is 0%)",
            AHMED_FRACTIONAL_FLOW,
            inputs={"k_ro": k_ro, "k_rw": k_rw, "mu_o_cp": mu_o_cp, "mu_w_cp": mu_w_cp},
            assumptions={"branch": "endpoint, not Eq. 14-19"})
    if k_ro <= 0.0:
        return Quantity(
            1.0, "bbl/bbl",
            "water cut at k_ro = 0 (Ahmed #182: at residual oil saturation the oil flow "
            "rate is zero and the water cut reaches its upper limit of 100%)",
            AHMED_FRACTIONAL_FLOW,
            inputs={"k_ro": k_ro, "k_rw": k_rw, "mu_o_cp": mu_o_cp, "mu_w_cp": mu_w_cp},
            assumptions={"branch": "endpoint, not Eq. 14-19"})

    fw = 1.0 / (1.0 + (k_ro / k_rw) * (mu_w_cp / mu_o_cp))
    return Quantity(
        fw, "bbl/bbl",
        "fractional flow of water (Ahmed Eq. 14-19, horizontal and with the capillary "
        "pressure gradient neglected per #182)", AHMED_FRACTIONAL_FLOW,
        inputs={"k_ro": k_ro, "k_rw": k_rw, "mu_o_cp": mu_o_cp, "mu_w_cp": mu_w_cp,
                "kro_over_krw": k_ro / k_rw, "mu_w_over_mu_o": mu_w_cp / mu_o_cp,
                "oil_cut": 1.0 - fw},
        assumptions={"dip_angle": "zero; Eq. 14-22's gravity term carries sin(alpha)",
                     "capillary_gradient": "neglected, Ahmed #182",
                     "units": "reservoir barrels; f_w is a downhole cut, not a "
                              "stock-tank one"})


# --------------------------------------------------------------------------
# N5 - capillary_pressure
# --------------------------------------------------------------------------

def capillary_pressure(pc_lab_psi: float, *,
                       sigma_lab_dynes_cm: float | None = None,
                       sigma_res_dynes_cm: float | None = None,
                       phi_core: float | None = None,
                       k_core_md: float | None = None,
                       phi_res: float | None = None,
                       k_res_md: float | None = None) -> Quantity | Refusal:
    """Laboratory capillary pressure at reservoir conditions. Ahmed Eq. 4-37.

        (p_c)res = (p_c)lab (sigma_res/sigma_lab) sqrt(phi_res k_core / (phi_core k_res))

    Two corrections, applied in the order Ahmed applies them and reported
    separately so the caller can see which one moved the number.

    The tension correction is not optional and has no default: the laboratory
    system is normally air-mercury or air-brine, whose tension is several times
    the reservoir oil-water value, so omitting it leaves a pressure that is
    several times too high, and then Eq. 4-34 turns that into a transition zone
    several times too thick.

    The permeability and porosity correction IS optional: Ahmed introduces it as
    a further step for when the core is not representative of the reservoir, and
    without it the result is the first form he prints.
    """
    _positive("pc_lab_psi", pc_lab_psi)
    need = _missing(sigma_lab_dynes_cm=sigma_lab_dynes_cm,
                    sigma_res_dynes_cm=sigma_res_dynes_cm)
    if need:
        return Refusal(
            reason=("the interfacial tension of both systems is required. Ahmed #50: "
                    "'Since the laboratory fluid system does not have the same surface "
                    "tension as the reservoir system, it becomes necessary to convert "
                    "laboratory capillary pressure to reservoir capillary pressure.' "
                    "Air-mercury and air-brine tensions are several times the reservoir "
                    "oil-water value, so skipping this leaves the transition zone "
                    "several times too thick"),
            needed=need, source=AHMED_LEVERETT)
    _positive("sigma_lab_dynes_cm", sigma_lab_dynes_cm)
    _positive("sigma_res_dynes_cm", sigma_res_dynes_cm)

    tension_ratio = sigma_res_dynes_cm / sigma_lab_dynes_cm
    rock_terms = (phi_core, k_core_md, phi_res, k_res_md)
    rock_ratio = 1.0
    if any(term is not None for term in rock_terms):
        rock_need = _missing(phi_core=phi_core, k_core_md=k_core_md,
                             phi_res=phi_res, k_res_md=k_res_md)
        if rock_need:
            return Refusal(
                reason=("the permeability and porosity correction of Eq. 4-37 takes all "
                        f"four of phi_core, k_core, phi_res, k_res; missing "
                        f"{', '.join(rock_need)}. Supply all four or none"),
                needed=rock_need, source=AHMED_LEVERETT)
        _fraction("phi_core", phi_core)
        _fraction("phi_res", phi_res)
        _positive("k_core_md", k_core_md)
        _positive("k_res_md", k_res_md)
        if phi_core <= 0 or phi_res <= 0:
            raise ValueError("core and reservoir porosity must both be positive")
        rock_ratio = math.sqrt((phi_res * k_core_md) / (phi_core * k_res_md))

    pc_res = pc_lab_psi * tension_ratio * rock_ratio
    applied = "tension only" if rock_ratio == 1.0 else "tension and rock quality"
    return Quantity(
        pc_res, "psi",
        f"laboratory capillary pressure converted to reservoir conditions, {applied} "
        "(Ahmed Eq. 4-37)", AHMED_LEVERETT,
        inputs={"pc_lab_psi": pc_lab_psi, "tension_ratio": tension_ratio,
                "rock_ratio": rock_ratio, "sigma_lab_dynes_cm": sigma_lab_dynes_cm,
                "sigma_res_dynes_cm": sigma_res_dynes_cm, "phi_core": phi_core,
                "k_core_md": k_core_md, "phi_res": phi_res, "k_res_md": k_res_md},
        assumptions={
            "contact_angle": "Ahmed's Eq. 4-37 carries sigma alone, while Eqs. 4-30/4-32 "
                             f"({AHMED_CAPILLARY}) build p_c on sigma cos(theta). "
                             "Dropping the cosines means the contact angles are taken as "
                             "equal between the laboratory and reservoir systems",
            "j_function_invariance": "Ahmed #50: the conversion assumes 'the Leverett "
                                     "J-function is a property of rock and does not "
                                     "change from the laboratory to the reservoir'",
            "rock_correction_applied": rock_ratio != 1.0,
        })


# --------------------------------------------------------------------------
# N6 - saturation_height
# --------------------------------------------------------------------------

def saturation_height(height_above_fwl_ft: float, delta_rho_lb_ft3: float, *,
                      method: str = "analytical",
                      swc: float | None = None,
                      sor: float | None = None,
                      pc_swc_psi: float | None = None,
                      n_p: float | None = None,
                      lab_curve: Sequence[Sequence[float]] | None = None,
                      sigma_lab_dynes_cm: float | None = None,
                      sigma_res_dynes_cm: float | None = None,
                      phi_core: float | None = None,
                      k_core_md: float | None = None,
                      phi_res: float | None = None,
                      k_res_md: float | None = None) -> Quantity | Refusal:
    """Water saturation at a height above the FREE WATER LEVEL. Ahmed Eq. 4-34.

    This is what finally attaches a consequence to `standoff_compute`: a standoff
    is a distance, and this turns the distance into the saturation a perforation
    at that height would see.

    The height is above the FWL and not above the WOC. Ahmed #48 is explicit that
    they are different depths and Eq. 4-35 says by how much; feeding a height
    above the logged contact into this tool understates the capillary pressure by
    the entry-pressure head and reads the transition zone too wet. Call
    `free_water_level` first.

    `method="analytical"` inverts Ahmed Eq. 5-24, the capillary-pressure companion
    of the Eqs. 5-22/5-23 relative-permeability pair:

        p_c = h delta-rho / 144                                   (Eq. 4-34)
        S_w = 1 - S_orw - (1 - S_wc - S_orw) (p_c / (p_c)_Swc)^(1/n_p)

    `method="leverett_j"` takes a laboratory `lab_curve` of (S_w, p_c) pairs,
    rescales it to the reservoir with Eq. 4-36 through `capillary_pressure`, and
    reads S_w off the rescaled curve at this height.

    Brooks-Corey is deliberately absent: it is not in this corpus. Eq. 5-24 is the
    same power-law shape and is printed here, so it is what runs.
    """
    if method not in _SATURATION_HEIGHT_METHODS:
        raise ValueError(
            f"method must be one of {_SATURATION_HEIGHT_METHODS}, got {method!r}")
    if not _finite(height_above_fwl_ft):
        raise ValueError(f"height_above_fwl_ft must be a number, got "
                         f"{height_above_fwl_ft!r}")
    if height_above_fwl_ft < 0:
        return Refusal(
            reason=(f"a height of {height_above_fwl_ft:g} ft is below the free water "
                    "level, where Eq. 4-34 gives a negative capillary pressure. Below "
                    "the FWL the rock is water"),
            needed=("a height at or above the free water level",), source=AHMED_FWL)
    _positive("delta_rho_lb_ft3", delta_rho_lb_ft3)

    pc = height_above_fwl_ft * delta_rho_lb_ft3 / PSI_FT_PER_LB_FT3       # Eq. 4-34

    if method == "analytical":
        need = _missing(swc=swc, sor=sor, pc_swc_psi=pc_swc_psi, n_p=n_p)
        if need:
            return Refusal(
                reason=("Ahmed Eq. 5-24 is anchored on the connate-water capillary "
                        f"pressure and the saturation endpoints; missing "
                        f"{', '.join(need)}"),
                needed=need, source=AHMED_RELPERM)
        _fraction("swc", swc)
        _fraction("sor", sor)
        _positive("pc_swc_psi", pc_swc_psi)
        _positive("n_p", n_p)
        window = 1.0 - swc - sor
        if window <= 0:
            raise ValueError(f"S_wc + S_or = {swc + sor:g} leaves no saturation window")
        flags: tuple[str, ...] = (
            "Ahmed Eq. 5-24 reaches S_w = 1 - S_orw at p_c = 0, not S_w = 1: it is the "
            "capillary-pressure companion of Eqs. 5-22/5-23 and shares their saturation "
            "window. The saturation this returns AT the free water level is "
            f"{1.0 - sor:.3f}, not 1.0",)
        if pc >= pc_swc_psi:
            sw = swc
            flags += (f"p_c = {pc:.3f} psi is at or above the connate-water capillary "
                      f"pressure of {pc_swc_psi:g} psi, so this height is above the "
                      "transition zone and S_w is pinned at S_wc",)
        else:
            sw = 1.0 - sor - window * (pc / pc_swc_psi) ** (1.0 / n_p)
        transition_ft = PSI_FT_PER_LB_FT3 * pc_swc_psi / delta_rho_lb_ft3
        return Quantity(
            sw, "v/v",
            "water saturation at height above the free water level, Ahmed Eq. 5-24 "
            "inverted with p_c from Eq. 4-34", f"{AHMED_RELPERM}; {AHMED_FWL}",
            inputs={"height_above_fwl_ft": height_above_fwl_ft, "pc_psi": pc,
                    "delta_rho_lb_ft3": delta_rho_lb_ft3, "swc": swc, "sor": sor,
                    "pc_swc_psi": pc_swc_psi, "n_p": n_p,
                    "transition_zone_ft": transition_ft},
            assumptions={"model": "Ahmed Eq. 5-24 (oil-water analytical p_c), inverted",
                         "datum": "height above the FREE WATER LEVEL, not the WOC "
                                  "(Ahmed Eq. 4-35 gives the offset)",
                         "brooks_corey": "not implemented: Brooks and Corey do not "
                                         "appear in this corpus. Eq. 5-24 is the same "
                                         "power-law shape and is printed here"},
            flags=flags)

    # leverett_j
    if not lab_curve:
        return Refusal(
            reason=("the Leverett route rescales a measured laboratory curve; it needs "
                    "lab_curve as (S_w, p_c) pairs. Ahmed #50: 'Capillary pressure data "
                    "are obtained on small core samples'"),
            needed=("lab_curve, a sequence of (S_w, p_c_psi) pairs",),
            source=AHMED_LEVERETT)

    pairs: list[tuple[float, float]] = []
    for item in lab_curve:
        if not isinstance(item, Sequence) or len(item) != 2:
            raise ValueError(f"lab_curve entries must be (S_w, p_c) pairs, got {item!r}")
        if not _finite(item[1]) or item[1] < 0:
            raise ValueError(f"lab_curve p_c must be a non-negative number, got {item[1]!r}")
        pairs.append((_fraction("lab_curve S_w", item[0]), float(item[1])))
    if len(pairs) < 2:
        return Refusal(reason="lab_curve needs at least two points to read against",
                       needed=("a second (S_w, p_c) point",), source=AHMED_LEVERETT)

    converted: list[tuple[float, float]] = []
    for sw_i, pc_lab in pairs:
        if pc_lab <= 0:
            converted.append((sw_i, 0.0))
            continue
        result = capillary_pressure(
            pc_lab, sigma_lab_dynes_cm=sigma_lab_dynes_cm,
            sigma_res_dynes_cm=sigma_res_dynes_cm, phi_core=phi_core,
            k_core_md=k_core_md, phi_res=phi_res, k_res_md=k_res_md)
        if isinstance(result, Refusal):
            return result
        converted.append((sw_i, result.value))

    converted.sort(key=lambda pair: pair[1])          # ascending p_c
    lo_sw, lo_pc = converted[0]
    hi_sw, hi_pc = converted[-1]
    if pc <= lo_pc:
        sw, where = lo_sw, "below the lowest measured p_c; held at that point"
    elif pc >= hi_pc:
        sw, where = hi_sw, "above the highest measured p_c; held at that point"
    else:
        sw, where = hi_sw, "interpolated"
        for (sw_a, pc_a), (sw_b, pc_b) in zip(converted, converted[1:]):
            if pc_a <= pc <= pc_b:
                span = pc_b - pc_a
                sw = sw_a if span == 0 else sw_a + (sw_b - sw_a) * (pc - pc_a) / span
                break

    return Quantity(
        sw, "v/v",
        "water saturation read off a laboratory capillary-pressure curve converted to "
        "reservoir conditions (Ahmed Eq. 4-37), at the p_c for this height above the "
        "free water level (Eq. 4-34)", f"{AHMED_LEVERETT}; {AHMED_FWL}",
        inputs={"height_above_fwl_ft": height_above_fwl_ft, "pc_psi": pc,
                "delta_rho_lb_ft3": delta_rho_lb_ft3, "points": len(converted),
                "pc_res_range_psi": [lo_pc, hi_pc]},
        assumptions={"model": "Leverett J-function invariance (Ahmed #50)",
                     "interpolation": "linear in p_c between measured points",
                     "datum": "height above the FREE WATER LEVEL, not the WOC"},
        flags=(f"S_w at this height was {where}",) if where != "interpolated" else ())


# --------------------------------------------------------------------------
# N7 - free_water_level
# --------------------------------------------------------------------------

def free_water_level(woc_ft: float, delta_rho_lb_ft3: float,
                     entry_pressure_psi: float | None = None) -> Quantity | Refusal:
    """FWL from the WOC and the capillary entry pressure. Ahmed Eq. 4-35.

        FWL = WOC + 144 p_d / delta-rho

    Refuses without an entry pressure, and that refusal is the entire reason this
    tool is separate from `contact_project`. Ahmed #48: "the free water level is
    defined by zero capillary pressure", and the WOC is where S_w reaches 100%.
    They coincide only if the largest pore is large enough to have no capillary
    rise at all. Substituting one for the other moves the contact by the
    entry-pressure head, which on his own Example 4-5 is 10.5 feet and on a
    tighter rock with a lower density contrast is tens of feet.

    Depths increase downward, so the FWL comes back BELOW the WOC.
    """
    if not _finite(woc_ft):
        raise ValueError(f"woc_ft must be a number, got {woc_ft!r}")
    _positive("delta_rho_lb_ft3", delta_rho_lb_ft3)

    if entry_pressure_psi is None:
        return Refusal(
            reason=(
                "no capillary entry (displacement) pressure was supplied, and without it "
                "the free water level cannot be separated from the water-oil contact. "
                "Ahmed #48: 'there is a difference between the free water level (FWL) and "
                "the depth at which 100% water saturation exists ... the free water level "
                "is defined by zero capillary pressure.' Returning the WOC as the FWL "
                "would move the contact by 144 p_d / delta-rho feet, which is 10.5 ft on "
                "Ahmed's own Example 4-5 and more in tighter rock"),
            needed=("entry_pressure_psi, the displacement pressure p_d read at the foot "
                    "of the capillary pressure curve (Ahmed #46, Figure 4-5)",),
            source=AHMED_FWL)
    _positive("entry_pressure_psi", entry_pressure_psi)

    offset = PSI_FT_PER_LB_FT3 * entry_pressure_psi / delta_rho_lb_ft3
    return Quantity(
        woc_ft + offset, "ft",
        "free water level from the water-oil contact and the capillary entry pressure "
        "(Ahmed Eq. 4-35)", f"{AHMED_FWL}; {AHMED_FWL_EXAMPLE}",
        inputs={"woc_ft": woc_ft, "entry_pressure_psi": entry_pressure_psi,
                "delta_rho_lb_ft3": delta_rho_lb_ft3, "offset_ft": offset},
        assumptions={"sign": "depth increases downward, so the FWL is BELOW the WOC by "
                             "the entry-pressure head",
                     "density_unit": "lb/ft3, which is what the 144 in Eq. 4-35 is built "
                                     "on (144 in2/ft2)",
                     "woc_definition": "the depth at which S_w reaches 100%, which is "
                                       "what a log pick gives"},
        flags=("the WOC and the FWL are different depths; this tool converts between "
               "them and does not treat either as the other",))
