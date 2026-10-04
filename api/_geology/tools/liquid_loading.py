"""Liquid loading: Turner, Coleman, and the actual tubing velocity.

Specs: `specs/52-turner_critical_rate.md`, `specs/53-coleman_critical_rate.md`,
`specs/54-tubing_velocity.md`.

Three things in here are easy to get backwards and all three have a published
number that settles them, so they are pinned rather than remembered.

**The 20% belongs to Turner, and it is a multiplication.** 1.593 is the
theoretical terminal velocity (McInerney Eq A-11, derived from the droplet force
balance with C_D = 0.44 and Weber number 30). Turner multiplied it by 1.2 to fit
his field data, giving 1.912; Coleman et al. concluded that adjustment came from
a misreading of the data and dropped it. Hapsari's prose says Coleman "reduce[d]
20%" from Turner, which read literally is x0.8 = 1.5296 and is *not* 1.593 - so
the printed coefficients are held as independent constants here and neither is
ever derived from the other.

**Because 1.2 x 1.593 = 1.912, a 1.2 margin applied on top of a Turner critical
velocity counts the adjustment twice.** PetroWiki states its criterion against
the *terminal* velocity ("higher than 1.2 times the terminal velocity"), which is
the Coleman form. `is_loading` therefore compares directly, margin 1.0: the
margin was already chosen when the caller chose which correlation to use.

**The rate conversion constant is unit-bound.** q = 3.06 p v A / (Tz) is MMscf/d
at 60 degF and 14.7 psia - 86400 x 520 / 14.7 = 3.056e6 scf/d. McInerney prints
the same equation as A-17 with (T - 460) in the denominator, which is a
transcription error: T in that appendix is already Rankine. Use Hapsari Eq 3.

Reporting one correlation alone hides that the two disagree by the whole 20%,
which is the method's real uncertainty, so `turner_coleman_spread` returns both
and the band.
"""
from __future__ import annotations

from .result import Quantity, Range, Refusal

HAPSARI = "05-liquid-loading/hapsari-dynamic-simulation-liquid-loading-horizontal#1"
MCINERNEY = "05-liquid-loading/mcinerney-lea-cox-uncertainty-critical-velocity#1"
# The same paper's introduction and conclusions, which carry the prose limits the
# appendix does not: the 20% upward adjustment, and the pressure range Coleman's
# data cover. Cited separately because #1 is Appendix A and states neither.
MCINERNEY_INTRO = "05-liquid-loading/mcinerney-lea-cox-uncertainty-critical-velocity#0"
SHALETEC = "05-liquid-loading/shaletec-introduction-to-plunger-lift#1"
PETROWIKI = "05-liquid-loading/petrowiki-liquid-loading#2"

# Velocity coefficients, ft/s with sigma in dyne/cm and densities in lbm/ft3.
TURNER_C = 1.912   # Hapsari Eq 1; = 1.593 x 1.2, printed rounded
COLEMAN_C = 1.593  # Hapsari Eq 2; McInerney Eq A-11, derived, no fitting factor

# Turner's fit adjustment. Held beside the coefficients, never applied to them:
# 1.593 x 1.20 = 1.9116 while the source prints 1.912, so multiplying would give
# a third, unpublished number. PetroWiki#2 for the 20%.
TURNER_ADJUSTMENT = 1.20

# Hapsari Eq 3. q [MMscf/d] = 3.06 p v A / (T z), p psia, v ft/s, A ft2, T degR.
RATE_CONSTANT = 3.06
STD_T_DEGR = 520.0   # 60 degF   } the base conditions 3.06 encodes:
STD_P_PSIA = 14.7    # psia      } 86400 x 520 / 14.7 = 3.0563e6 scf/d

# Assumptions of the droplet model, not tunable parameters (catalog #52).
DRAG_COEFFICIENT = 0.44  # McInerney Eq A-10, fully turbulent
WEBER_NUMBER = 30        # McInerney Eq A-6, Hinze (1955)

# Wellhead pressure at which the corpus changes its mind about which correlation
# applies. The number is stated in the corpus, not inferred from the catalog:
# McInerney #0 has Coleman fitting "well data from wells with lower wellhead
# pressures, typically well less than 1000 psi" and again "a few hundred psi
# (mostly all below 1000 psi)", and shaletec #1 heads its two forms "Critical
# Flow Rate (Coleman, P Less Than 1,000 psi)" and "Turner (P Greater Than 1,000
# psi)". Hapsari #1 corroborates the direction ("wells where the pressure in the
# well was already low", 66 North Sea data sets) but publishes no number.
# A regime boundary for flagging only - nothing here refuses on it, because both
# sources describe the extent of a data set, not a validity cliff.
PRESSURE_REGIME_PSIA = 1000.0

# Veeken, quoted by Hapsari #1: for deviated wells and large tubing the
# correlation "could be different from actual/field results where the difference
# in results could reach the range of 20-200%". The corpus supplies no angle or
# diameter cutoff, so these are flags with no threshold attached.
VEEKEN_ERROR_RANGE = "20-200%"

# McInerney's short forms. Each bakes in a gas-density-versus-pressure relation
# and a fluid, and the printed coefficient does not tell you which: the water and
# air/fresh-water forms share 5.321 but not their rho_G(P). Never a default path.
SHORT_FORMS: dict[str, dict] = {
    # McInerney Eq A-13 (Coleman) / A-15 (Turner), rho_G = .0031 P from Eq A-12.
    "water": {
        "turner_c": 5.321, "coleman_c": 4.434,
        "rho_l_lbm_ft3": 67.0, "sigma_dyne_cm": 60.0,
        "rho_g_per_psi": 0.0031,
        "gamma_g": 0.6, "z": 0.9, "t_degf": 120.0,
        "equations": "McInerney Eq A-13 (Coleman) / A-15 (Turner), rho_G per A-12",
    },
    # McInerney Eq A-14 (Coleman) / A-16 (Turner), same A-12 gas density.
    "condensate": {
        "turner_c": 4.043, "coleman_c": 3.369,
        "rho_l_lbm_ft3": 45.0, "sigma_dyne_cm": 20.0,
        "rho_g_per_psi": 0.0031,
        "gamma_g": 0.6, "z": 0.9, "t_degf": 120.0,
        "equations": "McInerney Eq A-14 (Coleman) / A-16 (Turner), rho_G per A-12",
    },
    # McInerney Eq C-1, the Texas Tech air/fresh-water facility. Same numerals as
    # "water" because sigma is still 60 dyne/cm, but rho_L and rho_G(P) differ.
    "air_fresh_water": {
        "turner_c": 5.321, "coleman_c": 4.434,
        "rho_l_lbm_ft3": 62.4, "sigma_dyne_cm": 60.0,
        "rho_g_per_psi": 0.0049,
        "gamma_g": 1.0, "z": 1.0, "t_degf": 90.0,
        "equations": "McInerney Eq C-1 (Turner form); Coleman form by /1.2",
    },
}

_COEFFICIENTS = {"turner": TURNER_C, "coleman": COLEMAN_C}


# --------------------------------------------------------------------------- #
# shared internals
# --------------------------------------------------------------------------- #

def _coefficient(method: str) -> float:
    try:
        return _COEFFICIENTS[method]
    except KeyError:
        raise ValueError(f"method must be 'turner' or 'coleman', got {method!r}") from None


def _velocity(c: float, sigma: float, rho_l: float, rho_g: float) -> float:
    """v = C sigma^0.25 (rho_L - rho_g)^0.25 / rho_g^0.5.  Hapsari Eq 1 / Eq 2."""
    if sigma <= 0:
        raise ValueError("surface tension must be positive")
    if rho_g <= 0:
        raise ValueError("gas density must be positive")
    if rho_l <= 0:
        raise ValueError("liquid density must be positive")
    return c * (sigma ** 0.25 * (rho_l - rho_g) ** 0.25) / (rho_g ** 0.5)


def _density_inversion(rho_l: float, rho_g: float) -> Refusal | None:
    """The droplet model needs a droplet denser than the gas carrying it."""
    if rho_l <= rho_g:
        return Refusal(
            reason=(f"liquid density {rho_l} lbm/ft3 is not above gas density "
                    f"{rho_g} lbm/ft3; the droplet-fallback model has no meaning "
                    "when the phases are not density-separated (near the critical "
                    "point, or one density is at the wrong conditions)"),
            needed=("in-situ liquid and gas densities at the same point, "
                    "with rho_L > rho_g",),
            source=HAPSARI,
        )
    return None


# The catalog lists sigma, rho_L, gamma_g (through rho_g), z, T, p AND the tubing
# flow area as required inputs, and tool-verification.md's finding about this tool
# is that the omitted input is the one that has to make it refuse. sigma and rho_L
# are properties of the LOADING LIQUID and the corpus supplies no correlation for
# either, only two typicals: water 60 dyne/cm / 67 lbm/ft3 against condensate
# 20 / 45. Defaulting to the wrong one moves the answer by tens of percent
# silently, so an absent value is refused by name rather than defaulted - and
# rather than surfacing as an anonymous TypeError from inside the arithmetic.
_REQUIRED_INPUTS = {
    "sigma_dyne_cm": "gas-liquid surface tension at the evaluation point, dyne/cm "
                     "(water ~60, condensate ~20; no in-corpus correlation, no default)",
    "rho_l_lbm_ft3": "density of the liquid that is loading, lbm/ft3 "
                     "(water ~67, condensate ~45)",
    "rho_g_lbm_ft3": "in-situ gas density at the evaluation point, lbm/ft3 "
                     "(gas.gas_density(p, T, z, gamma_g))",
    "p_psia": "pressure at the evaluation point, psia",
    "area_ft2": "tubing flow area, ft2 (pi/4 x ID^2; not annulus, not casing) - "
                "the velocity equation gives a velocity and nothing in it knows "
                "the tubing",
    "t_degr": "temperature at the evaluation point, degR",
    "z": "gas deviation factor at p and T (gas.gas_z_factor(p, T, gamma_g))",
}


def _missing_required(**values: object) -> Refusal | None:
    missing = [name for name, value in values.items() if value is None]
    if not missing:
        return None
    return Refusal(
        reason=("cannot compute a critical rate without " + ", ".join(missing)
                + ": every one is a required input of the Turner/Coleman "
                  "correlation and none has a defensible default"),
        needed=tuple(f"{name}: {_REQUIRED_INPUTS[name]}" for name in missing),
        source=HAPSARI,
    )


def _check_rate_arguments(p_psia: float, area_ft2: float, t_degr: float, z: float) -> None:
    if p_psia <= 0:
        raise ValueError("pressure must be positive (psia, not psig)")
    if area_ft2 <= 0:
        raise ValueError("tubing flow area must be positive")
    if t_degr <= 0:
        raise ValueError("temperature must be positive (degR, not degF)")
    if z <= 0:
        raise ValueError("z factor must be positive")


def _regime_flags(method: str, wellhead_pressure_psia: float | None,
                  deviation_deg: float | None, tubing_id_in: float | None) -> list[str]:
    """Validity warnings the sources state. None of them is a refusal: the corpus
    gives no threshold at which the correlation stops being the best available
    number, and inventing one would be worse than reporting it with the caveat."""
    flags: list[str] = []

    if wellhead_pressure_psia is not None:
        if method == "turner" and wellhead_pressure_psia < PRESSURE_REGIME_PSIA:
            flags.append(
                f"Turner was fitted to high-wellhead-pressure wells; below "
                f"~{PRESSURE_REGIME_PSIA:.0f} psi it over-predicts. McInerney #0 "
                "('the Turner method over-predicted the required critical rate by "
                "about 20%'; Coleman's set is 'typically well less than 1000 psi') "
                f"and {SHALETEC} ('Turner (P Greater Than 1,000 psi)'). "
                "The corpus disputes even the direction: McInerney App. B's Shell "
                "correlation gives a required rate ABOVE Turner at low FTHP, "
                "'an opposite effect compared to what Coleman et al. found', while "
                "App. C's measured low-pressure data track Coleman. Report the "
                "Turner-Coleman spread here, not one number.")
        if method == "coleman" and wellhead_pressure_psia > PRESSURE_REGIME_PSIA:
            flags.append(
                f"Coleman's data are 66 North Sea wells at low wellhead pressure "
                f"(Hapsari #1), 'typically well less than {PRESSURE_REGIME_PSIA:.0f} "
                f"psi' ({MCINERNEY_INTRO}; shaletec #1 heads the same form "
                "'Coleman, P Less Than 1,000 psi'); at "
                f"{wellhead_pressure_psia:.0f} psi this extrapolates outside that "
                "set, into the range Turner's own data cover")
        if method == "coleman" and wellhead_pressure_psia < PRESSURE_REGIME_PSIA:
            flags.append(
                "low-pressure regime: the corpus disagrees about it. McInerney "
                "App. C's measurements track Coleman; App. B's Shell correlation "
                "puts the required rate above Turner. Report the spread.")

    if deviation_deg is not None and deviation_deg > 0:
        flags.append(
            f"hole deviation {deviation_deg:.1f} deg from vertical: the "
            "coefficient is a vertical-well one (McInerney drops the cos(phi) of "
            f"Eq A-5 at Eq A-10). Veeken, via Hapsari #1: for deviated wells the "
            f"correlation can differ from field results by {VEEKEN_ERROR_RANGE}. "
            "The corpus gives no cutoff angle, so this is a caveat, not a limit.")

    if tubing_id_in is not None:
        flags.append(
            f"tubing ID {tubing_id_in} in: Turner is 'accurate for wells with "
            "small diameter tubing and for vertical wells' (Hapsari #1); Veeken "
            f"reports {VEEKEN_ERROR_RANGE} differences for large tubing. The "
            "corpus gives no diameter cutoff.")

    return flags


def _critical_rate(method: str, sigma_dyne_cm: float, rho_l_lbm_ft3: float,
                   rho_g_lbm_ft3: float, p_psia: float, area_ft2: float,
                   t_degr: float, z: float, *,
                   wellhead_pressure_psia: float | None = None,
                   deviation_deg: float | None = None,
                   tubing_id_in: float | None = None,
                   horizontal: bool = False) -> Quantity | Refusal:
    c = _coefficient(method)
    refusal = _missing_required(
        sigma_dyne_cm=sigma_dyne_cm, rho_l_lbm_ft3=rho_l_lbm_ft3,
        rho_g_lbm_ft3=rho_g_lbm_ft3, p_psia=p_psia, area_ft2=area_ft2,
        t_degr=t_degr, z=z)
    if refusal is not None:
        return refusal
    refusal = _density_inversion(rho_l_lbm_ft3, rho_g_lbm_ft3)
    if refusal is not None:
        return refusal
    _check_rate_arguments(p_psia, area_ft2, t_degr, z)

    v = _velocity(c, sigma_dyne_cm, rho_l_lbm_ft3, rho_g_lbm_ft3)
    q = RATE_CONSTANT * p_psia * v * area_ft2 / (t_degr * z)

    flags = _regime_flags(method, wellhead_pressure_psia, deviation_deg, tubing_id_in)
    if horizontal:
        flags.append(
            "horizontal well: steady-state correlations 'cannot capture changes "
            "in the flow regime' (Hapsari #1). For its well X-1 both Turner (4.1) "
            "and Coleman (3.4 MMscfd) fell below the dynamic OLGA answer (5.0) "
            "and the actual rate (6.0).")

    label = "Turner" if method == "turner" else "Coleman"
    return Quantity(
        q, "MMscf/d",
        f"{label} critical gas rate: v = {c} sigma^0.25 (rho_L-rho_g)^0.25 / "
        f"rho_g^0.5 (Hapsari Eq {1 if method == 'turner' else 2}), "
        f"q = {RATE_CONSTANT} p v A / (T z) (Hapsari Eq 3)",
        HAPSARI if method == "coleman" else f"{MCINERNEY}; {HAPSARI}",
        inputs={"sigma_dyne_cm": sigma_dyne_cm, "rho_L_lbm_ft3": rho_l_lbm_ft3,
                "rho_g_lbm_ft3": rho_g_lbm_ft3, "p_psia": p_psia,
                "area_ft2": area_ft2, "T_degR": t_degr, "z": z,
                "v_t_ft_s": v},
        assumptions={
            "C": c,
            "turner_adjustment_applied": method == "turner",
            "turner_adjustment": TURNER_ADJUSTMENT,
            "C_D": DRAG_COEFFICIENT, "Weber": WEBER_NUMBER,
            "rate_constant": RATE_CONSTANT,
            "standard_conditions": f"{STD_T_DEGR:.0f} degR (60 degF) and "
                                   f"{STD_P_PSIA} psia; 3.06 encodes them",
            "evaluation_point": "as supplied by the caller; Turner and Coleman "
                                "are wellhead correlations",
        },
        flags=tuple(flags),
    )


# --------------------------------------------------------------------------- #
# #52 / #53 - the named catalog tools
# --------------------------------------------------------------------------- #

def turner_critical_rate(sigma_dyne_cm: float, rho_l_lbm_ft3: float,
                         rho_g_lbm_ft3: float, p_psia: float, area_ft2: float,
                         t_degr: float, z: float, *,
                         wellhead_pressure_psia: float | None = None,
                         deviation_deg: float | None = None,
                         tubing_id_in: float | None = None,
                         horizontal: bool = False) -> Quantity | Refusal:
    """#52. Minimum gas rate to keep liquids lifted, Turner (C = 1.912, the 20%
    adjustment included). MMscf/d at 60 degF and 14.7 psia.

    Takes the physical inputs, not a short form: the commonly quoted
    water/condensate forms bake rho_L, sigma and a rho_G(P) relation into a
    constant at gamma_g = 0.6, z = 0.9, T = 120 degF and are wrong off those
    conditions. `short_form_critical_velocity` is where those live, declared.

    Converting the velocity to a rate needs the tubing flow area `area_ft2`
    (pi/4 x ID^2) - nothing in the velocity equation knows about the tubing.

    Report this beside `coleman_critical_rate`; `turner_coleman_spread` returns
    the pair and the band, which is what the catalog asks an operator to see.
    """
    return _critical_rate("turner", sigma_dyne_cm, rho_l_lbm_ft3, rho_g_lbm_ft3,
                          p_psia, area_ft2, t_degr, z,
                          wellhead_pressure_psia=wellhead_pressure_psia,
                          deviation_deg=deviation_deg, tubing_id_in=tubing_id_in,
                          horizontal=horizontal)


def coleman_critical_rate(sigma_dyne_cm: float, rho_l_lbm_ft3: float,
                          rho_g_lbm_ft3: float, p_psia: float, area_ft2: float,
                          t_degr: float, z: float, *,
                          wellhead_pressure_psia: float | None = None,
                          deviation_deg: float | None = None,
                          tubing_id_in: float | None = None,
                          horizontal: bool = False) -> Quantity | Refusal:
    """#53. The same calculation without Turner's 20% adjustment (C = 1.593).
    MMscf/d at 60 degF and 14.7 psia.

    Always the lower of the two, by exactly 1.912/1.593 = 1.20025. A well flowing
    between the two rates is loaded by Turner and unloaded by Coleman, and the
    corpus does not rank them - report both and the spread.
    """
    return _critical_rate("coleman", sigma_dyne_cm, rho_l_lbm_ft3, rho_g_lbm_ft3,
                          p_psia, area_ft2, t_degr, z,
                          wellhead_pressure_psia=wellhead_pressure_psia,
                          deviation_deg=deviation_deg, tubing_id_in=tubing_id_in,
                          horizontal=horizontal)


# --------------------------------------------------------------------------- #
# the two steps on their own
# --------------------------------------------------------------------------- #

def critical_velocity(sigma: float, rho_l: float, rho_g: float, method: str = "turner",
                      wellhead_pressure: float | None = None,
                      deviation_deg: float | None = None,
                      tubing_id_in: float | None = None) -> Quantity | Refusal:
    """v_t = C sigma^0.25 (rho_L - rho_g)^0.25 / rho_g^0.5.  Hapsari Eq 1 / Eq 2.

    sigma in dyne/cm (NOT lbf/ft - the conversion is the 17.514 -> 1.593 step in
    McInerney Eq A-10/A-11), densities in lbm/ft3, wellhead_pressure in psia,
    result in ft/s.
    """
    c = _coefficient(method)
    refusal = _density_inversion(rho_l, rho_g)
    if refusal is not None:
        return refusal
    v = _velocity(c, sigma, rho_l, rho_g)
    flags = _regime_flags(method, wellhead_pressure, deviation_deg, tubing_id_in)
    return Quantity(v, "ft/s", f"{method} critical velocity (C = {c})",
                    HAPSARI if method == "coleman" else f"{MCINERNEY}; {HAPSARI}",
                    inputs={"sigma_dyne_cm": sigma, "rho_L_lbm_ft3": rho_l,
                            "rho_g_lbm_ft3": rho_g, "C": c},
                    assumptions={"C_D": DRAG_COEFFICIENT, "Weber": WEBER_NUMBER,
                                 "turner_adjustment_applied": method == "turner",
                                 "turner_adjustment": TURNER_ADJUSTMENT},
                    flags=tuple(flags))


def critical_rate(velocity_ft_s: float, p_psia: float, area_ft2: float,
                  t_degr: float, z: float) -> Quantity:
    """q_c = 3.06 p v A / (T z).  Hapsari Eq 3.  MMscf/d at 60 degF, 14.7 psia.

    McInerney's Eq A-17 prints (T - 460) in the denominator, which is wrong when
    T is already Rankine - and it is, Eq A-12 writes (460 + 120) for 120 degF.
    This is the Hapsari form.
    """
    _check_rate_arguments(p_psia, area_ft2, t_degr, z)
    q = RATE_CONSTANT * p_psia * velocity_ft_s * area_ft2 / (t_degr * z)
    return Quantity(q, "MMscf/d", "critical gas rate (Hapsari Eq 3)", HAPSARI,
                    inputs={"v": velocity_ft_s, "p_psia": p_psia, "A_ft2": area_ft2,
                            "T_degR": t_degr, "z": z},
                    assumptions={"rate_constant": RATE_CONSTANT,
                                 "standard_conditions": f"{STD_T_DEGR:.0f} degR "
                                                        f"(60 degF) and {STD_P_PSIA} psia"})


def turner_coleman_spread(sigma: float, rho_l: float, rho_g: float,
                          p_psia: float, area_ft2: float, t_degr: float, z: float,
                          *, wellhead_pressure_psia: float | None = None,
                          deviation_deg: float | None = None,
                          tubing_id_in: float | None = None,
                          horizontal: bool = False) -> Range | Refusal:
    """Both correlations and the band between them, MMscf/d.

    Reporting one alone hides that the two disagree by the whole 20% adjustment,
    which is the method's real uncertainty (McInerney/Lea/Cox is entirely about
    that scatter). The low end is always Coleman.
    """
    turner = turner_critical_rate(sigma, rho_l, rho_g, p_psia, area_ft2, t_degr, z,
                                  wellhead_pressure_psia=wellhead_pressure_psia,
                                  deviation_deg=deviation_deg,
                                  tubing_id_in=tubing_id_in, horizontal=horizontal)
    if isinstance(turner, Refusal):
        return turner
    coleman = coleman_critical_rate(sigma, rho_l, rho_g, p_psia, area_ft2, t_degr, z,
                                    wellhead_pressure_psia=wellhead_pressure_psia,
                                    deviation_deg=deviation_deg,
                                    tubing_id_in=tubing_id_in, horizontal=horizontal)
    if isinstance(coleman, Refusal):
        return coleman
    qt, qc = turner.value, coleman.value
    return Range(low=min(qt, qc), high=max(qt, qc), unit="MMscf/d",
                 method=f"Turner ({TURNER_C}) and Coleman ({COLEMAN_C}) critical "
                        "rates, Hapsari Eq 1-3; the band is the 20% adjustment "
                        "the two sources disagree about",
                 source=HAPSARI,
                 # The two rates and nothing else: `members` is the pair the
                 # catalog asks to be reported. The underlying velocities are on
                 # each tool's own result as inputs["v_t_ft_s"].
                 members={"turner": qt, "coleman": qc})


# --------------------------------------------------------------------------- #
# #54
# --------------------------------------------------------------------------- #

def tubing_velocity(q_mmscf_d: float, p_psia: float, area_ft2: float,
                    t_degr: float, z: float,
                    evaluation_point: str | None = "wellhead") -> Quantity | Refusal:
    """#54. Actual gas velocity in tubing: Hapsari Eq 3 solved for v.

        v = q T z / (3.06 p A)      ft/s, with q in MMscf/d at 60 degF / 14.7 psia

    `q_mmscf_d` is MMscf/d, not Mscf/d - most daily-production feeds report Mscf/d
    and the slip is a factor of 1000 in the velocity.

    Turner and Coleman are WELLHEAD correlations, so p, T and z must all be taken
    at the same point and that point should be the wellhead. Gas expands up the
    string, so a bottomhole evaluation gives a much smaller velocity against a
    critical velocity that was never meant for that depth, and a loaded well reads
    as healthy. If the caller cannot say where the pressure was measured this
    refuses rather than assuming.

    This is the gas SUPERFICIAL velocity - gas rate over the full tubing flow
    area, holdup ignored - which is the basis every correlation in this corpus is
    written on.
    """
    if q_mmscf_d < 0:
        raise ValueError("gas rate cannot be negative")
    _check_rate_arguments(p_psia, area_ft2, t_degr, z)

    if evaluation_point is None or str(evaluation_point).strip().lower() in ("", "unknown"):
        return Refusal(
            reason="the point at which p, T and z were measured is not stated, so "
                   "the velocity cannot be compared with a Turner or Coleman "
                   "critical velocity - those are wellhead correlations and "
                   "gas velocity varies several-fold along the tubing",
            needed=("evaluation_point: where the flowing pressure and temperature "
                    "were measured (Turner's comparison wants the wellhead)",),
            source=HAPSARI,
        )

    v = q_mmscf_d * t_degr * z / (RATE_CONSTANT * p_psia * area_ft2)

    flags: list[str] = []
    if str(evaluation_point).strip().lower() != "wellhead":
        flags.append(
            f"evaluated at '{evaluation_point}', not the wellhead: Turner and "
            "Coleman are wellhead correlations (Coleman's set is indexed by "
            "wellhead pressure, McInerney's Shell fit by FTHP), so comparing this "
            "velocity with a critical velocity answers a different question and "
            "is systematically low downhole")
    if q_mmscf_d == 0:
        flags.append("zero rate: the well is shut in or dead, velocity is 0 ft/s "
                     "and any loading comparison is trivially true")

    return Quantity(v, "ft/s", "tubing gas velocity (Hapsari Eq 3, inverted)", HAPSARI,
                    inputs={"q_MMscf_d": q_mmscf_d, "p_psia": p_psia,
                            "A_ft2": area_ft2, "T_degR": t_degr, "z": z},
                    assumptions={
                        "evaluation_point": evaluation_point,
                        "velocity_basis": "gas superficial velocity over the full "
                                          "tubing flow area; liquid holdup ignored, "
                                          "as in every correlation in this corpus",
                        "rate_constant": RATE_CONSTANT,
                        "standard_conditions": f"{STD_T_DEGR:.0f} degR (60 degF) "
                                               f"and {STD_P_PSIA} psia",
                    },
                    flags=tuple(flags))


def is_loading(v_actual_ft_s: float, v_critical_ft_s: float, margin: float = 1.0,
               basis: str | None = None) -> Quantity:
    """Loading criterion: the well is loading when v_actual < margin x v_critical.

    **margin defaults to 1.0, not 1.2.** PetroWiki #2 states the criterion against
    the TERMINAL velocity - "if the gas superficial velocity is higher than 1.2
    times the terminal velocity, no liquid loading occurs" - and 1.2 x 1.593 =
    1.912, which is the Turner coefficient. Applying 1.2 on top of a Turner
    critical velocity counts the 20% twice (effective C = 2.294, 44% above
    terminal) and reports a healthy well as loaded. The margin was already chosen
    when the caller chose the correlation.

    `basis` ("turner" / "coleman") is optional and only records which correlation
    the critical velocity came from, so a double-counted margin is visible in
    `assumptions` rather than buried.
    """
    if margin <= 0:
        raise ValueError("margin must be positive")
    loading = v_actual_ft_s < margin * v_critical_ft_s

    assumptions: dict = {"margin": margin,
                         "criterion": "loading when v_actual < margin x v_critical"}
    if basis is not None:
        c = _coefficient(basis)
        assumptions["basis"] = basis
        assumptions["effective_coefficient"] = margin * c
        if basis == "turner" and margin != 1.0:
            assumptions["warning"] = (
                f"margin {margin} applied to the Turner velocity, which already "
                f"contains the 20% adjustment: effective C = {margin * c:.4f} "
                f"against a terminal {COLEMAN_C}")

    return Quantity(float(loading), "bool",
                    f"liquid loading check (margin {margin})", PETROWIKI,
                    inputs={"v_actual_ft_s": v_actual_ft_s,
                            "v_critical_ft_s": v_critical_ft_s},
                    assumptions=assumptions)


# --------------------------------------------------------------------------- #
# the short forms, declared
# --------------------------------------------------------------------------- #

def short_form_critical_velocity(p_psia: float, liquid: str = "water",
                                 method: str = "turner", *,
                                 gamma_g: float | None = None,
                                 z: float | None = None,
                                 t_degf: float | None = None) -> Quantity | Refusal:
    """McInerney's one-argument forms, e.g. Eq A-15:

        V_C,water = 5.321 (67 - .0031 P)^0.25 / (.0031 P)^0.5   ft/s

    These are NOT a convenience wrapper on the general form. Each bakes in a
    fluid (rho_L, sigma) AND a gas-density-versus-pressure relation at fixed
    gamma_g, z and temperature. The printed coefficient does not tell you which:
    "water" and "air_fresh_water" share 5.321 but differ in rho_L and rho_G(P).

    Everything baked in is declared in `assumptions`, and stating any condition
    that contradicts one is a refusal pointing at `turner_critical_rate`.

    (McInerney's Eq A-12 prose says "T=20 degF" while its own arithmetic uses
    (460 + 120): 2.715 x 0.6 / (580 x 0.9) = 0.003121, the printed .0031. The
    baked-in temperature is 120 degF.)
    """
    _coefficient(method)  # validates the name
    try:
        form = SHORT_FORMS[liquid]
    except KeyError:
        raise ValueError(f"liquid must be one of {sorted(SHORT_FORMS)}, got {liquid!r}") from None
    if p_psia <= 0:
        raise ValueError("pressure must be positive (psia, not psig)")

    stated = {"gamma_g": gamma_g, "z": z, "t_degf": t_degf}
    conflicts = [f"{k} = {v} (form assumes {form[k]})"
                 for k, v in stated.items() if v is not None and v != form[k]]
    if conflicts:
        return Refusal(
            reason=(f"the {liquid} short form bakes gamma_g = {form['gamma_g']}, "
                    f"z = {form['z']} and T = {form['t_degf']} degF into its "
                    f"gas-density relation rho_g = {form['rho_g_per_psi']} P, and "
                    f"rho_L = {form['rho_l_lbm_ft3']} lbm/ft3 with sigma = "
                    f"{form['sigma_dyne_cm']} dyne/cm into its coefficient. "
                    "It is not valid off those conditions. Conflicts: "
                    + "; ".join(conflicts)),
            needed=("turner_critical_rate / coleman_critical_rate with the actual "
                    "sigma, rho_L, rho_g, p, T and z",),
            source=MCINERNEY,
        )

    rho_g = form["rho_g_per_psi"] * p_psia
    rho_l = form["rho_l_lbm_ft3"]
    refusal = _density_inversion(rho_l, rho_g)
    if refusal is not None:
        return refusal

    c = form["turner_c"] if method == "turner" else form["coleman_c"]
    v = c * (rho_l - rho_g) ** 0.25 / rho_g ** 0.5

    return Quantity(
        v, "ft/s",
        f"{method} critical velocity, {liquid} short form "
        f"({c} (rho_L - {form['rho_g_per_psi']} P)^0.25 / ({form['rho_g_per_psi']} P)^0.5)",
        MCINERNEY,
        inputs={"p_psia": p_psia, "liquid": liquid, "rho_g_lbm_ft3": rho_g},
        assumptions={
            "baked_in": {
                "gamma_g": form["gamma_g"], "z": form["z"],
                "t_degf": form["t_degf"],
                "rho_g_lbm_ft3": f"{form['rho_g_per_psi']} x p_psia",
                "rho_L_lbm_ft3": rho_l,
                "sigma_dyne_cm": form["sigma_dyne_cm"],
            },
            "equations": form["equations"],
            "turner_adjustment_applied": method == "turner",
            "prefer": "turner_critical_rate / coleman_critical_rate off these conditions",
        },
        flags=(f"short form: valid only at gamma_g = {form['gamma_g']}, "
               f"z = {form['z']}, T = {form['t_degf']} degF, "
               f"rho_L = {rho_l} lbm/ft3, sigma = {form['sigma_dyne_cm']} dyne/cm",),
    )
