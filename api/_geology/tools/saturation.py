"""Shaly-sand water saturation — tool #36 `shaly_sand_sw` (group D).

Three published models for the same quantity, reported side by side. See
`specs/36-shaly_sand_sw.md`. The decisions that are not obvious from the code:

**Waxman-Smits is genuinely sourced, and it was checked here rather than taken on
trust.** `tool-verification.md:98` says it is not ("16 mentions, all narrative; no
Qv, no CEC") and `tool-catalog.md:64` says that finding is stale. The corpus
settles it: `jmest-waxman-smits-saturation-modelling#4` prints Eq. 18
`C_t = φ^m* S_w^n* (C_W + B·Q_V/S_W)`, the working form
`1/R_t = φ^m* S_w^n* (1/R_w + B·Q_v/S_w)` in its Figure 4 procedure box, and
Eq. 23 solved for `S_w`; `#3` defines `B` and `Q_v` and `C_e = B·Q_V`; `#4` § 6
gives three ways to obtain `Q_v`. The catalog is right; the verification predates
the document. So all three legs are real and none is fabricated.

**Every member of what this returns carries its own anchor.** That is the whole
point of the file. `coning_critical_rate` was caught labelling a four-method
spread with one method's anchor (`tool-verification.md:101`), so here each leg is
a `Quantity` built with the anchor of the equation that produced *it*, a derived
`R_wa` carries `asquith#44` rather than the `#50` of the saturations it feeds, and
the `Range` names in its own `source` exactly the anchors of the legs that are in
its `members` — never one more.

**A leg with missing inputs refuses as that leg.** Each model needs something the
others do not: Waxman-Smits needs `B` and `Q_v` and lab `m*`/`n*`, dual water
needs `S_wb` and `R_b`, Simandoux needs `R_sh`. One absent input takes out one
leg and leaves the others to answer. The only thing that refuses the whole call is
missing `R_w` provenance, and that is because all three models are built on `R_w`.

**Two things Waxman-Smits needs are not in the corpus at all, and both refuse
rather than get filled in.** `B` exists only as an image chart (`jmest#3`,
Figure 2) — no correlation, no table — so it is a required caller input. And no
document anywhere in the corpus prints the `CEC` → `Q_v` conversion; `jmest`
conflates the two symbols outright. Passing a lab `CEC` therefore gets a refusal
naming the missing conversion, not a number off by a factor of ten to a thousand.

**The `B` unit convention here is not the one the source prints.** `jmest#3` says
`B` is in mho·cm²/meq and `B·Q_v` in mho/cm, but that term is added to
`C_W = 1/R_W`, which is mho/m — a factor of 100 the source never reconciles. The
parameter is named for the consistent convention, `(mho/m)/(meq/ml)`, and every
Waxman-Smits result flags the discrepancy. See the spec's Open Questions.

**Eq. 23 is solved by bisection, not by the fixed-point iteration it suggests.**
The source says only "Solution for `S_W` has to be iterative". Eq. 18's left side
is strictly increasing in `S_w` for `n* >= 1`, so bisection has a guaranteed
unique root and cannot fail to converge; a fixed-point sweep has no such
guarantee. For `n* < 1` monotonicity is lost and the leg refuses rather than
returning whichever root it stumbled onto.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field
from typing import Any

from .petrophysics import archie_sw, resistivity_at_temperature
from .result import Quantity, Range, Refusal

# --- corpus anchors -----------------------------------------------------------
#
# `#50` carries Simandoux Eq. 7.48 and dual water Eqs. 7.49-7.52 on pp. 127-128,
# plus the Rsh warning and the salinity applicability limit. `#44` is a different
# segment of the same book and is the only place Rwa is defined (Eq. 7.16), so a
# derived Rwa cites it and not `#50`.

ASQUITH_SHALY_SAND = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#50"
ASQUITH_RWA = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#44"

# `#4` holds Eq. 18, the Figure 4 working form, Eq. 23, the 10% shale-term rule,
# the 0.25 maximum-increase statement, and section 6 on obtaining Qv (including
# the Juhasz normalised-Qv method). `#3` is where B and Qv are defined and where
# the "B" chart (Figure 2) lives.
JMEST_WS_EQUATION = "01-curve-reading/jmest-waxman-smits-saturation-modelling#4"
JMEST_WS_B_CHART = "01-curve-reading/jmest-waxman-smits-saturation-modelling#3"

#: Leg name -> the anchor of the equation that produces it. A spread's `source`
#: is built from this table for exactly the legs that answered, never for all.
MODEL_SOURCES: dict[str, str] = {
    "simandoux": ASQUITH_SHALY_SAND,
    "waxman_smits": JMEST_WS_EQUATION,
    "dual_water_swt": ASQUITH_SHALY_SAND,
}

MODEL_LABELS: dict[str, str] = {
    "simandoux": "Simandoux 1963 (Asquith Eq. 7.48)",
    "waxman_smits": "Waxman-Smits (JMEST Eq. 18/23)",
    "dual_water_swt": "dual water Swt (Asquith Eq. 7.49)",
}

# --- published constants ------------------------------------------------------
#
# Simandoux's own pair, printed in Eq. 7.48. They are not `a`/`m`/`n` in disguise
# and are deliberately not overridable: at Vsh = 0 the equation collapses to
# 0.4*sqrt(5) = 0.8944 times Archie, i.e. Archie with a = 0.8, and that offset is
# a property of the published form.
SIMANDOUX_NUMERATOR = 0.4      # asquith#50, Eq. 7.48
SIMANDOUX_RADICAND = 5.0       # asquith#50, Eq. 7.48
SIMANDOUX_CLEAN_FACTOR = SIMANDOUX_NUMERATOR * math.sqrt(SIMANDOUX_RADICAND)

#: "The effect of shaliness may be ignored if this term is equal to or less than
#: 10% i.e. 0.1." -- jmest#4, item (2). The term is Rw*B*Qv/Sw.
WS_SHALE_TERM_NEGLIGIBLE = 0.1  # jmest#4

#: "the maximum increase in hydrocarbon saturation when using Waxman-Smits
#: equation instead of Archie's equation is about 25% (in absolute saturation)"
#: -- jmest#4. Exceeding it means the inputs, not the rock, are odd.
WS_MAX_HC_INCREASE = 0.25       # jmest#4

#: "Most shaly sand interpretation problems occur in formations with Rw values
#: that are not too salty [NaCl < 20,000 ppm or Rw > 0.3 ohm-m at 80 degF
#: (Hilchie, 1978)]." -- asquith#50. Below this, an uncorrected Archie is close.
SHALY_SAND_RW_LIMIT_OHMM = 0.3   # asquith#50
SHALY_SAND_RW_LIMIT_DEGF = 80.0  # asquith#50
SHALY_SAND_NACL_LIMIT_PPM = 20000.0  # asquith#50

# --- solver settings (house, not published) -----------------------------------
#
# The source says only that the solution "has to be iterative"; the bracket and
# the tolerance are ours. The upper bracket is deliberately far above any
# physical saturation so that an unphysical answer is *reported and flagged*
# rather than clipped, and only a root beyond it counts as inconsistent inputs.
WS_SW_BRACKET_HI = 10.0
WS_BISECTION_STEPS = 200

_RW_PROVENANCE_NEEDED = (
    "Rw from rw_from_sp, rw_pickett, or a measured water analysis",
)


# --- return records -----------------------------------------------------------


@dataclass(frozen=True)
class DualWaterSaturation:
    """The dual-water leg. Four published quantities, not one.

    Eq. 7.49 gives the total saturation, 7.51 the effective one and 7.52 the
    hydrocarbon volume; reporting only `Swt` would drop two thirds of what the
    source prints. Every field is a `Quantity`, and `rwa` carries `asquith#44`
    when it was derived from Eq. 7.16 rather than supplied.
    """

    swt: Quantity                # Eq. 7.49
    swe: Quantity                # Eq. 7.51
    phi_h: Quantity | Refusal    # Eq. 7.52; refuses when only Rwa was supplied
    b: Quantity                  # Eq. 7.50
    rwa: Quantity                # supplied, or Eq. 7.16

    @property
    def value(self) -> float:
        """The leg's headline number, so it reads like the other two legs."""
        return self.swt.value


def _models(simandoux: Quantity | Refusal, waxman_smits: Quantity | Refusal,
            dual_water: DualWaterSaturation | Refusal
            ) -> dict[str, Quantity | Refusal]:
    """Leg name -> its `Quantity`, or the `Refusal` standing in for it.

    Dual water is represented by `Swt`, the direct product of Eq. 7.49; its `Swe`
    and `phi_h` stay on the `DualWaterSaturation` record. Keys match
    `MODEL_SOURCES` so a spread's anchors can be looked up per participating leg.
    """
    dw: Quantity | Refusal
    dw = dual_water.swt if isinstance(dual_water, DualWaterSaturation) else dual_water
    return {"simandoux": simandoux, "waxman_smits": waxman_smits,
            "dual_water_swt": dw}


@dataclass(frozen=True)
class ShalySandSpread:
    """What #36 returns: three legs and, if two or more answered, their spread.

    A leg that could not be computed sits in its own slot as a `Refusal`. It is
    never omitted and never back-filled from a neighbouring model, so a caller
    reading `.waxman_smits` always learns either the number or why there isn't
    one.
    """

    simandoux: Quantity | Refusal
    waxman_smits: Quantity | Refusal
    dual_water: DualWaterSaturation | Refusal
    spread: Range | Refusal
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    @property
    def models(self) -> dict[str, Quantity | Refusal]:
        """Leg name -> its `Quantity`, or the `Refusal` that stands in for it."""
        return _models(self.simandoux, self.waxman_smits, self.dual_water)

    @property
    def answered(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.models.items() if isinstance(v, Quantity))

    @property
    def refused(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.models.items() if isinstance(v, Refusal))


# --- shared helpers -----------------------------------------------------------


def _rw_gate(rw_source: str | None, source: str) -> Refusal | None:
    """The `archie_sw` gate, applied identically here.

    A saturation computed from a guessed Rw is indistinguishable from a good one
    on the page, and all three of these models are built on Rw. So this is the
    one condition that takes down the whole call rather than a single leg.
    """
    if not rw_source:
        return Refusal(
            reason="Rw has no stated provenance; no shaly-sand model will return "
                   "a point saturation",
            needed=_RW_PROVENANCE_NEEDED,
            source=source,
        )
    return None


def _check_positive(name: str, value: float) -> None:
    """Impossible arguments are programmer error, per the build doc."""
    if value is None or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number, got {value!r}")


def _common_flags(rt_invasion_corrected: bool) -> list[str]:
    if rt_invasion_corrected:
        return []
    return ["Rt not declared invasion-corrected; deep readings are not Rt"]


def _salinity_flags(rw: float, rw_temp_degf: float | None) -> list[str]:
    """The `asquith#50` applicability limit, or a note that it could not be run.

    The limit is quoted at 80 degF, so an Rw at any other temperature has to be
    converted before it can be compared. The Arps correction that does this is
    already a tool, so it is called rather than re-derived. When no temperature is
    given the tool says the check was skipped; it does not assume 80 degF.
    """
    if rw_temp_degf is None:
        return ["Rw temperature not given, so the asquith#50 salinity "
                "applicability limit (Rw > 0.3 ohm-m at 80 degF) was not checked"]
    rw_80 = resistivity_at_temperature(rw, rw_temp_degf, SHALY_SAND_RW_LIMIT_DEGF,
                                       units="degF")
    if rw_80.value <= SHALY_SAND_RW_LIMIT_OHMM:
        return [f"Rw = {rw_80.value:.4g} ohm-m at 80 degF is at or below the "
                f"{SHALY_SAND_RW_LIMIT_OHMM} ohm-m / "
                f"{SHALY_SAND_NACL_LIMIT_PPM:.0f} ppm NaCl limit of asquith#50: "
                "where formation water is very salty, shale has less effect and "
                "an uncorrected Archie Sw is close to the true saturation"]
    return []


# --- leg 1: Simandoux ---------------------------------------------------------


def simandoux_sw(rt: float, phi_effective: float | None, rw: float,
                 rw_source: str | None, *,
                 vshale: float | None = None, rsh: float | None = None,
                 rw_temp_degf: float | None = None,
                 rt_invasion_corrected: bool = False) -> Quantity | Refusal:
    """Simandoux 1963, Asquith Eq. 7.48 (`asquith#50`, p. 127).

        Sw = (0.4 Rw / phi^2) * [ sqrt((Vsh/Rsh)^2 + 5 phi^2 / (Rt Rw)) - Vsh/Rsh ]

    `phi` is the shale-corrected (effective) porosity: the source's section opens
    "After the shale-corrected porosity has been determined, the water saturation
    can be calculated."
    """
    gate = _rw_gate(rw_source, ASQUITH_SHALY_SAND)
    if gate is not None:
        return gate
    _check_positive("rt", rt)
    _check_positive("rw", rw)

    missing = [name for name, value in
               (("phi_effective", phi_effective), ("vshale", vshale), ("rsh", rsh))
               if value is None]
    if missing:
        return Refusal(
            reason="Simandoux (Asquith Eq. 7.48) needs " + ", ".join(missing)
                   + "; the other shaly-sand models are unaffected",
            needed=tuple(missing),
            source=ASQUITH_SHALY_SAND,
        )
    assert phi_effective is not None and vshale is not None and rsh is not None
    if phi_effective <= 0:
        return Refusal(
            reason="Simandoux divides by phi^2; a non-positive shale-corrected "
                   "porosity has no saturation",
            needed=("a positive shale-corrected porosity",),
            source=ASQUITH_SHALY_SAND,
        )
    if rsh <= 0:
        return Refusal(
            reason="Simandoux divides Vsh by Rsh; shale resistivity must be positive",
            needed=("Rsh from an adjacent shale bed",),
            source=ASQUITH_SHALY_SAND,
        )

    vsh_over_rsh = vshale / rsh
    radicand = (vsh_over_rsh ** 2
                + SIMANDOUX_RADICAND * phi_effective ** 2 / (rt * rw))
    sw = ((SIMANDOUX_NUMERATOR * rw / phi_effective ** 2)
          * (math.sqrt(radicand) - vsh_over_rsh))

    flags = _common_flags(rt_invasion_corrected)
    flags.append("Rsh is assumed equal to the resistivity of the shale within the "
                 "formation; asquith#50: 'This assumption is not always correct.'")
    flags.extend(_salinity_flags(rw, rw_temp_degf))
    if sw > 1.0:
        flags.append("Sw > 1.0 - check Rw, Rsh, or that the interval is wet")
    return Quantity(
        sw, "v/v", MODEL_LABELS["simandoux"], ASQUITH_SHALY_SAND,
        inputs={"Rt": rt, "phi_effective": phi_effective, "Rw": rw,
                "Vsh": vshale, "Rsh": rsh},
        assumptions={
            "Rw_source": rw_source,
            "porosity_basis": "shale-corrected (effective), per asquith#50",
            "published_constants": {"numerator": SIMANDOUX_NUMERATOR,
                                    "radicand": SIMANDOUX_RADICAND},
            "clean_sand_factor_vs_archie": SIMANDOUX_CLEAN_FACTOR,
        },
        flags=tuple(flags),
    )


# --- leg 2: Waxman-Smits ------------------------------------------------------


def _ws_residual(sw: float, rt: float, phi_total: float, rw: float,
                 m_star: float, n_star: float, b: float, qv: float) -> float:
    """Eq. 18 rearranged to f(Sw) = 0.

    f(Sw) = phi^m* Sw^n* (1/Rw + B Qv / Sw) - 1/Rt

    Strictly increasing in Sw for n* >= 1, which is what makes bisection safe.
    """
    return phi_total ** m_star * sw ** n_star * (1.0 / rw + b * qv / sw) - 1.0 / rt


def waxman_smits_sw(rt: float, phi_total: float | None, rw: float,
                    rw_source: str | None, *,
                    m_star: float | None = None, n_star: float | None = None,
                    b_mho_per_m_per_meq_ml: float | None = None,
                    qv_meq_per_ml: float | None = None,
                    qv_shale_meq_per_ml: float | None = None,
                    vshale: float | None = None,
                    cec_meq_per_100g: float | None = None,
                    rw_temp_degf: float | None = None,
                    rt_invasion_corrected: bool = False) -> Quantity | Refusal:
    """Waxman-Smits, JMEST Eq. 18 / Eq. 23 (`jmest#4`, p. 4989).

        1/Rt = phi^m* Sw^n* (1/Rw + B Qv / Sw)

    `phi` is total porosity. `m*` and `n*` have no defaults: the source's own
    procedure (Figure 4) says "m* and n* from lab. measurements". `B` has no
    default either, because the source supplies it only as an image chart.
    """
    gate = _rw_gate(rw_source, JMEST_WS_EQUATION)
    if gate is not None:
        return gate
    _check_positive("rt", rt)
    _check_positive("rw", rw)

    if b_mho_per_m_per_meq_ml is None:
        return Refusal(
            reason="Waxman-Smits needs B, the counter-ion equivalent conductance. "
                   "The corpus supplies it only as an image chart (jmest#3, "
                   "Figure 2: 'B as a function of water resistivity (coupled to "
                   "salinity) and temperature') - there is no correlation or "
                   "table to evaluate, so it cannot be computed here",
            needed=("B in (mho/m)/(meq/ml), read from the jmest#3 Figure 2 chart "
                    "at this Rw and formation temperature",),
            source=JMEST_WS_B_CHART,
        )

    missing = [name for name, value in
               (("phi_total", phi_total), ("m_star", m_star), ("n_star", n_star))
               if value is None]
    if missing:
        return Refusal(
            reason="Waxman-Smits (JMEST Eq. 18) needs " + ", ".join(missing)
                   + "; jmest#4 states 'm* and n* from lab. measurements', so "
                     "there are no defaults for them here",
            needed=tuple(missing),
            source=JMEST_WS_EQUATION,
        )
    assert phi_total is not None and m_star is not None and n_star is not None

    qv = qv_meq_per_ml
    qv_method = "Qv supplied directly"
    qv_source = JMEST_WS_EQUATION
    if qv is None and qv_shale_meq_per_ml is not None and vshale is not None:
        # Juhasz normalised Qv, jmest#4 s.6 method (3): "Qv is then calculated in
        # shaly sand by multiplying Qv in pure shale by shale fraction Vsh."
        qv = qv_shale_meq_per_ml * vshale
        qv_method = "Juhasz normalised Qv = Qv(shale) * Vsh (jmest#4 s.6 method 3)"
    if qv is None:
        if cec_meq_per_100g is not None:
            return Refusal(
                reason="a laboratory CEC in meq/100 g is not Qv in meq/ml, and no "
                       "document in this corpus prints the conversion. jmest "
                       "conflates the two symbols outright ('the Cation Exchange "
                       "Capacity (CEC) also known as the Qv', jmest#4 s.6) but "
                       "never gives the grain-density and porosity relation that "
                       "converts one to the other. Using the CEC number as Qv "
                       "would be a unit error of two to three orders of magnitude",
                needed=("Qv in meq/ml, from lab measurement, from a water-zone "
                        "Waxman-Smits fit, or from Qv(shale) * Vsh (the three "
                        "methods jmest#4 s.6 lists)",),
                source=JMEST_WS_EQUATION,
            )
        return Refusal(
            reason="Waxman-Smits needs Qv, the cation-exchange capacity per unit "
                   "pore volume; none supplied and no Qv(shale) + Vsh pair to "
                   "derive it from",
            needed=("qv_meq_per_ml, or qv_shale_meq_per_ml together with vshale",),
            source=JMEST_WS_EQUATION,
        )

    _check_positive("m_star", m_star)
    _check_positive("n_star", n_star)
    if phi_total <= 0:
        return Refusal(
            reason="Waxman-Smits raises total porosity to m*; a non-positive "
                   "porosity has no saturation",
            needed=("a positive total porosity",),
            source=JMEST_WS_EQUATION,
        )
    if qv < 0:
        raise ValueError(f"Qv must be non-negative, got {qv!r}")
    if n_star < 1.0:
        return Refusal(
            reason=f"n* = {n_star} is below 1, where Eq. 18's right-hand side is "
                   "no longer monotone in Sw and the equation can have more than "
                   "one root; the source gives no rule for choosing between them",
            needed=("n* >= 1 from lab measurement",),
            source=JMEST_WS_EQUATION,
        )

    lo, hi = 1e-12, WS_SW_BRACKET_HI
    args = (rt, phi_total, rw, m_star, n_star, b_mho_per_m_per_meq_ml, qv)
    if _ws_residual(hi, *args) < 0.0:
        return Refusal(
            reason=f"Eq. 18 has no root below Sw = {WS_SW_BRACKET_HI}; Rt, phi, "
                   "Rw, B and Qv are mutually inconsistent for this interval",
            needed=("consistent Rt / phi_total / Rw / B / Qv",),
            source=JMEST_WS_EQUATION,
        )
    if _ws_residual(lo, *args) > 0.0:
        # At n* = 1 the clay term B.Qv.phi^m* does not vanish as Sw -> 0, so the
        # bracket's lower end is not guaranteed negative. Bisecting anyway would
        # return ~0 and look like a gas-filled sand.
        return Refusal(
            reason="Eq. 18 has no root above Sw = 0: the clay conductivity "
                   f"B.Qv.phi^m* alone already exceeds 1/Rt = {1.0 / rt:.4g} "
                   "mho/m, so no saturation satisfies the equation. Check B "
                   "(see the unit caveat in spec Open Question 1) and Qv",
            needed=("B and Qv consistent with the measured Rt",),
            source=JMEST_WS_EQUATION,
        )
    for _ in range(WS_BISECTION_STEPS):
        mid = 0.5 * (lo + hi)
        if _ws_residual(mid, *args) < 0.0:
            lo = mid
        else:
            hi = mid
    sw = 0.5 * (lo + hi)

    shale_term = rw * b_mho_per_m_per_meq_ml * qv / sw
    flags = _common_flags(rt_invasion_corrected)
    flags.append(
        "B taken in (mho/m)/(meq/ml) to match Cw = 1/Rw in mho/m. jmest#3 prints "
        "B in mho.cm^2/meq and B.Qv in mho/cm, which is 100x inconsistent with Rw "
        "in ohm-m; a chart value read in the source's stated units must be "
        "multiplied by 100 before it is passed here. See spec Open Question 1")
    flags.extend(_salinity_flags(rw, rw_temp_degf))
    if shale_term <= WS_SHALE_TERM_NEGLIGIBLE:
        flags.append(
            f"Rw.B.Qv/Sw = {shale_term:.4g} <= {WS_SHALE_TERM_NEGLIGIBLE}; jmest#4 "
            "says 'The effect of shaliness may be ignored' at or below this, so "
            "an uncorrected Archie Sw is adequate here")
    if sw > 1.0:
        flags.append("Sw > 1.0 - check Rw, B, Qv, or that the interval is wet")

    # The source's own claim about its result: Waxman-Smits reads lower than
    # Archie, and by no more than 0.25 in absolute saturation. Archie comes from
    # the real tool so the comparison number arrives with its own provenance
    # rather than being recomputed here without one.
    archie = archie_sw(rt, phi_total, rw, rw_source, a=1.0, m=m_star, n=n_star,
                       rt_invasion_corrected=rt_invasion_corrected)
    assumptions: dict[str, Any] = {
        "Rw_source": rw_source,
        "porosity_basis": "total, per jmest#4",
        "m*": m_star, "n*": n_star,
        "m_star_n_star_provenance": "caller-supplied; jmest#4 requires lab "
                                    "measurement or regional data",
        "B_units": "(mho/m)/(meq/ml)",
        "Qv_method": qv_method,
        "Qv_source": qv_source,
        "shale_term_Rw_B_Qv_over_Sw": shale_term,
        "solver": f"bisection on Eq. 18, {WS_BISECTION_STEPS} steps over "
                  f"(0, {WS_SW_BRACKET_HI}]; jmest#4: 'Solution for Sw has to be "
                  f"iterative'",
    }
    if isinstance(archie, Quantity):
        assumptions["archie_reference"] = archie
        if archie.value - sw > WS_MAX_HC_INCREASE:
            flags.append(
                f"Waxman-Smits Sw is {archie.value - sw:.4g} below Archie, past "
                f"the {WS_MAX_HC_INCREASE} maximum absolute increase in "
                "hydrocarbon saturation jmest#4 states for this substitution; "
                "check B and Qv")

    return Quantity(
        sw, "v/v", MODEL_LABELS["waxman_smits"], JMEST_WS_EQUATION,
        inputs={"Rt": rt, "phi_total": phi_total, "Rw": rw,
                "B": b_mho_per_m_per_meq_ml, "Qv": qv},
        assumptions=assumptions,
        flags=tuple(flags),
    )


# --- leg 3: dual water --------------------------------------------------------


def dual_water_sw(rt: float, phi_total: float | None, rw: float,
                  rw_source: str | None, *,
                  swb: float | None = None, rb: float | None = None,
                  rwa: float | None = None,
                  a: float = 1.0, m: float = 2.0,
                  rw_temp_degf: float | None = None,
                  rt_invasion_corrected: bool = False
                  ) -> DualWaterSaturation | Refusal:
    """Dual water, Asquith Eqs. 7.49-7.52 (`asquith#50`, pp. 127-128).

        Swt   = b + sqrt(b^2 + Rw/Rwa)          (7.49)
        b     = Swb (1 - Rw/Rb) / 2             (7.50)
        Swe   = (Swt - Swb) / (1 - Swb)         (7.51)
        phi_h = phi_t (1 - Swt)                 (7.52)

    `#50` says Rwa "is calculated" without giving the formula; the book's only
    Rwa is Eq. 7.16 in `#44`, so a derived Rwa cites `#44`. A caller-supplied Rwa
    is preferred and cites nothing but itself.
    """
    gate = _rw_gate(rw_source, ASQUITH_SHALY_SAND)
    if gate is not None:
        return gate
    _check_positive("rt", rt)
    _check_positive("rw", rw)

    missing = [name for name, value in (("swb", swb), ("rb", rb)) if value is None]
    if missing:
        return Refusal(
            reason="dual water (Asquith Eqs. 7.49-7.50) needs " + ", ".join(missing)
                   + "; asquith#50 takes both from nearby shales and clean sands, "
                     "so neither has a default; the other shaly-sand models are "
                     "unaffected",
            needed=tuple(missing),
            source=ASQUITH_SHALY_SAND,
        )
    assert swb is not None and rb is not None
    if rwa is None and phi_total is None:
        return Refusal(
            reason="dual water needs Rwa, and deriving it from Asquith Eq. 7.16 "
                   "needs total porosity; neither was supplied",
            needed=("rwa, or phi_total to derive it from Eq. 7.16",),
            source=ASQUITH_RWA,
        )
    if rb <= 0:
        return Refusal(
            reason="Eq. 7.50 divides Rw by Rb; bound-water resistivity must be "
                   "positive",
            needed=("Rb from an adjacent shale",),
            source=ASQUITH_SHALY_SAND,
        )
    if not 0.0 <= swb < 1.0:
        return Refusal(
            reason=f"Swb = {swb} is outside [0, 1); Eq. 7.51 divides by 1 - Swb",
            needed=("a bound-water saturation in [0, 1)",),
            source=ASQUITH_SHALY_SAND,
        )

    common = _common_flags(rt_invasion_corrected)
    common.extend(_salinity_flags(rw, rw_temp_degf))
    shared_inputs = {"Rt": rt, "Rw": rw, "Swb": swb, "Rb": rb}

    if rwa is not None:
        rwa_q = Quantity(
            rwa, "ohm-m", "apparent water resistivity, caller-supplied",
            ASQUITH_SHALY_SAND,
            inputs={"Rwa": rwa},
            assumptions={"origin": "supplied by caller, not derived"},
        )
    else:
        assert phi_total is not None
        if phi_total <= 0:
            return Refusal(
                reason="Eq. 7.16 raises total porosity to m; a non-positive "
                       "porosity gives no Rwa",
                needed=("a positive total porosity",),
                source=ASQUITH_RWA,
            )
        rwa_q = Quantity(
            rt * phi_total ** m / a, "ohm-m",
            "apparent water resistivity (Asquith Eq. 7.16)", ASQUITH_RWA,
            inputs={"Rt": rt, "phi": phi_total},
            assumptions={"a": a, "m": m,
                         "note": "Archie's a and m, not Waxman-Smits m*"},
        )
    if rwa_q.value <= 0:
        return Refusal(
            reason="Eq. 7.49 divides Rw by Rwa; apparent water resistivity must "
                   "be positive",
            needed=("a positive Rwa",),
            source=ASQUITH_RWA,
        )

    b_val = swb * (1.0 - (rw / rb)) / 2.0
    b_q = Quantity(
        b_val, "dimensionless", "dual water b term (Asquith Eq. 7.50)",
        ASQUITH_SHALY_SAND,
        inputs=dict(shared_inputs),
        assumptions={"Rw_source": rw_source},
        flags=("b is negative because Rb < Rw, i.e. the bound water is more "
               "conductive (more saline) than the free water; that is the usual "
               "case and Eq. 7.49 still gives a positive Swt",)
        if b_val < 0 else (),
    )

    swt_val = b_val + math.sqrt(b_val * b_val + rw / rwa_q.value)
    swt_flags = list(common)
    if swt_val > 1.0:
        swt_flags.append("Swt > 1.0 - check Rw, Rwa, Swb or Rb")
    if swt_val < swb:
        swt_flags.append(
            f"Swt = {swt_val:.4g} is below Swb = {swb}; Eq. 7.51 then returns a "
            "negative effective saturation, which means the bound-water pick is "
            "inconsistent with the resistivity")
    swt_q = Quantity(
        swt_val, "v/v", MODEL_LABELS["dual_water_swt"], ASQUITH_SHALY_SAND,
        inputs={**shared_inputs, "Rwa": rwa_q.value, "b": b_val},
        assumptions={"Rw_source": rw_source,
                     "porosity_basis": "total, per asquith#50 Eq. 7.52",
                     "Rwa_source": rwa_q.source},
        flags=tuple(swt_flags),
    )

    swe_val = (swt_val - swb) / (1.0 - swb)
    swe_q = Quantity(
        swe_val, "v/v", "dual water Swe (Asquith Eq. 7.51)", ASQUITH_SHALY_SAND,
        inputs={"Swt": swt_val, "Swb": swb},
        assumptions={"basis": "effective (free-water) saturation"},
        flags=("Swe < 0; the bound-water saturation exceeds the total",)
        if swe_val < 0 else (),
    )

    if phi_total is None:
        phi_h_q: Quantity | Refusal = Refusal(
            reason="Eq. 7.52 needs total porosity to turn Swt into a hydrocarbon "
                   "volume; Rwa was supplied directly so none was needed for the "
                   "saturations",
            needed=("phi_total",),
            source=ASQUITH_SHALY_SAND,
        )
    else:
        phi_h_q = Quantity(
            phi_total * (1.0 - swt_val), "v/v",
            "dual water hydrocarbon volume (Asquith Eq. 7.52)",
            ASQUITH_SHALY_SAND,
            inputs={"phi_t": phi_total, "Swt": swt_val},
            assumptions={"phi_t": "total porosity, from the neutron and density"},
        )

    return DualWaterSaturation(swt=swt_q, swe=swe_q, phi_h=phi_h_q, b=b_q,
                               rwa=rwa_q)


# --- #36 ----------------------------------------------------------------------


def shaly_sand_sw(rt: float, rw: float, rw_source: str | None, *,
                  phi_effective: float | None = None,
                  phi_total: float | None = None,
                  vshale: float | None = None,
                  rsh: float | None = None,
                  m_star: float | None = None,
                  n_star: float | None = None,
                  b_mho_per_m_per_meq_ml: float | None = None,
                  qv_meq_per_ml: float | None = None,
                  qv_shale_meq_per_ml: float | None = None,
                  cec_meq_per_100g: float | None = None,
                  swb: float | None = None,
                  rb: float | None = None,
                  rwa: float | None = None,
                  a: float = 1.0, m: float = 2.0,
                  rw_temp_degf: float | None = None,
                  rt_invasion_corrected: bool = False
                  ) -> ShalySandSpread | Refusal:
    """Simandoux, Waxman-Smits and dual-water saturation, side by side. Tool #36.

    Returns a `ShalySandSpread` in which each leg is either a `Quantity` carrying
    its own equation's anchor or a `Refusal` naming what that model lacked. The
    `spread` is a `Range` over exactly the legs that answered, and its `source`
    lists exactly those legs' anchors - never an anchor for a model that is not
    in it.

    A bare `Refusal` comes back only when `rw_source` is missing, because all
    three models are built on Rw.
    """
    gate = _rw_gate(rw_source, ASQUITH_SHALY_SAND)
    if gate is not None:
        return gate
    _check_positive("rt", rt)
    _check_positive("rw", rw)

    sim = simandoux_sw(rt, phi_effective, rw, rw_source, vshale=vshale, rsh=rsh,
                       rw_temp_degf=rw_temp_degf,
                       rt_invasion_corrected=rt_invasion_corrected)
    ws = waxman_smits_sw(rt, phi_total, rw, rw_source, m_star=m_star,
                         n_star=n_star,
                         b_mho_per_m_per_meq_ml=b_mho_per_m_per_meq_ml,
                         qv_meq_per_ml=qv_meq_per_ml,
                         qv_shale_meq_per_ml=qv_shale_meq_per_ml,
                         vshale=vshale, cec_meq_per_100g=cec_meq_per_100g,
                         rw_temp_degf=rw_temp_degf,
                         rt_invasion_corrected=rt_invasion_corrected)
    dw = dual_water_sw(rt, phi_total, rw, rw_source, swb=swb, rb=rb, rwa=rwa,
                       a=a, m=m, rw_temp_degf=rw_temp_degf,
                       rt_invasion_corrected=rt_invasion_corrected)

    legs = _models(sim, ws, dw)
    answered = {name: leg for name, leg in legs.items()
                if isinstance(leg, Quantity)}

    flags: list[str] = []
    if len(answered) >= 2:
        anchors = [MODEL_SOURCES[name] for name in answered]
        values = {name: leg.value for name, leg in answered.items()}
        bases = {"simandoux": "effective", "waxman_smits": "total",
                 "dual_water_swt": "total"}
        if len({bases[name] for name in answered}) > 1:
            flags.append(
                "the legs in this spread are not on a common saturation basis: "
                "Simandoux Sw is Vsh-based on shale-corrected (effective) "
                "porosity per asquith#50, Waxman-Smits Sw and dual-water Swt are "
                "total-porosity saturations; the spread is the models' "
                "disagreement, not an uncertainty band on one quantity")
        if not rt_invasion_corrected:
            flags.append(
                "Rt not declared invasion-corrected; deep readings are not Rt")
        spread: Range | Refusal = Range(
            low=min(values.values()), high=max(values.values()), unit="v/v",
            method="spread across the shaly-sand models that answered: "
                   + ", ".join(MODEL_LABELS[name] for name in answered),
            # One anchor per participating leg, in leg order, de-duplicated only
            # where two legs genuinely share a segment. Never an anchor for a leg
            # that is not in `members`.
            source="; ".join(dict.fromkeys(anchors)),
            members=values,
            # `Range` carries inputs/assumptions/flags (tools/result.py:52-77) and
            # they are filled here, not left to the parent record. The band is
            # what a caller puts in computed[], and a band whose "the legs are not
            # on a common basis" caveat lives only on an object it was detached
            # from is exactly the second-class spread that contract was widened to
            # end. `members` stays the per-leg values; `inputs` is what the band
            # was computed from.
            inputs={"Rt": rt, "Rw": rw, "phi_effective": phi_effective,
                    "phi_total": phi_total, "Vsh": vshale, "Rsh": rsh},
            assumptions={
                "Rw_source": rw_source,
                "models": {name: MODEL_LABELS[name] for name in answered},
                "model_sources": {name: MODEL_SOURCES[name] for name in answered},
                "saturation_basis": {name: bases[name] for name in answered},
                "no_model_is_preferred": "the tool reports the disagreement and "
                                         "does not select or average",
            },
            flags=tuple(flags),
        )
    else:
        refused_names = [n for n in legs if n not in answered]
        spread = Refusal(
            reason="a spread needs at least two sourced models; "
                   f"{len(answered)} answered and {', '.join(refused_names)} "
                   "refused",
            needed=tuple(f"inputs for {n}" for n in refused_names),
            source=ASQUITH_SHALY_SAND,
        )

    invasion_flag = "Rt not declared invasion-corrected; deep readings are not Rt"
    if not rt_invasion_corrected and invasion_flag not in flags:
        flags.append(invasion_flag)

    return ShalySandSpread(
        simandoux=sim, waxman_smits=ws, dual_water=dw, spread=spread,
        flags=tuple(flags),
        assumptions={
            "Rw_source": rw_source,
            "models_answered": tuple(answered),
            "models_refused": tuple(n for n in legs if n not in answered),
            "no_model_is_preferred": "the tool reports the disagreement and does "
                                     "not select or average",
        },
    )
