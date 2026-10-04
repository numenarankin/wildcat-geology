"""Group P, the classic Asquith techniques the catalog never grew a tool for.

Five of these seven are straight out of Asquith and Krygowski and were verified
segment by segment before a line was written. Two are not in this corpus at all,
and they refuse.

--- what the corpus actually contains -----------------------------------------

Checked by reading the segments, not by trusting the plan:

  * `asquith#45` prints Eq. 7.22 (BVW), the Buckles constancy rule in the
    source's own words, and Table 7.1 (BVW by grain size). `asquith#51` explains
    Figure 7.3 and is where the one worked at-irreducible example lives.
  * `asquith#43` prints Eq. 7.4 (the moveable hydrocarbon index), Eq. 7.5
    (Sxo = Sw^1/5) and Eq. 7.7 (the ratio-method Sw), plus the 1.0 / 0.7 / 0.6
    verdict cutoffs. `asquith#62` restates MHI, BVW, ROS and MOS as Eqs. 10.4
    to 10.7 for the case studies.
  * `asquith#44` prints Eq. 7.16 (Rwa), Eq. 7.17 (Sw from the Rwa ratio), the
    a = 1.0 / m = 2.0 convention and both interpretation pitfalls.
  * `asquith#22` prints Eqs. 4.9 and 4.10, M and N.
  * `asquith#24` prints Eqs. 4.11, 4.12 and 4.13, the apparent matrix values.

  * A general N-mineral log-response system, solved by least squares, is NOWHERE
    in this corpus. `asquith#24` gives the three-mineral solution graphically, as
    a mineral triangle read off Figure 4.18, and the one deterministic
    multimineral result shown in the book (p. 74) is a screenshot of somebody
    else's software with no response matrix printed. So `multimineral_solve`
    refuses.
  * Thomas and Stieber appear once, as Figures 8 and 9 of the JMEST paper
    (`jmest#4`), with no equations. `jmest#1` names the three shale distributions
    and says which saturation model each admits, which is the useful half, so the
    refusal carries it. `thomas_stieber` refuses.

--- the three decisions worth explaining --------------------------------------

**The Buckles tolerance is ours, and it is derived from the source's own
example rather than picked.** `asquith#45` says only "constant or very close to
constant". `asquith#51` works the one example: Figure 7.3a, a formation
producing 96% oil, "all the points plot between 0.04 and 0.05 BVW ... very close
to, or at, irreducible water saturation". BUCKLES_SPREAD_TOLERANCE is the
relative spread of exactly that band, 0.01/0.045, and the constant is computed
from the two published endpoints so it cannot drift away from them. It is still
a house rule and every verdict says so.

**`mn_plot` computes M and N and refuses to name a mineral.** Eqs. 4.9 and 4.10
are printed; the mineral points they are read against are Figure 4.15, an image.
Nothing in the corpus tabulates M and N for quartz, calcite or dolomite, so a
lithology from this tool would be a number invented to match a picture. Same
posture as the Waxman-Smits B chart in `tools/saturation.py`.

**`mid_plot` does name candidates, and that is not the same concession.** Its two
axes ARE published constants: the MID mineral points are the matrix density of
Table 4.2 and the matrix travel time of Table 4.1, which `matrix_constant_lookup`
already holds. So the candidates come from published values. What is ours is the
DISTANCE, since the source reads the plot by eye, and the ranking is flagged
PROVISIONAL on every result.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# Aliased private so the dispatcher's auto-discovery does not re-home an
# existing tool: registry() takes the first module that exposes a name, and
# `tools.classic` sorts ahead of `tools.petrophysics`.
from .petrophysics import FLUID, MATRIX
from .petrophysics import matrix_constant_lookup as _matrix_constant_lookup
from .result import Quantity, Range, Refusal

# --- corpus anchors -----------------------------------------------------------

#: Eq. 7.22, the Buckles constancy rule, and Table 7.1 (BVW by grain size).
ASQUITH_BVW = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#45"
#: Figure 7.3a-c explained. The only worked at-irreducible band in the book.
ASQUITH_BUCKLES_FIGURES = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#51"
#: Eq. 7.4 (MHI), Eq. 7.5 (Sxo = Sw^1/5), Eqs. 7.6/7.7 (ratio-method Sw), cutoffs.
ASQUITH_RATIO = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#43"
#: Eqs. 10.4-10.7: MHI, BVW, ROS = 1 - Sxo, MOS = Sxo - Sw.
ASQUITH_CASE_EQUATIONS = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#62"
#: Case Study 3, where Sxo came out above 1.0 and the book calls the resulting
#: MHI and MOS "of no value". The only place the corpus says what to do about it.
ASQUITH_SXO_PITFALL = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#71"
#: Eq. 7.16 (Rwa), Eq. 7.17 (Sw from the Rwa ratio), and both pitfalls.
ASQUITH_RWA = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#44"
#: Eqs. 4.9 and 4.10, M and N.
ASQUITH_MN = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#22"
#: Eqs. 4.11, 4.12, 4.13: rho_maa, Dt_maa, U_maa.
ASQUITH_MID = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#24"
#: Table 4.1 (Dt_ma, Dt_fl) and Table 4.2 (rho_ma, rho_fl, Pe).
ASQUITH_T41 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#17"
ASQUITH_T42 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#18"
#: The three shale distributions, and which saturation model each admits.
JMEST_SHALE_DISTRIBUTION = "01-curve-reading/jmest-waxman-smits-saturation-modelling#1"
#: Thomas-Stieber, as Figures 8 and 9. Images, no equations.
JMEST_THOMAS_STIEBER = "01-curve-reading/jmest-waxman-smits-saturation-modelling#4"


# --- published constants ------------------------------------------------------

#: `asquith#51`, Figure 7.3a: the one formation the book calls at irreducible
#: saturation has "all the points plot between 0.04 and 0.05 BVW".
BUCKLES_EXAMPLE_LOW = 0.04
BUCKLES_EXAMPLE_HIGH = 0.05

#: The constancy tolerance, as a relative spread (max - min) / mean. PROVISIONAL:
#: `asquith#45` says only "constant or very close to constant" and prints no
#: number, so this is the relative spread of the source's own example above,
#: 0.01/0.045 = 0.2222. Computed from the endpoints so it cannot drift off them.
BUCKLES_SPREAD_TOLERANCE = ((BUCKLES_EXAMPLE_HIGH - BUCKLES_EXAMPLE_LOW)
                            / ((BUCKLES_EXAMPLE_HIGH + BUCKLES_EXAMPLE_LOW) / 2.0))

#: Table 7.1, `asquith#45`. Rock class -> the published BVW band. The book warns
#: the carbonate rows "should be used only as a very general guide".
BVW_TABLE_7_1: dict[str, tuple[float, float]] = {
    "coarse": (0.02, 0.025),
    "medium": (0.025, 0.035),
    "fine": (0.035, 0.05),
    "very fine": (0.05, 0.07),
    "silt": (0.07, 0.09),
    "vuggy": (0.005, 0.015),
    "vuggy intercrystalline": (0.015, 0.025),
    "intercrystalline": (0.025, 0.04),
    "chalky": (0.05, 0.05),
}

#: `asquith#43`: "If the ratio Sw/Sxo is equal to or greater than 1.0, then
#: hydrocarbons were not moved during invasion."
MHI_NO_MOVEMENT = 1.0
#: Same segment: "Whenever the ratio Sw/Sxo is less than 0.7 for sandstones or
#: less than 0.6 for carbonates, moveable hydrocarbons are indicated
#: (Schlumberger, 1972)."
MHI_MOVEABLE_CUTOFF: dict[str, float] = {"sandstone": 0.7, "carbonate": 0.6}

#: `asquith#44`: "In low-porosity zones (less than about 10% porosity), the Rwa
#: value is lower than the actual Rw value."
RWA_LOW_POROSITY = 0.10
#: Same segment: "In practice ... the following values are used for simplicity:
#: a = 1.0, m = 2.0", and Eq. 7.17 assumes n = 2.
RWA_A_DEFAULT = 1.0
RWA_M_DEFAULT = 2.0

#: Eq. 4.9, `asquith#22`. English scaling, and the metric one the source prints
#: in the same equation.
MN_SCALE_ENGLISH = 0.01
MN_SCALE_METRIC = 0.003
#: Eq. 4.10, `asquith#22`: "phi_Nfl = neutron porosity of the fluid of the
#: formation (usually = 1.0)".
NPHI_FLUID_DEFAULT = 1.0

#: Eq. 4.13, `asquith#24`: "U_fl = fluid volumetric cross section (0.398
#: barns/cm3 for fresh water, 1.36 barns/cm3 for salt water)".
U_FLUID: dict[str, float] = {"fresh": 0.398, "salt": 1.36}


def _finite(name: str, value: Any) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a finite number, got {value!r}") from None
    if not math.isfinite(out):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return out


def _rows(samples: Any, name: str) -> list[dict[str, Any]]:
    """Accept a sequence of mappings, which is what the JSON dispatcher sends."""
    if isinstance(samples, Mapping) or isinstance(samples, (str, bytes)):
        raise ValueError(f"{name} must be a sequence of records, got {type(samples).__name__}")
    if not isinstance(samples, Sequence):
        raise ValueError(f"{name} must be a sequence of records, got {type(samples).__name__}")
    out: list[dict[str, Any]] = []
    for i, row in enumerate(samples):
        if not isinstance(row, Mapping):
            raise ValueError(f"{name}[{i}] must be a mapping, got {type(row).__name__}")
        out.append({str(k): v for k, v in row.items()})
    return out


def _unique_members(values: Sequence[Quantity]) -> dict[str, float]:
    """label -> value, with duplicate labels kept apart rather than overwritten.

    Two samples at the same depth are a real input, and silently collapsing them
    would leave a `Range` whose members do not add up to the band beside them.
    """
    out: dict[str, float] = {}
    for i, q in enumerate(values):
        key = str(q.assumptions["label"])
        if key in out:
            key = f"{key} (#{i})"
        out[key] = q.value
    return out


def _label(row: Mapping[str, Any], i: int) -> str:
    for key in ("name", "zone", "depth_ft", "depth"):
        if row.get(key) is not None:
            return str(row[key])
    return f"sample {i}"


# --- #P1 bulk_volume_water ----------------------------------------------------


@dataclass(frozen=True)
class BulkVolumeWater:
    """BVW per depth, and the Buckles verdict the operator actually wants.

    `at_irreducible` is the whole point: `asquith#45` says a zone whose BVW is
    constant "is of a single rock type and at irreducible water saturation" and
    that "hydrocarbon production from a zone at irreducible water saturation
    should be water free". It is None, not False, when fewer than two depths were
    supplied, because one point cannot be constant or scattered.
    """

    bvw: tuple[Quantity, ...]
    mean: Quantity
    spread: Range | Refusal
    at_irreducible: bool | None
    verdict: str
    tolerance: float
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


def bulk_volume_water(samples: Sequence[Mapping[str, Any]],
                      *, tolerance: float = BUCKLES_SPREAD_TOLERANCE,
                      rock_class: str | None = None
                      ) -> BulkVolumeWater | Refusal:
    """BVW = Sw x phi per depth, plus the Buckles constancy verdict. Asquith Eq. 7.22.

    Each `samples` record needs `phi` and `sw`, and may carry `depth_ft` or
    `name`. The verdict compares the relative spread (max - min) / mean against
    `tolerance`, whose default is the relative spread of the source's own
    at-irreducible example (`asquith#51`, Figure 7.3a, BVW 0.04 to 0.05). That
    threshold is a house rule and every result says so: the source states the
    rule qualitatively and prints no cutoff.

    `rock_class` compares the mean against Table 7.1, which publishes BVW by
    grain size and carbonate pore type. It changes no verdict, it only flags.
    """
    rows = _rows(samples, "samples")
    if not rows:
        return Refusal(
            reason="no samples; BVW is computed per depth and the Buckles verdict "
                   "is a comparison across depths",
            needed=("samples, each with phi and sw",),
            source=ASQUITH_BVW,
        )
    tolerance = _finite("tolerance", tolerance)
    if tolerance < 0:
        raise ValueError(f"tolerance must be non-negative, got {tolerance!r}")

    values: list[Quantity] = []
    for i, row in enumerate(rows):
        if row.get("phi") is None or row.get("sw") is None:
            return Refusal(
                reason=f"{_label(row, i)} is missing phi or sw; Eq. 7.22 is the "
                       "product of the two and neither has a default",
                needed=("phi and sw on every sample",),
                source=ASQUITH_BVW,
            )
        phi = _finite("phi", row["phi"])
        sw = _finite("sw", row["sw"])
        inputs: dict[str, Any] = {"phi": phi, "Sw": sw}
        if row.get("depth_ft") is not None:
            inputs["depth_ft"] = _finite("depth_ft", row["depth_ft"])
        values.append(Quantity(
            sw * phi, "v/v", "bulk volume water (Asquith Eq. 7.22)", ASQUITH_BVW,
            inputs=inputs, assumptions={"label": _label(row, i)},
        ))

    nums = [q.value for q in values]
    mean_value = sum(nums) / len(nums)
    mean = Quantity(
        mean_value, "v/v", "mean bulk volume water over the interval", ASQUITH_BVW,
        inputs={"n_samples": len(nums)},
        assumptions={"basis": "arithmetic mean of the per-depth Eq. 7.22 values"},
    )

    flags: list[str] = []
    spread: Range | Refusal
    at_irreducible: bool | None
    if len(nums) < 2:
        spread = Refusal(
            reason="one depth cannot be constant or scattered; the Buckles test "
                   "compares BVW across several depths in the same formation",
            needed=("at least two samples in the same zone",),
            source=ASQUITH_BVW,
        )
        at_irreducible = None
        verdict = ("no irreducible-saturation verdict: the Buckles test needs BVW at "
                   "several depths, and one was supplied")
    else:
        low, high = min(nums), max(nums)
        relative = float("inf") if mean_value == 0 else (high - low) / abs(mean_value)
        spread = Range(
            low=low, high=high, unit="v/v",
            method="BVW spread across the interval (Asquith Eq. 7.22 per depth)",
            source=ASQUITH_BVW,
            members=_unique_members(values),
            inputs={"n_samples": len(nums)},
            assumptions={"relative_spread": relative, "tolerance": tolerance},
        )
        at_irreducible = relative <= tolerance
        if at_irreducible:
            verdict = (
                f"BVW is constant within {relative:.3f} relative spread (tolerance "
                f"{tolerance:.3f}), so by asquith#45 the interval is of a single rock "
                "type and at irreducible water saturation; hydrocarbon production "
                "from it should be water free")
        else:
            verdict = (
                f"BVW varies by {relative:.3f} relative spread, past the {tolerance:.3f} "
                "tolerance; asquith#45: a formation not at irreducible water saturation "
                "exhibits wide variations in bulk volume water, so this interval holds "
                "more water than capillary pressure can hold and will produce some")
        flags.append(
            f"the constancy tolerance {tolerance:.4f} is a PROVISIONAL house rule: "
            "asquith#45 says only 'constant or very close to constant' and prints no "
            f"cutoff. The default is the relative spread of the source's own example "
            f"(asquith#51, Figure 7.3a: BVW {BUCKLES_EXAMPLE_LOW} to "
            f"{BUCKLES_EXAMPLE_HIGH} in a formation producing 96% oil)")

    assumptions: dict[str, Any] = {
        "verdict_rule": "asquith#45: constant BVW across depths indicates a single "
                        "rock type at irreducible water saturation (Morris and "
                        "Biggs, 1967)",
        "tolerance_status": "PROVISIONAL house rule",
        "tolerance_basis": ASQUITH_BUCKLES_FIGURES,
    }
    if rock_class is not None:
        key = str(rock_class).strip().lower()
        if key not in BVW_TABLE_7_1:
            return Refusal(
                reason=f"unknown rock_class {rock_class!r}; Table 7.1 publishes bands "
                       f"for {sorted(BVW_TABLE_7_1)} and this tool does not interpolate "
                       "between them",
                needed=(f"a rock_class from {sorted(BVW_TABLE_7_1)}",),
                source=ASQUITH_BVW,
            )
        band = BVW_TABLE_7_1[key]
        assumptions["table_7_1_band"] = band
        if not band[0] <= mean_value <= band[1]:
            flags.append(
                f"mean BVW {mean_value:.4f} is outside the Table 7.1 band {band} for "
                f"{key!r}; the table relates BVW to grain size, so a mismatch means "
                "either the rock class or the saturation is wrong")
        if key in ("vuggy", "vuggy intercrystalline", "intercrystalline", "chalky"):
            flags.append("asquith#45: 'The bulk volume water values for carbonates "
                         "should be used only as a very general guide'")

    return BulkVolumeWater(
        bvw=tuple(values), mean=mean, spread=spread,
        at_irreducible=at_irreducible, verdict=verdict, tolerance=tolerance,
        flags=tuple(flags), assumptions=assumptions,
    )


# --- #P2 movable_hydrocarbon_index --------------------------------------------


@dataclass(frozen=True)
class MovableHydrocarbons:
    """MHI, and the two saturations `asquith#62` prints alongside it.

    `mos` and `ros` need Sxo. By the ratio route Sxo comes from Eq. 7.5, which
    the source qualifies as holding "in the flushed zone of formations with
    moderate invasion and average residual hydrocarbon saturation", so it is an
    assumption, and it is recorded as one rather than buried in the arithmetic.
    """

    mhi: Quantity
    mos: Quantity | Refusal
    ros: Quantity | Refusal
    sw: Quantity | Refusal
    sxo: Quantity | Refusal
    verdict: str
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


#: The book states the cutoff for "sandstones" and for "carbonates", so a named
#: carbonate has to resolve to its class before the cutoff can be applied. An
#: unlisted lithology resolves to nothing and gets both cutoffs reported.
MHI_LITHOLOGY_CLASS: dict[str, str] = {
    "sandstone": "sandstone", "sand": "sandstone", "clastic": "sandstone",
    "carbonate": "carbonate", "limestone": "carbonate", "dolomite": "carbonate",
}


def _mhi_verdict(mhi: float, lithology: str | None) -> tuple[str, list[str]]:
    if mhi >= MHI_NO_MOVEMENT:
        return (f"MHI {mhi:.4f} is at or above {MHI_NO_MOVEMENT}: asquith#43, "
                "'hydrocarbons were not moved during invasion. This is true "
                "regardless of whether or not a formation contains hydrocarbons'",
                [])
    key = None if lithology is None else MHI_LITHOLOGY_CLASS.get(
        str(lithology).strip().lower())
    if key in MHI_MOVEABLE_CUTOFF:
        cut = MHI_MOVEABLE_CUTOFF[key]
        if mhi < cut:
            return (f"MHI {mhi:.4f} is below the {cut} {key} cutoff: moveable "
                    "hydrocarbons are indicated (asquith#43, Schlumberger 1972)", [])
        return (f"MHI {mhi:.4f} is below {MHI_NO_MOVEMENT} but not below the {cut} "
                f"{key} cutoff, so asquith#43 supports neither verdict here", [])
    return (f"MHI {mhi:.4f} is below {MHI_NO_MOVEMENT}; asquith#43 indicates moveable "
            f"hydrocarbons below {MHI_MOVEABLE_CUTOFF['sandstone']} for sandstones and "
            f"below {MHI_MOVEABLE_CUTOFF['carbonate']} for carbonates, and no lithology "
            "class was resolved to choose between them",
            [f"lithology {lithology!r} did not resolve to sandstone or carbonate, so "
             "the asquith#43 cutoff was not applied"])


def movable_hydrocarbon_index(sw: float | None = None, sxo: float | None = None, *,
                              rxo: float | None = None, rt: float | None = None,
                              rmf: float | None = None, rw: float | None = None,
                              lithology: str | None = None
                              ) -> MovableHydrocarbons | Refusal:
    """MHI = Sw / Sxo, with moveable and residual oil saturation. Asquith Eqs. 7.4, 10.6, 10.7.

    Two routes, and the tool takes whichever the caller has.

    Saturations: MHI = Sw/Sxo directly, MOS = Sxo - Sw (Eq. 10.7), ROS = 1 - Sxo
    (Eq. 10.6).

    Resistivities, when no porosity log exists: MHI = ((Rxo/Rt)/(Rmf/Rw))^0.5
    (Eq. 7.4), Sw = ((Rxo/Rt)/(Rmf/Rw))^0.625 (Eq. 7.7), and Sxo = Sw^(1/5)
    (Eq. 7.5). The three are consistent by construction, which is the check:
    Sw/Sxo reduces to the same power of the ratio that Eq. 7.4 states.

    This is the number `invasion_profile` should be fed, and the verdict cutoffs
    (1.0, and 0.7 sandstone / 0.6 carbonate) are the source's own.
    """
    flags: list[str] = []
    assumptions: dict[str, Any] = {}

    if sw is not None and sxo is not None:
        sw_v = _finite("sw", sw)
        sxo_v = _finite("sxo", sxo)
        if sxo_v <= 0:
            return Refusal(
                reason="MHI divides by Sxo; a non-positive flushed-zone saturation "
                       "has no moveable hydrocarbon index",
                needed=("a positive Sxo",),
                source=ASQUITH_CASE_EQUATIONS,
            )
        mhi_value = sw_v / sxo_v
        route = "saturations (Asquith Eq. 10.4)"
        route_source = ASQUITH_CASE_EQUATIONS
        mhi_inputs: dict[str, Any] = {"Sw": sw_v, "Sxo": sxo_v}
        sw_q: Quantity | Refusal = Quantity(
            sw_v, "v/v", "uninvaded-zone water saturation, caller-supplied",
            ASQUITH_CASE_EQUATIONS, inputs={"Sw": sw_v},
            assumptions={"origin": "supplied by caller, not derived"})
        sxo_q: Quantity | Refusal = Quantity(
            sxo_v, "v/v", "flushed-zone water saturation, caller-supplied",
            ASQUITH_CASE_EQUATIONS, inputs={"Sxo": sxo_v},
            assumptions={"origin": "supplied by caller, not derived"})
    elif None not in (rxo, rt, rmf, rw):
        rxo_v = _finite("rxo", rxo)
        rt_v = _finite("rt", rt)
        rmf_v = _finite("rmf", rmf)
        rw_v = _finite("rw", rw)
        for name, value in (("rxo", rxo_v), ("rt", rt_v), ("rmf", rmf_v), ("rw", rw_v)):
            if value <= 0:
                raise ValueError(f"{name} must be a positive resistivity, got {value!r}")
        ratio = (rxo_v / rt_v) / (rmf_v / rw_v)
        mhi_value = ratio ** 0.5
        sw_value = ratio ** 0.625
        sxo_value = sw_value ** 0.2
        route = "ratio method (Asquith Eq. 7.4)"
        route_source = ASQUITH_RATIO
        mhi_inputs = {"Rxo": rxo_v, "Rt": rt_v, "Rmf": rmf_v, "Rw": rw_v,
                      "ratio": ratio}
        sw_q = Quantity(
            sw_value, "v/v", "ratio-method water saturation (Asquith Eq. 7.7)",
            ASQUITH_RATIO, inputs=dict(mhi_inputs),
            assumptions={"n": 2.0, "note": "asquith#43: 'The cementation exponent "
                                           "(n) is assumed to be 2.0'"})
        sxo_q = Quantity(
            sxo_value, "v/v", "flushed-zone saturation from Asquith Eq. 7.5 (Sxo = Sw^1/5)",
            ASQUITH_RATIO, inputs={"Sw": sw_value},
            assumptions={"validity": "asquith#43: Eq. 7.5 'normally works well' in "
                                     "the flushed zone of formations with moderate "
                                     "invasion and average residual hydrocarbon "
                                     "saturation"})
        sw_v, sxo_v = sw_value, sxo_value
        flags.append("Sxo came from Eq. 7.5, not from a measurement; MOS and ROS "
                     "inherit that assumption")
        assumptions["route_note"] = ("the ratio method cancels the formation factor, "
                                     "so no porosity log is needed (asquith#43)")
    else:
        return Refusal(
            reason="no route to MHI: supply either Sw and Sxo, or all four of Rxo, "
                   "Rt, Rmf and Rw for the ratio method of Eq. 7.4",
            needed=("sw and sxo", "or rxo, rt, rmf and rw"),
            source=ASQUITH_RATIO,
        )

    mhi = Quantity(
        mhi_value, "v/v", f"moveable hydrocarbon index, {route}", route_source,
        inputs=mhi_inputs,
        assumptions={"cutoffs": dict(MHI_MOVEABLE_CUTOFF),
                     "no_movement_at_or_above": MHI_NO_MOVEMENT},
    )

    if sxo_v > 1.0:
        unusable = Refusal(
            reason=f"Sxo = {sxo_v:.4f} exceeds 1.0, which is not physical; asquith#71 "
                   "meets the same case and calls the resulting MHI and MOS 'of no "
                   "value'. It names two causes: an incorrectly recorded Rmf, or a "
                   "short normal used as Rxo",
            needed=("an Sxo at or below 1.0", "or a corrected Rmf / Rxo"),
            source=ASQUITH_SXO_PITFALL,
        )
        mos: Quantity | Refusal = unusable
        ros: Quantity | Refusal = unusable
        flags.append("Sxo > 1.0, so MOS and ROS were refused rather than returned negative")
    else:
        mos = Quantity(
            sxo_v - sw_v, "v/v", "moveable oil saturation (Asquith Eq. 10.7)",
            ASQUITH_CASE_EQUATIONS, inputs={"Sxo": sxo_v, "Sw": sw_v},
            flags=("MOS is negative, so Sw exceeds Sxo and no hydrocarbon was moved "
                   "during invasion",) if sxo_v < sw_v else (),
        )
        ros = Quantity(
            1.0 - sxo_v, "v/v", "residual oil saturation (Asquith Eq. 10.6)",
            ASQUITH_CASE_EQUATIONS, inputs={"Sxo": sxo_v},
        )

    verdict, verdict_flags = _mhi_verdict(mhi_value, lithology)
    flags.extend(verdict_flags)
    assumptions["route"] = route
    return MovableHydrocarbons(mhi=mhi, mos=mos, ros=ros, sw=sw_q, sxo=sxo_q,
                               verdict=verdict, flags=tuple(flags),
                               assumptions=assumptions)


# --- #P3 rwa_method -----------------------------------------------------------


@dataclass(frozen=True)
class RwaScan:
    """Rwa per zone, the wet-zone pick, and the Sw that follows from it.

    `rw_estimate` is the MINIMUM Rwa, which is the whole technique: `asquith#44`
    assumes the lowest-Rwa porous and permeable zone is wet, so its Rwa is the
    best available Rw. It is a `Refusal` when only one zone was given, because a
    minimum over one zone is not a comparison and would hand back Rw = Rwa with
    no evidence at all.
    """

    rwa: tuple[Quantity, ...]
    rw_estimate: Quantity | Refusal
    sw: tuple[Quantity, ...]
    wet_zone: str | None
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


def rwa_method(zones: Sequence[Mapping[str, Any]], *,
               a: float = RWA_A_DEFAULT, m: float = RWA_M_DEFAULT
               ) -> RwaScan | Refusal:
    """Rwa = Rt x phi^m / a per zone, the wet pick, and Sw. Asquith Eqs. 7.16, 7.17.

    Each `zones` record needs `rt` and `phi`, and may carry `name` or `depth_ft`.
    The lowest Rwa is taken as the estimate of Rw and every other zone's
    saturation follows from Eq. 7.17, Sw = sqrt(Rwa_min / Rwa_zone), whose n is
    2 by the source's own statement.

    Two pitfalls from `asquith#44` are carried rather than left to the reader:
    all compared zones are assumed to have the SAME Rw, and below about 10%
    porosity Rwa reads lower than the true Rw, which is exactly the zone that
    would then be mistaken for the wet one.
    """
    rows = _rows(zones, "zones")
    if not rows:
        return Refusal(
            reason="no zones; the Rwa technique is a comparison of Rwa between "
                   "intervals and there is nothing to compare",
            needed=("zones, each with rt and phi",),
            source=ASQUITH_RWA,
        )
    a = _finite("a", a)
    m = _finite("m", m)
    if a <= 0:
        raise ValueError(f"a must be positive, got {a!r}")

    values: list[Quantity] = []
    flags: list[str] = []
    for i, row in enumerate(rows):
        if row.get("rt") is None or row.get("phi") is None:
            return Refusal(
                reason=f"{_label(row, i)} is missing rt or phi; Eq. 7.16 needs both",
                needed=("rt and phi on every zone",),
                source=ASQUITH_RWA,
            )
        rt = _finite("rt", row["rt"])
        phi = _finite("phi", row["phi"])
        if rt <= 0:
            raise ValueError(f"rt must be a positive resistivity, got {rt!r}")
        if phi <= 0:
            return Refusal(
                reason=f"{_label(row, i)} has phi = {phi}; Eq. 7.16 raises porosity to "
                       "m and a non-positive porosity gives no Rwa",
                needed=("a positive porosity on every zone",),
                source=ASQUITH_RWA,
            )
        label = _label(row, i)
        zone_flags: tuple[str, ...] = ()
        if phi < RWA_LOW_POROSITY:
            zone_flags = (
                f"porosity {phi:.3f} is below {RWA_LOW_POROSITY}; asquith#44: 'In "
                "low-porosity zones (less than about 10% porosity), the Rwa value is "
                "lower than the actual Rw value', so this zone can look wet when it "
                "is not",)
            flags.append(f"{label}: low-porosity Rwa bias, see the flag on that zone")
        values.append(Quantity(
            rt * phi ** m / a, "ohm-m",
            "apparent water resistivity (Asquith Eq. 7.16)", ASQUITH_RWA,
            inputs={"Rt": rt, "phi": phi},
            assumptions={"a": a, "m": m, "label": label},
            flags=zone_flags,
        ))

    assumptions: dict[str, Any] = {
        "a": a, "m": m,
        "same_Rw_assumed": "asquith#44 interpretation pitfall: 'The Rw values in the "
                           "zones that are compared are assumed to be the same.'",
        "wet_pick_rule": "asquith#44: the zone with the lowest Rwa is the most likely "
                         "to be water bearing, and its Rwa is closest to Rw",
    }
    if len(values) < 2:
        return RwaScan(
            rwa=tuple(values),
            rw_estimate=Refusal(
                reason="one zone gives no Rw estimate: the technique picks the LOWEST "
                       "Rwa among several zones as the wet one, and a minimum over a "
                       "single zone is the zone itself, not evidence that it is wet",
                needed=("at least two zones to compare",),
                source=ASQUITH_RWA,
            ),
            sw=(), wet_zone=None, flags=tuple(flags), assumptions=assumptions,
        )

    wet = min(values, key=lambda q: q.value)
    wet_label = str(wet.assumptions["label"])
    rw_estimate = Quantity(
        wet.value, "ohm-m",
        "Rw estimated as the minimum Rwa across the compared zones (Asquith Eq. 7.16)",
        ASQUITH_RWA,
        inputs={"Rwa_minimum": wet.value, "n_zones": len(values)},
        assumptions={"wet_zone": wet_label, **assumptions},
        flags=("if the minimum-Rwa zone itself holds hydrocarbons, asquith#44 notes "
               "the other zones contain even more than this makes them look",)
        + wet.flags,
    )
    saturations = [
        Quantity(
            math.sqrt(wet.value / q.value), "v/v",
            "water saturation from the Rwa ratio (Asquith Eq. 7.17)", ASQUITH_RWA,
            inputs={"Rwa_minimum": wet.value, "Rwa_zone": q.value},
            assumptions={"n": 2.0, "label": q.assumptions["label"],
                         "note": "asquith#44: 'the cementation exponent (n) in the "
                                 "equation above is assumed to be 2'"},
            flags=q.flags,
        )
        for q in values
    ]
    return RwaScan(rwa=tuple(values), rw_estimate=rw_estimate, sw=tuple(saturations),
                   wet_zone=wet_label, flags=tuple(flags), assumptions=assumptions)


# --- #P4 mn_plot --------------------------------------------------------------


@dataclass(frozen=True)
class MNPoint:
    """M and N for one depth. `lithology` is always a `Refusal`, see the docstring."""

    m: Quantity
    n: Quantity
    lithology: Refusal
    assumptions: dict[str, Any] = field(default_factory=dict)


def mn_plot(dt: float, rho_b: float, nphi: float, *,
            dt_fl: float | None = None, rho_fl: float = 1.0,
            nphi_fl: float = NPHI_FLUID_DEFAULT,
            metric: bool = False) -> MNPoint:
    """M and N from sonic, density and neutron. Asquith Eqs. 4.9 and 4.10.

        M = (Dt_fl - Dt) / (rho_b - rho_fl) x 0.01   (x 0.003 metric)
        N = (phiN_fl - phiN) / (rho_b - rho_fl)

    `nphi` is neutron porosity in LIMESTONE units, which is what Eq. 4.10 is
    written against. `dt_fl` defaults to Asquith Table 4.1's freshwater 189
    usec/ft and `nphi_fl` to the 1.0 the source calls usual.

    The lithology is refused, always. Eqs. 4.9 and 4.10 are printed; the mineral
    points M and N are read against are Figure 4.15, an image, and nothing in
    this corpus tabulates M and N for quartz, calcite or dolomite. Returning a
    mineral here would mean inventing the endpoints. `mid_plot` answers the same
    question from constants the corpus does publish.
    """
    dt = _finite("dt", dt)
    rho_b = _finite("rho_b", rho_b)
    nphi = _finite("nphi", nphi)
    rho_fl = _finite("rho_fl", rho_fl)
    nphi_fl = _finite("nphi_fl", nphi_fl)
    dt_fl = FLUID["fresh"]["dt_fl"] if dt_fl is None else _finite("dt_fl", dt_fl)
    if rho_b == rho_fl:
        raise ValueError(
            f"rho_b and rho_fl are both {rho_b}; Eqs. 4.9 and 4.10 divide by their "
            "difference and are undefined")

    scale = MN_SCALE_METRIC if metric else MN_SCALE_ENGLISH
    unit_note = "metric (x0.003)" if metric else "English (x0.01)"
    denominator = rho_b - rho_fl
    shared = {"rho_b": rho_b, "rho_fl": rho_fl}

    m_q = Quantity(
        (dt_fl - dt) / denominator * scale, "dimensionless",
        f"M, sonic-density lithology parameter, {unit_note} (Asquith Eq. 4.9)",
        ASQUITH_MN,
        inputs={"Dt": dt, "Dt_fl": dt_fl, **shared},
        assumptions={"scale": scale,
                     "Dt_fl_source": f"{ASQUITH_T41} (Table 4.1 fresh water 189 usec/ft)"
                     if dt_fl == FLUID["fresh"]["dt_fl"] else "caller-supplied"},
    )
    n_q = Quantity(
        (nphi_fl - nphi) / denominator, "dimensionless",
        "N, neutron-density lithology parameter (Asquith Eq. 4.10)", ASQUITH_MN,
        inputs={"phiN": nphi, "phiN_fl": nphi_fl, **shared},
        assumptions={"phiN_basis": "limestone units, as Eq. 4.10 is written",
                     "phiN_fl_basis": "asquith#22: 'usually = 1.0'"},
    )
    lithology = Refusal(
        reason="M and N identify a mineral only by where they plot against the "
               "mineral points of Figure 4.15, and that figure is an image. No "
               "document in this corpus tabulates M and N for quartz, calcite or "
               "dolomite, so naming a lithology here would mean inventing the "
               "endpoints the plot is read against",
        needed=("tabulated M and N mineral endpoints",
                "or mid_plot, whose axes are the published matrix constants of "
                "Asquith Tables 4.1 and 4.2"),
        source=ASQUITH_MN,
    )
    return MNPoint(m=m_q, n=n_q, lithology=lithology,
                   assumptions={"units": unit_note})


# --- #P5 mid_plot -------------------------------------------------------------


@dataclass(frozen=True)
class MidPoint:
    """Apparent matrix values, and the published matrix points they sit nearest.

    `candidates` is ordered nearest first and every entry names a lithology that
    Asquith Tables 4.1 and 4.2 publish. The DISTANCE is a house rule, since the
    source reads Figure 4.18 by eye, so `flags` says so on every result.
    """

    rho_maa: Quantity
    dt_maa: Quantity | Refusal
    u_maa: Quantity | Refusal
    candidates: tuple[tuple[str, float], ...]
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


def _matrix_points() -> dict[str, tuple[float, float]]:
    """Lithology -> (rho_ma, Dt_ma) from Asquith Tables 4.2 and 4.1, Wyllie column.

    Sandstone's Wyllie cell is a published RANGE, so the point used is whatever
    `matrix_constant_lookup` collapses it to, which is the published-first
    endpoint and is flagged there. One home for that decision, not two.
    """
    points: dict[str, tuple[float, float]] = {}
    for key in MATRIX:
        consts = _matrix_constant_lookup(key, variant="wyllie")
        dt = consts.dt_ma_point()
        if isinstance(dt, Refusal):  # pragma: no cover - Wyllie has every cell
            continue
        points[key] = (consts.rho_ma.value, dt.value)
    return points


def mid_plot(rho_b: float, phi_nd: float, *,
             dt: float | None = None, phi_ns: float | None = None,
             pe: float | None = None, fluid: str = "fresh",
             rho_fl: float | None = None, dt_fl: float | None = None,
             u_fl: float | None = None) -> MidPoint:
    """Matrix identification by apparent matrix values. Asquith Eqs. 4.11-4.13.

        rho_maa = (rho_b - phi_ND x rho_fl) / (1 - phi_ND)          (4.11)
        Dt_maa  = (Dt - phi_NS x Dt_fl) / (1 - phi_NS)              (4.12)
        U_maa   = (Pe x rho_b - phi_ND x U_fl) / (1 - phi_ND)       (4.13)

    `phi_nd` is neutron-density crossplot porosity and `phi_ns` neutron-sonic,
    which is what the equations are written against: they are NOT the same
    porosity and swapping them moves the point.

    Dt_maa needs both `dt` and `phi_ns`, U_maa needs `pe`; each refuses on its
    own rather than taking the whole call down. `candidates` ranks the published
    matrix points of Tables 4.1 and 4.2 by distance from (rho_maa, Dt_maa), and
    is empty when there is no Dt_maa to place the point in two dimensions.
    """
    rho_b = _finite("rho_b", rho_b)
    phi_nd = _finite("phi_nd", phi_nd)
    fkey = str(fluid).strip().lower()
    if fkey not in FLUID:
        raise ValueError(f"unknown fluid {fluid!r}; known: {sorted(FLUID)}")
    rho_fl = FLUID[fkey]["rho_fl"] if rho_fl is None else _finite("rho_fl", rho_fl)
    dt_fl = FLUID[fkey]["dt_fl"] if dt_fl is None else _finite("dt_fl", dt_fl)
    u_fl = U_FLUID[fkey] if u_fl is None else _finite("u_fl", u_fl)
    if phi_nd == 1.0:
        raise ValueError("phi_nd is 1.0; Eqs. 4.11 and 4.13 divide by 1 - phi_ND")

    rho_maa = Quantity(
        (rho_b - phi_nd * rho_fl) / (1.0 - phi_nd), "g/cm3",
        "apparent matrix density (Asquith Eq. 4.11)", ASQUITH_MID,
        inputs={"rho_b": rho_b, "phi_ND": phi_nd, "rho_fl": rho_fl},
        assumptions={"fluid": fkey, "rho_fl_source": ASQUITH_T42},
    )

    dt_maa: Quantity | Refusal
    if dt is None or phi_ns is None:
        missing = [n for n, v in (("dt", dt), ("phi_ns", phi_ns)) if v is None]
        dt_maa = Refusal(
            reason="Eq. 4.12 needs " + " and ".join(missing)
                   + "; apparent matrix travel time comes from the sonic and the "
                     "neutron-sonic crossplot porosity, not from the neutron-density one",
            needed=tuple(missing),
            source=ASQUITH_MID,
        )
    else:
        dt_v = _finite("dt", dt)
        phi_ns_v = _finite("phi_ns", phi_ns)
        if phi_ns_v == 1.0:
            raise ValueError("phi_ns is 1.0; Eq. 4.12 divides by 1 - phi_NS")
        dt_maa = Quantity(
            (dt_v - phi_ns_v * dt_fl) / (1.0 - phi_ns_v), "usec/ft",
            "apparent matrix travel time (Asquith Eq. 4.12)", ASQUITH_MID,
            inputs={"Dt": dt_v, "phi_NS": phi_ns_v, "Dt_fl": dt_fl},
            assumptions={"fluid": fkey, "Dt_fl_source": ASQUITH_T41},
        )

    u_maa: Quantity | Refusal
    if pe is None:
        u_maa = Refusal(
            reason="Eq. 4.13 needs the photoelectric curve; without Pe there is no "
                   "apparent matrix volumetric cross section",
            needed=("pe",),
            source=ASQUITH_MID,
        )
    else:
        pe_v = _finite("pe", pe)
        u_maa = Quantity(
            (pe_v * rho_b - phi_nd * u_fl) / (1.0 - phi_nd), "b/cm3",
            "apparent matrix volumetric photoelectric factor (Asquith Eq. 4.13)",
            ASQUITH_MID,
            inputs={"Pe": pe_v, "rho_b": rho_b, "phi_ND": phi_nd, "U_fl": u_fl},
            assumptions={"fluid": fkey,
                         "U_fl_basis": "asquith#24: 0.398 b/cm3 fresh, 1.36 b/cm3 salt"},
        )

    flags: list[str] = []
    candidates: tuple[tuple[str, float], ...] = ()
    if isinstance(dt_maa, Quantity):
        points = _matrix_points()
        rho_span = max(p[0] for p in points.values()) - min(p[0] for p in points.values())
        dt_span = max(p[1] for p in points.values()) - min(p[1] for p in points.values())
        ranked = sorted(
            ((key, math.hypot((rho_maa.value - p[0]) / rho_span,
                              (dt_maa.value - p[1]) / dt_span))
             for key, p in points.items()),
            key=lambda pair: pair[1],
        )
        candidates = tuple(ranked)
        flags.append(
            "the candidate ORDER is a PROVISIONAL house rule: distance is normalised "
            "by the span of the published matrix points on each axis, because "
            "asquith#24 reads Figure 4.18 by eye and publishes no metric. The POINTS "
            f"are published, from Asquith Table 4.2 ({ASQUITH_T42}) and Table 4.1 "
            f"({ASQUITH_T41})")
        flags.append(
            "asquith#24: 'Note that porosity is not predicted from this plot' - "
            "porosity comes from the two-measurement crossplots that fed phi_ND and "
            "phi_NS")

    return MidPoint(
        rho_maa=rho_maa, dt_maa=dt_maa, u_maa=u_maa, candidates=candidates,
        flags=tuple(flags),
        assumptions={"fluid": fkey,
                     "matrix_points": "Asquith Table 4.2 rho_ma with the Table 4.1 "
                                      "Wyllie Dt_ma column"},
    )


# --- #P6 multimineral_solve ---------------------------------------------------


def multimineral_solve(log_readings: Mapping[str, Any] | None = None,
                       minerals: Sequence[str] | None = None, *,
                       response_matrix: Mapping[str, Any] | None = None,
                       ) -> Refusal:
    """Always refuses. This corpus prints no N-mineral log-response system.

    Arguments are accepted and ignored so a caller's call site does not have to
    change to get the honest answer, the same way `underbalance_recommend` does.

    What the corpus does have was checked, not assumed: Eq. 4.7 and Eq. 4.1 are
    the TWO-component mixing law for one tool each, Eq. 4.11 is the same identity
    rearranged, and `asquith#24` solves the three-mineral case GRAPHICALLY as a
    triangle read off Figure 4.18. The one deterministic multimineral result the
    book shows (five volumes: calcite, dolomite, anhydrite, quartz, shale) is a
    screenshot of software, with no response matrix, no endpoint table and no
    normalisation. A least-squares inversion needs all three, and inventing them
    would produce volumes that look computed and are not.
    """
    return Refusal(
        reason=(
            "No least-squares lithology inversion is defensible from this corpus. "
            "The N-mineral log-response system, its mineral endpoint matrix and the "
            "unit-sum constraint are not printed anywhere: Asquith gives the "
            "two-component mixing law per tool (Eqs. 4.1, 4.7, 4.11) and solves the "
            "three-mineral case graphically as a mineral triangle on Figure 4.18. "
            "Writing the response matrix from memory would attach a real citation to "
            "a fabricated model. Use mid_plot for the corpus-backed answer to the "
            "same question, or mn_plot for M and N."
        ),
        needed=(
            "a source printing the log-response equations per mineral and their "
            "endpoint responses, for example Doveton, Log Analysis of Subsurface "
            "Geology, or an SPWLA multimineral / probabilistic inversion paper",
            "or mid_plot, which is citable today",
        ),
        source=ASQUITH_MID,
    )


# --- #P7 thomas_stieber -------------------------------------------------------


def thomas_stieber(phi_total: float | None = None, vshale: float | None = None, *,
                   phi_sand: float | None = None, phi_shale: float | None = None,
                   ) -> Refusal:
    """Always refuses. Thomas-Stieber is in this corpus as two figures, no equations.

    The refusal is the useful part. `jmest#1` names the three distributions and,
    more to the point, says which saturation model each one admits, and that is
    what `shaly_sand_sw` has been missing: it offers Simandoux, Waxman-Smits and
    dual water side by side with nothing to choose between them. A caller who
    knows the distribution from core or from a crossplot read by eye can act on
    the mapping quoted below without this tool computing anything.
    """
    return Refusal(
        reason=(
            "The Thomas-Stieber laminated/dispersed/structural distribution cannot be "
            "computed from this corpus: it appears only as jmest Figures 8 and 9, "
            "'The Thomas-Stieber Crossplot for Shale Typing', which are images, and "
            "no document here prints the porosity-versus-Vsh trend equations the "
            "crossplot is read against. What IS sourced is what the distribution "
            "implies once it is known (jmest#1): Simandoux and Indonesia are "
            "'essentially applicable to laminated clay models'; Waxman-Smits and dual "
            "water are 'essentially designed for the case of dispersed or structural "
            "clay models', with 'the Waxman-Smits equations only applying in the case "
            "of dispersed clay'. Pass a distribution you already know to "
            "correlation_selector rather than taking one from here."
        ),
        needed=(
            "Thomas and Stieber, 1975, SPWLA, for the laminated / dispersed / "
            "structural trend equations",
            "or a distribution established from core or a crossplot, which "
            "correlation_selector can act on, using the model mapping at "
            f"{JMEST_SHALE_DISTRIBUTION}",
        ),
        source=JMEST_THOMAS_STIEBER,
    )
