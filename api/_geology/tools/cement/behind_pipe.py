"""#107 behind_pipe_isolation_check — competent cement between proposed
perforations and the nearest water zone.

Merge target: `tools/cement.py` (same module as #103/#104/#105/#106).

The Pilkington footage rule lives in ONE place in this codebase — #104
`isolation_length_check` — and this tool reads it from there. There is no
footage table below and there must never be one: the last transcription error in
this project survived because two copies of one table drifted and each looked
corroborated by the other. What #107 adds on top of #104 is the geometry (which
interval is between the perfs and the water pick, and in which direction), the
water-zone pick as a hard requirement, and the bond log's own validity gates.

Three outcomes, deliberately never blurred, because the wrong answer here
perforates into water:

  Quantity(1.0, "bool")  isolated - a sustained >=80% BI run between the perfs
                         and the water pick meets the Pilkington footage.
  Quantity(0.0, "bool")  NOT isolated - the log is valid, complete and gap-free
                         across that interval and no run reaches the footage.
                         A real answer, not an abstention.
  Refusal                cannot tell - an input is absent, gapped or unsourced.

See `specs/107-behind_pipe_isolation_check.md` for the quoted rule, the consumed
#104 contract, and the oracle.
"""
from __future__ import annotations

import inspect
import math
from typing import Any, Sequence

from ..result import Quantity, Refusal
from .isolation import (  # names #107 resolves from its own globals()
    PILKINGTON_BI_BASIS, PILKINGTON_REQUIRED_FT_AT_80PCT,
    gap_scan, pilkington_required_length_ft, sustained_bi_runs,
)
from .vdl import (  # #106's validity thresholds, read here and never copied
    CEMENT_TYPES, FAST_FORMATION_TRANSIT_US_PER_FT, GREEN_CEMENT_HOURS,
)

DRILLINGMANUAL = "13-cement-integrity/drillingmanual-cement-bond-log"
PETROWIKI_CBL = "13-cement-integrity/petrowiki-cement-bond-logs#2"
SPE_BOND_THEORY = "13-cement-integrity/spe-back-to-basics-bond-log-theory#0"

# ---------------------------------------------------------------------------
# Consumed from #104 `isolation_length_check`, resolved from the merged module
# namespace at call time. Contract documented in the spec. NOTHING here is a
# footage number; the table is #104's and is read, never copied.
# ---------------------------------------------------------------------------

# A function taking casing OD and returning the required footage at 80% BI.
_REQUIRED_FOOTAGE_FUNCS = (
    "pilkington_required_length_ft",
    "pilkington_required_footage_ft",
    "required_isolation_length_ft",
    "isolation_length_required_ft",
)
# Fallback: #104's verdict function, whose result carries `required_ft` in
# `inputs` (the shape the existing tools/cement.py already returns).
_VERDICT_FUNCS = ("isolation_length_check",)
# Last resort: #104's own module-level table object. Exact-match lookup only -
# interpolation policy belongs to #104, so an off-table OD refuses here.
_FOOTAGE_TABLES = (
    "PILKINGTON_REQUIRED_FT_AT_80PCT",
    "PILKINGTON_80PCT",
    "PILKINGTON_REQUIRED_FT_80PCT",
    "PILKINGTON_FOOTAGE_80PCT",
)
# A sustained-run scanner over a bond-index curve.
_RUN_SCANNER_FUNCS = (
    "sustained_bi_runs",
    "sustained_runs",
    "scan_sustained_runs",
    "bi_sustained_runs",
)
# #104's sampling-continuity scan: depth steps larger than one sample interval.
_GAP_SCAN_FUNCS = ("gap_scan", "depth_gap_scan", "scan_depth_gaps")

# ---------------------------------------------------------------------------
# Log-validity gates, consumed from #106 `vdl_classify`. A bond index computed
# on a log #106 would refuse is not evidence of isolation - and #106's numbers
# are #106's, so they are resolved from the merged namespace for exactly the
# reason the footage table is: two copies of a source number drift.
#
#   57 usec/ft  petrowiki-cement-bond-logs#2 - "Formations with transit times
#               less than casing (57 usec/ft) can cause problems when
#               interpreting the amplitude curves because the formation signal
#               can arrive in the amplitude gate."
#   48 hours    spe-back-to-basics-bond-log-theory#0 - "Rule of thumb is to not
#               run bond logs up to 48 hours after cementing". Green cement
#               reads HIGH amplitude, i.e. LOW bond index, so the bias is toward
#               a false "not isolated"; #107 still refuses rather than passing
#               the pessimistic answer through, because the operator has to be
#               able to tell "the cement is bad" from "the log was run early".
#   cement type #106's CEMENT_TYPES, whose False entries are the foam,
#               lightweight, low-density and microsphere systems the acoustic
#               interpretation is not valid for.
# ---------------------------------------------------------------------------
_FAST_FORMATION_NAMES = ("FAST_FORMATION_TRANSIT_US_PER_FT",
                         "FAST_FORMATION_TRANSIT_US_FT",
                         "CASING_TRANSIT_TIME_US_FT")
_GREEN_CEMENT_NAMES = ("GREEN_CEMENT_HOURS", "GREEN_CEMENT_WAIT_HOURS")
_CEMENT_TYPE_TABLES = ("CEMENT_TYPES", "CEMENT_TYPE_VALIDITY")

# ---------------------------------------------------------------------------
# House rules. Neither is in the corpus; both are data-completeness guards, not
# petrophysical thresholds, and both are recorded as open questions in the spec.
# ---------------------------------------------------------------------------

# Sampling continuity is #104's `gap_scan` rule, consumed not reinvented: a
# depth step larger than the curve's own median step means at least one sample
# is missing, and a run length measured across a hole in the data is not
# measured at all. The threshold is measured from the data, not chosen, so
# there is no invented number here. `max_gap_ft` lets a caller override it.

# Bond index outside this band inside the scanned interval is treated as an
# un-scrubbed null (LAS -999.25) rather than as poor bond. Refusing is the
# conservative direction: a null read as 0.0 would produce a confident wrong
# "not isolated". PROVISIONAL.
BI_PLAUSIBLE_MIN = -0.05
BI_PLAUSIBLE_MAX = 1.05

# The bond index the Pilkington rule is stated at is ALSO #104's to own. It is
# not redefined here: an 0.80 literal in this module would be a second copy of a
# source number, which is the drift this build keeps getting bitten by. Resolved
# from the merged namespace, like the footage table.
_BI_BASIS_NAMES = ("PILKINGTON_BI_BASIS", "PILKINGTON_BOND_INDEX_BASIS",
                   "PILKINGTON_BASIS_BI")

_METHOD = ("behind-pipe isolation: Pilkington footage of sustained bond index "
           "between the proposed perforations and the water-zone pick")

_SEAL_CAVEAT = (
    "meets the Pilkington footage criterion; not a proof of hydraulic seal - "
    "the same source warns a channelled high-strength cement can read like an "
    "unchannelled low-strength one, and a 3 ft amplitude curve cannot identify "
    "channelling (see #106 vdl_classify)"
)


# ---------------------------------------------------------------------------
# #104 resolution
# ---------------------------------------------------------------------------

def _call_flexible(fn, **kwargs):
    """Call `fn` with only the keyword arguments its signature accepts.

    #104 is written in parallel; this keeps a merge from breaking on an extra
    keyword while still failing loudly if a REQUIRED argument has no match.
    """
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):        # builtins / C callables
        return fn(**kwargs)
    accepts_var_kw = any(p.kind is inspect.Parameter.VAR_KEYWORD
                         for p in sig.parameters.values())
    if accepts_var_kw:
        return fn(**kwargs)
    allowed = {name for name, p in sig.parameters.items()
               if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                             inspect.Parameter.KEYWORD_ONLY)}
    return fn(**{k: v for k, v in kwargs.items() if k in allowed})


def _resolve(names: Sequence[str], predicate) -> tuple[str, Any] | tuple[None, None]:
    g = globals()
    for name in names:
        obj = g.get(name)
        if obj is not None and predicate(obj):
            return name, obj
    return None, None


def _interpolation_kwargs(interpolation: Any) -> dict[str, Any]:
    """Translate #107's single caller declaration into #104's two switches.

    The declaration is the caller's to make and own; #107 never turns one on by
    itself. `None` means undeclared, which is how an off-table OD comes back as
    a refusal.
    """
    if interpolation is None or interpolation is False:
        return {"allow_interpolation": False, "allow_extrapolation": False,
                "interpolation": None}
    if interpolation is True:
        return {"allow_interpolation": True, "allow_extrapolation": True,
                "interpolation": "declared"}
    token = str(interpolation).lower()
    inter = any(w in token for w in ("interp", "linear", "between", "both"))
    extra = any(w in token for w in ("extrap", "beyond", "past", "outside", "both"))
    if not inter and not extra:
        raise ValueError(
            f"interpolation={interpolation!r} is not a recognised declaration; use "
            "'interpolate', 'extrapolate', 'both', True, or None")
    return {"allow_interpolation": inter, "allow_extrapolation": extra,
            "interpolation": token}


def _pilkington_bi_basis() -> float:
    """The bond index the rule is stated at, read from #104. Never redefined."""
    name, value = _resolve(_BI_BASIS_NAMES,
                           lambda o: isinstance(o, (int, float)) and not isinstance(o, bool))
    if value is None:
        raise RuntimeError(
            "#107 could not resolve the Pilkington bond-index basis from #104 "
            f"(expected one of {_BI_BASIS_NAMES}). #107 deliberately holds no "
            "copy of it.")
    return float(value)


def _required_footage_ft(casing_od_in: float, bi_basis: float,
                         interpolation: Any,
                         flags_out: list[str] | None = None) -> tuple[Any, str]:
    """Required Pilkington footage for this casing OD, obtained from #104.

    Returns `(value_or_Refusal, provider_label)`. `value` is a float in ft.
    #104's own flags are collected into `flags_out` and ride out on the
    result: an interpolated footage is an assumption, not a published number,
    and it must not reach an operator looking like one.
    Raises RuntimeError if #104 exposes nothing at all - a failed merge is
    programmer error, not a source limitation, so it is not a Refusal.
    """
    interp = _interpolation_kwargs(interpolation)
    name, fn = _resolve(_REQUIRED_FOOTAGE_FUNCS, callable)
    if fn is not None:
        out = _call_flexible(fn, casing_od_in=casing_od_in,
                             bi_threshold=bi_basis, bond_index=bi_basis,
                             sustained_bi=bi_basis, bi_basis=bi_basis, **interp)
        if flags_out is not None:
            flags_out.extend(getattr(out, "flags", ()))
        return _as_footage(out, name), name

    name, fn = _resolve(_VERDICT_FUNCS, callable)
    if fn is not None:
        # #104's verdict form: ask it about a length it cannot fail on, then
        # read the required footage it recorded in `inputs`.
        out = _call_flexible(fn, casing_od_in=casing_od_in,
                             bi_threshold=bi_basis, sustained_bi=bi_basis,
                             bond_index=bi_basis, bi_basis=bi_basis,
                             depth_ft=0.0, bonded_length_ft=0.0, length_ft=0.0,
                             **interp)
        if isinstance(out, Refusal):
            return out, name
        req = getattr(out, "inputs", {}).get("required_ft")
        if req is None:
            raise RuntimeError(
                f"#107 could not read `required_ft` from {name}(); #104 must "
                f"expose one of {_REQUIRED_FOOTAGE_FUNCS} or record required_ft"
            )
        if flags_out is not None:
            flags_out.extend(getattr(out, "flags", ()))
        return float(req), name

    name, table = _resolve(_FOOTAGE_TABLES, lambda o: isinstance(o, dict))
    if table is not None:
        if interpolation is not None:
            return Refusal(
                reason=(f"interpolation {interpolation!r} was declared, but #104 "
                        f"exposes no footage function to apply it; only the raw "
                        f"table {name} is available and it is exact-match only"),
                needed=("a Pilkington footage function from #104 "
                        "(isolation_length_check) that implements interpolation",),
                source=DRILLINGMANUAL,
            ), name
        required = table.get(round(float(casing_od_in), 3))
        if required is None:
            return Refusal(
                reason=(f"no published Pilkington footage for {casing_od_in} in. "
                        f"casing; the source gives {sorted(table)} in. only, and "
                        f"interpolating between two points is an assumption the "
                        f"caller must declare"),
                needed=("a caller-declared interpolation, or a source covering "
                        "this casing size",),
                source=DRILLINGMANUAL,
            ), name
        return float(required), name

    raise RuntimeError(
        "#107 behind_pipe_isolation_check could not resolve the Pilkington "
        "footage rule from #104. Expected one of "
        f"{_REQUIRED_FOOTAGE_FUNCS + _VERDICT_FUNCS + _FOOTAGE_TABLES} in the "
        "merged module. #107 deliberately holds no footage table of its own."
    )


def _as_footage(out: Any, provider: str) -> Any:
    if isinstance(out, Refusal):
        return out
    if isinstance(out, Quantity):
        if out.unit not in ("ft", "feet"):
            raise RuntimeError(
                f"#107 expected {provider}() to return feet, got unit {out.unit!r}"
            )
        return float(out.value)
    if isinstance(out, (int, float)) and not isinstance(out, bool):
        return float(out)
    raise RuntimeError(
        f"#107 could not read a required footage from {provider}(); got "
        f"{type(out).__name__}. See the consumed-contract table in "
        "specs/107-behind_pipe_isolation_check.md"
    )


def _sustained_runs(depths: Sequence[float], bi: Sequence[float],
                    bi_basis: float) -> tuple[list[tuple[float, float]], str]:
    """Maximal runs where BI >= bi_basis, from #104's scanner where available."""
    name, fn = _resolve(_RUN_SCANNER_FUNCS, callable)
    if fn is not None:
        out = _call_flexible(fn, depth_ft=depths, depths_ft=depths, depth=depths,
                             bond_index=bi, bi=bi, bi_threshold=bi_basis,
                             bi_basis=bi_basis, threshold=bi_basis,
                             sustained_bi=bi_basis)
        return _normalize_runs(out, name), name
    return _local_sustained_runs(depths, bi, bi_basis), "#107 local scan"


def _gap_pairs(depths: Sequence[float], max_gap_ft: float | None):
    """Depth steps that skip at least one sample, from #104's `gap_scan`."""
    name, fn = _resolve(_GAP_SCAN_FUNCS, callable)
    if fn is not None:
        out = _call_flexible(fn, depth_ft=depths, depths_ft=depths, depth=depths,
                             max_gap_ft=max_gap_ft)
        return [(float(a), float(b)) for a, b in out], name
    return _local_gap_pairs(depths, max_gap_ft), "#107 local scan"


def _local_gap_pairs(depths: Sequence[float], max_gap_ft: float | None):
    """Fallback with the same rule as #104's: one missing sample is a gap."""
    if len(depths) < 2:
        return []
    steps = [depths[i + 1] - depths[i] for i in range(len(depths) - 1)]
    if max_gap_ft is None:
        ordered = sorted(steps)
        mid = len(ordered) // 2
        max_gap_ft = (ordered[mid] if len(ordered) % 2
                      else 0.5 * (ordered[mid - 1] + ordered[mid]))
    return [(depths[i], depths[i + 1])
            for i, s in enumerate(steps) if s > max_gap_ft + 1e-3]


def _normalize_runs(out: Any, provider: str) -> list[tuple[float, float]]:
    if isinstance(out, Refusal):
        return []
    runs: list[tuple[float, float]] = []
    for run in out:
        if isinstance(run, (tuple, list)) and len(run) >= 2:
            top, base = float(run[0]), float(run[1])
        elif isinstance(run, dict):
            top = run.get("top_ft", run.get("top"))
            base = run.get("base_ft", run.get("base"))
            if top is None or base is None:
                raise RuntimeError(
                    f"#107 could not read a (top, base) pair from {provider}()")
            top, base = float(top), float(base)
        else:
            top = getattr(run, "top_ft", getattr(run, "top", None))
            base = getattr(run, "base_ft", getattr(run, "base", None))
            if top is None or base is None:
                raise RuntimeError(
                    f"#107 could not read a (top, base) pair from {provider}(); "
                    f"got {type(run).__name__}. See the consumed-contract table "
                    "in specs/107-behind_pipe_isolation_check.md")
            top, base = float(top), float(base)
        runs.append((min(top, base), max(top, base)))
    return runs


def _local_sustained_runs(depths: Sequence[float], bi: Sequence[float],
                          bi_basis: float) -> list[tuple[float, float]]:
    """Fallback maximal-run scan. Pure array logic, no source constants, so it
    cannot drift from the source the way a copied table would."""
    runs: list[tuple[float, float]] = []
    start = None
    for i, v in enumerate(bi):
        ok = (isinstance(v, (int, float)) and not isinstance(v, bool)
              and math.isfinite(v) and v >= bi_basis)
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            runs.append((depths[start], depths[i - 1]))
            start = None
    if start is not None:
        runs.append((depths[start], depths[-1]))
    return runs


# ---------------------------------------------------------------------------
# The tool
# ---------------------------------------------------------------------------

def behind_pipe_isolation_check(
    *,
    depth_ft: Sequence[float] | None = None,
    bond_index: Sequence[float] | None = None,
    perf_top_ft: float | None = None,
    perf_base_ft: float | None = None,
    water_zone_top_ft: float | None = None,
    water_zone_base_ft: float | None = None,
    casing_od_in: float | None = None,
    bi_basis: float | None = None,   # None -> #104's PILKINGTON_BI_BASIS
    depth_basis: str = "MD",
    hole_deviated: bool | None = None,
    formation_transit_time_us_ft: float | None = None,
    hours_since_cementing: float | None = None,
    cement_type: str | None = None,
    log_validity: Any = None,
    interpolation: Any = None,
    max_gap_ft: float | None = None,
):
    """Is there competent cement between the proposed perfs and the water zone?

    Keyword-only on purpose: a missing water-zone pick must be a refusal, not a
    positional slip that silently shifts the geometry.
    """
    # -- programmer errors, which are exceptions, not refusals ---------------
    if perf_top_ft is None or perf_base_ft is None:
        raise ValueError("perf_top_ft and perf_base_ft are required")
    perf_top_ft, perf_base_ft = float(perf_top_ft), float(perf_base_ft)
    if perf_top_ft >= perf_base_ft:
        raise ValueError("perf_top_ft must be shallower than perf_base_ft "
                         "(depths increase downward)")
    if depth_ft is not None and bond_index is not None and \
            len(depth_ft) != len(bond_index):
        raise ValueError("depth_ft and bond_index must be the same length")
    if max_gap_ft is not None and float(max_gap_ft) <= 0:
        raise ValueError("max_gap_ft must be positive")
    bi_basis = _pilkington_bi_basis() if bi_basis is None else float(bi_basis)

    # -- 1. required inputs -------------------------------------------------
    if water_zone_top_ft is None:
        return Refusal(
            reason="no water-zone pick supplied. The nearest water zone cannot be "
                   "inferred from a bond log - the log measures cement, not "
                   "formation fluid - and without it there is no interval to "
                   "scan, because the whole question is what lies between the "
                   "proposed perforations and that pick",
            needed=("water_zone_top_ft: the depth of the nearest water zone, in ft, "
                    "on the same datum as the bond log",),
            source=DRILLINGMANUAL,
        )
    water_top = float(water_zone_top_ft)
    water_base = float(water_zone_base_ft) if water_zone_base_ft is not None else water_top
    if water_base < water_top:
        raise ValueError("water_zone_base_ft must be at or below water_zone_top_ft")

    if casing_od_in is None:
        return Refusal(
            reason="no casing OD supplied. Pilkington's required footage is a "
                   "function of casing OD - 5 ft for 5 in. against 15 ft for "
                   "9-5/8 in. at the same 80% bond index - so there is no "
                   "defensible default",
            needed=("casing_od_in: casing outside diameter in inches",),
            source=DRILLINGMANUAL,
        )
    casing_od_in = float(casing_od_in)

    if depth_ft is None or bond_index is None or len(depth_ft) == 0:
        return Refusal(
            reason="no bond-index curve supplied; there is nothing to scan for a "
                   "sustained cement column",
            needed=("depth_ft and bond_index: a depth-indexed bond-index curve "
                    "from #103 cbl_bond_index",),
            source=DRILLINGMANUAL,
        )

    # -- 2. the log's own validity gates ------------------------------------
    invalid = _log_validity_refusal(
        formation_transit_time_us_ft=formation_transit_time_us_ft,
        hours_since_cementing=hours_since_cementing,
        cement_type=cement_type,
        log_validity=log_validity,
    )
    if invalid is not None:
        return invalid

    if depth_basis.upper() not in ("MD", "TVD"):
        raise ValueError("depth_basis must be 'MD' or 'TVD'")
    if depth_basis.upper() == "MD" and hole_deviated:
        return Refusal(
            reason="depths are measured depth in a hole the caller declared "
                   "deviated. Pilkington's footage is a height 'required for "
                   "vertical isolation'; measured footage over-states the "
                   "vertical column in a deviated hole, which is the unsafe "
                   "direction, and the corpus supplies no deviation correction",
            needed=("TVD-referenced depths (depth_basis='TVD'), or a survey to "
                    "convert with #17 md_to_tvd",),
            source=DRILLINGMANUAL,
        )

    # -- 3. the interval between the perfs and the water zone ---------------
    if water_base <= perf_top_ft:
        scan_top, scan_base, direction = water_base, perf_top_ft, "above"
    elif water_top >= perf_base_ft:
        scan_top, scan_base, direction = perf_base_ft, water_top, "below"
    else:
        return Refusal(
            reason=f"the proposed perforations {perf_top_ft:.1f}-{perf_base_ft:.1f} ft "
                   f"overlap the water-zone pick {water_top:.1f}-{water_base:.1f} ft. "
                   "There is no annular interval between them for cement to "
                   "isolate, so the Pilkington criterion does not apply - this is "
                   "a completion-design problem, not a cement-evaluation one",
            needed=("perforations that do not straddle the water zone, or a "
                    "different water-zone pick",),
            source=DRILLINGMANUAL,
        )
    separation_ft = scan_base - scan_top

    # -- 4. required footage, from #104 -------------------------------------
    footage_flags: list[str] = []
    required, footage_provider = _required_footage_ft(casing_od_in, bi_basis,
                                                      interpolation, footage_flags)
    if isinstance(required, Refusal):
        return required
    if required <= 0:
        raise RuntimeError(f"#104 returned a non-positive required footage: {required}")

    base_inputs: dict[str, Any] = {
        "perf_interval_ft": (perf_top_ft, perf_base_ft),
        "water_zone_ft": (water_top, water_base),
        "water_zone_direction": direction,
        "scanned_interval_ft": (scan_top, scan_base),
        "scanned_length_ft": separation_ft,
        "casing_od_in": casing_od_in,
        "bi_basis": bi_basis,
        "required_ft": required,
    }
    base_assumptions: dict[str, Any] = {
        "footage_rule": f"Pilkington via #104 ({footage_provider}); no footage "
                        "table is held by #107",
        "depth_basis": depth_basis.upper(),
        "length_basis": "continuous sustained bond index clipped to the interval "
                        "between the perforations and the water zone, never an "
                        "interval average - averaging lets a channel pass",
    }
    if interpolation is not None:
        base_assumptions["interpolation"] = f"caller-declared: {interpolation}"

    md_flags: tuple[str, ...] = tuple(footage_flags)
    if depth_basis.upper() == "MD":
        md_flags += ("depths are MD; Pilkington's footage is a vertical height and "
                     "equals MD only in a vertical hole",)
    if cement_type is not None and not _cement_type_recognised(cement_type):
        md_flags += (f"cement type {cement_type!r} is not in #106's cement-type "
                     "table; whether the acoustic interpretation is valid for it "
                     "is unverified, not confirmed",)
    elif cement_type is None:
        md_flags += ("cement type not supplied; a foam or lightweight system "
                     "would invalidate this bond index and #107 cannot detect "
                     "one from the curve",)

    # -- 5. geometric impossibility -----------------------------------------
    # A definite negative, not an abstention: no bond quality can put 15 ft of
    # cement into a 10 ft gap.
    if separation_ft < required:
        return Quantity(
            0.0, "bool", _METHOD, DRILLINGMANUAL,
            inputs={**base_inputs, "longest_sustained_run_ft": None,
                    "longest_run_interval_ft": None},
            assumptions=base_assumptions,
            flags=md_flags + (
                f"NOT isolated: only {separation_ft:.1f} ft separates the "
                f"perforations from the water zone ({direction}), short of the "
                f"{required:.1f} ft Pilkington requires for {casing_od_in} in. "
                f"casing at {bi_basis:.0%} bond index - no bond quality can "
                f"satisfy the rule over an interval this short",),
        )

    # -- 6. curve coverage, nulls and gaps across the scanned interval -------
    pairs = sorted(zip((float(d) for d in depth_ft), bond_index),
                   key=lambda p: p[0])
    depths = [p[0] for p in pairs]
    values = [p[1] for p in pairs]

    if depths[0] > scan_top + 1e-9 or depths[-1] < scan_base - 1e-9:
        return Refusal(
            reason=f"the bond-index curve spans {depths[0]:.1f}-{depths[-1]:.1f} ft "
                   f"and does not cover the whole {scan_top:.1f}-{scan_base:.1f} ft "
                   "interval between the perforations and the water zone. "
                   "Unlogged annulus is unevaluated cement, and the uncovered "
                   "part could be the channel",
            needed=(f"bond index over the full {scan_top:.1f}-{scan_base:.1f} ft "
                    "interval",),
            source=DRILLINGMANUAL,
        )

    idx = [i for i, d in enumerate(depths) if scan_top - 1e-9 <= d <= scan_base + 1e-9]
    if len(idx) < 2:
        return Refusal(
            reason=f"only {len(idx)} bond-index sample(s) fall inside the "
                   f"{scan_top:.1f}-{scan_base:.1f} ft interval; a sustained run "
                   "length cannot be measured from that",
            needed=("a bond-index curve sampled through the interval",),
            source=DRILLINGMANUAL,
        )

    for i in idx:
        v = values[i]
        if v is None or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            return Refusal(
                reason=f"bond index is null at {depths[i]:.1f} ft, inside the "
                       f"{scan_top:.1f}-{scan_base:.1f} ft interval. A run length "
                       "measured across a null is not measured",
                needed=("a null-free bond-index curve over the interval "
                        "(run #12 null_scrub first)",),
                source=DRILLINGMANUAL,
            )
        if not (BI_PLAUSIBLE_MIN <= float(v) <= BI_PLAUSIBLE_MAX):
            return Refusal(
                reason=f"bond index {float(v):g} at {depths[i]:.1f} ft is outside "
                       f"the plausible band {BI_PLAUSIBLE_MIN} to {BI_PLAUSIBLE_MAX}. "
                       "This is an un-scrubbed null or a miscalibrated curve, not "
                       "poor bond; read as poor bond it would produce a confident "
                       "wrong 'not isolated'",
                needed=("a scrubbed, calibrated bond-index curve (#102 "
                        "cbl_calibration, #12 null_scrub)",),
                source=DRILLINGMANUAL,
            )

    window = depths[idx[0]:idx[-1] + 1]
    if any(window[i + 1] - window[i] <= 0 for i in range(len(window) - 1)):
        return Refusal(
            reason="the bond-index curve has a non-positive depth step inside the "
                   "scanned interval; depths are duplicated",
            needed=("a strictly monotonic depth index",),
            source=DRILLINGMANUAL,
        )
    gaps, gap_provider = _gap_pairs(window, max_gap_ft)
    base_assumptions["gap_rule"] = (
        f"#104 sampling continuity via {gap_provider}: a depth step larger than "
        "the curve's own median step skips a sample; the threshold is measured "
        "from the data, not chosen"
    )
    if gaps:
        a, b = gaps[0]
        return Refusal(
            reason=f"the bond-index curve is gapped inside the "
                   f"{scan_top:.1f}-{scan_base:.1f} ft interval: {len(gaps)} skipped "
                   f"sample(s), the first a {b - a:.2f} ft step from {a:.1f} to "
                   f"{b:.1f} ft. A sustained run cannot be credited across a hole "
                   f"in the data - the hole could be the channel",
            needed=(f"a continuously sampled bond-index curve over "
                    f"{scan_top:.1f}-{scan_base:.1f} ft",),
            source=DRILLINGMANUAL,
        )

    # -- 7. sustained runs, clipped to the interval -------------------------
    runs, scanner = _sustained_runs(depths, values, bi_basis)
    base_assumptions["run_scanner"] = scanner

    clipped = []
    for top, bottom in runs:
        t, b = max(top, scan_top), min(bottom, scan_base)
        if b > t:
            clipped.append((t, b))
    if clipped:
        best = max(clipped, key=lambda r: r[1] - r[0])
        best_len = best[1] - best[0]
    else:
        best, best_len = None, 0.0

    base_inputs["longest_sustained_run_ft"] = best_len
    base_inputs["longest_run_interval_ft"] = best
    base_inputs["sustained_runs_in_interval"] = tuple(clipped)

    # -- 8. the verdict ------------------------------------------------------
    isolated = best_len >= required
    if isolated:
        flags = md_flags + (_SEAL_CAVEAT,)
    else:
        flags = md_flags + (
            f"NOT isolated: longest sustained run of BI >= {bi_basis:.2f} between "
            f"the perforations and the water zone ({direction}) is "
            f"{best_len:.1f} ft, {required - best_len:.1f} ft short of the "
            f"{required:.1f} ft Pilkington requires for {casing_od_in} in. casing",)

    return Quantity(1.0 if isolated else 0.0, "bool", _METHOD, DRILLINGMANUAL,
                    inputs=base_inputs, assumptions=base_assumptions, flags=flags)


def _log_validity_refusal(*, formation_transit_time_us_ft, hours_since_cementing,
                          cement_type, log_validity) -> Refusal | None:
    """The bond log's own validity gates - #106 vdl_classify's refusals.

    A bond index computed on a log #106 would refuse is not evidence of
    isolation. This is the difference between 'not isolated' and 'the log cannot
    tell you'.
    """
    if isinstance(log_validity, Refusal):
        return Refusal(
            reason="the underlying bond log was refused by the waveform "
                   f"classifier (#106 vdl_classify): {log_validity.reason}. A bond "
                   "index computed on a log that cannot be interpreted is not "
                   "evidence of isolation",
            needed=log_validity.needed or ("a bond log #106 vdl_classify accepts",),
            source=log_validity.source or PETROWIKI_CBL,
        )
    if log_validity is False or isinstance(log_validity, str):
        detail = log_validity if isinstance(log_validity, str) else "flagged invalid"
        return Refusal(
            reason=f"the caller flagged the underlying bond log invalid: {detail}. "
                   "A bond index from an invalid log is not evidence of isolation",
            needed=("a bond log the caller does not flag invalid",),
            source=PETROWIKI_CBL,
        )

    casing_transit = _source_number(_FAST_FORMATION_NAMES, "fast-formation "
                                    "transit-time limit", "#106 vdl_classify")
    if formation_transit_time_us_ft is not None and \
            float(formation_transit_time_us_ft) < casing_transit:
        return Refusal(
            reason=f"fast formation: transit time "
                   f"{float(formation_transit_time_us_ft):.1f} usec/ft is below the "
                   f"casing's {casing_transit:.0f} usec/ft, so the "
                   "formation signal arrives inside the amplitude gate and the "
                   "bond index is not a measure of cement. The log cannot tell "
                   "you whether this interval is isolated",
            needed=("a bond log in a formation slower than casing, or an "
                    "ultrasonic/radial evaluation",),
            source=PETROWIKI_CBL,
        )

    green_hours = _source_number(_GREEN_CEMENT_NAMES, "green-cement wait",
                                 "#106 vdl_classify")
    if hours_since_cementing is not None and \
            float(hours_since_cementing) < green_hours:
        return Refusal(
            reason=f"green cement: the log was run {float(hours_since_cementing):.1f} "
                   f"hours after cementing, inside the {green_hours:.0f}-hour "
                   "rule of thumb. Low compressive strength gives higher than "
                   "normal amplitudes, i.e. an understated bond index, so the "
                   "answer would be pessimistic for a reason that has nothing to "
                   "do with the cement's final quality",
            needed=(f"a bond log run at least {green_hours:.0f} hours after "
                    "cementing",),
            source=SPE_BOND_THEORY,
        )

    if cement_type is not None:
        return _cement_type_refusal(cement_type)
    return None


def _source_number(names: Sequence[str], what: str, owner: str) -> float:
    """A threshold owned by another tool, read from the merged namespace."""
    _, value = _resolve(names, lambda o: isinstance(o, (int, float))
                        and not isinstance(o, bool))
    if value is None:
        raise RuntimeError(
            f"#107 could not resolve the {what} from {owner} (expected one of "
            f"{tuple(names)}). #107 deliberately holds no copy of it.")
    return float(value)


def _normalize_cement_token(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in str(text).lower())


def _cement_type_recognised(cement_type: Any) -> bool:
    _, table = _resolve(_CEMENT_TYPE_TABLES, lambda o: isinstance(o, dict))
    if table is None:
        return False
    token = _normalize_cement_token(cement_type)
    return any(key in token for key in table)


def _cement_type_refusal(cement_type: Any) -> Refusal | None:
    """Refuse on the systems #106's CEMENT_TYPES marks un-interpretable.

    The table is #106's, keys and reasons both. An unrecognised string is not
    refused - unknown is not the same as invalid - but nothing silently passes
    either: the caller's own string is echoed back on the result.
    """
    name, table = _resolve(_CEMENT_TYPE_TABLES, lambda o: isinstance(o, dict))
    if table is None:
        raise RuntimeError(
            "#107 could not resolve the cement-type validity table from #106 "
            f"vdl_classify (expected one of {_CEMENT_TYPE_TABLES}). #107 "
            "deliberately holds no copy of it.")
    token = _normalize_cement_token(cement_type)
    for key, entry in table.items():
        interpretable = entry[0] if isinstance(entry, (tuple, list)) else bool(entry)
        if interpretable or key not in token:
            continue
        why = entry[2] if isinstance(entry, (tuple, list)) and len(entry) > 2 else ""
        anchor = entry[1] if isinstance(entry, (tuple, list)) and len(entry) > 1 else PETROWIKI_CBL
        return Refusal(
            reason=f"cement type {cement_type!r} matches {key!r}, which #106 "
                   f"vdl_classify marks un-interpretable: {why}. A bond index "
                   "computed against a conventional calibration on this system is "
                   "not evidence of isolation",
            needed=("a service-company calibration for this cement system, or an "
                    "ultrasonic/radial evaluation",),
            source=str(anchor),
        )
    return None
