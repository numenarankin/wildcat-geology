"""#95 `hingle_plot` — the Hingle (1959) resistivity-porosity crossplot.

Asquith & Krygowski #47, pp. 122-123, Eqs. 7.28 and 7.29; worked example in the
Figure 7.7 caption at #51, p. 134; data in Table 7.4 at #48, p. 124.

Three decisions worth stating, because none of them is obvious from the equation:

* `a` and `m` are required arguments with no defaults. They are not tuning
  knobs — they define the printed grid the resistivity axis is scaled on
  ("the grid constructed using a = 1.0 and m = 2.0 is usually used for
  sandstones", #47), and the whole method is that scaling. Defaulting them
  would silently pick a chart.
* The matrix value is required too, by an explicit number or by a stated
  lithology. Asquith's own Hingle example uses rho_ma = 2.65 read off the plot,
  while his Table 4.2 (what `matrix_constant_lookup` returns) says 2.644 for
  sandstone; the two differ by about one porosity unit, so the route taken is
  recorded and the lithology route is flagged.
* The tool will not guess that a water-bearing zone exists. A Hingle plot fitted
  through hydrocarbon-bearing points returns a low Rw and uniformly optimistic
  saturations, and it looks entirely reasonable (#44: "If the zone with the
  minimum R_wa value actually contains some hydrocarbons, then the other zones
  contain even more hydrocarbons than anticipated"). No arithmetic on Rt and phi
  can detect that, so it is a caller declaration or a refusal.

The wet line is fitted by least squares through the matrix point rather than as
an upper envelope: Asquith draws it "through the cluster of points"
(Figure 7.7 caption), and an envelope is set by whichever single point is
noisiest.

If this file is merged into `tools/petrophysics.py`, drop the `.petrophysics`
import line — FLUID and matrix_constant_lookup are already there.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from ..result import Quantity, Range, Refusal
from ..petrophysics import FLUID, matrix_constant_lookup

# Asquith & Krygowski, Basic Well Log Analysis (2004).
HINGLE = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#47"
HINGLE_EXAMPLE = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#51"
RWA_METHOD = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#44"
CROSSPLOT_LIMITS = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#48"

# The two printed Hingle grids, #47 p. 122. Offered as named pairs so a caller
# can say which chart they read the points off; they are not defaults.
HINGLE_GRIDS: dict[str, dict[str, float]] = {
    # "The grid constructed using a = 1.0 and m = 2.0 is usually used for
    # sandstones (Figure 7.5)" - Western Atlas Chart 7-79.
    "sandstone": {"a": 1.0, "m": 2.0},
    # "... and the grid constructed using a = 0.62 and m = 2.15 is used for
    # carbonates (Figure 7.6)" - Western Atlas Chart 7-80.
    "carbonate": {"a": 0.62, "m": 2.15},
}

X_AXES = ("rho_b", "dt", "porosity")
_X_UNIT = {"rho_b": "g/cm3", "dt": "usec/ft", "porosity": "v/v"}

# Physically impossible input bands. These raise ValueError, not Refusal:
# a bulk density of 6 g/cm3 is a bad argument, not an unanswerable question.
_X_LIMITS = {"rho_b": (0.0, 5.0), "dt": (0.0, 300.0), "porosity": (-0.5, 1.0)}

# --- thresholds that are ours, not Asquith's -------------------------------
# #44 states only "lowest R_wa" and "greater than the minimum" with no cutoff.
# 2.0 corresponds to Sw = (1/2)^(1/2) = 0.707 at n = 2. It reproduces Asquith's
# own wet/hydrocarbon split of Table 7.4 (wet R_wa 0.031-0.046, hydrocarbon
# 1.80-2.02), and every run that uses it is flagged.
DEFAULT_WET_RWA_RATIO = 2.0
# Table 7.3: "A wide range of porosity must be present to positively determine a
# water-bearing line." Asquith supplies no number; below MIN we refuse, below
# CAVEAT we flag using his own words about this very example.
MIN_WET_POROSITY_SPREAD = 0.03
CAVEAT_WET_POROSITY_SPREAD = 0.10
# #44: "In low-porosity zones (less than about 10% porosity), the R_wa value is
# lower than the actual R_w value." This one IS sourced.
LOW_POROSITY_RWA = 0.10
# How far the free-fit x-intercept may sit from the supplied matrix value before
# the disagreement is worth reporting. Ours.
MATRIX_DISAGREEMENT = {"rho_b": 0.05, "dt": 2.0, "porosity": 0.02}


@dataclass(frozen=True)
class HinglePoint:
    """One plotted zone. Every number on it is a Quantity, never a float."""

    index: int
    x: float
    rt: float
    water_bearing: bool
    porosity: Quantity
    rwa: Quantity | None
    ro: Quantity | None
    sw: Quantity | None
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class HinglePlot:
    """Rw and the per-point porosities together, which is what the plot is.

    The catalog entry for #95 says the tool "solves porosity and Rw together",
    and the source agrees: Rw is the slope of the wet line in porosity units, so
    it is not interpretable without the porosity scale that produced it, and the
    per-point Sw is not interpretable without Rw.
    """

    rw: Quantity
    points: tuple[HinglePoint, ...]
    wet_indices: tuple[int, ...]
    slope: Quantity
    matrix_estimate: Quantity | None = None
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    @property
    def porosity(self) -> tuple[Quantity, ...]:
        return tuple(p.porosity for p in self.points)

    @property
    def water_saturation(self) -> tuple[Quantity | None, ...]:
        return tuple(p.sw for p in self.points)


def _resolve_matrix(x_axis: str, matrix_value: float | None,
                    lithology: str | Sequence[str] | None,
                    fluid: str) -> tuple[float | None, float | None, dict[str, Any],
                                         tuple[str, ...], Refusal | None]:
    """Matrix and fluid constants for the porosity axis, or a refusal."""
    assumptions: dict[str, Any] = {"fluid": fluid}
    flags: list[str] = []
    if fluid not in FLUID:
        raise ValueError(f"unknown fluid {fluid!r}; known: {sorted(FLUID)}")

    if lithology is not None and not isinstance(lithology, str):
        names = [str(x) for x in lithology]
        if len(set(names)) > 1:
            return None, None, assumptions, (), Refusal(
                reason=("Hingle plot given more than one lithology "
                        f"({', '.join(names)}); the plot has a single matrix point and "
                        "a single grid, and Table 7.3 requires lithology to be constant "
                        "over the intervals compared"),
                needed=("one lithology per plot; split the interval and plot separately",),
                source=CROSSPLOT_LIMITS)
        lithology = names[0] if names else None

    if x_axis == "porosity":
        if matrix_value is not None or lithology is not None:
            flags.append("porosity axis: the supplied matrix value is not used, "
                         "porosity was given directly")
        return None, None, assumptions, tuple(flags), None

    if matrix_value is None and lithology is None:
        return None, None, assumptions, (), Refusal(
            reason=("no matrix value: the porosity axis of a Hingle plot cannot be "
                    "entered without rho_ma or dt_ma, and this tool does not default one"),
            needed=("matrix_value (rho_ma g/cm3 or dt_ma usec/ft), or a lithology to "
                    "resolve through matrix_constant_lookup",),
            source=HINGLE)
    if matrix_value is not None and lithology is not None:
        raise ValueError("give matrix_value or lithology, not both")

    if matrix_value is None:
        consts = matrix_constant_lookup(str(lithology))  # raises on unknown lithology
        matrix_value = consts["rho_ma"] if x_axis == "rho_b" else consts["dt_ma"]
        assumptions["matrix_source"] = f"matrix_constant_lookup({lithology!r}), Asquith Table 4.1/4.2"
        flags.append(
            f"matrix taken from the {lithology} table entry ({matrix_value:g} "
            f"{_X_UNIT[x_axis]}); Asquith's own Hingle example (#51) instead reads the "
            "matrix off the wet line's x-intercept (2.65 g/cm3 for this sandstone), and "
            "the two differ by about one porosity unit")
    else:
        assumptions["matrix_source"] = "caller-supplied"
    assumptions["matrix_value"] = matrix_value

    if matrix_value <= 0:
        raise ValueError(f"matrix value must be positive, got {matrix_value}")
    fluid_value = FLUID[fluid]["rho_fl"] if x_axis == "rho_b" else FLUID[fluid]["dt_fl"]
    if x_axis == "rho_b" and fluid_value >= matrix_value:
        raise ValueError(
            f"fluid density {fluid_value} >= matrix density {matrix_value}; porosity undefined")
    if x_axis == "dt" and fluid_value <= matrix_value:
        raise ValueError(
            f"fluid transit time {fluid_value} <= matrix {matrix_value}; porosity undefined")
    assumptions["fluid_value"] = fluid_value
    return matrix_value, fluid_value, assumptions, tuple(flags), None


def _porosity(x: float, x_axis: str, matrix_value: float | None,
              fluid_value: float | None) -> tuple[float, str]:
    if x_axis == "porosity":
        return x, "porosity supplied directly"
    if x_axis == "rho_b":
        # Asquith Eq. 4.7.
        return (matrix_value - x) / (matrix_value - fluid_value), \
            "density porosity (Asquith Eq. 4.7)"
    # Wyllie time-average, Asquith Eq. 4.1.
    return (x - matrix_value) / (fluid_value - matrix_value), \
        "sonic porosity, Wyllie time-average (Asquith Eq. 4.1)"


def hingle_plot(points: Sequence[Sequence[float]],
                x_axis: str,
                m: float,
                a: float,
                clean_single_lithology: bool,
                *,
                matrix_value: float | None = None,
                lithology: str | Sequence[str] | None = None,
                fluid: str = "fresh",
                wet_indices: Sequence[int] | None = None,
                water_bearing_zone_present: bool = False,
                wet_rwa_ratio: float = DEFAULT_WET_RWA_RATIO,
                n: float = 2.0) -> HinglePlot | Refusal:
    """Hingle crossplot: Rw from the water-bearing line, plus porosity per point.

    `points` is a sequence of (x, Rt) pairs, x being bulk density, sonic transit
    time or porosity per `x_axis`. `a` and `m` come from the grid the points were
    plotted on (see HINGLE_GRIDS) and have no defaults, because the resistivity
    axis is scaled as (a/Rt)^(1/m) and choosing them silently would choose the
    chart. `clean_single_lithology` is the caller affirming Table 7.3's
    assumption; it is positional because it is not optional.

    Returns a HinglePlot, or a Refusal when the source's conditions are not met.
    Raises ValueError only for impossible arguments.
    """
    if x_axis not in X_AXES:
        raise ValueError(f"x_axis must be one of {X_AXES}, got {x_axis!r}")
    if not (m > 0):
        raise ValueError(f"cementation exponent m must be positive, got {m}")
    if not (a > 0):
        raise ValueError(f"tortuosity factor a must be positive, got {a}")
    if not (n > 0):
        raise ValueError(f"saturation exponent n must be positive, got {n}")
    if not (wet_rwa_ratio > 1.0):
        raise ValueError(f"wet_rwa_ratio must exceed 1.0, got {wet_rwa_ratio}")

    lo, hi = _X_LIMITS[x_axis]
    parsed: list[tuple[float, float]] = []
    for i, point in enumerate(points):
        x, rt = float(point[0]), float(point[1])
        if not (rt > 0):
            raise ValueError(f"point {i}: Rt = {rt} ohm-m is not positive")
        if not (lo < x < hi):
            raise ValueError(
                f"point {i}: {x_axis} = {x} {_X_UNIT[x_axis]} is outside the physical "
                f"range ({lo}, {hi})")
        parsed.append((x, rt))

    if not clean_single_lithology:
        return Refusal(
            reason=("the caller has not affirmed a clean, single-lithology interval; "
                    "Table 7.3 requires that formation lithology and water resistivity "
                    "be constant over the intervals compared on the plot"),
            needed=("an interval of one lithology, clean (shale-free), with constant Rw; "
                    "otherwise split it and plot each part separately",),
            source=CROSSPLOT_LIMITS)

    if len(parsed) < 2:
        return Refusal(
            reason=(f"{len(parsed)} point(s) supplied; a water-bearing line cannot be "
                    "determined from fewer than two"),
            needed=("at least two zones, spanning a range of porosity (Table 7.3)",),
            source=CROSSPLOT_LIMITS)

    matrix_value, fluid_value, assumptions, matrix_flags, refusal = _resolve_matrix(
        x_axis, matrix_value, lithology, fluid)
    if refusal is not None:
        return refusal

    flags: list[str] = list(matrix_flags)
    phis: list[float] = []
    ys: list[float] = []
    rwas: list[float | None] = []
    phi_method = ""
    for x, rt in parsed:
        phi, phi_method = _porosity(x, x_axis, matrix_value, fluid_value)
        phis.append(phi)
        ys.append((a / rt) ** (1.0 / m))          # Eq. 7.28, left-hand side
        rwas.append(rt * phi ** m / a if phi > 0 else None)  # Eq. 7.16

    # --- which points are water-bearing ------------------------------------
    if wet_indices is not None:
        wet = sorted({int(i) for i in wet_indices})
        for i in wet:
            if not 0 <= i < len(parsed):
                raise ValueError(f"wet index {i} is out of range for {len(parsed)} points")
        assumptions["wet_selection"] = "declared by caller"
    else:
        if not water_bearing_zone_present:
            return Refusal(
                reason=("no water-bearing zone identified: a Hingle plot fitted through "
                        "hydrocarbon-bearing points returns a low Rw and optimistic "
                        "saturations that look entirely reasonable, and nothing in Rt "
                        "and porosity can tell the two cases apart (Asquith #44)"),
                needed=("wet_indices naming the water-bearing zones, or "
                        "water_bearing_zone_present=True on independent evidence "
                        "(DST water recovery, produced water, a known wet sand)",),
                source=RWA_METHOD)
        known = [(i, r) for i, r in enumerate(rwas) if r is not None]
        if not known:
            return Refusal(
                reason=("no point has positive porosity, so no apparent water resistivity "
                        "can be computed and no water-bearing trend can be identified"),
                needed=("a matrix value consistent with the log readings",),
                source=RWA_METHOD)
        rwa_min = min(r for _, r in known)
        cutoff = rwa_min * wet_rwa_ratio
        wet = [i for i, r in known if r <= cutoff]
        assumptions["wet_selection"] = (
            f"minimum-Rwa cluster (Asquith Eq. 7.16): Rwa <= {wet_rwa_ratio} x "
            f"{rwa_min:.6g} ohm-m")
        flags.append(
            f"water-bearing points selected mechanically at Rwa <= {wet_rwa_ratio}x the "
            "minimum; Asquith states only 'lowest Rwa' and gives no cutoff, so this "
            "ratio is a house threshold, not a published one")

    if not wet:
        return Refusal(
            reason=("no water-bearing points were declared, so there is no water-bearing "
                    "line to fit; Rw is the slope of that line and nothing else in the "
                    "plot determines it"),
            needed=("wet_indices naming at least two water-bearing zones of different "
                    "porosity, or water_bearing_zone_present=True to let the minimum-Rwa "
                    "cluster (Asquith Eq. 7.16) select them",),
            source=CROSSPLOT_LIMITS)

    usable = [i for i in wet if phis[i] > 0]
    if len(usable) < len(wet):
        flags.append(
            f"{len(wet) - len(usable)} declared water-bearing point(s) have porosity <= 0 "
            "and were excluded from the fit; the matrix value may be wrong")
    if not usable:
        return Refusal(
            reason=("every water-bearing point has porosity <= 0 at the supplied matrix "
                    f"value ({matrix_value} {_X_UNIT[x_axis]}); the wet line has no slope"),
            needed=("a matrix value consistent with the log readings, or an interval that "
                    "is actually porous",),
            source=HINGLE)
    if len(usable) < 2:
        return Refusal(
            reason=(f"{len(usable)} water-bearing point(s) with positive porosity; one "
                    "point plus the matrix intercept fixes a line arithmetically but does "
                    "not determine one - Table 7.3: 'A wide range of porosity must be "
                    "present to positively determine a water-bearing line'"),
            needed=("at least two water-bearing zones of different porosity; with a single "
                    "wet reading use Eq. 7.29 directly (Rw = Ro*phi^m/a)",),
            source=CROSSPLOT_LIMITS)

    spread = max(phis[i] for i in usable) - min(phis[i] for i in usable)
    if spread < MIN_WET_POROSITY_SPREAD:
        return Refusal(
            reason=(f"the water-bearing points span {spread:.4f} v/v of porosity; that is "
                    "too narrow to determine the wet line's slope, and Table 7.3 requires "
                    "a wide range of porosity"),
            needed=(f"water-bearing zones spanning at least {MIN_WET_POROSITY_SPREAD} v/v "
                    "porosity (this floor is ours, not Asquith's - he states the "
                    "requirement without a number)",),
            source=CROSSPLOT_LIMITS)
    if spread < CAVEAT_WET_POROSITY_SPREAD:
        flags.append(
            f"water-bearing porosity range is only {spread:.3f} v/v; Asquith's caption on "
            "this same plot warns that with a limited porosity range and scatter, other "
            "matrix values and other m from 1.8 to 2.15 could equally be justified")
    if any(phis[i] < LOW_POROSITY_RWA for i in usable):
        flags.append(
            f"water-bearing points below {LOW_POROSITY_RWA:g} v/v porosity are included; "
            "Asquith #44 notes Rwa reads low below about 10% porosity, which biases both "
            "the wet-point selection and the fit")

    # --- the wet line: least squares through the matrix point ---------------
    sxy = sum(phis[i] * ys[i] for i in usable)
    sxx = sum(phis[i] ** 2 for i in usable)
    k = sxy / sxx                        # y = k*phi, Eq. 7.28 at Sw = 1
    rw_value = k ** (-m)                 # equivalently Eq. 7.29 at any phi on the line

    assumptions.update({"a": a, "m": m, "n": n, "x_axis": x_axis,
                        "porosity_method": phi_method,
                        "wet_line": "least squares through the matrix point (phi = 0), "
                                    "Asquith draws it 'through the cluster of points'"})

    slope_q = Quantity(
        k, f"({_X_UNIT[x_axis]} porosity)^-1" if x_axis == "porosity" else "1/v/v",
        "slope of the water-bearing line, y = (a/Rt)^(1/m) vs porosity (Asquith Eq. 7.28)",
        HINGLE,
        inputs={"sum_phi_y": sxy, "sum_phi2": sxx, "n_wet": len(usable)},
        assumptions=dict(assumptions))

    out_points: list[HinglePoint] = []
    sw_over_one = 0
    for i, (x, rt) in enumerate(parsed):
        phi = phis[i]
        pflags: list[str] = []
        if phi <= 0:
            pflags.append("porosity <= 0 at the supplied matrix value")
        phi_q = Quantity(phi, "v/v", phi_method, HINGLE,
                         inputs={x_axis: x},
                         assumptions={"matrix_value": matrix_value,
                                      "fluid_value": fluid_value},
                         flags=tuple(pflags))
        rwa_q = (Quantity(rwas[i], "ohm-m", "apparent water resistivity (Asquith Eq. 7.16)",
                          RWA_METHOD, inputs={"Rt": rt, "phi": phi},
                          assumptions={"a": a, "m": m})
                 if rwas[i] is not None else None)
        ro_q = sw_q = None
        if phi > 0:
            ro = a / (k * phi) ** m
            ro_q = Quantity(ro, "ohm-m",
                            "resistivity of the water-bearing line at this porosity "
                            "(Asquith Eq. 7.29 rearranged, Ro = a*Rw/phi^m)",
                            HINGLE, inputs={"phi": phi, "Rw": rw_value},
                            assumptions={"a": a, "m": m})
            sw = (ro / rt) ** (1.0 / n)
            swf: list[str] = []
            if sw > 1.0:
                sw_over_one += 1
                swf.append("Sw > 1.0 - the point lies above the fitted wet line")
            sw_q = Quantity(sw, "v/v", "Sw = (Ro/Rt)^(1/n) (Asquith Eq. 7.27)", HINGLE,
                            inputs={"Ro": ro, "Rt": rt},
                            assumptions={"n": n}, flags=tuple(swf))
        out_points.append(HinglePoint(i, x, rt, i in usable or i in wet,
                                      phi_q, rwa_q, ro_q, sw_q, tuple(pflags)))
    if sw_over_one:
        flags.append(f"{sw_over_one} point(s) return Sw > 1.0; scatter about the wet line, "
                     "not clipped")

    # --- diagnostic: the plot's own estimate of the matrix value ------------
    matrix_est = None
    if len(usable) >= 3:
        xs = [parsed[i][0] for i in usable]
        yy = [ys[i] for i in usable]
        mx = sum(xs) / len(xs)
        my = sum(yy) / len(yy)
        s_xx = sum((v - mx) ** 2 for v in xs)
        s_xy = sum((v - mx) * (w - my) for v, w in zip(xs, yy))
        if s_xx > 0 and s_xy != 0:
            slope = s_xy / s_xx
            intercept = my - slope * mx
            x0 = -intercept / slope
            mflags: list[str] = [
                "diagnostic only: this free fit is not used for the porosities or Rw, "
                "which use the matrix value supplied"]
            if matrix_value is not None and \
                    abs(x0 - matrix_value) > MATRIX_DISAGREEMENT[x_axis]:
                mflags.append(
                    f"the wet line's own x-intercept ({x0:.4g} {_X_UNIT[x_axis]}) disagrees "
                    f"with the matrix value used ({matrix_value:g}); Table 7.3 makes this "
                    "intercept the Hingle plot's advertised product, so the disagreement "
                    "is a real signal about the matrix, the lithology, or the scatter")
            matrix_est = Quantity(
                x0, _X_UNIT[x_axis],
                "x-intercept of the unconstrained water-bearing line - the matrix value "
                "the plot itself predicts (Asquith Table 7.3, #47 p. 123)",
                CROSSPLOT_LIMITS,
                inputs={"slope": slope, "intercept": intercept, "n_wet": len(usable)},
                assumptions={"a": a, "m": m},
                flags=tuple(mflags))

    rw_q = Quantity(
        rw_value, "ohm-m",
        "Rw from the Hingle water-bearing line, Rw = Ro*phi^m/a (Asquith Eq. 7.29) with "
        "the line fitted as y = (a/Rt)^(1/m) = Rw^(-1/m) * phi (Eq. 7.28 at Sw = 1)",
        HINGLE,
        inputs={"wet_points": tuple(usable), "slope_k": k,
                "Rt": tuple(parsed[i][1] for i in usable),
                "phi": tuple(phis[i] for i in usable)},
        assumptions=dict(assumptions),
        flags=tuple(flags) + ("Rw is at formation temperature, as read; convert with "
                              "resistivity_at_temperature if the points were not at Tf",))

    return HinglePlot(rw=rw_q, points=tuple(out_points), wet_indices=tuple(usable),
                      slope=slope_q, matrix_estimate=matrix_est, flags=tuple(flags),
                      assumptions=dict(assumptions))
