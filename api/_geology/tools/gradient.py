"""Gas column pressure gradient — Cullender-Smith and average-T-and-z.

Both methods integrate the same governing equation (thesis p. 7 / IJMRET Eq. 22);
they differ only in what they are willing to assume about T and z between the
wellhead and the bottom of the column. That choice is worth ~0.2% on a shallow
well and several percent on a deep hot one, so `method` has no default and is
never inferred from the other arguments.

**Read `specs/55-gas_gradient.md` before editing any constant here.** The thesis
prints every one of its equations with at least one defect — `e^s` typeset as
`e^5`, a sign flipped in the Cullender-Smith trapezoid, `I_tf` printed as the
T_pr value from the line above — and each repair in this module is pinned to the
thesis's own worked example (p_wf = 2658 psia) and to IJMRET's independent
statement of the same equations in 1000x units. Changing a constant from memory
here reintroduces a defect the source itself contains.

Units are typed into the argument names because two of them have already caused
errors in this codebase: p in psia (never psig), T in degrees Rankine (never
Fahrenheit). The rate is in **Mscf/d**, which is the thesis's scaling: the
friction constant 6.67e-4 belongs to Mscf/d and IJMRET's 0.6666 belongs to
MMscf/d, and mixing them is a factor of 10^6 that still returns a plausible
pressure.

z is never assumed: every node calls `tools.gas.gas_z_factor` (Hall-Yarborough),
and a refusal from it propagates rather than being replaced by a constant.
"""
from __future__ import annotations

import math

from .gas import gas_density, gas_viscosity, gas_z_factor
from .result import Quantity, Refusal

# --- corpus anchors -------------------------------------------------------
THESIS = "09-gas-deliverability/utp-thesis-cullender-smith-bottomhole-flowing-pressure#2"
THESIS_EXAMPLE = "09-gas-deliverability/utp-thesis-cullender-smith-bottomhole-flowing-pressure#3"
IJMRET = "09-gas-deliverability/ijmret-bottomhole-pressure-gradient-methods-comparison#2"
IJMRET_SHALLOW = "09-gas-deliverability/ijmret-bottomhole-pressure-gradient-methods-comparison#1"
IJMRET_LIMITS = "09-gas-deliverability/ijmret-bottomhole-pressure-gradient-methods-comparison#3"

# --- equation constants ---------------------------------------------------
# Thesis p. 24 (#3): alpha = 0.01875 gamma_g L, verified by its own arithmetic
# (0.01875)(0.65)(6818) = 83.09. IJMRET Eq. 20 states the same constant as
# 37.5/2 with an integrand 1000x larger; do not mix the two scalings.
CS_GRAVITY_COEFF = 0.01875          # per half-string, q in Mscf/d
CS_SIMPSON_MULT = 6.0               # thesis p. 25: p_wf = p_tf + 6*alpha/(I_tf+4I_mp+I_wf)
CS_SIMPSON_MID_WEIGHT = 4.0

# Thesis p. 24 (#3): friction group F = 6.67e-4 f q^2 / d^5, q in Mscf/d, d in
# inches. Verified against the thesis's printed F = 5.95 for the example well.
FRICTION_COEFF = 6.67e-4

# Thesis p. 23 (#2) / IJMRET Eq. 27b: s = 0.0375 gamma_g Z / (T_bar z_bar).
# Printed as e^5 in both documents; recovered from the thesis's own s = 0.31.
AVG_S_COEFF = 0.0375

# Thesis p. 24 (#3): N_Re = 20 gamma_g q / (mu d), verified against its printed
# 2,071,100; f = 4[2.28 - 4 log10(eps/d + 21.25/N_Re^0.9)]^-2 (Moody), verified
# against its printed f = 0.0195.
REYNOLDS_COEFF = 20.0
MOODY_A = 2.28
MOODY_B = 4.0
MOODY_C = 21.25
MOODY_NRE_EXP = 0.9
MOODY_FANNING_TO_MOODY = 4.0

# Thesis p. 24 example datum ("e = 0.0023"), NOT a general recommendation. The
# corpus supplies no roughness table; see spec open question 3.
DEFAULT_ROUGHNESS_IN = 0.0023

# --- validity limits, all quoted in the refusal/flag text below -----------
# IJMRET #3: average-T-z "cannot be relied on very large depths above 10000ft".
AVG_TZ_REFUSE_DEPTH_FT = 10_000.0
# IJMRET #3: "For true vertical depths up to 7500ft, a constant compressibility
# factor and temperature can be assumed over the entire depth for all models".
AVG_TZ_CONSTANT_Z_DEPTH_FT = 7_500.0
# IJMRET #1: the refinement "makes little difference at less than 4,000 or
# 5,000 ft ... but it does make a significant difference in deep, high-pressure,
# high-temperature gas wells".
AVG_TZ_SHALLOW_DEPTH_FT = 4_000.0

# The corpus supplies only the fully-turbulent explicit correlation; the thesis
# checks turbulence before applying it.
LAMINAR_NRE = 2_000.0

# A Rankine argument below this is Fahrenheit. Both have been passed here.
MIN_PLAUSIBLE_DEGR = 200.0

METHODS = ("cullender_smith", "average_t_z")
FLOW_STATES = ("static", "flowing")


def _z_at(p_psia: float, t_degr: float, gamma_g: float, fluid: str,
          y_co2: float, y_h2s: float, y_n2: float):
    """z from Hall-Yarborough. Returns a float or the underlying Refusal."""
    q = gas_z_factor(p_psia, t_degr, gamma_g, fluid=fluid,
                     y_co2=y_co2, y_h2s=y_h2s, y_n2=y_n2)
    if isinstance(q, Refusal):
        return q
    return q.value


def _viscosity_cp(p_psia: float, t_degr: float, gamma_g: float, z: float,
                  sour: bool):
    """Lee-Gonzalez-Eakin, via gas density. Float or Refusal."""
    rho = gas_density(p_psia, t_degr, z, gamma_g)
    mu = gas_viscosity(t_degr, rho.value, gamma_g, sour=sour)
    if isinstance(mu, Refusal):
        return mu
    return mu.value


def _moody_friction(n_re: float, roughness_in: float, d_in: float) -> float:
    """f = 4[2.28 - 4 log10(eps/d + 21.25/N_Re^0.9)]^-2.  Thesis p. 24."""
    inner = MOODY_A - MOODY_B * math.log10(
        roughness_in / d_in + MOODY_C / n_re ** MOODY_NRE_EXP)
    return MOODY_FANNING_TO_MOODY * inner ** -2


def _friction_group(q_mscfd: float, d_in: float, roughness_in: float,
                    p_psia: float, t_degr: float, gamma_g: float, z: float,
                    sour: bool):
    """F = 6.67e-4 f q^2 / d^5, plus the (f, N_Re, mu) it was built from."""
    mu = _viscosity_cp(p_psia, t_degr, gamma_g, z, sour)
    if isinstance(mu, Refusal):
        return mu
    n_re = REYNOLDS_COEFF * gamma_g * q_mscfd / (mu * d_in)
    if n_re < LAMINAR_NRE:
        return Refusal(
            reason=(f"N_Re = {n_re:.0f} is below {LAMINAR_NRE:.0f}: the flow is not "
                    "turbulent, and both source documents supply only the "
                    "fully-turbulent explicit friction-factor correlation"),
            needed=("a laminar friction factor for gas in tubing — not in this corpus",),
            source=THESIS_EXAMPLE)
    f = _moody_friction(n_re, roughness_in, d_in)
    return FRICTION_COEFF * f * q_mscfd ** 2 / d_in ** 5, f, n_re, mu


def _integrand(p_psia: float, t_degr: float, z: float, cos_theta: float,
               friction: float) -> float:
    """I = (p/Tz) / [(p/Tz)^2 cos(theta) + F].  Thesis p. 10, repaired.

    The printed step-3 form of this in the thesis has `Z/L` where `F` belongs
    and prints I_tf as the T_pr value from the line above; both are corrected
    here against the thesis's own step 2d (F = 5.95) and step 4 (I_tf = 0.169).
    """
    x = p_psia / (t_degr * z)
    return x / (x * x * cos_theta + friction)


def _cullender_smith(p_top_psia, length_ft, gamma_g, t_top_degr,
                     t_bottom_degr, cos_theta, friction, fluid, y_co2, y_h2s,
                     y_n2, tol, n_iter):
    """Two-step depth integration, closed with Simpson's rule.

    Upper half   (p_mp - p_tf)(I_mp + I_tf) = alpha
    Lower half   (p_wf - p_mp)(I_wf + I_mp) = alpha
    Simpson      p_wf = p_tf + 6 alpha / (I_tf + 4 I_mp + I_wf)

    The thesis prints the two halves fused into one line with a flipped sign
    (`P_mp + P_tf`) and a wrong index (`I_wf + I_tf`); the form above is
    IJMRET Eqs. 37a/37b and is what the thesis's own worked example executes.
    """
    alpha = CS_GRAVITY_COEFF * gamma_g * length_ft
    t_mid_degr = 0.5 * (t_top_degr + t_bottom_degr)

    def node(p, t):
        z = _z_at(p, t, gamma_g, fluid, y_co2, y_h2s, y_n2)
        if isinstance(z, Refusal):
            return z
        return _integrand(p, t, z, cos_theta, friction), z

    top = node(p_top_psia, t_top_degr)
    if isinstance(top, Refusal):
        return _node_refusal(top, "wellhead")
    i_top, z_top = top

    def half(p_start, i_start, t_node, label):
        i_node = i_start
        p_node = p_start
        for _ in range(n_iter):
            p_new = p_start + alpha / (i_node + i_start)
            got = node(p_new, t_node)
            if isinstance(got, Refusal):
                return _node_refusal(got, label)
            i_new, z_new = got
            converged = abs(p_new - p_node) < tol
            p_node, i_node, z_node = p_new, i_new, z_new
            if converged:
                return p_node, i_node, z_node
        return Refusal(
            reason=(f"Cullender-Smith did not converge at the {label} node in "
                    f"{n_iter} iterations"),
            needed=("a looser tolerance or a different starting pressure",),
            source=THESIS_EXAMPLE)

    mid = half(p_top_psia, i_top, t_mid_degr, "midpoint")
    if isinstance(mid, Refusal):
        return mid
    p_mid, i_mid, z_mid = mid

    bot = half(p_mid, i_mid, t_bottom_degr, "bottom")
    if isinstance(bot, Refusal):
        return bot
    p_bot_trapezoid, i_bot, z_bot = bot

    p_bottom = p_top_psia + CS_SIMPSON_MULT * alpha / (
        i_top + CS_SIMPSON_MID_WEIGHT * i_mid + i_bot)
    detail = {
        "alpha": alpha,
        "I_tf": i_top, "I_mp": i_mid, "I_wf": i_bot,
        "z_tf": z_top, "z_mp": z_mid, "z_wf": z_bot,
        "p_mp_psia": p_mid,
        "p_bottom_trapezoid_psia": p_bot_trapezoid,
        "T_mp_degR": t_mid_degr,
    }
    return p_bottom, detail


def _average_t_z(p_top_psia, depth_ft, gamma_g, t_top_degr,
                 t_bottom_degr, cos_theta, q_mscfd, d_in, roughness_in,
                 fluid, y_co2, y_h2s, y_n2, tol, n_iter):
    """p_wf = sqrt(p_tf^2 e^s + 6.67e-4 f q^2 T_bar^2 z_bar^2 (e^s - 1)/(d^5 cos t))

    with s = 0.0375 gamma_g Z / (T_bar z_bar).  Thesis p. 23, repaired: both it
    and IJMRET Eq. 27a typeset the exponent `s` as the digit `5`.

    Static (q = 0) collapses to p_ws = p_ts exp(s/2), which is IJMRET Eq. 11.
    """
    t_bar = 0.5 * (t_top_degr + t_bottom_degr)
    sour = bool(y_co2 or y_h2s or y_n2)
    p_bottom = p_top_psia
    detail: dict = {}
    for _ in range(n_iter):
        p_bar = 0.5 * (p_top_psia + p_bottom)
        z_bar = _z_at(p_bar, t_bar, gamma_g, fluid, y_co2, y_h2s, y_n2)
        if isinstance(z_bar, Refusal):
            return _node_refusal(z_bar, "column average")
        s = AVG_S_COEFF * gamma_g * depth_ft / (t_bar * z_bar)
        friction_term = 0.0
        f = n_re = mu = None
        if q_mscfd:
            got = _friction_group(q_mscfd, d_in, roughness_in, p_bar, t_bar,
                                  gamma_g, z_bar, sour)
            if isinstance(got, Refusal):
                return got
            f_group, f, n_re, mu = got
            friction_term = (f_group * t_bar ** 2 * z_bar ** 2
                             * (math.exp(s) - 1.0) / cos_theta)
        p_new = math.sqrt(p_top_psia ** 2 * math.exp(s) + friction_term)
        converged = abs(p_new - p_bottom) < tol
        p_bottom = p_new
        detail = {"T_bar_degR": t_bar, "p_bar_psia": p_bar, "z_bar": z_bar,
                  "s": s, "moody_f": f, "N_Re": n_re, "mu_cp": mu}
        if converged:
            return p_bottom, detail
    return Refusal(
        reason=f"average-T-and-z did not converge on z_bar in {n_iter} iterations",
        needed=("a looser tolerance",), source=THESIS)


def _node_refusal(inner: Refusal, where: str) -> Refusal:
    return Refusal(
        reason=f"z could not be computed at the {where}: {inner.reason}",
        needed=inner.needed, source=inner.source)


def gas_gradient(p_top_psia: float, depth_ft: float, gamma_g: float,
                 t_top_degr: float, t_bottom_degr: float, *,
                 method: str, flow_state: str,
                 q_mscfd: float | None = None,
                 tubing_id_in: float | None = None,
                 roughness_in: float = DEFAULT_ROUGHNESS_IN,
                 inclination_deg: float = 0.0,
                 fluid: str = "natural_gas",
                 y_co2: float = 0.0, y_h2s: float = 0.0, y_n2: float = 0.0,
                 tol: float = 1e-9, n_iter: int = 100):
    """Average pressure gradient of a gas column, psi/ft.

    `method` and `flow_state` are required keywords: the first changes the
    answer by several percent on a deep well and the second by the whole
    friction term, and neither may be inferred. `depth_ft` is **true vertical
    depth**; `q_mscfd` is **Mscf/d**, not MMscf/d.

    Returns a Quantity whose value is (p_bottom - p_top)/depth, with the
    bottomhole pressure itself on `inputs["p_bottom_psia"]` — that is the number
    both source documents tabulate.
    """
    # --- programmer errors: impossible arguments --------------------------
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    if flow_state not in FLOW_STATES:
        raise ValueError(f"flow_state must be one of {FLOW_STATES}")
    if p_top_psia <= 0:
        raise ValueError("p_top_psia must be positive (psia, not psig)")
    if depth_ft <= 0:
        raise ValueError("depth_ft must be positive")
    if gamma_g <= 0:
        raise ValueError("gamma_g must be positive")
    for name, t in (("t_top_degr", t_top_degr), ("t_bottom_degr", t_bottom_degr)):
        if t <= 0:
            raise ValueError(f"{name} must be positive")
        if t < MIN_PLAUSIBLE_DEGR:
            raise ValueError(
                f"{name} = {t} is below {MIN_PLAUSIBLE_DEGR} degR — that is "
                "Fahrenheit; add 459.67")
    if not 0.0 <= inclination_deg < 90.0:
        raise ValueError("inclination_deg must be in [0, 90) — degrees from vertical")
    if q_mscfd is not None and q_mscfd < 0:
        raise ValueError("q_mscfd must not be negative")
    if tubing_id_in is not None and tubing_id_in <= 0:
        raise ValueError("tubing_id_in must be positive")
    if roughness_in < 0:
        raise ValueError("roughness_in must not be negative")

    flags: list[str] = []
    flowing = flow_state == "flowing"
    cos_theta = math.cos(math.radians(inclination_deg))
    measured_ft = depth_ft / cos_theta

    # --- refusals: cases the sources state the method is not valid for ----
    if method == "average_t_z" and depth_ft > AVG_TZ_REFUSE_DEPTH_FT:
        return Refusal(
            reason=(f"depth {depth_ft:.0f} ft exceeds {AVG_TZ_REFUSE_DEPTH_FT:.0f} ft: "
                    "the average-T-and-z method 'cannot be relied on very large "
                    "depths above 10000ft with the variation of temperatures and "
                    "pressures with depth' (IJMRET 3.4)"),
            needed=("method='cullender_smith', which makes no assumption about "
                    "how T and z vary with depth",),
            source=IJMRET_LIMITS)

    if method == "cullender_smith" and flowing and inclination_deg > 0:
        return Refusal(
            reason=(f"Cullender-Smith is not supported for a flowing deviated well "
                    f"({inclination_deg:.1f} deg from vertical): it 'accounted for a "
                    "lot of errors due to deviation of the well' (+6.9% and +8.71% on "
                    "IJMRET's two deviated wells, against +0.84%/+1.79% static "
                    "vertical), and IJMRET concludes that without modification the "
                    "average-T-and-z method is preferred over it for inclined wells"),
            needed=("Sukkar-Cornell (IJMRET Eqs. 28-32) — its B-integral table is "
                    "not in this corpus",
                    "or the Oden et al. (1988) Cullender-Smith modification",
                    "or method='average_t_z'"),
            source=IJMRET_LIMITS)

    if flowing:
        if q_mscfd is None or tubing_id_in is None:
            missing = [n for n, v in (("q_mscfd", q_mscfd),
                                      ("tubing_id_in", tubing_id_in)) if v is None]
            return Refusal(
                reason=("a flowing column needs the friction term, which cannot be "
                        f"formed without {' and '.join(missing)}"),
                needed=tuple(missing), source=THESIS_EXAMPLE)
        if q_mscfd == 0:
            return Refusal(
                reason="flow_state='flowing' with q_mscfd = 0 is a static column",
                needed=("flow_state='static'",), source=THESIS)

    # --- flags: answered, with the caveat attached ------------------------
    if method == "average_t_z":
        if depth_ft > AVG_TZ_CONSTANT_Z_DEPTH_FT:
            flags.append(
                f"depth {depth_ft:.0f} ft is past the {AVG_TZ_CONSTANT_Z_DEPTH_FT:.0f} ft "
                "to which IJMRET 3.4 certifies a constant z and T; prefer "
                "method='cullender_smith'")
        elif depth_ft > AVG_TZ_SHALLOW_DEPTH_FT:
            flags.append(
                "the constant-T-and-z simplification 'makes little difference at "
                "less than 4,000 or 5,000 ft ... but it does make a significant "
                "difference in deep, high-pressure, high-temperature gas wells' "
                "(IJMRET I)")
    if not flowing and inclination_deg > 0:
        flags.append(
            f"inclination {inclination_deg:.1f} deg does not enter a static column: "
            "with no friction term the weight of the gas depends only on true "
            "vertical depth (IJMRET Eq. 23, cos(theta) = Z/L)")
    if flowing and inclination_deg > 0:
        flags.append(
            "deviated flowing well: the friction term is divided by cos(theta) per "
            "the thesis's printed form, but neither document gives an error bound "
            "for the average-T-and-z method on an inclined well")
    if flowing:
        flags.append(
            "this gradient includes friction and is NOT a hydrostatic gradient — it "
            "must not be used to identify a fluid type or a contact")
        if roughness_in == DEFAULT_ROUGHNESS_IN:
            flags.append(
                f"roughness defaulted to {DEFAULT_ROUGHNESS_IN} in, which is the "
                "thesis's datum for its own example well and not a recommended "
                "value; the corpus supplies no roughness table")
    if y_co2 or y_h2s or y_n2:
        flags.append(
            "sour/inert components correct z via Wichert-Aziz, but neither source "
            "document validated its method on sour gas (IJMRET IV records the "
            "absence of compositional data as an uncertainty in all its results)")
    if gamma_g > 0.75:
        flags.append("gamma_g > 0.75: see the pseudo-critical flag from tools.gas")

    # --- solve ------------------------------------------------------------
    detail: dict = {}
    if method == "cullender_smith":
        # A static column has no friction term and no dependence on trajectory,
        # so it is integrated on TVD with cos(theta) = 1; a flowing one reaches
        # here only when vertical (see the refusal above).
        friction = 0.0
        f_detail: dict = {}
        if flowing:
            z_top = _z_at(p_top_psia, t_top_degr, gamma_g, fluid, y_co2, y_h2s, y_n2)
            if isinstance(z_top, Refusal):
                return _node_refusal(z_top, "wellhead")
            got = _friction_group(q_mscfd, tubing_id_in, roughness_in, p_top_psia,
                                  t_top_degr, gamma_g, z_top,
                                  bool(y_co2 or y_h2s or y_n2))
            if isinstance(got, Refusal):
                return got
            friction, f, n_re, mu = got
            f_detail = {"friction_group_F": friction, "moody_f": f,
                        "N_Re": n_re, "mu_cp": mu}
        out = _cullender_smith(p_top_psia, depth_ft, gamma_g,
                               t_top_degr, t_bottom_degr, 1.0, friction, fluid,
                               y_co2, y_h2s, y_n2, tol, n_iter)
        if isinstance(out, Refusal):
            return out
        p_bottom, detail = out
        detail.update(f_detail)
        method_name = ("Cullender-Smith two-step depth integration, Simpson close "
                       "(thesis p. 24-25; IJMRET Eqs. 16-21)")
        source = THESIS_EXAMPLE
    else:
        out = _average_t_z(p_top_psia, depth_ft, gamma_g, t_top_degr,
                           t_bottom_degr, cos_theta,
                           q_mscfd if flowing else 0.0, tubing_id_in,
                           roughness_in, fluid, y_co2, y_h2s, y_n2, tol, n_iter)
        if isinstance(out, Refusal):
            return out
        p_bottom, detail = out
        method_name = ("average temperature and deviation factor "
                       + ("(thesis p. 23; IJMRET Eq. 27a)" if flowing
                          else "(static form, IJMRET Eq. 11)"))
        source = THESIS if flowing else IJMRET

    gradient = (p_bottom - p_top_psia) / depth_ft
    inputs = {"p_top_psia": p_top_psia, "p_bottom_psia": p_bottom,
              "depth_ft": depth_ft, "measured_length_ft": measured_ft,
              "gamma_g": gamma_g, "t_top_degr": t_top_degr,
              "t_bottom_degr": t_bottom_degr, "cos_theta": cos_theta}
    inputs.update({k: v for k, v in detail.items() if v is not None})
    if flowing:
        inputs["q_mscfd"] = q_mscfd
        inputs["tubing_id_in"] = tubing_id_in
    return Quantity(
        gradient, "psi/ft", method_name, source, inputs=inputs,
        assumptions={
            "method": method,
            "flow_state": flow_state,
            "z_method": "Hall-Yarborough via tools.gas.gas_z_factor",
            "viscosity_method": ("Lee-Gonzalez-Eakin via tools.gas.gas_viscosity"
                                 if flowing else None),
            "temperature_profile": "linear between t_top_degr and t_bottom_degr",
            "q_units": "Mscf/d",
            "roughness_in": roughness_in if flowing else None,
            "depth_basis": "true vertical depth",
            "gradient_basis": "average over the column, (p_bottom - p_top)/depth_ft",
        },
        flags=tuple(flags))
