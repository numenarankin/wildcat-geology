"""Arps decline analysis. Tools #116-#118, catalog section 18.

`tool-verification.md` lists `decline_forecast` as unsourced ("Arps rate-time
equations nowhere") and warns that the corpus's other "Arps" is the
resistivity-temperature correlation. **That row is stale** - section 18 was added
to the catalog after the verification was written, once `16-decline-curves/`
entered the corpus, and all three rate-time forms are printed at
`petroleumoffice-arps-decline-curve-analysis#0` pp. 4-5. The homonym warning is
still live and still correct: `resistivity_at_temperature` is Arps's *other*
equation and shares no anchor with anything here.

**Three forms, three code paths, on purpose.** The catalog requires it for
`decline_eur` ("the three Arps cases are three different integrals and must not
share one code path") and the same holds for the rates and the times. The reason
is not tidiness: the hyperbolic EUR carries `(1-b)` in a denominator, so it
degrades as b approaches 1 long before it equals it, and a hard `b == 1.0` test
never fires on a fitted b. The switch is on
`x = (1-b)*ln(q_i/q_econ)`, which is what actually governs the cancellation.

**The gate is the tool.** Arps holds only in boundary-dominated flow, and b > 1
means the well is still transient - which is exactly the well someone most wants
a forecast for. `decline_forecast` refuses there rather than returning a tidy
number, and the b search deliberately runs past 1 to 2.5 so that a transient well
is *diagnosed* rather than silently clamped into a harmonic fit. Boundary-dominated
flow cannot be read off a rate series, so it must be declared and has no default.

One thing the source does not settle: it prescribes no regression and prints no
worked example. The fits here are linearised per-form OLS, which is the published
graphical workflow made numeric; on noisy data it is not a joint nonlinear least
squares and each form weights its own tail differently. That choice is recorded in
`assumptions["fit_objective"]` on every fit rather than left implicit.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .result import Quantity, Range, Refusal



# ======================================================================
# Tool #116 - decline_forecast
# ======================================================================


# --- anchors ---------------------------------------------------------------

ARPS = "16-decline-curves/petroleumoffice-arps-decline-curve-analysis#0"
ARPS_RATE_TIME = ARPS + " p. 4 (exponential), p. 5 (hyperbolic, harmonic)"
ARPS_GATE = ARPS + " pp. 3-4, 7-8 (boundary-dominated flow; b > 1 transient)"
ARPS_UNITS = ARPS + " p. 7 ([D_i] x [t] = dimensionless)"
PHDWIN = "16-decline-curves/phdwin-arps-equations-rate-time"
PHDWIN_B_RANGE = PHDWIN + " p. 2 (b seldom above 2.0 or 2.5)"
PHDWIN_EFFECTIVE = PHDWIN + " pp. 3, 7 (effective decline, tangent at q_i)"
PHDWIN_NOMINAL_TIME_BASE = PHDWIN + " p. 1 (nominal decline per year / 12 = per month)"
RFOUR = "16-decline-curves/rfour-arps-dca-practical-guide"
RFOUR_WORKFLOW = RFOUR + ' ("Recommended workflow", steps 1-5)'

# The source's own words, kept whole so a refusal hands the operator the
# sentence rather than a paraphrase of it.
BDF_ONLY = (
    '"Arps equations are only valid during boundary-dominated flow. Values of '
    'b > 1 indicate transient flow conditions where alternative models (PLE, '
    'SEPD, Duong) should be used." (petroleumoffice p. 4)'
)
OVERESTIMATES = (
    '"When b > 1, the well is still in transient flow and Arps equations will '
    'overestimate reserves" (petroleumoffice p. 8, Limitations 1)'
)

# --- forms -----------------------------------------------------------------

FORM_EXPONENTIAL = "exponential"
FORM_HYPERBOLIC = "hyperbolic"
FORM_HARMONIC = "harmonic"

B_EXPONENTIAL = 0.0
B_HARMONIC = 1.0
B_TRANSIENT_ABOVE = 1.0  # petroleumoffice p. 4 and p. 8: b > 1 is transient flow

FIT_METHODS = {
    # form: (the linearization solved, the source that asks for it)
    FORM_EXPONENTIAL: (
        "OLS of ln q on t (ln q = ln q_i - D_i t), the semilog straight line",
        RFOUR_WORKFLOW,
    ),
    FORM_HARMONIC: (
        "OLS of 1/q on t (1/q = 1/q_i + (D_i/q_i) t)",
        ARPS_RATE_TIME,
    ),
    FORM_HYPERBOLIC: (
        "OLS of q^-b on t at fixed b (q^-b = q_i^-b (1 + b D_i t)), b chosen by "
        "grid + ternary search minimising the sum of squared ln q residuals",
        ARPS_RATE_TIME,
    ),
}

# --- thresholds ------------------------------------------------------------
# Each carries its status: SOURCED (the corpus states it), CONVENTION (calendar
# arithmetic the corpus does not state), OURS (chosen here, in the open).

#: phdwin p. 2: "Reservoirs with duel porosity, multi-porosity, fracture
#: stimulated or poor reservoir drive energy (i.e. only gravity drainage) will
#: demonstrate larger b factors but seldom go above 2.0 or 2.5."  The ceiling of
#: the b search - above it the fit is outside any published range (R10).
B_SEARCH_MAX = 2.5                    # SOURCED, PHDWIN_B_RANGE
B_SEARCH_GRID_STEP = 0.02             # OURS - resolution of the coarse pass
B_SEARCH_REFINE_ITERATIONS = 100      # OURS - ternary, to float resolution
HYPERBOLIC_B_FLOOR = 1e-9             # OURS - below it q^-b loses all precision

#: Fitted b within this of 0 or 1 is snapped to it exactly and refitted in that
#: form.  Ours, and it exists for a numerical reason: #117's hyperbolic EUR
#: divides by b and by (1 - b), so a fitted b = 3e-9 is a cancellation bomb where
#: b = 0 is exact.
B_FORM_SNAP = 1e-6                    # OURS

#: rfour, workflow step 4: "Check the residual. If R2 < 0.85, the fit is
#: unreliable - try a different window or form."  A flag here, not a refusal:
#: the guidance is to change the window, which is the caller's move.
R2_UNRELIABLE_BELOW = 0.85            # SOURCED, RFOUR_WORKFLOW

#: rfour: "Anything less than 12 months of stable decline is noise-fitting", and
#: "You have enough data to fit b reliably (>= 12-18 months of stable decline)".
MIN_STABLE_WINDOW_MONTHS = 12.0       # SOURCED, RFOUR
MIN_MONTHS_TO_FIT_B = 12.0            # SOURCED, RFOUR

#: Points a form needs before its line is determined at all.
MIN_POINTS_FIXED_B = 2                # two parameters, q_i and D_i
MIN_POINTS_FITTED_B = 3               # three, b as well

TIME_UNITS = ("day", "month", "year")

#: How many of each unit make a year.  months/year = 12 is what phdwin p. 1
#: converts a nominal decline by; days/year = 365.25 is the Gregorian mean year
#: and is a CONVENTION - no corpus document states a days-per-year figure, so any
#: result that goes through it says so.
TIME_UNIT_PER_YEAR = {
    "day": (365.25, "CONVENTION", "Gregorian mean year; not stated in the corpus"),
    "month": (12.0, "SOURCED", PHDWIN_NOMINAL_TIME_BASE),
    "year": (1.0, "SOURCED", ARPS_UNITS),
}

METHOD = (
    "Arps decline fit: rate-time forms of petroleumoffice pp. 4-5 inverted by "
    "per-form linearised least squares, gated on boundary-dominated flow and b <= 1"
)


# --- the forward forms, written once ---------------------------------------


def _arps_rate(qi: float, di: float, b: float, t: float) -> float:
    """q(t) for the three published forms.  Ungated - callers gate.

    Exponential  q(t) = q_i e^(-D_i t)                petroleumoffice p. 4
    Hyperbolic   q(t) = q_i / (1 + b D_i t)^(1/b)     petroleumoffice p. 5
    Harmonic     q(t) = q_i / (1 + D_i t)             petroleumoffice p. 5

    Three branches because they are three equations, not one with a parameter:
    the hyperbolic expression is 0/0 at b = 0 and the harmonic is its b -> 1
    limit.  This is used both by `decline_rate` (which gates first) and by the
    fitter's scoring pass, so the fit is always scored against the published
    forward form rather than against the linearisation it was solved in.
    """
    if b == 0:
        return qi * math.exp(-di * t)
    if b == 1:
        return qi / (1 + di * t)
    return qi / (1 + b * di * t) ** (1 / b)


def arps_form(b: float) -> str:
    """Which of the source's three headings a b value falls under (p. 3)."""
    if b == 0:
        return FORM_EXPONENTIAL
    if b == 1:
        return FORM_HARMONIC
    return FORM_HYPERBOLIC


# --- the gate --------------------------------------------------------------


def arps_flow_regime_gate(
    b: float | None,
    boundary_dominated: bool | None,
    *,
    fitted_b: bool = False,
    fitted_params: str = "",
):
    """The two conditions the source puts on every Arps calculation.

    Returns a `Refusal` or `None`.  Shared by `decline_forecast`, `decline_rate`,
    `decline_eur` and `economic_limit_time` so the gate cannot drift between
    them - the same shape as Chierici's chart bounds, per `tool-catalog.md` s18.

    `boundary_dominated is None` is a *distinct* refusal from `False`: one is an
    undeclared assumption, the other a declared failure, and the operator needs
    to be told which.
    """
    if boundary_dominated is None:
        return Refusal(
            reason=(
                "boundary-dominated flow has not been declared. Arps holds only "
                "there - " + BDF_ONLY + " - and boundary-dominated flow cannot be "
                "read off a rate series: a declining series is equally consistent "
                "with transient flow, which is the regime in which the same "
                "equations " + OVERESTIMATES + ". So this is declared by the "
                "caller, never defaulted and never inferred here. A fit that "
                "silently assumes it returns a number with no validity attached."
            ),
            needed=(
                "boundary_dominated_flow=True, on evidence outside the rate "
                "series: a flow-regime diagnostic (pressure-transient analysis, "
                "a rate-transient/Fetkovich type-curve match), or a drainage "
                "boundary argument for the well",
                "failing that, a transient model - petroleumoffice p. 4 names "
                "PLE, SEPD and Duong, none of which the corpus states an "
                "equation for",
            ),
            source=ARPS_GATE,
        )
    if not boundary_dominated:
        return Refusal(
            reason=(
                "the caller has declared that boundary-dominated flow has not "
                "been established, which is condition 1 of the source's four "
                'valid conditions ("Boundary-dominated flow has been '
                'established", petroleumoffice p. 7). ' + BDF_ONLY
            ),
            needed=("production from a well that has reached boundary-dominated flow",
                    "or a transient model (PLE, SEPD, Duong) - no corpus document "
                    "states one"),
            source=ARPS_GATE,
        )
    if b is None:
        return None
    if b < 0:
        return Refusal(
            reason=(
                f"b = {b:g} is negative. No source in the corpus gives a form for "
                "it: petroleumoffice p. 8 prints the typical range as 0 - 1.0 and "
                "phdwin p. 2 extends it upward only. A negative b is an "
                "accelerating decline, and no adjacent equation is substituted for "
                "one the corpus does not state."
            ),
            needed=("b in [0, 1]", "or a source stating an Arps form for b < 0"),
            source=ARPS_GATE,
        )
    if b > B_TRANSIENT_ABOVE:
        how = "fitted from the production history" if fitted_b else "supplied"
        diagnosis = f" ({fitted_params})" if fitted_params else ""
        return Refusal(
            reason=(
                f"b = {b:g} > 1, {how}. Arps does not apply: b > 1 is the "
                f"signature of transient flow, not boundary-dominated flow. "
                + BDF_ONLY + " and " + OVERESTIMATES + ". This is exactly the well "
                "someone wants a forecast for, and that is the problem - a "
                "still-transient well reads as the most attractive one on the "
                "board precisely because the fit that flatters it is invalid. The "
                "fitted parameters are reported here as a diagnosis" + diagnosis
                + " and must not be forecast from."
            ),
            needed=(
                "production far enough into boundary-dominated flow that the fit "
                "returns b <= 1 - rfour: \"Wait until production stabilizes into "
                "pseudosteady-state, then fit\"",
                "or a transient model (PLE, SEPD, Duong): the corpus discusses "
                "all three and states an equation for none, so none is built",
            ),
            source=ARPS_GATE,
        )
    return None


def _guard(b: float, boundary_dominated: bool):
    """Back-compatible shim for the pre-existing private gate in this module.

    `decline_eur` and `economic_limit_time` call this.  It now delegates so the
    gate exists once.  Note the default `boundary_dominated: bool = True` on
    those two functions declares the source's one hard condition on the caller's
    behalf; `decline_forecast` has no such default, and the two should agree.
    """
    return arps_flow_regime_gate(b, boundary_dominated)


def decline_rate(qi: float, di: float, b: float, t: float,
                 boundary_dominated: bool | None = None):
    """q(t): exponential b=0, hyperbolic 0<b<1, harmonic b=1.

    Signature and behaviour unchanged; the three forms now live in `_arps_rate`
    so the fitter scores against the same code the forecast returns.
    """
    refusal = arps_flow_regime_gate(b, boundary_dominated)
    if refusal:
        return refusal
    label = {FORM_EXPONENTIAL: "Arps exponential",
             FORM_HARMONIC: "Arps harmonic",
             FORM_HYPERBOLIC: "Arps hyperbolic"}[arps_form(b)]
    return Quantity(_arps_rate(qi, di, b, t), "rate", label, ARPS,
                    inputs={"qi": qi, "Di": di, "b": b, "t": t})


# --- least squares ---------------------------------------------------------


def _ols(xs: Sequence[float], ys: Sequence[float]) -> tuple[float, float] | None:
    """Ordinary least squares of y on x.  Returns (slope, intercept) or None."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return slope, my - slope * mx


# --- the three fitters, one per form ---------------------------------------
# Each inverts its own published equation.  They do not share a code path, for
# the same reason the three integrals in #117 do not: they are different
# equations, and the hyperbolic one is singular at both ends of its range.


def _fit_exponential(ts: Sequence[float], qs: Sequence[float]):
    """q = q_i e^(-D_i t)  =>  ln q = ln q_i - D_i t.  The semilog straight line."""
    fit = _ols(ts, [math.log(q) for q in qs])
    if fit is None:
        return None
    slope, intercept = fit
    try:
        qi = math.exp(intercept)
    except OverflowError:
        return None
    if not math.isfinite(qi) or qi <= 0:
        return None
    return qi, -slope


def _fit_harmonic(ts: Sequence[float], qs: Sequence[float]):
    """q = q_i/(1 + D_i t)  =>  1/q = 1/q_i + (D_i/q_i) t."""
    fit = _ols(ts, [1.0 / q for q in qs])
    if fit is None:
        return None
    slope, intercept = fit
    if intercept <= 0 or not math.isfinite(intercept):
        return None
    return 1.0 / intercept, slope / intercept


def _fit_hyperbolic(ts: Sequence[float], qs: Sequence[float], b: float):
    """q = q_i(1 + b D_i t)^(-1/b)  =>  q^-b = q_i^-b + q_i^-b b D_i t.

    Exact rearrangement, so at fixed b the fit is one linear solve rather than a
    search.  Refuses to run below `HYPERBOLIC_B_FLOOR`, where q^-b = 1 - b ln q
    to within float noise and the intercept carries no information.
    """
    if b < HYPERBOLIC_B_FLOOR:
        return None
    try:
        ys = [q ** (-b) for q in qs]
    except (OverflowError, ValueError):
        return None
    if not all(math.isfinite(y) for y in ys):
        return None
    fit = _ols(ts, ys)
    if fit is None:
        return None
    slope, intercept = fit
    if intercept <= 0 or not math.isfinite(intercept):
        return None
    try:
        qi = intercept ** (-1.0 / b)
    except (OverflowError, ZeroDivisionError, ValueError):
        return None
    if not math.isfinite(qi) or qi <= 0:
        return None
    return qi, slope / (intercept * b)


def _fit_at_b(ts: Sequence[float], qs: Sequence[float], b: float):
    """Dispatch on b, exactly as the source's three headings do (p. 3)."""
    if b == 0:
        return _fit_exponential(ts, qs)
    if b == 1:
        return _fit_harmonic(ts, qs)
    return _fit_hyperbolic(ts, qs, b)


def _sse_log(ts: Sequence[float], qs: Sequence[float],
             qi: float, di: float, b: float) -> float:
    """Sum of squared ln q residuals against the published forward form.

    Log space because a decline spans orders of magnitude and an absolute-rate
    objective would fit the first month and ignore the last five years.  The
    source prescribes no objective at all - see the spec, open question 1.
    """
    total = 0.0
    for t, q in zip(ts, qs):
        try:
            pred = _arps_rate(qi, di, b, t)
        except (ValueError, OverflowError, ZeroDivisionError):
            return math.inf
        if not math.isfinite(pred) or pred <= 0:
            return math.inf
        total += (math.log(q) - math.log(pred)) ** 2
    return total


def _score_b(ts: Sequence[float], qs: Sequence[float], b: float):
    """(sse, qi, di) for one b, or None if that b has no admissible fit."""
    fit = _fit_at_b(ts, qs, b)
    if fit is None:
        return None
    qi, di = fit
    return _sse_log(ts, qs, qi, di, b), qi, di


def _search_b(ts: Sequence[float], qs: Sequence[float], b_search_max: float):
    """Coarse grid then ternary refinement.  Returns (b, qi, di, sse).

    The grid runs to `b_search_max` and *not* to 1.0 on purpose: clamping the
    search at the gate would convert every transient well into a tidy harmonic
    fit instead of refusing it.
    """
    grid = [0.0]
    step = B_SEARCH_GRID_STEP
    k = 1
    while k * step < b_search_max:
        grid.append(round(k * step, 10))
        k += 1
    grid.append(b_search_max)

    scored: list[tuple[float, float, float, float]] = []   # (b, sse, qi, di)
    for b in grid:
        s = _score_b(ts, qs, b)
        if s is not None:
            scored.append((b, s[0], s[1], s[2]))
    if not scored:
        return None

    best_i = min(range(len(scored)), key=lambda i: scored[i][1])
    best = scored[best_i]

    lo = scored[best_i - 1][0] if best_i > 0 else 0.0
    hi = scored[best_i + 1][0] if best_i + 1 < len(scored) else b_search_max

    def f(b: float) -> float:
        s = _score_b(ts, qs, b)
        return math.inf if s is None else s[0]

    for _ in range(B_SEARCH_REFINE_ITERATIONS):
        if hi - lo <= 0:
            break
        m1 = lo + (hi - lo) / 3.0
        m2 = hi - (hi - lo) / 3.0
        if f(m1) <= f(m2):
            hi = m2
        else:
            lo = m1
    refined_b = 0.5 * (lo + hi)
    refined = _score_b(ts, qs, refined_b)

    if refined is not None and refined[0] < best[1]:
        return refined_b, refined[1], refined[2], refined[0]
    return best[0], best[2], best[3], best[1]


# --- output ----------------------------------------------------------------


@dataclass(frozen=True)
class DeclineFit:
    """An Arps fit, in the shape #117 and #118 read it.

    `q_i`, `d_i` and `b` are the whole handshake: `as_arps_kwargs()` hands them
    to `decline_eur`/`economic_limit_time` under the names those already use.

    `d_i` is the **nominal** decline, per `time_unit` (petroleumoffice p. 7,
    "Initial (nominal) decline rate ... 1/d, 1/month, 1/yr (must match time
    units)").  `d_effective_tangent` is phdwin's effective decline alongside it,
    because that is the one an operator reads off a graph.
    """

    q_i: Quantity
    d_i: Quantity
    b: Quantity
    form: str
    b_source: str                 # "supplied" | "fitted"
    fit_method: str
    time_unit: str
    rate_unit: str
    q_i_per_time_unit: Quantity
    d_effective_tangent: Quantity
    r2_log: Quantity
    rmse_log: Quantity
    t_span: Quantity
    n_points: int
    eur_units_consistent: bool
    method: str
    source: str
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    @property
    def params(self) -> tuple[float, float, float]:
        """(q_i, D_i, b) as plain floats, in the units named on the fields."""
        return self.q_i.value, self.d_i.value, self.b.value

    def as_arps_kwargs(self) -> dict[str, Any]:
        """Keyword arguments for `decline_eur` / `economic_limit_time` (#117/#118).

        `boundary_dominated=True` is carried through rather than re-defaulted: it
        is only True here because the caller declared it and the gate passed.
        """
        return {"qi": self.q_i.value, "di": self.d_i.value, "b": self.b.value,
                "boundary_dominated": True}

    def rate_at(self, t: float):
        """Forecast rate at t, in `time_unit`, through the module's own forward form."""
        return decline_rate(self.q_i.value, self.d_i.value, self.b.value, t,
                            boundary_dominated=True)


# --- the tool --------------------------------------------------------------


def decline_forecast(
    t_values: Sequence[float],
    q_values: Sequence[float],
    *,
    time_unit: str,
    rate_time_unit: str,
    rate_volume_unit: str,
    boundary_dominated_flow: bool | None = None,
    b: float | None = None,
    fit_from_time: float | None = None,
    fit_to_time: float | None = None,
    operating_conditions_constant: bool | None = None,
    drainage_area_fixed: bool | None = None,
    producing_at_capacity: bool | None = None,
    min_r2: float | None = None,
    b_search_max: float = B_SEARCH_MAX,
    b_form_snap: float = B_FORM_SNAP,
    max_increasing_step_fraction: float | None = None,
):
    """Fit Arps q_i, D_i and b to a production history.

    `time_unit` and `rate_time_unit` are separate and both required. The source
    only demands `[D_i] x [t] = dimensionless` (p. 7), which the rate-time forms
    satisfy under any pairing - but the *cumulative* forms #117 integrates have
    units [rate] x [time], a volume only when the rate's own time base equals
    D_i's.  A STB/day history fitted on a year axis forecasts correctly and gives
    an EUR 365.25x too large.  So both bases are carried, `eur_units_consistent`
    says whether they agree, and `q_i_per_time_unit` is q_i on the decline's base.

    `boundary_dominated_flow` has no default.  Supplying `b` gates which form
    runs; leaving it `None` fits it, and the fitted b is then gated the same way.
    """
    # --- programmer error, not source limits -------------------------------
    for name, unit in (("time_unit", time_unit), ("rate_time_unit", rate_time_unit)):
        if unit not in TIME_UNITS:
            raise ValueError(
                f"{name}={unit!r} is not one of {TIME_UNITS}; the Arps forms are "
                "unit-flexible but the unit still has to be named (petroleumoffice "
                "p. 7)")
    if not rate_volume_unit:
        raise ValueError("rate_volume_unit must be named (STB, Mscf, ...); it is "
                         "carried onto every number this returns")
    ts_all = [float(t) for t in t_values]
    qs_all = [float(q) for q in q_values]
    if len(ts_all) != len(qs_all):
        raise ValueError(f"t_values and q_values differ in length: "
                         f"{len(ts_all)} vs {len(qs_all)}")
    for t in ts_all:
        if not math.isfinite(t):
            raise ValueError(f"non-finite time value {t!r} in the production history")
    for earlier, later in zip(ts_all, ts_all[1:]):
        if later <= earlier:
            raise ValueError(
                f"a production history must be ordered in time and strictly "
                f"increasing; found {earlier!r} followed by {later!r}")
    if b_search_max <= B_TRANSIENT_ABOVE:
        raise ValueError(
            f"b_search_max={b_search_max!r} must exceed {B_TRANSIENT_ABOVE}: the "
            "search has to be able to reach the transient range for the b > 1 "
            "gate to have anything to refuse")
    if b_form_snap < 0:
        raise ValueError("b_form_snap must be non-negative")
    if (fit_from_time is not None and fit_to_time is not None
            and fit_from_time > fit_to_time):
        raise ValueError("fit_from_time is after fit_to_time")

    per_year, time_status, time_status_source = TIME_UNIT_PER_YEAR[time_unit]
    rate_per_year, rate_status, _ = TIME_UNIT_PER_YEAR[rate_time_unit]
    rate_unit = f"{rate_volume_unit}/{rate_time_unit}"
    flags: list[str] = []

    # --- the flow-regime gate, before any arithmetic -----------------------
    gate = arps_flow_regime_gate(b, boundary_dominated_flow)
    if gate is not None:
        return gate

    # --- the window (rfour steps 2-3) --------------------------------------
    kept = [(t, q) for t, q in zip(ts_all, qs_all)
            if (fit_from_time is None or t >= fit_from_time)
            and (fit_to_time is None or t <= fit_to_time)]
    if fit_from_time is not None or fit_to_time is not None:
        flags.append(
            f"fitted on a caller-selected window "
            f"[{fit_from_time if fit_from_time is not None else '-inf'}, "
            f"{fit_to_time if fit_to_time is not None else '+inf'}] {time_unit}: "
            f"{len(kept)} of {len(ts_all)} points. rfour: \"Where you start your "
            "fit matters more than which equation you choose\"")
    ts = [t for t, _ in kept]
    qs = [q for _, q in kept]

    b_source = "supplied" if b is not None else "fitted"
    need = MIN_POINTS_FIXED_B if b is not None else MIN_POINTS_FITTED_B
    if len(ts) < need:
        return Refusal(
            reason=(
                f"{len(ts)} point(s) in the fit window; the "
                f"{arps_form(b) if b is not None else 'three-parameter'} fit needs "
                f"at least {need}. A two-parameter line (q_i, D_i) needs two "
                "points; fitting b as well needs three."),
            needed=(f"at least {need} rate/time pairs"
                    + (" inside the requested window" if kept != list(zip(ts_all, qs_all))
                       else ""),),
            source=ARPS_RATE_TIME)

    # --- the data has to be a decline --------------------------------------
    for t, q in zip(ts, qs):
        if not math.isfinite(q) or q <= 0:
            return Refusal(
                reason=(
                    f"rate {q!r} at t = {t:g} {time_unit} is zero, negative or not "
                    "finite. Every Arps form is a ratio to q_i and every fit here "
                    "goes through ln q or q^-b, both undefined at or below zero. A "
                    "shut-in or missing month is not decline data - rfour, common "
                    "pitfall 4: \"Wells that cycle on/off, or have long shut-in "
                    "periods within the fit window, give garbage fits. Either "
                    "clean the data or pick a window where production is "
                    "continuous.\""),
                needed=("a rate series that is strictly positive over the fit window",
                        "or fit_from_time/fit_to_time selecting a continuous window"),
                source=ARPS_RATE_TIME)

    if qs[-1] >= qs[0]:
        return Refusal(
            reason=(
                f"the series does not decline: q at t = {ts[-1]:g} {time_unit} is "
                f"{qs[-1]:g} {rate_unit}, at or above the {qs[0]:g} {rate_unit} at "
                f"t = {ts[0]:g}. Decline curve analysis extrapolates a decline; a "
                "well that is not declining has none to fit, and every form here "
                "would return D_i <= 0."),
            needed=("a window over which the rate falls - rfour: \"Use the past "
                    "12-24 months of consistent decline as the fit window\"",),
            source=ARPS_RATE_TIME)

    rises = sum(1 for a, c in zip(qs, qs[1:]) if c > a)
    rise_fraction = rises / (len(qs) - 1)
    if max_increasing_step_fraction is not None and rise_fraction > max_increasing_step_fraction:
        return Refusal(
            reason=(
                f"{rises} of {len(qs) - 1} steps increase "
                f"({rise_fraction:.1%}), above the caller's "
                f"max_increasing_step_fraction={max_increasing_step_fraction:.1%}. "
                "rfour, pitfall 4: intermittent production gives garbage fits."),
            needed=("a continuous, monotonically declining window",),
            source=RFOUR_WORKFLOW)
    if rises:
        flags.append(
            f"{rises} of {len(qs) - 1} steps in the fit window increase rather than "
            "decline; rfour warns that intermittent production \"gives garbage "
            "fits\". Not refused - the series declines on net - but the fit is "
            "reading through the noise")

    # --- fit ---------------------------------------------------------------
    if b is not None:
        fit = _fit_at_b(ts, qs, float(b))
        if fit is None:
            return Refusal(
                reason=(f"the {arps_form(float(b))} linearisation has no admissible "
                        f"solution at b = {b:g} for this series (the fitted "
                        "intercept is not positive, so q_i would not be a rate)."),
                needed=("a longer or cleaner decline window", "or a different b"),
                source=ARPS_RATE_TIME)
        b_value, qi, di = float(b), fit[0], fit[1]
        sse = _sse_log(ts, qs, qi, di, b_value)
    else:
        found = _search_b(ts, qs, b_search_max)
        if found is None:
            return Refusal(
                reason=("no admissible Arps fit was found at any b in "
                        f"[0, {b_search_max:g}] for this series."),
                needed=("a longer or cleaner decline window",),
                source=ARPS_RATE_TIME)
        b_value, qi, di, sse = found
        # Snap to a form boundary and refit in that form, so the value handed to
        # #117 does not divide its integral by 3e-9.
        for boundary, name in ((B_EXPONENTIAL, FORM_EXPONENTIAL),
                               (B_HARMONIC, FORM_HARMONIC)):
            if b_value != boundary and abs(b_value - boundary) < b_form_snap:
                refit = _fit_at_b(ts, qs, boundary)
                if refit is not None:
                    flags.append(
                        f"fitted b = {b_value:.3e} snapped to exactly {boundary:g} "
                        f"({name}) and refitted in that form; the boundary is "
                        f"within b_form_snap = {b_form_snap:g}, which is ours, not "
                        "the source's")
                    b_value, qi, di = boundary, refit[0], refit[1]
                    sse = _sse_log(ts, qs, qi, di, b_value)
                break
        if b_value >= b_search_max:
            return Refusal(
                reason=(
                    f"the b search ran to its ceiling, b = {b_value:g}. phdwin p. 2 "
                    "puts the upper end of observed b factors at 2.0 to 2.5 "
                    "(\"seldom go above 2.0 or 2.5\"), so a fit that reaches it is "
                    "outside the range any corpus document describes - not merely "
                    "transient. Fitted alongside it: q_i = "
                    f"{qi:.6g} {rate_unit}, D_i = {di:.6g} /{time_unit}."),
                needed=("a fit window in boundary-dominated flow",
                        "or a transient/unconventional model, for which the corpus "
                        "states no equation"),
                source=PHDWIN_B_RANGE)

    # --- gate the fitted b, and report the numbers as a diagnosis ----------
    gate = arps_flow_regime_gate(
        b_value, boundary_dominated_flow, fitted_b=(b is None),
        fitted_params=(f"q_i = {qi:.6g} {rate_unit}, D_i = {di:.6g} /{time_unit}, "
                       f"b = {b_value:.6g}"))
    if gate is not None:
        return gate

    if di <= 0:
        return Refusal(
            reason=(f"the fitted initial decline is D_i = {di:.6g} /{time_unit}, "
                    "at or below zero: the regression says this series is flat or "
                    "rising, whatever its endpoints do. There is no Arps decline "
                    "to extrapolate."),
            needed=("a window over which the rate consistently falls",),
            source=ARPS_RATE_TIME)

    form = arps_form(b_value)

    # --- score (rfour step 4) ----------------------------------------------
    logs = [math.log(q) for q in qs]
    mean_log = sum(logs) / len(logs)
    ss_tot = sum((l - mean_log) ** 2 for l in logs)
    r2 = 1.0 - sse / ss_tot if ss_tot > 0 else float("nan")
    rmse = math.sqrt(sse / len(qs))
    if math.isfinite(r2) and r2 < R2_UNRELIABLE_BELOW:
        flags.append(
            f"R2 = {r2:.4f} on ln q, below rfour's {R2_UNRELIABLE_BELOW}: \"If "
            "R2 < 0.85, the fit is unreliable - try a different window or form\"")
    if min_r2 is not None and (not math.isfinite(r2) or r2 < min_r2):
        return Refusal(
            reason=(f"R2 = {r2:.4f} on ln q residuals, below the caller's "
                    f"min_r2 = {min_r2:g}. rfour, workflow step 4: \"If R2 < 0.85, "
                    "the fit is unreliable - try a different window or form.\""),
            needed=("a different fit window, or a different form",),
            source=RFOUR_WORKFLOW)

    # --- window length (rfour) ---------------------------------------------
    span = ts[-1] - ts[0]
    months_per_time_unit = 12.0 / per_year
    span_months = span * months_per_time_unit
    if span_months < MIN_STABLE_WINDOW_MONTHS:
        flags.append(
            f"fit window is {span:g} {time_unit} = {span_months:.1f} months; rfour: "
            f"\"Anything less than {MIN_STABLE_WINDOW_MONTHS:.0f} months of stable "
            "decline is noise-fitting\"")
        if b is None and span_months < MIN_MONTHS_TO_FIT_B:
            flags.append(
                "b was fitted, not supplied, from a window shorter than the "
                ">= 12-18 months rfour asks for before b can be fitted reliably; "
                "treat b as indicative, and note the b -> reservoir-type table "
                "(petroleumoffice p. 4) is the sanity check rfour step 5 wants")
    if time_status != "SOURCED":
        flags.append(f"time base '{time_unit}': {time_status_source} ({time_status})")

    # --- the other three valid conditions (petroleumoffice p. 7) -----------
    for label, declared, note in (
        ("operating conditions constant", operating_conditions_constant,
         "bottomhole pressure, completion, artificial lift"),
        ("drainage area fixed", drainage_area_fixed,
         "no infill drilling or recompletions"),
        ("producing at or near capacity", producing_at_capacity, ""),
    ):
        if declared is None:
            flags.append(
                f"'{label}' undeclared - one of the source's four valid conditions "
                f"(petroleumoffice p. 7{'; ' + note if note else ''}). Not refused: "
                "only boundary-dominated flow is a gate here")
        elif not declared:
            flags.append(
                f"'{label}' declared NOT met. petroleumoffice p. 8: significant "
                "changes in bottomhole pressure, artificial lift, completion or "
                "regulatory constraints \"will invalidate the forecast\"")

    if ts[0] != 0:
        flags.append(
            f"the history starts at t = {ts[0]:g} {time_unit}, not 0, so q_i is the "
            "rate extrapolated back to t = 0 of the caller's own time origin "
            "(p. 7: t is \"time since start of decline\"). phdwin p. 4 does the "
            "same deliberately - its \"curve fit algorithms 'back up' the curve fit "
            "projections to the beginning of a month\", giving a q_i above the "
            "month's produced volume")

    eur_units_consistent = (rate_time_unit == time_unit)
    if not eur_units_consistent:
        flags.append(
            f"rate is per {rate_time_unit} while the decline is per {time_unit}. "
            "The rate-time forecast is unaffected (p. 7 only requires [D_i] x [t] "
            "dimensionless), but a cumulative or EUR built from q_i/D_i comes out "
            f"in {rate_volume_unit}.{rate_time_unit}/{time_unit}, not "
            f"{rate_volume_unit} - out by a factor of "
            f"{rate_per_year / per_year:g}. Use q_i_per_time_unit for #117")

    if form == FORM_HARMONIC:
        flags.append(
            "harmonic: petroleumoffice p. 5 - \"For harmonic decline, cumulative "
            "production approaches infinity as t -> infinity. This is physically "
            "unrealistic for finite reservoirs\". EUR requires an economic limit; "
            "#117 makes q_econ required for exactly this reason")
    if form == FORM_HYPERBOLIC and b_value > 0.6:
        flags.append(
            f"b = {b_value:.4g}: rfour calls a long-horizon pure hyperbolic "
            "forecast at this b \"a fantasy\" without a terminal decline switch. "
            "No corpus document states that switch's equation, so tool-catalog.md "
            "s18 keeps it out and this fit does not apply one")

    method_note, method_source = FIT_METHODS[form]
    fit_method = f"{form}: {method_note}"
    inputs = {
        "n_points": len(ts), "t_first": ts[0], "t_last": ts[-1],
        "q_first": qs[0], "q_last": qs[-1], "time_unit": time_unit,
        "rate_unit": rate_unit, "b_source": b_source,
        "boundary_dominated_flow": True,
    }
    assumptions = {
        "fit_objective": (
            "least squares on ln q residuals (relative error), solved through each "
            "form's own exact linearisation. THE SOURCE PRESCRIBES NO REGRESSION - "
            "petroleumoffice prints no worked example and no fitting method; this "
            "follows rfour's graphical workflow (\"Plot rate vs time on semi-log "
            "paper ... Check the residual\"), which is not the same estimator as a "
            "joint nonlinear least squares on noisy data"),
        "b_source": b_source,
        "b_search_range": f"[0, {b_search_max:g}]" if b is None else "n/a (b supplied)",
        "b_search_max_basis": PHDWIN_B_RANGE if b is None else "n/a",
        "b_form_snap": b_form_snap,
        "d_i_kind": "nominal (petroleumoffice p. 7)",
        "flow_regime": "boundary-dominated, declared by the caller and not inferred",
        "window": {"from": fit_from_time, "to": fit_to_time,
                   "points_used": len(ts), "points_supplied": len(ts_all)},
        "eur_units_consistent": eur_units_consistent,
    }

    def qty(value: float, unit: str, label: str, src: str, extra: dict | None = None):
        return Quantity(value, unit, f"{METHOD}; {label}", src,
                        inputs=inputs, assumptions={**assumptions, **(extra or {})},
                        flags=tuple(flags))

    return DeclineFit(
        q_i=qty(qi, rate_unit, f"q_i from {fit_method}", method_source),
        d_i=qty(di, f"1/{time_unit}", f"D_i (nominal) from {fit_method}", method_source),
        b=qty(b_value, "dimensionless",
              f"b {b_source} ({form}; the source's three headings, p. 3)",
              ARPS_RATE_TIME if b is not None else PHDWIN_B_RANGE),
        form=form,
        b_source=b_source,
        fit_method=fit_method,
        time_unit=time_unit,
        rate_unit=rate_unit,
        q_i_per_time_unit=qty(
            qi * rate_per_year / per_year, f"{rate_volume_unit}/{time_unit}",
            f"q_i re-expressed on the decline's own time base "
            f"(x {rate_per_year / per_year:g}), so a cumulative built from "
            f"q_i/D_i comes out in {rate_volume_unit}",
            ARPS_UNITS,
            {"conversion_status": rate_status if rate_time_unit != time_unit else "identity"}),
        d_effective_tangent=qty(
            1.0 - math.exp(-di), f"fraction/{time_unit}",
            "effective decline D_Te = 1 - e^(-D), the tangent at q_i - phdwin p. 3: "
            "\"Effective Decline is the most intuitive decline measurement. Unlike "
            "Nominal decline, it can be read directly from a graph\"",
            PHDWIN_EFFECTIVE),
        r2_log=qty(r2, "dimensionless",
                   "R2 of ln q residuals against the forward Arps form "
                   "(rfour workflow step 4)", RFOUR_WORKFLOW),
        rmse_log=qty(rmse, "ln(rate)", "RMSE of ln q residuals", RFOUR_WORKFLOW),
        t_span=qty(span, time_unit, "length of the fit window", RFOUR_WORKFLOW),
        n_points=len(ts),
        eur_units_consistent=eur_units_consistent,
        method=METHOD,
        source=ARPS_RATE_TIME,
        inputs=inputs,
        assumptions=assumptions,
        flags=tuple(flags),
    )


# ======================================================================
# Tool #117 - decline_eur
# ======================================================================


# --- sources -----------------------------------------------------------------

#: Arps decline curve analysis. The typeset math is vector art in the PDF and is
#: absent from the text extraction; the authoritative transcription is the
#: page-anchored OCR sidecar
#: `petroleumoffice-arps-decline-curve-analysis.equations.md`.

#: Corroborating practical guide. Source of the leading `N_p` term (line 111,
#: "EUR = Np + (qi - qeco) / D ... where Np is cumulative production to date")
#: and of the harmonic-divergence warning (line 121).
ARPS_RFOUR = "16-decline-curves/rfour-arps-dca-practical-guide"

#: PDF page of each EUR equation in the source, carried onto the result so a
#: reviewer can check the branch that actually ran against the printed page.
ARPS_EQ_PAGES = {
    "exponential": "p. 4",   # EUR = (q_i - q_econ) / D_i
    "hyperbolic": "p. 5",    # EUR = q_i^b/((1-b)D_i) (q_i^(1-b) - q_econ^(1-b))
    "harmonic": "p. 6",      # EUR = (q_i/D_i) ln(q_i/q_econ)
}

# --- thresholds the corpus does not supply -----------------------------------
# Both of these are THE TOOL'S, not the source's. The corpus states `b = 1` and
# says nothing about a neighbourhood of it. Both are recorded on every result
# they touch.

#: Switch to the harmonic integral when `x = (1 - b) * ln(q_i/q_econ) <= this`.
#:
#: Derivation (spec §"The near-harmonic band"): the hyperbolic numerator is
#: `q_i^(1-b) - q_econ^(1-b) = q_econ^(1-b) * (e^x - 1)` with `x = (1-b)*L`,
#: `L = ln(q_i/q_econ)`. Evaluated literally in float64 its relative error is
#: about `machine_eps / x` (cancellation); substituting the harmonic form
#: instead costs about `x / 2`. They cross at `x = sqrt(2 * machine_eps)`, which
#: is where total error is minimised. Either branch is then correct to ~1e-8
#: relative. `b = 1.0` exactly gives `x = 0` and lands here, as it must.
HARMONIC_X_TOL = math.sqrt(2.0 * 2.220446049250313e-16)  # 2.107e-08

#: Advisory only — changes no value. `1/(1-b) > 100` means the EUR is amplifying
#: the fitted `b` a hundredfold and the forecast is limit-dominated: the
#: divergence the source warns about at `b = 1` showing up in a fit that is not
#: formally harmonic.
NEAR_HARMONIC_B = 0.99

#: Time-unit aliases for the consistency check the source demands on p. 7:
#: `[D_i] x [t] = dimensionless`. q in STB/d against D_i in 1/yr is wrong by
#: 365x and is silent otherwise.
_TIME_UNITS = {
    "d": "d", "day": "d", "days": "d",
    "mo": "mo", "month": "mo", "months": "mo",
    "yr": "yr", "y": "yr", "year": "yr", "years": "yr", "a": "yr", "ann": "yr",
}

#: Field names accepted off a #116 `decline_forecast` fit, in lookup order.
#: `Di`/`qi` are what this module's own `decline_rate` records in `inputs`.
_FIT_KEYS = {
    "qi": ("qi", "q_i", "qi_rate"),
    "di": ("di", "Di", "D_i"),
    "b": ("b",),
    "boundary_dominated": ("boundary_dominated",),
    "rate_unit": ("rate_unit",),
    "di_time_unit": ("di_time_unit",),
    "cumulative_before_fit": ("cumulative_before_fit", "cumulative_to_date", "Np"),
}


def _read_fit(fit, name):
    """Pull one field off a #116 fit. Never imports #116 — reads it structurally.

    Accepts a Mapping, a `Quantity` (looking in `.inputs` then `.assumptions`),
    or any object with the attributes. Returns None when absent.
    """
    for key in _FIT_KEYS[name]:
        if isinstance(fit, Mapping):
            if key in fit:
                return fit[key]
        elif isinstance(fit, Quantity):
            if key in fit.inputs:
                return fit.inputs[key]
            if key in fit.assumptions:
                return fit.assumptions[key]
        elif hasattr(fit, key):
            return getattr(fit, key)
    return None


def _norm_time_unit(u):
    """'1/d' -> 'd', 'per year' -> 'yr', 'D' -> 'd'. None when unrecognised."""
    if not u:
        return None
    s = str(u).strip().lower()
    for prefix in ("1/", "1 /", "per ", "/"):
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
            break
    return _TIME_UNITS.get(s)


def _volume_unit(rate_unit, di_time_unit):
    """(unit_label, flags, refusal). Enforces p. 7's `[D_i] x [t] = dimensionless`.

    Only checkable when the caller declares both units; undeclared is a flag,
    not a refusal, because the source calls the equations "unit-flexible".
    """
    if rate_unit is None and di_time_unit is None:
        return "volume", ("volume unit unlabelled: pass rate_unit and di_time_unit "
                          "to have the [D_i]x[t] consistency checked (source p. 7)",), None
    if rate_unit is None or di_time_unit is None:
        return "volume", ("only one of rate_unit / di_time_unit declared, so the "
                          "[D_i]x[t] consistency check (source p. 7) could not run",), None

    di_base = _norm_time_unit(di_time_unit)
    if di_base is None:
        return "volume", (f"unrecognised di_time_unit {di_time_unit!r}; consistency "
                          "check skipped",), None

    if "/" not in str(rate_unit):
        return "volume", (f"rate_unit {rate_unit!r} has no time base, so the "
                          "[D_i]x[t] consistency check could not run",), None

    numerator, _, denominator = str(rate_unit).partition("/")
    rate_base = _norm_time_unit(denominator)
    if rate_base is None:
        return "volume", (f"unrecognised time base in rate_unit {rate_unit!r}; "
                          "consistency check skipped",), None

    if rate_base != di_base:
        return None, (), Refusal(
            reason=(f"unit mismatch: q is per {rate_base} but D_i is per {di_base}. "
                    "The Arps equations require [D_i] x [t] to be dimensionless "
                    "(source p. 7); as given, EUR would be wrong by the "
                    f"{rate_base}-to-{di_base} conversion factor"),
            needed=(f"D_i restated in 1/{rate_base}, or q restated per {di_base}",),
            source=ARPS)

    return numerator.strip(), (), None


def _guard_fit(qi, di, b, boundary_dominated):
    """The gates that belong to the fit itself, not to the economic limit.

    Inherits #116's refusals rather than re-litigating them: `b > 1` is transient
    flow (source line 149/292/298) and Arps outside boundary-dominated flow is
    not valid at all (line 111/151).
    """
    if not boundary_dominated:
        return Refusal(
            reason="Arps holds only in boundary-dominated flow",
            needed=("confirmation the well has reached boundary-dominated flow",),
            source=ARPS)
    if b is None:
        return Refusal(
            reason="no Arps exponent b: the EUR integral is a different function "
                   "for b = 0, 0 < b < 1 and b = 1, so the case cannot be chosen",
            needed=("b, from a decline_forecast (#116) fit",), source=ARPS)
    if b > 1.0:
        return Refusal(
            reason=f"b = {b} exceeds 1.0, which indicates transient flow rather "
                   "than a valid Arps fit; Arps would overestimate reserves",
            needed=("a longer production history, or a transient model "
                    "(PLE, SEPD, Duong)",),
            source=ARPS)
    if b < 0.0:
        return Refusal(
            reason=f"b = {b} is below 0.0 and outside the published range (0 - 1.0); "
                   "a negative Arps exponent implies the loss ratio shrinks with "
                   "time, which no Arps case describes",
            needed=("a b within 0 - 1.0, or a non-Arps model",), source=ARPS)
    if qi is None or qi <= 0:
        return Refusal(
            reason=f"initial rate q_i = {qi} is not positive; the source requires "
                   "q_i > 0 (p. 7, Typical Parameter Ranges)",
            needed=("a positive q_i from the fit",), source=ARPS)
    if di is None or di <= 0:
        return Refusal(
            reason=(f"initial decline rate D_i = {di} is not positive. D_i divides "
                    "every Arps EUR form: D_i = 0 is no decline at all (EUR "
                    "unbounded) and D_i < 0 is growth, neither of which the "
                    "equations describe"),
            needed=("a positive D_i (source p. 7 gives 5% - 95% per year)",),
            source=ARPS)
    return None


def decline_eur(qi=None, di=None, q_econ=None, b=None,
                cumulative_before_fit=0.0, boundary_dominated=None, *,
                fit=None, rate_unit=None, di_time_unit=None,
                cumulative_to_date=None):
    """EUR integrated to the economic limit, not to infinity.

    Three Arps cases, three integrals, three branches -- they do not share a
    code path, because they are not one function:

      exponential  b = 0        EUR = (q_i - q_econ) / D_i                  (p. 4)
      hyperbolic   0 < b < 1    EUR = q_i^b/((1-b) D_i) (q_i^(1-b) - q_econ^(1-b))
                                                                           (p. 5)
      harmonic     b = 1        EUR = (q_i / D_i) ln(q_i / q_econ)          (p. 6)

    The harmonic case is a logarithm, not a power, and its integral **diverges**
    as q_econ -> 0 ("cumulative production approaches infinity as t -> inf ...
    physically unrealistic for finite reservoirs", source line 229). That is why
    `q_econ` is required here and never defaulted, for every b -- so that the
    failure does not depend on a fitted parameter.

    `fit` is a #116 `decline_forecast` result, read structurally rather than
    imported. Fields read: `qi`/`q_i`, `di`/`Di`/`D_i`, `b`, and optionally
    `boundary_dominated`, `rate_unit`, `di_time_unit`, `cumulative_before_fit`.
    **A `Refusal` arriving as `fit` is returned unchanged** -- #116's gate is
    inherited, not re-litigated, and never mistaken for a missing argument.
    Explicit arguments override the fit.

    `cumulative_before_fit` is the volume produced before t = 0 of the fit
    (rfour line 111's `N_p`). Default 0.0 reproduces the petroleumoffice
    equations exactly.

    Returns `Quantity` (volume) or `Refusal`.
    """
    # 1. A refusing fit propagates. Not a missing argument -- an answered
    #    question whose answer was "no".
    if isinstance(fit, Refusal):
        return fit

    # 2. Merge the fit. Explicit arguments win.
    if fit is not None:
        if qi is None:
            qi = _read_fit(fit, "qi")
        if di is None:
            di = _read_fit(fit, "di")
        if b is None:
            b = _read_fit(fit, "b")
        if boundary_dominated is None:
            boundary_dominated = _read_fit(fit, "boundary_dominated")
        if rate_unit is None:
            rate_unit = _read_fit(fit, "rate_unit")
        if di_time_unit is None:
            di_time_unit = _read_fit(fit, "di_time_unit")

    # Deprecated alias for the renamed slot-5 argument. Old name meant
    # "cumulative to date", which was ambiguous about which date.
    if cumulative_to_date is not None:
        cumulative_before_fit = cumulative_to_date

    if qi is None and di is None:
        raise TypeError("decline_eur needs a fit: pass qi and di, or fit=<#116 result>")

    # Sentinels resolve only after the fit has had its say, so an explicit
    # `b=0.0` is honoured as exponential rather than being overwritten by a
    # fit's b, and `boundary_dominated=False` is not overwritten by a fit's True.
    if b is None:
        b = 0.0
    if boundary_dominated is None:
        # Left undeclared by both the caller and the fit. Do NOT assume True:
        # boundary-dominated flow is the one condition Arps requires and it
        # cannot be read off a rate series, which is why #116 refuses without
        # it. `arps_flow_regime_gate` turns None into that refusal.
        pass

    # 3. Gates on the fit itself.
    refusal = _guard_fit(qi, di, b, boundary_dominated)
    if refusal:
        return refusal

    # 4. Gates on the economic limit. `q_econ` missing is a refusal rather than a
    #    TypeError because the source makes the quantity undefined without it,
    #    not because the caller mistyped.
    if q_econ is None:
        return Refusal(
            reason=("EUR requires an economic limit rate. The harmonic case (b = 1) "
                    "diverges without one -- cumulative production approaches "
                    "infinity as t -> infinity -- and the hyperbolic case is "
                    "unbounded as q_econ -> 0 for every b > 0. An EUR integrated "
                    "to infinity is not a large number, it is a meaningless one"),
            needed=("q_econ, the rate at which the well stops paying for itself, "
                    "in the same units as q_i",),
            source=ARPS)
    if q_econ <= 0:
        return Refusal(
            reason=(f"economic limit rate q_econ = {q_econ} is not positive; "
                    "q_econ -> 0 is the divergence itself, not a limit"),
            needed=("a positive q_econ in the same units as q_i",), source=ARPS)
    if q_econ >= qi:
        # Refusal, not zero EUR. All three forms return exactly 0 here and go
        # negative above it, but a zero carries no information from the decline
        # model (same zero for every b and D_i), the likeliest cause is a
        # rate-unit mismatch between the fit's q_i and an operator-typed q_econ,
        # and the source's own t_econ forms all give t <= 0 -- the economic limit
        # lies at or before the start of the fit, so there is nothing forward of
        # q_i to integrate. See specs/117-decline_eur.md.
        return Refusal(
            reason=(f"economic limit q_econ = {q_econ} is at or above the fit's "
                    f"initial rate q_i = {qi}: the interval to integrate is empty "
                    "and t_econ <= 0, so the economic limit lies at or before the "
                    "start of the fit. Check that q_econ and q_i are in the same "
                    "rate units before reading this as a depleted well"),
            needed=("q_econ below q_i in matching units, or economic_limit_time "
                    "(#118), which is where 'this well is already finished' is the "
                    "informative answer",),
            source=ARPS)

    # 5. Unit consistency, source p. 7: [D_i] x [t] = dimensionless.
    unit, unit_flags, refusal = _volume_unit(rate_unit, di_time_unit)
    if refusal:
        return refusal

    flags = list(unit_flags)
    assumptions = {
        "integrated_to": "economic limit, not infinity",
        "t_zero": "start of the fit window, not necessarily first production",
    }

    # 6. Branch. Three integrals, three paths, each quoting its own page.
    #    `x` measures how close to harmonic the fit is in the only way that
    #    matters to the hyperbolic form's arithmetic.
    ln_ratio = math.log(qi / q_econ)
    x = (1.0 - b) * ln_ratio

    if b == 0.0:
        # Exponential, source p. 4. Integral of q_i e^(-D_i t) to t_econ.
        # No tolerance on this side: the hyperbolic form is perfectly stable as
        # b -> 0 ((1-b) -> 1, no cancellation), so a near-zero b needs no special
        # case and inventing one symmetric to the b = 1 case would be cargo cult.
        eur = (qi - q_econ) / di
        case, method = "exponential", "Arps EUR (exponential, b = 0)"

    elif x > HARMONIC_X_TOL:
        # Hyperbolic, source p. 5. Evaluated as printed.
        eur = (qi ** b / ((1.0 - b) * di)) * (qi ** (1.0 - b) - q_econ ** (1.0 - b))
        case, method = "hyperbolic", "Arps EUR (hyperbolic, 0 < b < 1)"

    else:
        # Harmonic, source p. 6 -- a logarithm, not a power, and the reason
        # q_econ is required. Entered by b == 1.0 exactly (x = 0) and by the
        # near-degenerate band, where the printed hyperbolic form loses more
        # digits to cancellation than the harmonic substitution costs.
        eur = (qi / di) * ln_ratio
        case = "harmonic"
        if b == 1.0:
            method = "Arps EUR (harmonic, b = 1)"
        else:
            method = "Arps EUR (harmonic form applied to a near-harmonic fit)"
            assumptions["harmonic_substitution"] = (
                f"b = {b} is within the tool's near-degenerate band "
                f"((1-b)*ln(q_i/q_econ) = {x:.3e} <= {HARMONIC_X_TOL:.3e}); the "
                "hyperbolic form's (1-b) denominator loses more precision to "
                "cancellation here than this substitution costs")
            assumptions["tolerance_is_the_tool's"] = (
                "HARMONIC_X_TOL is derived from float64 precision, NOT from the "
                "source; the corpus states b = 1 and nothing about a neighbourhood")
            flags.append(
                f"b = {b} is not exactly 1 but the harmonic integral was used; "
                "both branches agree to ~1e-8 relative here")

    # 7. Advisory, not a switch: near-harmonic fits are limit-dominated.
    if b == 1.0:
        flags.append(
            "harmonic decline: cumulative production is unbounded as t -> infinity "
            "(source p. 8, Limitation 2), so this EUR is entirely a statement about "
            f"q_econ = {q_econ}. Halving q_econ raises EUR by (q_i/D_i) ln 2")
    elif b >= NEAR_HARMONIC_B:
        flags.append(
            f"b = {b} >= {NEAR_HARMONIC_B}: 1/(1-b) = {1.0 / (1.0 - b):.0f}, so EUR "
            "amplifies the fitted b that many times over and the forecast is "
            "controlled by q_econ. The source warns that harmonic decline implies "
            "unbounded cumulative production; this fit behaves that way")

    if cumulative_before_fit == 0.0:
        flags.append(
            "EUR is measured from t = 0 of the fit. If the fit window does not "
            "start at first production, add the volume produced before it as "
            "cumulative_before_fit (rfour line 111's N_p)")
    else:
        flags.append(
            "cumulative_before_fit must be the volume produced BEFORE t = 0 of "
            "the fit, not cumulative to today; cumulative-to-today double-counts "
            "the segment between the fit's start and now")

    return Quantity(
        eur + cumulative_before_fit, unit, method, ARPS,
        inputs={"qi": qi, "Di": di, "q_econ": q_econ, "b": b,
                "cumulative_before_fit": cumulative_before_fit},
        assumptions={**assumptions,
                     "case": case,
                     "equation_page": ARPS_EQ_PAGES[case],
                     "cumulative_term_source": ARPS_RFOUR + " (line 111)",
                     "boundary_dominated": boundary_dominated,
                     "rate_unit": rate_unit,
                     "di_time_unit": di_time_unit},
        flags=tuple(flags))


# ======================================================================
# Tool #118 - economic_limit_time
# ======================================================================


# --- constants and tables ---------------------------------------------------


#: Source p. 6, "Unit Consistency": [D_i] x [t] must be dimensionless, so
#: t_econ comes out in whatever time unit D_i was fitted per. The unit symbol
#: is carried on the result so a per-month D_i cannot masquerade as per-day.
#: Deliberately no day-conversion factor: the source defines no month length
#: (calendar vs 30 vs 30.4375 days) and inventing one is out of bounds.
TIME_BASIS_UNITS = {
    "day": "d",
    "days": "d",
    "month": "month",
    "months": "month",
    "year": "yr",
    "years": "yr",
}

UNSTATED_TIME_UNIT = "t (basis of D_i)"

#: Source p. 8, "Typical Parameter Ranges": b range 0 - 1.0; values > 1 indicate
#: transient flow, where PLE / SEPD / Duong apply instead.
B_MIN, B_MAX = 0.0, 1.0

#: Below this, 1/(b*D_i) in the hyperbolic form is ill-conditioned and the
#: exponential limit is the intended model. Flagged, never silently switched:
#: switching would change which published equation the result cites. Not a
#: sourced threshold - the source names only b = 0, 0 < b < 1, b = 1.
B_NEAR_ZERO = 1e-6

#: Fit fields read from decline_forecast (#116), first match wins. The
#: capitalised aliases match the `inputs={"qi":..., "Di":..., "b":...}`
#: convention already used in tools/decline.py.
_FIT_ALIASES = {
    "qi": ("qi", "q_i", "qi_rate"),
    "di": ("di", "Di", "D_i"),
    "b": ("b", "b_exponent"),
    "time_basis": ("time_basis", "basis", "time_unit"),
    "boundary_dominated": ("boundary_dominated",),
}


# --- fit plumbing -----------------------------------------------------------

def _fit_lookup(fit: Any, names: tuple[str, ...]):
    """Read a field from a mapping, an object, or a Quantity's .inputs."""
    sources = [fit]
    inputs = getattr(fit, "inputs", None)
    if isinstance(inputs, dict):
        sources.append(inputs)
    for src in sources:
        for name in names:
            if isinstance(src, dict):
                if name in src and src[name] is not None:
                    return src[name]
            else:
                got = getattr(src, name, None)
                if got is not None:
                    return got
    return None


# --- guards -----------------------------------------------------------------

def _guard_inputs(qi, di, q_econ, b, boundary_dominated):
    """Every refusal this tool can make on its own arguments, in order."""
    if not boundary_dominated:
        return Refusal(
            reason="Arps decline holds only in boundary-dominated flow, which the "
                   "caller has not asserted, so no economic limit time can be forecast",
            needed=("confirmation the well has reached boundary-dominated flow",),
            source=ARPS)
    if b is None:
        return Refusal(
            reason="no Arps exponent b supplied, so the applicable economic-limit-time "
                   "equation cannot be chosen",
            needed=("b, from decline_forecast (#116)",), source=ARPS)
    if b < B_MIN or b > B_MAX:
        return Refusal(
            reason=f"b = {b} is outside the Arps range {B_MIN}-{B_MAX}; b > 1 indicates "
                   "transient rather than boundary-dominated flow, where PLE, SEPD or "
                   "Duong apply, and b < 0 is outside Arps' framework entirely",
            needed=("a b within 0-1, or a transient decline model",), source=ARPS)
    if qi is None:
        return Refusal(
            reason="no initial rate q_i supplied",
            needed=("q_i, from decline_forecast (#116)",), source=ARPS)
    if qi <= 0:
        return Refusal(
            reason=f"initial rate q_i = {qi} is not positive; the source requires q_i > 0",
            needed=("a positive initial rate",), source=ARPS)
    if di is None:
        return Refusal(
            reason="no initial decline rate D_i supplied",
            needed=("D_i, from decline_forecast (#116)",), source=ARPS)
    if di <= 0:
        return Refusal(
            reason=f"initial decline rate D_i = {di} is not positive; every economic-limit-time "
                   "form divides by D_i, and a non-positive decline never reaches an "
                   "economic limit",
            needed=("a positive D_i (the source's typical range is 5%-95% per year)",),
            source=ARPS)
    if q_econ is None:
        return Refusal(
            reason="no economic limit rate q_econ supplied; it is an economics input "
                   "(price, operating cost, working interest) and the corpus supplies "
                   "no default",
            needed=("q_econ, in the same rate units as q_i",), source=ARPS)
    if q_econ <= 0:
        return Refusal(
            reason=f"economic limit rate q_econ = {q_econ} is not positive; every form "
                   "diverges as q_econ approaches zero, which is the statement that a "
                   "well with no economic limit produces forever",
            needed=("a positive q_econ",), source=ARPS)
    if q_econ > qi:
        return Refusal(
            reason=f"the well is already below its economic limit: q_econ = {q_econ} "
                   f"exceeds the fitted initial rate q_i = {qi}, so remaining economic "
                   "life is not positive. The published forms return a negative t here, "
                   "which is the time in the past at which the decline passed q_econ, "
                   "not a forecast",
            needed=("a q_i above q_econ, or acceptance that the well is uneconomic now",),
            source=ARPS)
    return None


# --- the tool ---------------------------------------------------------------

def economic_limit_time(qi: float, di: float, q_econ: float, b: float = 0.0,
                        time_basis: str | None = None,
                        boundary_dominated: bool | None = None):
    """Time at which a fitted Arps decline reaches the economic limit rate.

    Three published branches, `16-decline-curves/petroleumoffice-arps-decline-curve-analysis#0`:

      exponential (b = 0)      t_econ = (1/D_i) ln(q_i/q_econ)                p. 4
      hyperbolic  (0 < b < 1)  t_econ = 1/(b D_i) [(q_i/q_econ)^b - 1]        p. 4
      harmonic    (b = 1)      t_econ = (1/D_i) (q_i/q_econ - 1)              p. 5

    `t_econ` is returned in the time unit `D_i` was fitted per: pass
    `time_basis` ("day" / "month" / "year") so the result can say which.
    Measured from the start of decline (the fit's t = 0), not from today.
    """
    refusal = _guard_inputs(qi, di, q_econ, b, boundary_dominated)
    if refusal:
        return refusal

    flags: list[str] = []
    unit = TIME_BASIS_UNITS.get(str(time_basis).lower()) if time_basis else None
    if unit is None:
        unit = UNSTATED_TIME_UNIT
        flags.append("time_basis_unstated")
    basis = str(time_basis).lower() if time_basis else "unstated"

    ratio = qi / q_econ

    # Three branches, one per published equation. Not one general form: the
    # exponential case is a true singularity of the hyperbolic form, and each
    # branch must name the equation it cites.
    if b == 0.0:
        t = (1.0 / di) * math.log(ratio)
        method = "Arps economic limit time (exponential, b = 0)"
        equation = "t_econ = (1/D_i) ln(q_i/q_econ)"
    elif b == 1.0:
        t = (1.0 / di) * (ratio - 1.0)
        method = "Arps economic limit time (harmonic, b = 1)"
        equation = "t_econ = (1/D_i) (q_i/q_econ - 1)"
    else:
        t = (1.0 / (b * di)) * (ratio ** b - 1.0)
        method = "Arps economic limit time (hyperbolic, 0 < b < 1)"
        equation = "t_econ = 1/(b D_i) [(q_i/q_econ)^b - 1]"
        if b < B_NEAR_ZERO:
            flags.append("b_near_zero_use_exponential_limit")

    if t == 0.0:
        # q_econ == q_i exactly. A correct, non-negative forecast: the well is
        # at its economic limit now, and #117 then integrates to zero remaining
        # volume, which is true.
        flags.append("at_economic_limit")

    return Quantity(
        t, unit, method, ARPS,
        inputs={"qi": qi, f"Di_per_{basis}": di, "q_econ": q_econ, "b": b},
        assumptions={
            "equation": equation,
            "time_basis": basis,
            "t_zero": "start of decline (the fit's t = 0), not today",
            "boundary_dominated": boundary_dominated,
        },
        flags=tuple(flags))


def economic_limit_time_from_fit(fit: Any, q_econ: float,
                                 time_basis: str | None = None,
                                 boundary_dominated: bool | None = None):
    """`economic_limit_time` driven by a `decline_forecast` (#116) fit.

    Reads q_i, D_i, b, time_basis and boundary_dominated from the fit (see
    `_FIT_ALIASES`; a mapping, an attribute-carrying object, or a Quantity whose
    `.inputs` holds them all work). A refusing fit is propagated as a refusal
    quoting the upstream reason, never re-reported as a missing argument.
    """
    if isinstance(fit, Refusal):
        return Refusal(
            reason=f"decline_forecast (#116) declined to fit this well, so there is no "
                   f"decline to project to an economic limit: {fit.reason}",
            needed=fit.needed or ("a decline fit that does not refuse",),
            source=fit.source or ARPS)
    if fit is None:
        return Refusal(
            reason="no decline fit supplied",
            needed=("a fit from decline_forecast (#116)",), source=ARPS)

    qi = _fit_lookup(fit, _FIT_ALIASES["qi"])
    di = _fit_lookup(fit, _FIT_ALIASES["di"])
    b = _fit_lookup(fit, _FIT_ALIASES["b"])
    missing = [name for name, got in (("q_i", qi), ("D_i", di), ("b", b)) if got is None]
    if missing:
        return Refusal(
            reason=f"the supplied decline fit carries no {', '.join(missing)}; looked for "
                   f"{_FIT_ALIASES['qi']}, {_FIT_ALIASES['di']}, {_FIT_ALIASES['b']}",
            needed=tuple(f"{m} on the fit from decline_forecast (#116)" for m in missing),
            source=ARPS)

    if time_basis is None:
        time_basis = _fit_lookup(fit, _FIT_ALIASES["time_basis"])
    if boundary_dominated is None:
        from_fit = _fit_lookup(fit, _FIT_ALIASES["boundary_dominated"])
        boundary_dominated = True if from_fit is None else bool(from_fit)

    return economic_limit_time(qi=float(qi), di=float(di), q_econ=q_econ,
                               b=float(b), time_basis=time_basis,
                               boundary_dominated=boundary_dominated)
