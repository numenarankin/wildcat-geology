"""Assumption bookkeeping and uncertainty bands: #68, #69, #70.

All three are plumbing — no equation is owed — so the contracts live in
`specs/68-assumption_registry.md`, `specs/69-sensitivity_sweep.md` and
`specs/70-uncertainty_propagate.md`. Four decisions here are not obvious from the
code.

**The registry is fed, never filled in.** `assumption_registry` reads
`Quantity.assumptions`, the dict every tool in this codebase already writes, and
has no `register()` entry point. A hand-maintained side table would be a second
place the truth lives, and two answers to one question is the reconciliation
failure this project treats as a bug in itself. The cost is that a tool which
fails to declare an assumption is invisible to the ledger; that is the tool
author's defect and the registry does not paper over it.

**Every grid point is evaluated, because monotonicity is not assumed.** The
obvious sweep is `f(low)` and `f(high)`. It is wrong for any function with an
interior extremum, and wrong quietly — the band comes back too narrow with
nothing on it to say so. So the whole grid is evaluated and `interior_extremum`
is reported as a finding when the extremes are not at the ends.

**Sampling, not interval arithmetic, and the band is not an enclosure.**
Interval arithmetic works on expressions; what is propagated through here are
compiled tools with branches, table lookups and refusal gates, so there is no
expression to rewrite. Shadowing each tool with an interval version would
duplicate every equation in the codebase. Sampling is therefore forced, and it
has two failures which are written onto every result's `method` rather than
buried: it can miss an extremum between grid points (band too narrow) and it
treats inputs as independent (band too wide when they are correlated).

**Refusals are counted, never dropped.** A swept tool that declines at some
samples produces a partial band. Reporting the survivors' spread as if it were
the answer would understate the truth, so coverage is on the result and `method`
leads with `PARTIAL:`.
"""
from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable

from .result import Quantity, Range, Refusal

# No citation is owed; provenance travels on each ledger row instead.
PLUMBING = "not applicable - plumbing; provenance is carried per row"

# 21 points: odd, so the midpoint is on the grid, and 5% of the range per step.
DEFAULT_SWEEP_SAMPLES = 21
# 5 per input: cost is samples**k here, not samples, so resolution is traded for
# dimensionality deliberately rather than by accident.
DEFAULT_PROPAGATE_SAMPLES = 5
# A tool that quietly runs 50,000 evaluations inside a chat turn is broken.
MAX_EVALUATIONS = 10000
# Distinct refusal reasons quoted on a partial band before it is elided.
MAX_QUOTED_REASONS = 3

_SAMPLING_CAVEAT = (
    "explicit sampling on a stated grid - not interval arithmetic; the band is a "
    "lower bound on the true spread and is widened by any correlation between inputs"
)


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------
def _dedup(items: Iterable[Any]) -> list[Any]:
    """Order-preserving dedup. Order-preserving so the output is reproducible."""
    seen: set[Any] = set()
    out: list[Any] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _check_bounds(name: str, low: float, high: float) -> None:
    if not (math.isfinite(low) and math.isfinite(high)):
        raise ValueError(f"{name}: sweep bounds must be finite, got [{low}, {high}]")
    if low > high:
        raise ValueError(f"{name}: low {low} is above high {high}")


def _normalise_samples(samples: int, name: str) -> tuple[int, int]:
    """(used, requested). An even count omits the midpoint, so it is raised."""
    if isinstance(samples, bool) or not isinstance(samples, int):
        raise ValueError(f"{name}: samples must be an int, got {samples!r}")
    if samples < 3:
        raise ValueError(
            f"{name}: samples must be at least 3 (endpoints plus one interior point); "
            "endpoint-only evaluation is the defect this tool exists to avoid"
        )
    return (samples + 1 if samples % 2 == 0 else samples), samples


def _grid(low: float, high: float, n: int) -> list[float]:
    """Closed-form uniform grid, inclusive of both ends.

    Computed as low + i*(high-low)/(n-1) rather than by repeated addition, so no
    drift accumulates and the last point is exactly `high`.
    """
    if low == high:
        return [low]
    return [low + i * (high - low) / (n - 1) for i in range(n)]


def _fmt(value: float) -> str:
    return f"{value:g}"


@dataclass(frozen=True)
class _GridRun:
    """Outcome of evaluating a callable over a grid of coordinate tuples."""

    ok: list[tuple[tuple[float, ...], float]]
    refusals: list[Refusal]
    unit: str
    error: Refusal | None


def _run_grid(fn: Callable[..., Any], label: str, names: Sequence[str],
              points: Sequence[tuple[float, ...]],
              fixed: Mapping[str, Any],
              band_clause: str = "propagating through a band is out of scope for v1"
              ) -> _GridRun:
    """Evaluate `fn` at every point. Refusals are collected, never dropped.

    `band_clause` is the caller's own wording for the Range-return refusal:
    #69's refusal table says "sweeping a band ... sensitivity_sweep v1" and
    #70's says "propagating through a band". A shared helper that named one
    operation in both would tell a caller of #69 that #70 declined, which is a
    refusal an operator cannot act on.
    """
    ok: list[tuple[tuple[float, ...], float]] = []
    refusals: list[Refusal] = []
    unit = ""
    for coords in points:
        kwargs = dict(fixed)
        kwargs.update({name: value for name, value in zip(names, coords)})
        result = fn(**kwargs)
        if isinstance(result, Refusal):
            refusals.append(result)
            continue
        if isinstance(result, Range):
            return _GridRun([], [], "", Refusal(
                reason=(f"{label} returns a band; {band_clause} - taking its midpoint or "
                        "its endpoints would invent a number"),
                needed=("a function returning a Quantity",), source=PLUMBING))
        if not isinstance(result, Quantity):
            return _GridRun([], [], "", Refusal(
                reason=(f"{label} returned {type(result).__name__}, which carries no "
                        "provenance"),
                needed=("a tool returning Quantity or Refusal",), source=PLUMBING))
        if not ok:
            unit = result.unit
        elif result.unit != unit:
            return _GridRun([], [], "", Refusal(
                reason=(f"{label} returned mixed units across the grid "
                        f"({unit!r}, {result.unit!r}); the band would be dimensionless "
                        "nonsense"),
                needed=("a function whose unit does not depend on the swept input",),
                source=PLUMBING))
        ok.append((coords, float(result.value)))
    return _GridRun(ok, refusals, unit, None)


def _all_refused(label: str, refusals: Sequence[Refusal], where: str) -> Refusal:
    reasons = _dedup(r.reason for r in refusals)
    needed = _dedup(item for r in refusals for item in r.needed)
    quoted = "; ".join(reasons[:MAX_QUOTED_REASONS])
    if len(reasons) > MAX_QUOTED_REASONS:
        quoted += f"; (+{len(reasons) - MAX_QUOTED_REASONS} more)"
    return Refusal(
        reason=f"{label} refused at all {len(refusals)} samples over {where}: {quoted}",
        needed=tuple(needed),
        source=refusals[0].source or PLUMBING,
    )


def _partial_clause(n_refused: int, n_total: int, refusals: Sequence[Refusal]) -> str:
    reasons = _dedup(r.reason for r in refusals)
    quoted = "; ".join(reasons[:MAX_QUOTED_REASONS])
    if len(reasons) > MAX_QUOTED_REASONS:
        quoted += f"; (+{len(reasons) - MAX_QUOTED_REASONS} more)"
    return (f"PARTIAL: {n_refused} of {n_total} samples refused ({quoted}); the true "
            "band over the stated range may be wider. ")


# ---------------------------------------------------------------------------
# #68 - assumption_registry
# ---------------------------------------------------------------------------
def _kind(value: Any) -> str:
    """`True == 1` and `2 == 2.0` in Python; a bool matching an int is a type
    error wearing a match, so the kind is part of the comparison key."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _compare_key(value: Any) -> tuple[str, Any]:
    kind = _kind(value)
    if kind == "number":
        return (kind, float(value))
    if kind == "bool":
        return (kind, bool(value))
    try:
        hash(value)
    except TypeError:
        return (kind, repr(value))
    return (kind, value)


def assumption_registry(results: Any, overrides: Mapping[str, Any] | None = None):
    """#68 - the ledger of every assumption in play, read off the results.

    Fed from `Quantity.assumptions` and nothing else. It reports conflicts rather
    than refusing on them: a ledger that refuses suppresses the honest rows and
    leaves the operator with less than they had. The one thing it will not do is
    certify a value it cannot trace, which is its only refusal.
    """
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, Mapping):
        raise ValueError("overrides must be a mapping of assumption name to value")

    if isinstance(results, Mapping):
        items = [(str(key), value) for key, value in results.items()]
    elif isinstance(results, Iterable) and not isinstance(results, (str, bytes)):
        items = []
        for result in results:
            label = getattr(result, "method", "") or repr(result)
            items.append((str(label), result))
    else:
        raise ValueError("results must be an iterable or a mapping of results")

    n_quantities = n_ranges = n_refusals = 0
    rows: list[dict[str, Any]] = []
    for label, result in items:
        if isinstance(result, Quantity):
            n_quantities += 1
            for name, value in result.assumptions.items():
                row: dict[str, Any] = {
                    "name": str(name),
                    "value": value,
                    "label": label,
                    "source": result.source,
                    "method": result.method,
                    "status": "default",
                }
                if name in overrides:
                    stated = overrides[name]
                    row["override_value"] = stated
                    row["status"] = ("overridden"
                                     if _compare_key(stated) == _compare_key(value)
                                     else "override_conflict")
                rows.append(row)
        elif isinstance(result, Range):
            n_ranges += 1
        elif isinstance(result, Refusal):
            n_refusals += 1
        else:
            return Refusal(
                reason=(f"an object with no provenance was submitted to the registry: "
                        f"{result!r}; the registry cannot certify what it cannot trace"),
                needed=("wrap the value in a Quantity carrying its method and source",
                        "or route it through provenance_audit [#67]"),
                source=PLUMBING,
            )

    rows.sort(key=lambda r: (r["name"], r["label"], repr(r["value"])))

    by_name: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_name.setdefault(row["name"], []).append(row)

    n_defaults = sum(1 for r in rows if r["status"] == "default")
    n_overridden = sum(1 for r in rows if r["status"] == "overridden")
    n_conflicts = sum(1 for r in rows if r["status"] == "override_conflict")

    flags: list[str] = []
    if n_defaults:
        flags.append(f"{n_defaults} of {len(rows)} assumptions in play are defaults "
                     "the user never stated")
    for row in rows:
        if row["status"] == "override_conflict":
            flags.append(f"override_conflict: {row['name']} - user stated "
                         f"{row['override_value']!r}, {row['label']} used "
                         f"{row['value']!r}")
    for name in sorted(overrides):
        if name not in by_name:
            flags.append(f"override_not_consumed: {name} - no result declared it")
    for name in sorted(by_name):
        distinct = _dedup([(_compare_key(r["value"]), repr(r["value"]), r["label"])
                           for r in by_name[name]])
        seen_keys = _dedup([entry[0] for entry in distinct])
        if len(seen_keys) > 1:
            shown = _dedup([f"{entry[1]} ({entry[2]})" for entry in distinct])
            flags.append(f"assumption_conflict: {name} - " + " vs ".join(sorted(shown)))
    if not rows:
        flags.append("no result carried any assumptions")
    if n_ranges or n_refusals:
        flags.append(f"{n_ranges + n_refusals} results carried no assumption ledger "
                     "(Range/Refusal)")

    return Quantity(
        value=float(len(rows)),
        unit="assumptions",
        method="assumption_registry v1",
        source=PLUMBING,
        inputs={
            "entries": rows,
            "n_distinct_names": len(by_name),
            "n_results": len(items),
            "n_quantities": n_quantities,
            "n_ranges": n_ranges,
            "n_refusals": n_refusals,
            "n_defaults": n_defaults,
            "n_overridden": n_overridden,
            "n_override_conflicts": n_conflicts,
        },
        assumptions={
            "fed_from": "Quantity.assumptions only - nothing is registered by hand",
            "comparison": "by (kind, value); bool is not int, int is not str",
        },
        flags=tuple(flags),
    )


# ---------------------------------------------------------------------------
# #69 - sensitivity_sweep
# ---------------------------------------------------------------------------
def expose_constant(fn: Callable[..., Any], table: dict, path: Sequence[str],
                    arg_name: str) -> Callable[..., Any]:
    """Adapter: drive a module-level constant as a keyword argument of `fn`.

    `density_porosity` derives rho_ma from `lithology`, so the catalogued
    contested-constant sweep is not reachable through the public tool. This wraps
    it so the real tool runs - its equation, its DRHO gate, its flags - with one
    table entry set for the duration of a single call and restored afterwards.

    Weaknesses, stated because they are real: it mutates module state, so it is
    not thread-safe or re-entrant, and it depends on the table's layout. It is an
    adapter for a missing feature. The right fix is for the tool to accept the
    override so it lands in `assumptions` where the registry can see it.

    **`density_porosity` no longer needs this.** It now takes `rho_ma` and
    `rho_ma_source` directly, and both land in `assumptions`, so sweep the tool
    itself rather than wrapping it:

        sensitivity_sweep(density_porosity, "rho_ma", 2.644, 2.65,
                          fixed={"rho_b": 2.40, "lithology": "sandstone"})

    That reproduces the catalog's contested-constant figures (0.31 pu on
    sandstone, 1.04 on salt) without touching shared state. This adapter is kept
    only for tools that still derive a constant internally with no override; when
    the last of those gains one, delete it.
    """
    if not path:
        raise ValueError("path must name at least one key")

    def wrapped(**kwargs: Any) -> Any:
        if arg_name not in kwargs:
            raise ValueError(f"{arg_name} must be supplied to the exposed constant")
        value = kwargs.pop(arg_name)
        node: Any = table
        for key in path[:-1]:
            node = node[key]
        leaf = path[-1]
        saved = node[leaf]
        node[leaf] = value
        try:
            return fn(**kwargs)
        finally:
            node[leaf] = saved

    wrapped.__name__ = getattr(fn, "__name__", "fn")
    return wrapped


def sensitivity_sweep(fn: Callable[..., Any], input_name: str, low: float, high: float,
                      range_source: str, *, fixed: Mapping[str, Any] | None = None,
                      samples: int = DEFAULT_SWEEP_SAMPLES, input_unit: str = "",
                      label: str | None = None):
    """#69 - recompute an output across the plausible range of one input.

    The whole grid is evaluated, not just the endpoints: an interior extremum
    would otherwise come back as a band that is too narrow with nothing on it to
    say so. `range_source` is required for the same reason `archie_sw` requires
    an Rw provenance - a band whose width nobody vouched for is a guess wearing
    error bars.
    """
    fixed = dict(fixed or {})
    label = label or getattr(fn, "__name__", "the function under test")
    if input_name in fixed:
        raise ValueError(f"{input_name} is both swept and fixed; state one value for it")
    _check_bounds(input_name, low, high)
    n_used, n_requested = _normalise_samples(samples, input_name)

    if not (range_source or "").strip():
        return Refusal(
            reason=("a sweep range with no stated provenance is not a range; refusing "
                    "to publish a band whose width nobody vouched for"),
            needed=("the corpus anchors, measurement or stated tolerance the range "
                    "comes from",),
            source=PLUMBING)
    if low == high:
        return Refusal(
            reason=f"the stated range has zero width ({_fmt(low)}); there is nothing to sweep",
            needed=("two distinct plausible values, or the two sources that disagree",),
            source=range_source)

    xs = _grid(low, high, n_used)
    run = _run_grid(fn, label, [input_name], [(x,) for x in xs], fixed,
                    band_clause="sweeping a band is out of scope for sensitivity_sweep v1")
    if run.error is not None:
        return run.error
    unit_txt = f" {input_unit}" if input_unit else ""
    where = f"{input_name} = [{_fmt(low)}, {_fmt(high)}]{unit_txt}"
    if not run.ok:
        return _all_refused(label, run.refusals, where)

    values = [value for _, value in run.ok]
    band_low, band_high = min(values), max(values)
    argmin_x = min(run.ok, key=lambda item: item[1])[0][0]
    argmax_x = max(run.ok, key=lambda item: item[1])[0][0]
    first_x, first_value = run.ok[0]
    last_x, last_value = run.ok[-1]
    tol = 1e-12 * max(1.0, abs(first_value), abs(last_value))

    non_decreasing = all(b >= a - tol for a, b in zip(values, values[1:]))
    non_increasing = all(b <= a + tol for a, b in zip(values, values[1:]))
    monotonic = non_decreasing or non_increasing
    endpoint_lo, endpoint_hi = min(first_value, last_value), max(first_value, last_value)
    interior = band_low < endpoint_lo - tol or band_high > endpoint_hi + tol

    clauses: list[str] = []
    if n_requested != n_used:
        clauses.append(f"samples raised from {n_requested} to {n_used} so the midpoint "
                       "is on the grid")
    clauses.append("monotonic" if monotonic else "NON-MONOTONIC across the swept range")
    if interior:
        outlier_x = argmin_x if band_low < endpoint_lo - tol else argmax_x
        clauses.append(f"INTERIOR EXTREMUM at {input_name} = {_fmt(outlier_x)} lies "
                       "outside the endpoint values - an endpoint-only sweep would have "
                       "understated this band")
    else:
        clauses.append("extremes at the endpoints")
    if first_x[0] != low or last_x[0] != high:
        clauses.append(f"the range endpoints refused; the band spans only "
                       f"[{_fmt(first_x[0])}, {_fmt(last_x[0])}]")

    method = (f"sensitivity_sweep of {label} over {where}, {n_used}-point uniform grid; "
              + "; ".join(clauses))
    if run.refusals:
        method = _partial_clause(len(run.refusals), n_used, run.refusals) + method

    return Range(
        low=band_low, high=band_high, unit=run.unit, method=method, source=range_source,
        members={
            "sweep_low": float(low), "sweep_high": float(high),
            "samples": float(n_used), "samples_requested": float(n_requested),
            "n_ok": float(len(run.ok)), "n_refused": float(len(run.refusals)),
            "coverage": len(run.ok) / n_used,
            "endpoint_low_value": first_value, "endpoint_high_value": last_value,
            "argmin_x": argmin_x, "argmax_x": argmax_x,
            "monotonic": 1.0 if monotonic else 0.0,
            "interior_extremum": 1.0 if interior else 0.0,
        },
    )


# ---------------------------------------------------------------------------
# #70 - uncertainty_propagate
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class InputRange:
    """One uncertain input, with the provenance of its range.

    `source` is not optional. A band assembled from ranges nobody vouched for is
    a fabricated error bar, which is worse than a point value because it looks
    careful.
    """

    name: str
    low: float
    high: float
    source: str
    samples: int = DEFAULT_PROPAGATE_SAMPLES
    unit: str = ""


def uncertainty_propagate(fn: Callable[..., Any], inputs: Sequence[InputRange], *,
                          fixed: Mapping[str, Any] | None = None,
                          label: str | None = None,
                          max_evaluations: int = MAX_EVALUATIONS):
    """#70 - carry several input ranges through a calculation.

    Explicit sampling on a full-factorial grid, chosen because interval
    arithmetic operates on expressions and what is propagated through here are
    compiled tools with branches and refusal gates. The method's two failures are
    written onto the result rather than argued away: it can miss an extremum
    between grid points, and it treats the inputs as independent.
    """
    fixed = dict(fixed or {})
    label = label or getattr(fn, "__name__", "the function under test")
    if not inputs:
        raise ValueError("uncertainty_propagate needs at least one InputRange")
    names = [item.name for item in inputs]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate input name in {names}")
    clash = sorted(set(names) & set(fixed))
    if clash:
        raise ValueError(f"{clash} are both uncertain and fixed; state one value for each")

    ordered = sorted(inputs, key=lambda item: item.name)
    axes: list[list[float]] = []
    counts: list[int] = []
    requested: list[int] = []
    for item in ordered:
        _check_bounds(item.name, item.low, item.high)
        if item.low == item.high:
            axes.append([item.low])
            counts.append(1)
            requested.append(1)
            continue
        used, req = _normalise_samples(item.samples, item.name)
        axes.append(_grid(item.low, item.high, used))
        counts.append(used)
        requested.append(req)

    blank = [item.name for item in ordered if not (item.source or "").strip()]
    if blank:
        return Refusal(
            reason=(f"input range {blank[0]!r} has no stated provenance; refusing to "
                    "publish a band whose width nobody vouched for"),
            needed=("the anchor, measurement or stated tolerance each range comes from",),
            source=PLUMBING)
    if all(item.low == item.high for item in ordered):
        return Refusal(
            reason=(f"no input carries any uncertainty; call {label} directly for a "
                    "point value"),
            needed=("at least one input whose low and high differ",),
            source=PLUMBING)

    n_eval = math.prod(counts)
    if n_eval > max_evaluations:
        return Refusal(
            reason=(f"{n_eval} evaluations requested ({'x'.join(str(c) for c in counts)}), "
                    f"above the {max_evaluations} cap; reduce samples per input or the "
                    "number of uncertain inputs"),
            needed=(f"a grid of at most {max_evaluations} points",),
            source=PLUMBING)

    axis_names = [item.name for item in ordered]
    points = [tuple(point) for point in itertools.product(*axes)]
    run = _run_grid(fn, label, axis_names, points, fixed)
    if run.error is not None:
        return run.error

    spans = ", ".join(
        f"{item.name}=[{_fmt(item.low)}, {_fmt(item.high)}]"
        f"{(' ' + item.unit) if item.unit else ''} ({count} pts)"
        for item, count in zip(ordered, counts))
    if not run.ok:
        return _all_refused(label, run.refusals, spans)

    values = [value for _, value in run.ok]
    band_low, band_high = min(values), max(values)
    argmin_coords = min(run.ok, key=lambda item: item[1])[0]
    argmax_coords = max(run.ok, key=lambda item: item[1])[0]

    def _is_corner(coords: tuple[float, ...]) -> bool:
        return all(value in (axis[0], axis[-1]) for value, axis in zip(coords, axes))

    interior = not (_is_corner(argmin_coords) and _is_corner(argmax_coords))

    clauses = [f"{n_eval} evaluations", _SAMPLING_CAVEAT]
    if any(r != c for r, c in zip(requested, counts) if r != 1):
        clauses.append("sample counts raised to odd values so each midpoint is on the grid")
    if interior:
        clauses.append("INTERIOR EXTREMUM - an extreme fell at a non-corner grid point, "
                       "so the response is not monotonic in every input and a "
                       "corner-only evaluation would have understated this band")
    else:
        clauses.append("extremes at box corners")
    method = f"uncertainty_propagate of {label} over {spans}; " + "; ".join(clauses)
    if run.refusals:
        method = _partial_clause(len(run.refusals), n_eval, run.refusals) + method

    members: dict[str, float] = {}
    for index, item in enumerate(ordered):
        members[f"{item.name}_low"] = float(item.low)
        members[f"{item.name}_high"] = float(item.high)
        members[f"{item.name}_samples"] = float(counts[index])
        members[f"argmin_{item.name}"] = argmin_coords[index]
        members[f"argmax_{item.name}"] = argmax_coords[index]
    members.update({
        "n_inputs": float(len(ordered)),
        "n_evaluations": float(n_eval),
        "n_ok": float(len(run.ok)),
        "n_refused": float(len(run.refusals)),
        "coverage": len(run.ok) / n_eval,
        "interior_extremum": 1.0 if interior else 0.0,
    })

    return Range(
        low=band_low, high=band_high, unit=run.unit, method=method,
        source="; ".join(sorted({item.source for item in ordered})),
        members=members,
    )
