"""Gas properties. Ahmed, Chapter 2.

Ordering matters and is enforced by the signatures: pseudo-criticals feed the
sour correction, which feeds z, which feeds density, which feeds viscosity. A
z computed from uncorrected pseudo-criticals moves density about 8% on a sour
gas, so `gas_density` takes a z rather than a gravity — you cannot skip the step.

Units are the other trap and are typed into the argument names: p in psia
(never psig), T in degrees Rankine (never Fahrenheit).
"""
from __future__ import annotations

import math

from .result import Quantity, Refusal

PSEUDOCRIT = "00-reference/ahmed-reservoir-engineering-handbook#12"
WICHERT = "00-reference/ahmed-reservoir-engineering-handbook#13"
#: "CORRECTION FOR HIGH-MOLECULAR WEIGHT GASES" -- Sutton (1985). This, NOT #12,
#: is where the gamma_g > 0.75 statement lives: "Kay's mixing rules should not be
#: used to determine the pseudo-critical pressure and temperature for reservoir
#: gases with specific gravities greater than about 0.75." #12 carries the
#: 5%-nonhydrocarbon accuracy statement and nothing about gravity.
SUTTON = "00-reference/ahmed-reservoir-engineering-handbook#14"
HALL_YARBOROUGH = "00-reference/ahmed-reservoir-engineering-handbook#16"
DENSITY = "00-reference/ahmed-reservoir-engineering-handbook#12"
FVF = "00-reference/ahmed-reservoir-engineering-handbook#18"
VISCOSITY = "00-reference/ahmed-reservoir-engineering-handbook#20"

R_GAS = 10.73  # psia ft3 / (lb-mol degR)
AIR_MW = 28.96


def pseudocritical(gamma_g: float, fluid: str = "natural_gas"):
    """Standing. Natural gas Eqs. 2-18/2-19; gas-condensate Eqs. 2-20/2-21.

    The two correlations are not interchangeable. At gamma_g = 0.7:
        natural gas    T_pc = 389.375 degR   p_pc = 669.125 psia
        gas-condensate T_pc = 382.965 degR   p_pc = 664.371 psia
    i.e. 6.41 degR and 4.75 psia apart, which moves z at 3000 psia / 640 degR
    from 0.84844 to 0.85947 — 1.3%, and it compounds through density, FVF and
    viscosity. So the fluid type is carried explicitly rather than defaulted
    silently. (This docstring previously said "about 28 degR" and
    `specs/77-gas_z_factor.md` says "34.6 psia in p_pc"; both are wrong, and the
    figures above are longhand from Eqs. 2-18/2-21. Pinned by
    `tests/group_h/h77_h80.py::TestGasZFactor::
    test_fluid_type_selects_the_other_correlation`.)
    """
    if fluid == "natural_gas":
        tpc = 168 + 325 * gamma_g - 12.5 * gamma_g ** 2
        ppc = 677 + 15.0 * gamma_g - 37.5 * gamma_g ** 2
        eqs = "Standing Eqs. 2-18/2-19"
    elif fluid == "gas_condensate":
        tpc = 187 + 330 * gamma_g - 71.5 * gamma_g ** 2
        ppc = 706 - 51.7 * gamma_g - 11.1 * gamma_g ** 2
        eqs = "Standing Eqs. 2-20/2-21"
    else:
        raise ValueError("fluid must be 'natural_gas' or 'gas_condensate'")
    flags = (f"gamma_g > 0.75: Kay's mixing rules degrade; consider the Sutton "
             f"correction ({SUTTON})",) if gamma_g > 0.75 else ()
    return Quantity(tpc, "degR", f"pseudo-critical temperature ({eqs})", PSEUDOCRIT,
                    inputs={"gamma_g": gamma_g, "p_pc": ppc},
                    assumptions={"fluid": fluid}, flags=flags)


def pseudocritical_pair(gamma_g: float, fluid: str = "natural_gas") -> tuple[float, float]:
    """(T_pc degR, p_pc psia) as plain numbers, for internal chaining."""
    q = pseudocritical(gamma_g, fluid)
    return q.value, q.inputs["p_pc"]


def wichert_aziz(tpc: float, ppc: float, y_co2: float, y_h2s: float, y_n2: float = 0.0):
    """Sour-gas correction. Eqs. 2-22 to 2-24.

    Refuses on nitrogen: Wichert-Aziz corrects for CO2 and H2S only, and
    silently ignoring y_N2 would return a plausible number for the wrong gas.
    Carr-Kobayashi-Burrows (Eqs. 2-25/2-26) is the nitrogen path.
    """
    if y_n2 > 0:
        return Refusal(
            reason="Wichert-Aziz does not handle nitrogen; y_N2 > 0 needs Carr-Kobayashi-Burrows",
            needed=("Carr-Kobayashi-Burrows correction (Ahmed Eqs. 2-25/2-26)",),
            source=WICHERT)
    a = y_co2 + y_h2s
    b = y_h2s
    eps = 120 * (a ** 0.9 - a ** 1.6) + 15 * (b ** 0.5 - b ** 4.0)
    tpc_c = tpc - eps
    ppc_c = (ppc * tpc_c) / (tpc + b * (1 - b) * eps)
    return Quantity(tpc_c, "degR", "Wichert-Aziz corrected T_pc (Eq. 2-22)", WICHERT,
                    inputs={"T_pc": tpc, "p_pc": ppc, "y_CO2": y_co2, "y_H2S": y_h2s,
                            "epsilon": eps, "p_pc_corrected": ppc_c})


def gas_z_factor(p_psia: float, t_degr: float, gamma_g: float,
                 fluid: str = "natural_gas", y_co2: float = 0.0, y_h2s: float = 0.0,
                 y_n2: float = 0.0, tol: float = 1e-12, max_iter: int = 100):
    """Hall-Yarborough, Eqs. 2-36 to 2-39, solved by Newton-Raphson.

    Refuses below T_pr = 1.0, which the source states the method is not
    recommended for. Applies Wichert-Aziz first where the gas is sour.

    Two things here deliberately depart from the printed source; both are
    argued in `specs/77-gas_z_factor.md`.

    **The `- y**4` below is right and the corpus is wrong.** Ahmed's Eq. 2-37
    prints the Starling-Carnahan numerator as `Y + Y^2 + Y^3 + Y^4`, but his own
    Eq. 2-39 is the derivative of the *minus* form: d/dY[(Y+Y^2+Y^3-Y^4)/(1-Y)^3]
    works out to exactly (1+4Y+4Y^2-4Y^3+Y^4)/(1-Y)^4, and the plus form does
    not. Do not "fix" this back to match the printed equation.

    **Newton is globalized onto 0 < Y < 1.** Y is a reduced density and
    (1-Y)^3 has a pole at Y = 1; a raw Newton step can vault the pole, after
    which the iterates wander and the tolerance is never met. That produced a
    false "did not converge" refusal over a swathe of the valid envelope
    (T_pr 1.0-1.55). F(Y) was verified to have exactly one root in (0,1) at
    every point of a 1.0 <= T_pr <= 3.0, 0.01 <= p_pr <= 30 grid, so bisecting
    back into the surviving bracket cannot cost the physical root.
    """
    if p_psia <= 0 or t_degr <= 0 or gamma_g <= 0:
        raise ValueError("p_psia, t_degr and gamma_g must all be positive")
    tpc, ppc = pseudocritical_pair(gamma_g, fluid)
    corrected = None
    if y_co2 or y_h2s or y_n2:
        corrected = wichert_aziz(tpc, ppc, y_co2, y_h2s, y_n2)
        if isinstance(corrected, Refusal):
            return corrected
        tpc, ppc = corrected.value, corrected.inputs["p_pc_corrected"]

    tpr, ppr = t_degr / tpc, p_psia / ppc
    if tpr < 1.0:
        return Refusal(
            reason=f"T_pr = {tpr:.3f} < 1.0; Hall-Yarborough is not recommended below one",
            needed=("a z-factor method valid below T_pr = 1",), source=HALL_YARBOROUGH)

    t = 1.0 / tpr
    x1 = -0.06125 * ppr * t * math.exp(-1.2 * (1 - t) ** 2)
    x2 = 14.76 * t - 9.76 * t ** 2 + 4.58 * t ** 3
    x3 = 90.7 * t - 242.2 * t ** 2 + 42.4 * t ** 3
    x4 = 2.18 + 2.82 * t

    def _f(yv: float) -> float:
        return (x1 + (yv + yv ** 2 + yv ** 3 - yv ** 4) / (1 - yv) ** 3
                - x2 * yv ** 2 + x3 * yv ** x4)

    # Ahmed's own initial guess, Eq. 2-37 Step 1, clamped into the physical domain.
    y = 0.0125 * ppr * t * math.exp(-1.2 * (1 - t) ** 2)
    y = min(max(y, 1e-10), 1.0 - 1e-10)
    for _ in range(max_iter):
        f = _f(y)
        df = ((1 + 4 * y + 4 * y ** 2 - 4 * y ** 3 + y ** 4) / (1 - y) ** 4
              - 2 * x2 * y + x4 * x3 * y ** (x4 - 1))
        if df == 0.0:
            return Refusal(reason="Hall-Yarborough Newton step hit a zero derivative",
                           needed=("another z-factor method",), source=HALL_YARBOROUGH)
        step = f / df
        y_next = y - step
        if not 0.0 < y_next < 1.0:
            # The step left the domain of Eq. 2-37; bisect toward the bound instead.
            y_next = y / 2.0 if y_next <= 0.0 else (y + 1.0) / 2.0
            step = y - y_next
        y = y_next
        if abs(step) < tol:
            break
    else:
        return Refusal(reason="Hall-Yarborough did not converge",
                       needed=("different initial guess or another z method",),
                       source=HALL_YARBOROUGH)

    # Never return a root the defining equation does not actually accept.
    residual = _f(y)
    if not 0.0 < y < 1.0 or abs(residual) > 1e-6 * max(1.0, abs(x1)):
        return Refusal(
            reason=(f"Hall-Yarborough converged to Y = {y:.6g} with residual "
                    f"F(Y) = {residual:.3g}; that is not a root of Eq. 2-37"),
            needed=("another z-factor method",), source=HALL_YARBOROUGH)

    z = (0.06125 * ppr * t / y) * math.exp(-1.2 * (1 - t) ** 2)
    flags = []
    if gamma_g > 0.75:
        flags.append(
            "gamma_g > 0.75: Ahmed #14 (Sutton 1985) says Kay's mixing rules should not "
            "be used above about 0.75; Sutton's compositional correction (Eqs. 2-27 to "
            "2-35) is the remedy and needs a full analysis, which a gravity-only call "
            "cannot supply")
    nonhc = y_co2 + y_h2s + y_n2
    if nonhc > 0.05:
        flags.append(
            f"nonhydrocarbon fraction {nonhc:.3f} > 0.05: Ahmed #12 states errors as large "
            "as 10% may occur above 5% nonhydrocarbons (an accuracy statement, not a bound)")
    return Quantity(z, "dimensionless", "Hall-Yarborough (Ahmed Eq. 2-36)", HALL_YARBOROUGH,
                    inputs={"p": p_psia, "T": t_degr, "T_pr": tpr, "p_pr": ppr,
                            "T_pc": tpc, "p_pc": ppc, "Y": y},
                    assumptions={"sour_corrected": bool(corrected), "fluid": fluid},
                    flags=tuple(flags))


def gas_density(p_psia: float, t_degr: float, z: float, gamma_g: float):
    """rho_g = p*Ma / (z*R*T).  Ahmed Eq. 2-17.  lb/ft3.

    Eq. 2-17 is the real-gas equation-of-state rearranged, so the source states
    no validity limits and this tool has no refusal conditions — every
    restriction that applies is inherited through `z`, and `gas_z_factor`
    already refuses on its own. Impossible arguments are programmer error and
    raise, so that a z of zero says what is wrong instead of surfacing as a
    bare ZeroDivisionError from inside the formula.
    """
    if p_psia <= 0 or t_degr <= 0 or z <= 0 or gamma_g <= 0:
        raise ValueError(
            f"p_psia, t_degr, z and gamma_g must all be positive; got "
            f"p={p_psia}, T={t_degr}, z={z}, gamma_g={gamma_g}")
    ma = gamma_g * AIR_MW
    rho = (p_psia * ma) / (z * R_GAS * t_degr)
    return Quantity(rho, "lb/ft3", "real-gas density (Ahmed Eq. 2-17)", DENSITY,
                    inputs={"p_psia": p_psia, "T_degR": t_degr, "z": z, "M_a": ma},
                    assumptions={"R": R_GAS})


def gas_fvf(p_psia: float, t_degr: float, z: float, unit: str = "ft3/scf",
            p_sc: float = 14.7, t_sc: float = 520.0):
    """Bg = 0.02827 zT/p (ft3/scf) or 0.005035 zT/p (bbl/scf). Eqs. 2-53/2-54.

    Those coefficients bake in p_sc = 14.7 psia and T_sc = 520 degR. Texas
    reports gas on a **14.65 psia** base, so the standard conditions are explicit
    arguments and a non-default base rescales the coefficient rather than being
    silently ignored — about 0.34% on RRC-reported volumes.

    The rescaling is **exact, not an approximation**. Ahmed derives the general
    coefficient one line above Eq. 2-53 -- `Bg = (p_sc/T_sc)(zT/p)` -- and
    0.02827 is simply 14.7/520 evaluated. So any other base is the same equation
    at different constants.

    Direction matters and was previously inverted here: Bg = V_res/V_sc, so a
    LOWER standard pressure means the gas occupies MORE volume at standard
    conditions, which makes Bg SMALLER. Bg scales as p_sc and as 1/T_sc. On the
    Texas base Bg is 14.65/14.7 = 0.34% *lower* than on 14.7, not higher.
    """
    base = {"ft3/scf": 0.02827, "bbl/scf": 0.005035}
    if unit not in base:
        raise ValueError("unit must be 'ft3/scf' or 'bbl/scf'")
    if p_psia <= 0 or t_degr <= 0 or z <= 0 or p_sc <= 0 or t_sc <= 0:
        raise ValueError(
            f"p_psia, t_degr, z, p_sc and t_sc must all be positive; got "
            f"p={p_psia}, T={t_degr}, z={z}, p_sc={p_sc}, t_sc={t_sc}")
    coeff = base[unit] * (p_sc / 14.7) * (520.0 / t_sc)
    bg = coeff * z * t_degr / p_psia
    flags = []
    if p_sc != 14.7:
        flags.append(f"non-standard base pressure {p_sc} psia "
                     f"(Bg is {p_sc / 14.7:.6f} of the 14.7 psia value)")
    if t_sc != 520.0:
        flags.append(f"non-standard base temperature {t_sc} degR "
                     f"(Bg is {520.0 / t_sc:.6f} of the 520 degR value)")
    return Quantity(bg, unit, f"gas FVF (Ahmed Eq. {'2-53' if unit == 'ft3/scf' else '2-54'})",
                    FVF, inputs={"p_psia": p_psia, "T_degR": t_degr, "z": z},
                    assumptions={"p_sc": p_sc, "T_sc": t_sc, "coefficient": coeff},
                    flags=tuple(flags))


def gas_viscosity(t_degr: float, rho_g: float, gamma_g: float, sour: bool = False):
    """Lee-Gonzalez-Eakin, Eqs. 2-63 to 2-66. cp.

    Refuses on sour gas: the authors state the method cannot be used there, and
    the corpus supplies the Standing/Dempsey route (Eqs. 2-58 to 2-62) with its
    CO2/H2S/N2 corrections instead. Returning a number anyway is the failure mode
    this refusal exists for.

    The source says three things about validity and they are NOT the same kind
    of statement, so they get three different treatments. "cannot be used for
    sour gases" is a prohibition -> refusal. "less accurate for gases with
    higher specific gravities" is a degradation with **no threshold attached**
    -> a flag with no invented cutoff (Sutton's 0.75 is about Kay's mixing rules
    for pseudo-criticals, a different correlation, and must not be borrowed
    here). The 2.7% / 8.99% figures are a stated accuracy -> carried in
    assumptions, at the source's printed precision.
    """
    if sour:
        return Refusal(
            reason="Lee-Gonzalez-Eakin cannot be used for sour gases (stated by the authors)",
            needed=("Standing/Dempsey with the CO2/H2S/N2 corrections, Ahmed Eqs. 2-58 to 2-62",),
            source=VISCOSITY)
    if t_degr <= 0 or rho_g < 0 or gamma_g <= 0:
        raise ValueError(
            f"t_degr and gamma_g must be positive and rho_g non-negative; got "
            f"T={t_degr}, rho_g={rho_g}, gamma_g={gamma_g}")
    ma = gamma_g * AIR_MW
    k = ((9.4 + 0.02 * ma) * t_degr ** 1.5) / (209 + 19 * ma + t_degr)
    x = 3.5 + 986.0 / t_degr + 0.01 * ma
    y = 2.4 - 0.2 * x
    mu = 1e-4 * k * math.exp(x * (rho_g / 62.4) ** y)
    return Quantity(mu, "cp", "Lee-Gonzalez-Eakin (Ahmed Eq. 2-63)", VISCOSITY,
                    inputs={"T_degR": t_degr, "rho_g": rho_g, "M_a": ma,
                            "K": k, "X": x, "Y": y},
                    assumptions={"validity": "sweet gas only; standard deviation 2.7%, "
                                             "maximum deviation 8.99% (ahmed#20)"},
                    flags=("Ahmed #20: 'the correlation is less accurate for gases with "
                           "higher specific gravities'. The source attaches no threshold "
                           "to this, so none is asserted here",))


# =====================================================================
# Tool #81 `pseudopressure` -- real-gas pseudopressure m(p), Ahmed Eq. 6-39.
#
# Lives here because it is a gas PVT transform: it integrates mu_g and z, the
# two functions above it in this module. Its consumers are all in
# `tools/deliverability/`.
#
# The one decision worth explaining is the integration base. Ahmed defines psi
# from p = 0 (Eq. 6-39, arrived at by splitting the wellbore-to-p integral at
# Eq. 6-38), and the deliverability chapter this feeds is built on that. The
# TAMU/ERCB lecture in the same corpus prints psi with p_base left open, plus a
# second "new pseudopressure" normalised by [mu z / p] at p_i that has units of
# pressure. Two curves on different bases differ by a constant that looks like
# nothing and is 4% of psi at Example 8-2's test pressures. So the base travels
# on every result in assumptions["convention"], a non-zero base is flagged as
# not comparable, and a supplied psi curve reaching p = 0 with psi != 0 is
# refused outright.
#
# Second decision: there is no closed form. Ahmed's own procedure is "the area
# under the curve ... calculated either numerically or graphically", so this is
# a composite trapezoidal rule over a supplied or generated grid and says so in
# `method`. It approximates the published integral; it is not the integral.
# =====================================================================

# ---------------------------------------------------------------- provenance

#: Ahmed, "Radial Flow of Compressible Gases", Eq. 6-39 and the procedure text.
AHMED_PSEUDOPRESSURE = "00-reference/ahmed-reservoir-engineering-handbook#75"
#: Example 8-2, the tabulated psi-vs-p curve (Figure 8-8) this transform feeds.
AHMED_EXAMPLE_8_2 = "00-reference/ahmed-reservoir-engineering-handbook#115"
#: The competing convention, recorded so the refusal can name it.
TAMU_LECTURE = ("09-gas-deliverability/"
                "tamu-png613-lec07-deliverability-testing-gas-wells")

#: The convention string that must appear on every result. `tool-catalog.md`
#: line 594 resolves the reconcile in Ahmed's favour; this is that decision made
#: machine-readable so a caller cannot mix the two bases silently.
AHMED_CONVENTION = (
    "Ahmed Eq. 6-39: m(p) = psi = integral from p = 0 to p of 2p/(mu_g z) dp, "
    "psi^2/cp. NOT the TAMU/ERCB reference-normalised form "
    f"({TAMU_LECTURE}), which leaves p_base open and whose 'new "
    "pseudopressure' has units of pressure."
)

#: Ahmed's Example 6-7 (Anaconda Gas Field, pp. 356-357) tabulates PVT on a
#: 400 psi grid and integrates it. That is a *precedent*, not a published
#: accuracy limit -- the corpus states no maximum spacing anywhere -- so a
#: coarser grid raises a flag naming its own provenance, never a refusal.
AHMED_EXAMPLE_GRID_PSI = 400.0

_UNIT = "psi^2/cp"
_RULE = "composite trapezoidal rule over the supplied grid"


# ------------------------------------------------------------------ internals

def _integrand(p_psia: float, mu_cp: float, z: float) -> float:
    """f(p) = 2p / (mu_g z), psia/cp.

    f(0) is exactly zero -- Ahmed's Example 6-7 table prints 0 there -- and is
    returned without touching mu or z, which are undefined at zero pressure.
    """
    if p_psia == 0.0:
        return 0.0
    if mu_cp <= 0.0 or z <= 0.0:
        raise ValueError(
            f"mu_g and z must both be positive; got mu={mu_cp}, z={z} "
            f"at p={p_psia} psia")
    return 2.0 * p_psia / (mu_cp * z)


def _check_table(pvt_table) -> Refusal | None:
    """R1 and R2: enough points, strictly ascending in pressure."""
    if pvt_table is None or len(pvt_table) < 2:
        return Refusal(
            reason=("pseudopressure is an area under a curve and needs at least "
                    "two (p, mu_g, z) points; "
                    f"got {0 if not pvt_table else len(pvt_table)}"),
            needed=("a PVT table of at least two (p_psia, mu_g_cp, z) triples",),
            source=AHMED_PSEUDOPRESSURE)
    ps = [row[0] for row in pvt_table]
    for a, b in zip(ps, ps[1:]):
        if b <= a:
            return Refusal(
                reason=("PVT table is not strictly increasing in pressure "
                        f"({a} then {b} psia); it cannot be integrated and will "
                        "not be re-sorted, because the ordering may itself be "
                        "the error"),
                needed=("a PVT table sorted ascending in p_psia, with no "
                        "duplicate pressures",),
                source=AHMED_PSEUDOPRESSURE)
    return None


def _interp(x, x0, x1, y0, y1):
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# ------------------------------------------------------- A. the primary path

def pseudopressure_from_pvt_table(p_psia: float,
                                  pvt_table: list[tuple[float, float, float]],
                                  pvt_source: str,
                                  p_base_psia: float = 0.0,
                                  sour: bool = False,
                                  _extra_flags: tuple[str, ...] = (),
                                  _extra_assumptions: dict | None = None):
    """psi(p) by trapezoidal quadrature of Ahmed Eq. 6-39 over a PVT table.

    pvt_table: [(p_psia, mu_g_cp, z), ...] ascending in p, reaching down to
    `p_base_psia` and up to at least `p_psia`.

    `pvt_source` is required, not decorative: mu and z drive the whole integral
    and their own validity limits (Lee-Gonzalez-Eakin is invalid for sour gas,
    Wichert-Aziz does not cover nitrogen) live with whoever produced them. A
    table with no stated origin is refused for the same reason Archie is refused
    without Rw provenance.
    """
    bad = _check_table(pvt_table)
    if bad is not None:
        return bad

    if not (pvt_source or "").strip():                                    # R6
        return Refusal(
            reason=("mu_g and z have no stated provenance, so their own "
                    "validity limits cannot be checked (Lee-Gonzalez-Eakin is "
                    "not valid for sour gas; Wichert-Aziz does not cover N2)"),
            needed=("pvt_source: where mu_g and z came from -- measured PVT "
                    "report, or the correlation and its stated range",),
            source=AHMED_PSEUDOPRESSURE)

    if p_psia < p_base_psia:                                              # R3
        return Refusal(
            reason=(f"p = {p_psia} psia is below the integration base "
                    f"{p_base_psia} psia; Eq. 6-39 defines psi upward from the "
                    "base and a negative area is not a pseudopressure"),
            needed=("a pressure at or above the integration base",),
            source=AHMED_PSEUDOPRESSURE)

    p_lo, p_hi = pvt_table[0][0], pvt_table[-1][0]
    if p_psia > p_hi:                                                     # R4
        return Refusal(
            reason=(f"p = {p_psia} psia is above the PVT table's top pressure "
                    f"{p_hi} psia; extrapolating mu_g and z past the data is "
                    "inventing PVT, and Ahmed's procedure reads area under a "
                    "curve he has data for"),
            needed=(f"PVT data covering {p_base_psia} to {p_psia} psia",),
            source=AHMED_PSEUDOPRESSURE)
    if p_lo > p_base_psia:                                                # R5
        return Refusal(
            reason=(f"PVT table starts at {p_lo} psia but the integration base "
                    f"is {p_base_psia} psia; the missing low-pressure area is "
                    "not negligible -- 13.2e6 psi^2/cp over 0-400 psi in "
                    "Ahmed's Example 6-7, of the order of a few percent of the "
                    "psi values the deliverability tools work at"),
            needed=(f"PVT data down to p = {p_base_psia} psia, or an explicit "
                    "p_base_psia matching the table",),
            source=AHMED_PSEUDOPRESSURE)

    # Quadrature. Walk the grid from the base to p, adding trapezoids.
    rows = [r for r in pvt_table if p_base_psia <= r[0] <= p_psia]
    if not rows or rows[0][0] > p_base_psia:
        # base falls between grid points: interpolate mu and z onto it
        below = [r for r in pvt_table if r[0] <= p_base_psia][-1]
        above = [r for r in pvt_table if r[0] > p_base_psia][0]
        rows.insert(0, (p_base_psia,
                        _interp(p_base_psia, below[0], above[0], below[1], above[1]),
                        _interp(p_base_psia, below[0], above[0], below[2], above[2])))

    grid = [(r[0], _integrand(r[0], r[1], r[2])) for r in rows]

    interpolated = False
    if grid[-1][0] < p_psia:
        # endpoint between grid points: interpolate the integrand, not psi
        nxt = [r for r in pvt_table if r[0] > p_psia][0]
        f_next = _integrand(nxt[0], nxt[1], nxt[2])
        f_end = _interp(p_psia, grid[-1][0], nxt[0], grid[-1][1], f_next)
        grid.append((p_psia, f_end))
        interpolated = True

    total = 0.0
    max_gap = 0.0
    for (pa, fa), (pb, fb) in zip(grid, grid[1:]):
        total += 0.5 * (fa + fb) * (pb - pa)
        max_gap = max(max_gap, pb - pa)

    flags = [f"{_RULE}: an approximation of the published integral, "
             "Ahmed Eq. 6-39"]
    if max_gap > AHMED_EXAMPLE_GRID_PSI:
        flags.append(
            f"grid coarser than the {AHMED_EXAMPLE_GRID_PSI:.0f} psi spacing "
            f"Ahmed integrates in Example 6-7 (largest interval {max_gap:.0f} "
            "psi). That is a precedent, not a published limit -- the corpus "
            "states no maximum spacing")
    if interpolated:
        flags.append("endpoint interpolated between grid points; the integrand "
                     "2p/(mu z), not psi, was interpolated")
    if p_base_psia != 0.0:
        flags.append(
            f"non-zero integration base ({p_base_psia} psia): NOT comparable "
            "with Ahmed-convention psi and must not be mixed with values from "
            "houpeurt_fit / gas_ipr_curve / aof_compute")
    if sour:
        flags.append("sour gas: confirm mu_g did not come from "
                     "Lee-Gonzalez-Eakin, which its authors state is not valid "
                     "for sour gases (ahmed#20, p. 93)")

    assumptions = {
        "convention": AHMED_CONVENTION,
        "p_base_psia": p_base_psia,
        "integration_rule": _RULE,
        "n_intervals": len(grid) - 1,
        "max_interval_psi": max_gap,
        "pvt_source": pvt_source,
        "sour": sour,
    }
    if _extra_assumptions:
        assumptions.update(_extra_assumptions)

    return Quantity(
        total, _UNIT,
        "real gas pseudopressure, trapezoidal integration of Ahmed Eq. 6-39",
        AHMED_PSEUDOPRESSURE,
        inputs={"p_psia": p_psia,
                "integrand_at_p": grid[-1][1],
                "pvt_points_used": len(grid),
                "pvt_range_psia": (p_lo, p_hi)},
        assumptions=assumptions,
        flags=tuple(flags) + tuple(_extra_flags))


# ----------------------------------------------------- B. the generated path

def pseudopressure(p_psia: float, t_degr: float, gamma_g: float,
                   fluid: str = "natural_gas",
                   y_co2: float = 0.0, y_h2s: float = 0.0, y_n2: float = 0.0,
                   sour: bool | None = None,
                   step_psi: float = AHMED_EXAMPLE_GRID_PSI,
                   p_base_psia: float = 0.0):
    """psi(p) with the PVT grid built from tools/gas.py.

    Chains the real implementations rather than reimplementing them:
    gas_z_factor (Hall-Yarborough, Wichert-Aziz where sour) -> gas_density
    (Eq. 2-17) -> gas_viscosity (Lee-Gonzalez-Eakin), then integrates with
    `pseudopressure_from_pvt_table`.

    Every refusal those functions can return is propagated unchanged: sour gas
    (Lee-Gonzalez-Eakin invalid), T_pr < 1 (Hall-Yarborough not recommended),
    y_N2 > 0 (Wichert-Aziz does not cover nitrogen). This path has no published
    oracle -- Ahmed gives no gravity for the Example 6-7 gas -- so results are
    flagged as correlation-derived.
    """
    if step_psi <= 0:
        raise ValueError("step_psi must be positive")
    if p_psia < p_base_psia:
        return Refusal(
            reason=(f"p = {p_psia} psia is below the integration base "
                    f"{p_base_psia} psia; Eq. 6-39 defines psi upward from the "
                    "base"),
            needed=("a pressure at or above the integration base",),
            source=AHMED_PSEUDOPRESSURE)
    if sour is None:
        sour = y_h2s > 0.0

    # Grid: base to p inclusive, at Ahmed's Example 6-7 spacing by default.
    n = max(1, int(round((p_psia - p_base_psia) / step_psi)))
    grid_p = [p_base_psia + i * (p_psia - p_base_psia) / n for i in range(n + 1)]
    grid_p[-1] = p_psia

    table: list[tuple[float, float, float]] = []
    for p in grid_p:
        if p == 0.0:
            # z and mu are undefined at zero pressure and the integrand is
            # exactly zero there; placeholders never reach the arithmetic.
            table.append((0.0, 1.0, 1.0))
            continue
        z = gas_z_factor(p, t_degr, gamma_g, fluid=fluid,
                         y_co2=y_co2, y_h2s=y_h2s, y_n2=y_n2)
        if isinstance(z, Refusal):
            return z
        rho = gas_density(p, t_degr, z.value, gamma_g)
        mu = gas_viscosity(t_degr, rho.value, gamma_g, sour=sour)
        if isinstance(mu, Refusal):
            return mu
        table.append((p, mu.value, z.value))

    if len(table) < 2:
        return Refusal(
            reason=(f"the grid from {p_base_psia} to {p_psia} psia at "
                    f"{step_psi} psi produced fewer than two points"),
            needed=("a smaller step_psi, or a pressure above the base",),
            source=AHMED_PSEUDOPRESSURE)

    return pseudopressure_from_pvt_table(
        p_psia, table,
        pvt_source=("correlations: Hall-Yarborough z (ahmed#16) with "
                    "Wichert-Aziz (ahmed#13) where sour; Lee-Gonzalez-Eakin "
                    "mu_g (ahmed#20) via real-gas density (ahmed#12 Eq. 2-17)"),
        p_base_psia=p_base_psia, sour=sour,
        _extra_flags=("PVT from correlations, not measured: this path has no "
                      "published oracle in the corpus and inherits the stated "
                      "error of each correlation (Lee-Gonzalez-Eakin sigma "
                      "2.7%, max ~9%)",),
        _extra_assumptions={"T_degR": t_degr, "gamma_g": gamma_g,
                            "fluid": fluid, "y_CO2": y_co2, "y_H2S": y_h2s,
                            "y_N2": y_n2, "grid_step_psi": step_psi})


# ------------------------------------------- C. reading a published psi curve

def pseudopressure_from_psi_curve(p_psia: float,
                                  psi_curve: list[tuple[float, float]],
                                  curve_source: str):
    """psi(p) read off an already-integrated psi-vs-p curve, by interpolation.

    Ahmed's Example 8-2 does exactly this: it never integrates anything, it
    reads psi off Figure 8-8. The job here is to stop a curve on a different
    base from entering the deliverability tools -- a curve that reaches p = 0
    with psi != 0 is on the TAMU/ERCB convention, not Ahmed's, and is refused.
    """
    if psi_curve is None or len(psi_curve) < 2:
        return Refusal(
            reason=("a psi-vs-p curve needs at least two points to interpolate;"
                    f" got {0 if not psi_curve else len(psi_curve)}"),
            needed=("a psi curve of at least two (p_psia, psi_psi2_per_cp) "
                    "points",),
            source=AHMED_EXAMPLE_8_2)
    if not (curve_source or "").strip():
        return Refusal(
            reason=("the psi curve has no stated provenance, so its "
                    "integration base cannot be attributed"),
            needed=("curve_source: the figure, report or tool the curve was "
                    "read from",),
            source=AHMED_EXAMPLE_8_2)

    pts = sorted(psi_curve, key=lambda r: r[0])
    for a, b in zip(pts, pts[1:]):
        if b[0] == a[0]:
            return Refusal(
                reason=f"psi curve has duplicate pressure {a[0]} psia",
                needed=("a curve with distinct pressures",),
                source=AHMED_EXAMPLE_8_2)

    flags = []
    zero = [r for r in pts if r[0] == 0.0]
    if zero:
        if zero[0][1] != 0.0:
            return Refusal(                                               # R7
                reason=(f"curve gives psi = {zero[0][1]:g} psi^2/cp at p = 0, "
                        "so it is not on Ahmed's p = 0 base (Eq. 6-39). Mixing "
                        "it with Ahmed-convention psi shifts every delta-psi "
                        "by a constant"),
                needed=("a psi curve integrated from p = 0, or the offset "
                        "needed to rebase this one",),
                source=AHMED_PSEUDOPRESSURE)
    else:
        flags.append("integration base not verifiable: the supplied curve does "
                     "not reach p = 0, so the Ahmed convention is assumed, not "
                     "confirmed")

    if p_psia < pts[0][0] or p_psia > pts[-1][0]:
        return Refusal(
            reason=(f"p = {p_psia} psia is outside the curve's range "
                    f"{pts[0][0]} to {pts[-1][0]} psia; psi is not "
                    "extrapolated"),
            needed=(f"a psi curve covering {p_psia} psia",),
            source=AHMED_EXAMPLE_8_2)

    exact = [r for r in pts if r[0] == p_psia]
    if exact:
        value = exact[0][1]
    else:
        lo = [r for r in pts if r[0] < p_psia][-1]
        hi = [r for r in pts if r[0] > p_psia][0]
        value = _interp(p_psia, lo[0], hi[0], lo[1], hi[1])
        flags.append(f"linearly interpolated between {lo[0]:g} and {hi[0]:g} "
                     "psia on the supplied curve")

    return Quantity(
        value, _UNIT,
        "real gas pseudopressure read from a tabulated psi-vs-p curve "
        "(Ahmed Example 8-2, Figure 8-8)",
        AHMED_EXAMPLE_8_2,
        inputs={"p_psia": p_psia, "curve_points": len(pts),
                "curve_range_psia": (pts[0][0], pts[-1][0])},
        assumptions={"convention": AHMED_CONVENTION,
                     "p_base_psia": 0.0,
                     "integration_rule": "none: the curve is already "
                                         "integrated; this is interpolation "
                                         "only",
                     "curve_source": curve_source},
        flags=tuple(flags))
