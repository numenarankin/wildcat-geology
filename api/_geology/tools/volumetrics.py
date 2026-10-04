"""Volumetrics and uncertainty. Group M.

The catalog computes column height, net pay and water saturation and then stops.
Nothing multiplied them, so the agent could tell an operator the zone is 14 feet
of 12% rock at 35% water and could not tell them how much oil that is. This
module is that multiplication, and four decisions in it are not obvious from the
arithmetic.

**Area has no default, and that is the whole point.** Ahmed Eq. 4-5 is linear in
A, so a guessed acreage scales the answer by exactly the factor of the guess and
leaves no symptom: the porosity is right, the saturation is right, the number is
wrong. The RRC publishes no lease boundaries, so there is nothing to guess from
either. `volumetrics` refuses without `area_acres` and `hcpv_thickness` exists so
that the per-well number, the one that needs no acreage at all, is still
reachable.

**Oil and gas are different equations, not one equation with a switch.** Ahmed
Eq. 4-7 puts pore volume in barrels at 7,758 per acre-foot and Eq. 13-3 puts it
in cubic feet at 43,560, because B_o is bbl/STB and B_gi is ft3/scf. Sharing one
constant and converting afterwards would work and would also hide which source
each answer came from, so the two branches carry their own coefficient, their own
anchor and their own unit.

**A recovery factor is a band in the source and stays a band here.** Ahmed #177
prints ranges, not numbers, and says outright that "oil recovery may fall outside
these ranges". `recovery_factor` therefore returns a `Range` and has no mode that
returns a point. Gravity drainage is the one row printed as "<80" with no lower
bound, which is recorded as such rather than being given an invented floor.

**The Monte Carlo is seeded or it is not reproducible.** The premise of this
catalog is that the same inputs give the same answer, so the one tool with error
bars would otherwise be the one tool that cannot be checked.
`volumetrics_probabilistic` takes an explicit `seed`, uses `random.Random(seed)`
rather than the module-level generator (which another tool could reseed), and
returns both the seed and the sample count beside the interval.

P90/P50/P10 follow the petroleum convention: P90 is the LOW estimate, the volume
with a 90% chance of being exceeded. That is the opposite of the statistical
reading of the same label, so it is stated in `assumptions` on every result.
"""
from __future__ import annotations

import math
import random
from typing import Any, Sequence

from .result import Quantity, Range, Refusal
from .petrophysics import archie_sw as _archie_sw

# --------------------------------------------------------------------------
# Corpus anchors
# --------------------------------------------------------------------------

#: Eqs. 4-3..4-7 (bulk volume, pore volume) and Eqs. 4-16..4-18 (phi-h weighted
#: average saturation), plus Example 4-1, the worked STOIIP.
AHMED_VOLUMETRIC = "00-reference/ahmed-reservoir-engineering-handbook#42"
#: N = 7758 A h phi (1 - S_wi) / B_oi, printed whole, pp. 873-874.
AHMED_STOIIP = "00-reference/ahmed-reservoir-engineering-handbook#179"
#: Eq. 13-3, G = 43,560 A h phi (1 - S_wi) / B_gi, and Eq. 13-4.
AHMED_OGIP = "00-reference/ahmed-reservoir-engineering-handbook#169"
#: Example 13-2, the worked G = 18.2 MMMscf.
AHMED_OGIP_EXAMPLE = "00-reference/ahmed-reservoir-engineering-handbook#171"
#: The drive-mechanism recovery table, p. 862.
AHMED_RECOVERY = "00-reference/ahmed-reservoir-engineering-handbook#177"
#: Chapter 11's gravity-drainage narrative, the only place the "<80" row is
#: explained ("recovery will vary widely ... reported cases ... exceeded 80%").
AHMED_GRAVITY_DRAINAGE = "00-reference/ahmed-reservoir-engineering-handbook#151"
#: Archie Eq. 7.1, for the saturation legs of the two sensitivity tools.
ASQUITH_SW = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#42"

# --------------------------------------------------------------------------
# Constants. Both are the SAME acre-foot in two units; they are never mixed.
#   7,758 bbl/acre-ft  goes with B_o in bbl/STB   -> STB      (Ahmed Eq. 4-5)
#   43,560 ft3/acre-ft goes with B_gi in ft3/scf  -> scf      (Ahmed Eq. 13-3)
# --------------------------------------------------------------------------

BBL_PER_ACRE_FT = 7758.0
CF_PER_ACRE_FT = 43560.0

OIL = "oil"
GAS = "gas"
FLUIDS = (OIL, GAS)

#: Ahmed #177, "The approximate oil recovery range is tabulated below for various
#: driving mechanisms." Fractions of original oil in place. The printed table
#: reads "Solution gap", an OCR of "Solution gas"; the same 5-30 band is printed
#: in words at #149 ("Oil recovery | 5 to 30%") for depletion drive, which is the
#: same mechanism, so the reading is corroborated rather than assumed.
RECOVERY_RANGES: dict[str, tuple[float, float]] = {
    "rock_and_liquid_expansion": (0.03, 0.07),
    "solution_gas": (0.05, 0.30),
    "gas_cap": (0.20, 0.40),
    "water_drive": (0.35, 0.75),
    "gravity_drainage": (0.00, 0.80),
    "combination": (0.30, 0.60),
}

#: The names an operator or the model is likely to use for the same six rows.
DRIVE_ALIASES: dict[str, str] = {
    "depletion": "solution_gas",
    "depletion_drive": "solution_gas",
    "solution_gas_drive": "solution_gas",
    "dissolved_gas": "solution_gas",
    "gas_cap_drive": "gas_cap",
    "water": "water_drive",
    "gravity": "gravity_drainage",
    "gravity_drainage_drive": "gravity_drainage",
    "combination_drive": "combination",
    "undersaturated": "rock_and_liquid_expansion",
}

#: Ahmed #177 prints this row as "<80", an upper bound with no floor. The floor
#: below is not published; it is the arithmetic bottom of a fraction.
GRAVITY_DRAINAGE_FLAG = (
    "gravity drainage is printed as \"<80\" at Ahmed #177: an upper bound with no "
    "published lower bound. The 0% floor is arithmetic, not sourced. #151 adds "
    "that recovery \"will vary widely\" and that cases exceeding 80% are reported, "
    "so the upper bound is soft too"
)

_P90, _P50, _P10 = 0.10, 0.50, 0.90   # petroleum convention: P90 is the LOW case


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _fraction(name: str, value: Any) -> float:
    if not _finite(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} must be a fraction in [0, 1], got {value!r}. Ahmed's equations "
            "take phi and S_w in v/v; a percentage inflates the answer by 100")
    return float(value)


def _positive(name: str, value: Any) -> float:
    if not _finite(value):
        raise ValueError(f"{name} must be a number, got {value!r}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}")
    return float(value)


def _series(name: str, value: Any, length: int) -> list[float]:
    """A per-sample column, or one scalar broadcast over `length` samples."""
    if isinstance(value, (str, bytes, dict)):
        raise ValueError(f"{name} must be a number or a sequence of numbers, got {value!r}")
    if isinstance(value, Sequence):
        if len(value) != length:
            raise ValueError(
                f"{name} has {len(value)} values but the interval has {length} samples")
        out = []
        for item in value:
            if not _finite(item):
                raise ValueError(f"{name} contains a non-finite value: {item!r}")
            out.append(float(item))
        return out
    if not _finite(value):
        raise ValueError(f"{name} must be a number or a sequence of numbers, got {value!r}")
    return [float(value)] * length


def _interval(name: str, value: Any) -> tuple[float, float]:
    """A declared range, or a scalar read as a degenerate one."""
    if isinstance(value, Sequence) and not isinstance(value, str):
        if len(value) != 2:
            raise ValueError(f"{name} must be a (low, high) pair, got {value!r}")
        low, high = float(value[0]), float(value[1])
        if not (_finite(low) and _finite(high)):
            raise ValueError(f"{name} must be finite, got {value!r}")
        if low > high:
            raise ValueError(f"{name} low {low} exceeds high {high}")
        return low, high
    if not _finite(value):
        raise ValueError(f"{name} must be a number or a (low, high) pair, got {value!r}")
    return float(value), float(value)


def _quantile(ordered: Sequence[float], q: float) -> float:
    """Nearest-rank quantile of an ascending list. No interpolation, so the
    reported value is always one the simulation actually produced."""
    idx = max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))
    return ordered[idx]


def _drive_key(name: Any) -> str | None:
    if not isinstance(name, str):
        return None
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    key = DRIVE_ALIASES.get(key, key)
    return key if key in RECOVERY_RANGES else None


# --------------------------------------------------------------------------
# M1 - hcpv_thickness
# --------------------------------------------------------------------------

def hcpv_thickness(phi: Any, sw: Any, thickness_ft: Any) -> Quantity | Refusal:
    """Hydrocarbon pore volume thickness, sum of phi (1 - S_w) dh, in feet.

    The per-well volumetric number, and the only one that needs no acreage. It is
    the `h phi (1 - S_w)` group of Ahmed's Eq. 4-7 evaluated sample by sample
    instead of on one averaged pair, which matters wherever porosity and
    saturation are correlated over the interval.

    Args:
        phi: porosity per sample, v/v. A scalar is broadcast over the interval.
        sw: water saturation per sample, v/v. A scalar is broadcast.
        thickness_ft: the depth increment each sample stands for, feet. A scalar
            is broadcast, which is the usual case (a fixed sample rate).

    The result cross-checks itself against Ahmed Eq. 4-17: the phi-h weighted
    average saturation must reproduce the same number, because
    sum(phi h (1 - S_w)) is identically phi_h (1 - S_w_avg). Two derivations of
    one quantity that disagree would be the bug, so the identity is asserted
    rather than assumed.
    """
    for name, value in (("phi", phi), ("sw", sw), ("thickness_ft", thickness_ft)):
        if isinstance(value, Sequence) and not isinstance(value, str) and not value:
            return Refusal(
                reason=f"{name} is empty; there is no interval to integrate over",
                needed=("porosity, water saturation and a thickness per sample",),
                source=AHMED_VOLUMETRIC)

    length = None
    for value in (phi, sw, thickness_ft):
        if isinstance(value, Sequence) and not isinstance(value, str):
            length = len(value)
            break
    if length is None:
        length = 1

    phis = _series("phi", phi, length)
    sws = _series("sw", sw, length)
    hs = _series("thickness_ft", thickness_ft, length)
    for value in phis:
        _fraction("phi", value)
    for value in sws:
        _fraction("sw", value)
    for value in hs:
        if value <= 0:
            raise ValueError(f"thickness_ft must be positive, got {value!r}")

    hcpv = sum(p * h * (1.0 - s) for p, s, h in zip(phis, sws, hs))
    phi_h = sum(p * h for p, h in zip(phis, hs))
    if phi_h <= 0:
        return Refusal(
            reason="phi-h over the interval is zero; there is no pore volume to fill",
            needed=("a sample with non-zero porosity",), source=AHMED_VOLUMETRIC)

    sw_avg = sum(p * h * s for p, s, h in zip(phis, sws, hs)) / phi_h   # Eq. 4-17
    identity = phi_h * (1.0 - sw_avg)
    if not math.isclose(hcpv, identity, rel_tol=1e-9, abs_tol=1e-12):
        raise AssertionError(
            f"hcpv_thickness disagrees with Ahmed Eq. 4-17: {hcpv!r} against "
            f"{identity!r}. One of the two readings of the same interval is wrong.")

    return Quantity(
        hcpv, "ft",
        "hydrocarbon pore volume thickness, sum of phi (1 - S_w) dh "
        "(the h phi (1 - S_w) group of Ahmed Eq. 4-7)",
        AHMED_VOLUMETRIC,
        inputs={"samples": length, "gross_ft": sum(hs), "phi_h_ft": phi_h,
                "sw_average": sw_avg},
        assumptions={"sw_average_equation": "Ahmed Eq. 4-17, phi-h weighted",
                     "porosity_basis": "effective porosity (Ahmed Eq. 4-3), which is "
                                       "what Eq. 4-7 takes"})


# --------------------------------------------------------------------------
# M2 - volumetrics
# --------------------------------------------------------------------------

def volumetrics(fluid: str, area_acres: float | None = None, *,
                net_pay_ft: float | None = None,
                phi: float | None = None,
                sw: float | None = None,
                b_i: float | None = None,
                hcpv_ft: float | None = None) -> Quantity | Refusal:
    """STOIIP or OGIP. Ahmed Eq. 4-7 with Eq. 4-5 (oil), Eq. 13-3 (gas).

        N = 7,758 A h phi (1 - S_w) / B_oi     STB      (Ahmed #179, #42)
        G = 43,560 A h phi (1 - S_w) / B_gi    scf      (Ahmed Eq. 13-3, #169)

    Refuses without `area_acres`. That is the one refusal this tool exists for:
    the equation is linear in A, so a guessed acreage scales the answer by the
    factor of the guess and changes nothing else about how the result looks.

    Args:
        fluid: "oil" or "gas". Selects the equation, the coefficient and the unit.
        area_acres: reservoir area, acres. Required.
        net_pay_ft: net pay thickness, feet.
        phi: porosity, v/v.
        sw: water saturation, v/v.
        b_i: initial formation volume factor. B_oi in bbl/STB for oil, B_gi in
            ft3/scf for gas. The two are not interchangeable.
        hcpv_ft: the `h phi (1 - S_w)` group in feet, from `hcpv_thickness`. Pass
            this INSTEAD of net_pay_ft/phi/sw when the interval was integrated
            sample by sample.
    """
    if fluid not in FLUIDS:
        raise ValueError(f"fluid must be one of {FLUIDS}, got {fluid!r}")

    if area_acres is None:
        return Refusal(
            reason=("no area was supplied. Ahmed Eq. 4-5 is linear in A, so an invented "
                    "acreage multiplies the answer by exactly the factor of the guess "
                    "and leaves the porosity, the pay and the saturation all looking "
                    "right. The RRC publishes no lease boundaries, so there is nothing "
                    "to guess from. Call hcpv_thickness for the per-well number that "
                    "needs no area."),
            needed=("area_acres, from a lease plat, a spacing unit or a mapped "
                    "hydrocarbon outline",),
            source=AHMED_VOLUMETRIC)
    _positive("area_acres", area_acres)

    if hcpv_ft is None:
        missing = [name for name, value in (("net_pay_ft", net_pay_ft),
                                            ("phi", phi), ("sw", sw)) if value is None]
        if missing:
            return Refusal(
                reason=f"needs {', '.join(missing)}, or hcpv_ft in their place",
                needed=tuple(missing), source=AHMED_VOLUMETRIC)
        _positive("net_pay_ft", net_pay_ft)
        _fraction("phi", phi)
        _fraction("sw", sw)
        hcpv = net_pay_ft * phi * (1.0 - sw)
        detail: dict[str, Any] = {"net_pay_ft": net_pay_ft, "phi": phi, "sw": sw}
    else:
        if None not in (net_pay_ft, phi, sw):
            raise ValueError(
                "supply either hcpv_ft or (net_pay_ft, phi, sw), not both; two "
                "hydrocarbon thicknesses that disagree would be silently averaged")
        hcpv = _positive("hcpv_ft", hcpv_ft)
        detail = {"hcpv_ft": hcpv}

    if b_i is None:
        return Refusal(
            reason=("needs the initial formation volume factor: B_oi in bbl/STB for oil "
                    "(Ahmed #179) or B_gi in ft3/scf for gas (Eq. 13-3). Without it the "
                    "answer is a reservoir volume, not a stock-tank or standard-condition "
                    "volume"),
            needed=("b_i",), source=AHMED_VOLUMETRIC)
    _positive("b_i", b_i)

    if fluid == OIL:
        value = BBL_PER_ACRE_FT * area_acres * hcpv / b_i
        unit, coeff = "STB", BBL_PER_ACRE_FT
        method = ("STOIIP, N = 7,758 A h phi (1 - S_w) / B_oi "
                  "(Ahmed Eq. 4-5 with Eq. 4-7)")
        source, b_unit = AHMED_STOIIP, "bbl/STB"
    else:
        value = CF_PER_ACRE_FT * area_acres * hcpv / b_i
        unit, coeff = "scf", CF_PER_ACRE_FT
        method = "OGIP, G = 43,560 A h phi (1 - S_wi) / B_gi (Ahmed Eq. 13-3)"
        source = f"{AHMED_OGIP}; {AHMED_OGIP_EXAMPLE}"
        b_unit = "ft3/scf"

    return Quantity(
        value, unit, method, source,
        inputs={"fluid": fluid, "area_acres": area_acres, "b_i": b_i,
                "hcpv_ft": hcpv,
                "hydrocarbon_pore_volume": coeff * area_acres * hcpv,
                **detail},
        assumptions={"coefficient": coeff,
                     "coefficient_basis": f"{coeff:,.0f} per acre-foot",
                     "b_i_unit": b_unit,
                     "area_source": "caller supplied; never defaulted",
                     "constant_saturation": "one S_w over the whole net pay unless "
                                            "hcpv_ft was integrated per sample"})


# --------------------------------------------------------------------------
# M3 - recovery_factor
# --------------------------------------------------------------------------

def recovery_factor(drive_mechanism: str, in_place: float | None = None,
                    in_place_unit: str = "STB") -> Range | Refusal:
    """Recoverable volume under a stated drive, as the published BAND.

    Ahmed #177 prints a range per mechanism and says the recovery "may fall
    outside these ranges". There is no mode of this tool that returns a single
    number: collapsing the band would invent a precision the source disclaims,
    the same reason `coning_critical_rate` returns a spread.

    With `in_place` the band is the recoverable volume in the same unit; without
    it the band is the recovery factor itself, as a fraction.
    """
    key = _drive_key(drive_mechanism)
    if key is None:
        return Refusal(
            reason=(f"no published recovery range for drive mechanism "
                    f"{drive_mechanism!r}. Ahmed #177 tabulates six: "
                    f"{', '.join(sorted(RECOVERY_RANGES))}"),
            needed=("one of the six driving mechanisms Ahmed Chapter 11 defines",),
            source=AHMED_RECOVERY)

    low_rf, high_rf = RECOVERY_RANGES[key]
    flags: tuple[str, ...] = (
        "Ahmed #177: \"these calculations are approximate and, therefore, oil "
        "recovery may fall outside these ranges\"",)
    source = AHMED_RECOVERY
    if key == "gravity_drainage":
        flags += (GRAVITY_DRAINAGE_FLAG,)
        source = f"{AHMED_RECOVERY}; {AHMED_GRAVITY_DRAINAGE}"

    if in_place is None:
        return Range(
            low_rf, high_rf, "fraction",
            f"published primary recovery range for a {key} reservoir (Ahmed #177)",
            source, members={"low": low_rf, "high": high_rf},
            inputs={"drive_mechanism": key},
            assumptions={"basis": "primary recovery, fraction of original oil in place",
                         "requested_as": drive_mechanism},
            flags=flags)

    _positive("in_place", in_place)
    low, high = low_rf * in_place, high_rf * in_place
    return Range(
        low, high, in_place_unit,
        f"recoverable volume at the published {key} recovery range "
        f"({low_rf:.0%} to {high_rf:.0%}, Ahmed #177)",
        source, members={"low": low, "high": high},
        inputs={"drive_mechanism": key, "in_place": in_place,
                "recovery_factor_low": low_rf, "recovery_factor_high": high_rf},
        assumptions={"basis": "primary recovery only; no secondary or tertiary "
                              "recovery is included",
                     "requested_as": drive_mechanism},
        flags=flags)


# --------------------------------------------------------------------------
# M4 - volumetrics_probabilistic
# --------------------------------------------------------------------------

def volumetrics_probabilistic(fluid: str, seed: int, *,
                              area_acres: Any = None,
                              net_pay_ft: Any = None,
                              phi: Any = None,
                              sw: Any = None,
                              b_i: Any = None,
                              samples: int = 10000) -> Range | Refusal:
    """P90, P50 and P10 in place, by Monte Carlo over the supplied input ranges.

    Every argument takes either a scalar or a `(low, high)` pair. Sampling is
    uniform inside each pair and independent between them, both of which are
    choices this corpus does not make for us and both of which are recorded in
    `assumptions` rather than left implicit: Ahmed prints the volumetric equation
    and no distribution for its inputs.

    `seed` is required and is returned. `random.Random(seed)` is used rather than
    the module-level generator, so no other tool reseeding `random` can move this
    answer.

    P90 is the LOW case (90% chance of being exceeded), P10 the high case. That
    is the petroleum convention and the reverse of the statistical one.
    """
    if fluid not in FLUIDS:
        raise ValueError(f"fluid must be one of {FLUIDS}, got {fluid!r}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(
            f"seed must be an integer, got {seed!r}. An unseeded sampler would make the "
            "one part of this catalog with error bars the one part that cannot be "
            "reproduced")
    if isinstance(samples, bool) or not isinstance(samples, int) or samples < 100:
        raise ValueError(f"samples must be an integer of at least 100, got {samples!r}")

    if area_acres is None:
        return Refusal(
            reason=("no area range was supplied. The equation is linear in A, so an "
                    "invented acreage scales P90, P50 and P10 alike and the spread "
                    "still looks honest"),
            needed=("area_acres, as a number or a (low, high) pair",),
            source=AHMED_VOLUMETRIC)
    missing = [name for name, value in (("net_pay_ft", net_pay_ft), ("phi", phi),
                                        ("sw", sw), ("b_i", b_i)) if value is None]
    if missing:
        return Refusal(reason=f"needs {', '.join(missing)}", needed=tuple(missing),
                       source=AHMED_VOLUMETRIC)

    ranges = {"area_acres": _interval("area_acres", area_acres),
              "net_pay_ft": _interval("net_pay_ft", net_pay_ft),
              "phi": _interval("phi", phi),
              "sw": _interval("sw", sw),
              "b_i": _interval("b_i", b_i)}
    for name in ("phi", "sw"):
        _fraction(f"{name} low", ranges[name][0])
        _fraction(f"{name} high", ranges[name][1])
    for name in ("area_acres", "net_pay_ft", "b_i"):
        _positive(f"{name} low", ranges[name][0])

    coeff = BBL_PER_ACRE_FT if fluid == OIL else CF_PER_ACRE_FT
    unit = "STB" if fluid == OIL else "scf"
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(samples):
        area = rng.uniform(*ranges["area_acres"])
        pay = rng.uniform(*ranges["net_pay_ft"])
        porosity = rng.uniform(*ranges["phi"])
        saturation = rng.uniform(*ranges["sw"])
        b = rng.uniform(*ranges["b_i"])
        draws.append(coeff * area * pay * porosity * (1.0 - saturation) / b)
    draws.sort()

    p90, p50, p10 = (_quantile(draws, _P90), _quantile(draws, _P50),
                     _quantile(draws, _P10))
    return Range(
        p90, p10, unit,
        f"Monte Carlo over the volumetric equation for {fluid}, "
        f"{samples} uniform samples at seed {seed}; low is P90, high is P10",
        AHMED_STOIIP if fluid == OIL else AHMED_OGIP,
        members={"P90": p90, "P50": p50, "P10": p10,
                 "minimum": draws[0], "maximum": draws[-1],
                 "mean": sum(draws) / len(draws)},
        inputs={"fluid": fluid, "seed": seed, "samples": samples,
                **{f"{k}_range": list(v) for k, v in ranges.items()}},
        assumptions={
            "seed": seed,
            "samples": samples,
            "generator": "random.Random(seed), not the module-level random",
            "distribution": "uniform inside each supplied (low, high); the corpus "
                            "prints the volumetric equation and no distribution for "
                            "its inputs, so this is the tool's choice, not Ahmed's",
            "correlation": "inputs sampled independently; porosity and saturation are "
                           "in fact anti-correlated in most reservoirs, so a real P90 "
                           "to P10 spread is narrower than this one",
            "percentile_convention": "petroleum: P90 is the low case, P10 the high",
            "quantile_rule": "nearest rank, so each reported value is one the "
                             "simulation actually produced",
        })


# --------------------------------------------------------------------------
# M5 - archie_sensitivity
# --------------------------------------------------------------------------

def archie_sensitivity(rt: float, phi: float, rw: float, rw_source: Any = None, *,
                       a_candidates: Sequence[float] | None = None,
                       m_candidates: Sequence[float] | None = None,
                       n_candidates: Sequence[float] | None = None,
                       rt_invasion_corrected: bool = False) -> Range | Refusal:
    """Sweep Archie's a, m and n and report the resulting S_w band.

    Same shape as `matrix_density_sensitivity`: a `Range` whose `members` carry
    every combination, so a reviewer can see which triple produced each end. No
    candidate list is defaulted, because defaulting one is the assumption being
    measured, and a single combination is refused because low and high would be
    equal and the result would read as "the exponents do not matter".

    Archie itself is not reimplemented here. Every combination goes through
    `archie_sw`, which keeps the Rw-provenance and Sw > 1 gates live and means
    the two cannot drift apart.
    """
    for name, arg in (("a_candidates", a_candidates), ("m_candidates", m_candidates),
                      ("n_candidates", n_candidates)):
        if isinstance(arg, str):
            raise ValueError(f"{name} must be a sequence of numbers, not the string {arg!r}")
        if not arg:
            return Refusal(
                reason=(f"no {name} supplied. This tool never defaults an Archie "
                        "exponent: S_w is exquisitely sensitive to n, and choosing one "
                        "silently is the error the sweep exists to measure"),
                needed=(f"a list of candidate values for {name.split('_')[0]}",),
                source=ASQUITH_SW)

    combos = [(a, m, n) for a in a_candidates for m in m_candidates for n in n_candidates]
    if len(combos) == 1:
        return Refusal(
            reason=("one a, one m and one n is a point estimate, not a sensitivity: low "
                    "and high would be equal. Call archie_sw for a stated triple, or add "
                    "a candidate to any axis"),
            needed=("a second candidate on the a, m or n axis",), source=ASQUITH_SW)

    members: dict[str, float] = {}
    refusals: list[str] = []
    for a, m, n in combos:
        label = f"a={a:g},m={m:g},n={n:g}"
        result = _archie_sw(rt, phi, rw, rw_source, a=a, m=m, n=n,
                            rt_invasion_corrected=rt_invasion_corrected)
        if isinstance(result, Refusal):
            refusals.append(f"{label}: {result.reason}")
        else:
            members[label] = result.value

    if not members:
        return Refusal(reason=" | ".join(refusals),
                       needed=("an Archie call that can answer; see the per-combination "
                               "reasons",),
                       source=ASQUITH_SW)

    low_label = min(members, key=members.get)
    high_label = max(members, key=members.get)
    flags: tuple[str, ...] = ()
    if refusals:
        flags += (f"{len(refusals)} of {len(combos)} combinations refused and are not in "
                  f"the band: {' | '.join(refusals)}",)
    if not rt_invasion_corrected:
        flags += ("Rt not declared invasion-corrected; deep readings are not Rt",)

    return Range(
        members[low_label], members[high_label], "v/v",
        f"Archie S_w swept across {len(members)} (a, m, n) combinations "
        f"(Asquith Eq. 7.1); low at {low_label}, high at {high_label}",
        ASQUITH_SW, members=members,
        inputs={"rt": rt, "phi": phi, "rw": rw,
                "a_candidates": list(a_candidates), "m_candidates": list(m_candidates),
                "n_candidates": list(n_candidates)},
        assumptions={"combinations": len(combos), "answered": len(members),
                     "sw_engine": "tools.petrophysics.archie_sw, not a second "
                                  "implementation of Eq. 7.1"},
        flags=flags)


# --------------------------------------------------------------------------
# M6 - propagate_uncertainty
# --------------------------------------------------------------------------

def propagate_uncertainty(thickness_ft: Any, phi_low: Sequence[float],
                          phi_high: Sequence[float], rt: Sequence[float],
                          rw: Any, rw_source: Any = None, *,
                          phi_cutoff: float, sw_cutoff: float,
                          a: Any = 1.0, m: Any = 2.0, n: Any = 2.0,
                          rt_invasion_corrected: bool = False) -> Range | Refusal:
    """Carry declared input intervals through porosity, saturation and net pay.

    The chain the catalog already has runs porosity -> saturation -> net pay and
    reports a point at every step. This runs the same chain at the CORNERS of the
    declared intervals and reports the interval that comes out.

    Corners rather than samples on purpose: net pay is monotone in each input
    (more porosity or less saturation can only add pay), so the extremes of a box
    are attained at its vertices and enumerating them is exact where sampling
    would only be close. Only the axes actually declared as intervals are
    enumerated, so a fully-pinned call costs one evaluation.

    `phi_low` / `phi_high` are the porosity band per sample, which is what
    `matrix_density_sensitivity` produces. `rw`, `a`, `m` and `n` each take a
    scalar or a `(low, high)` pair.

    A sample whose Archie call refuses for S_w > 1 is counted as not pay, not
    dropped: above unity means the zone is wet, which is a net-pay verdict, and
    the count is flagged.
    """
    _fraction("phi_cutoff", phi_cutoff)
    _fraction("sw_cutoff", sw_cutoff)
    if not phi_low or not phi_high or not rt:
        return Refusal(reason="phi_low, phi_high and rt must each carry at least one sample",
                       needed=("a logged interval",), source=ASQUITH_SW)

    count = len(phi_low)
    lows = _series("phi_low", phi_low, count)
    highs = _series("phi_high", phi_high, count)
    rts = _series("rt", rt, count)
    hs = _series("thickness_ft", thickness_ft, count)
    for value in lows + highs:
        _fraction("phi", value)
    for i, (lo, hi) in enumerate(zip(lows, highs)):
        if lo > hi:
            raise ValueError(f"phi_low[{i}] {lo} exceeds phi_high[{i}] {hi}")

    axes: list[tuple[str, tuple[float, float]]] = []
    scalars = {"rw": _interval("rw", rw), "a": _interval("a", a),
               "m": _interval("m", m), "n": _interval("n", n)}
    for name, (lo, hi) in scalars.items():
        if lo != hi:
            axes.append((name, (lo, hi)))
    phi_declared = any(lo != hi for lo, hi in zip(lows, highs))

    members: dict[str, float] = {}
    hcpvs: dict[str, float] = {}
    wet_samples = 0
    refusals: list[str] = []

    phi_ends = ("low", "high") if phi_declared else ("low",)
    for phi_end in phi_ends:
        column = lows if phi_end == "low" else highs
        for mask in range(1 << len(axes)):
            picked = {name: (bounds[1] if (mask >> i) & 1 else bounds[0])
                      for i, (name, bounds) in enumerate(axes)}
            values = {name: picked.get(name, bounds[0])
                      for name, bounds in scalars.items()}
            label = "phi=" + phi_end
            for name in ("rw", "a", "m", "n"):
                label += f",{name}={values[name]:g}"

            net_ft = 0.0
            hcpv = 0.0
            failed = None
            for phi_i, rt_i, h_i in zip(column, rts, hs):
                if phi_i < phi_cutoff or phi_i <= 0.0:
                    continue
                result = _archie_sw(rt_i, phi_i, values["rw"], rw_source,
                                    a=values["a"], m=values["m"], n=values["n"],
                                    rt_invasion_corrected=rt_invasion_corrected)
                if isinstance(result, Refusal):
                    # archie_sw's own words for the Sw > 1.0 case. Matched on the
                    # phrase rather than the class, because every other refusal it
                    # can return is a reason the whole corner is uncomputable and
                    # must not be quietly counted as "wet".
                    if "above 1.0" in result.reason:
                        wet_samples += 1
                        continue
                    failed = result
                    break
                if result.value <= sw_cutoff:
                    net_ft += h_i
                    hcpv += phi_i * h_i * (1.0 - result.value)
            if failed is not None:
                refusals.append(f"{label}: {failed.reason}")
                continue
            members[label] = net_ft
            hcpvs[label] = hcpv

    if not members:
        return Refusal(reason=" | ".join(refusals) or "no corner could be evaluated",
                       needed=("an Rw with stated provenance, and an Archie call that "
                               "can answer",),
                       source=ASQUITH_SW)

    low_label = min(members, key=members.get)
    high_label = max(members, key=members.get)
    flags: tuple[str, ...] = ()
    if wet_samples:
        flags += (f"{wet_samples} sample evaluations refused for S_w above 1.0 and were "
                  "counted as not pay; asquith#44 is the corpus's statement of what that "
                  "means",)
    if refusals:
        flags += (f"{len(refusals)} corners could not be evaluated and are not in the "
                  f"band: {' | '.join(refusals)}",)
    if not rt_invasion_corrected:
        flags += ("Rt not declared invasion-corrected; deep readings are not Rt",)

    return Range(
        members[low_label], members[high_label], "ft",
        "net pay carried through the porosity to saturation to net pay chain at the "
        f"corners of the declared input intervals ({len(members)} corners); "
        f"low at {low_label}, high at {high_label}",
        f"{ASQUITH_SW}; {AHMED_VOLUMETRIC}", members=members,
        inputs={"samples": count, "gross_ft": sum(hs), "phi_cutoff": phi_cutoff,
                "sw_cutoff": sw_cutoff,
                "declared_intervals": ["phi"] * int(phi_declared) + [nm for nm, _ in axes]},
        assumptions={
            "method": "corner enumeration, exact for a chain monotone in each input",
            "corners": len(members),
            "hcpv_ft_low": min(hcpvs.values()),
            "hcpv_ft_high": max(hcpvs.values()),
            "sw_engine": "tools.petrophysics.archie_sw",
            "net_pay_rule": "a sample counts as pay when phi >= phi_cutoff and "
                            "S_w <= sw_cutoff; cutoffs are the caller's, never defaulted",
        },
        flags=flags)
