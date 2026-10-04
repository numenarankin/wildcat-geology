"""Curve conditioning: nulls, resampling, and run boundaries.

Three tools that all sit between a parsed LAS file and any arithmetic done on
it, and all three are shaped by the same fact: the corpus describes the LAS
*format* and almost nothing about processing arrays, so most of what they do
would be an invented rule if it were not declared as an owned one.

- `null_scrub` removes the declared `~W NULL` and the two sentinels the source
  names, and **reports** anything else rather than removing it. The asymmetry is
  deliberate: a missed sentinel is loud — it is orders of magnitude out of range
  and `curve_inventory` already labels the resulting fraction a lower bound —
  while a value wrongly deleted is silent, untraceable, and moves the null count
  in the direction that looks like diligence. A declared NULL of 0.0 refuses
  outright, because zero is a real reading for GR, SP, Vsh and porosity and a
  header field is not consent to delete them.
- `depth_resample` will not choose an interpolation method for a curve. Halfway
  between 1 and 10 ohm-m is 3.162 geometrically and 5.5 linearly, and nothing
  downstream reveals which you got. It also never interpolates across a gap or
  past a null, and never extrapolates: a resampled log must contain no sample
  the tool invented.
- `curve_splice_detect` treats a step in a curve as a **bed**, not as a run
  boundary. Inferring boundaries from curve shape would nominate every formation
  top in the well, so boundaries come from the run table, the depth index, and
  the null pattern, and the magnitude that makes an offset a calibration problem
  is a caller threshold — the corpus states none.

`asquith#64`'s ±1 ft cross-run registry allowance is imported from `raster`
rather than restated, so the two tools that consume it cannot come to disagree
about one published number.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass, field
from statistics import median
from typing import Any, Mapping, Sequence
from typing import Any, Sequence
import math
import statistics

from .raster import ASQUITH_RUNS, CROSS_RUN_REGISTRY_FT
from .result import Quantity, Range, Refusal
from .result import Quantity, Range, Refusal  # noqa: F401  (Range unused; imported per house convention)

# ---------------------------------------------------------------------------
# 12_null_scrub
# Curve conditioning: null scrubbing.
# ---------------------------------------------------------------------------

KGS_LAS20 = "02-las-format/kgs-las-2.0-field-table#1"

# kgs#1, ~W required fields: "NULL . nnnn.nn : Null Value; Common Null Values
# are -999.25, -9999, etc." These two are named by the source. The "etc." is
# not enumerable from this corpus and is deliberately not guessed at - see the
# module docstring.
LAS20_COMMON_NULLS: tuple[float, ...] = (-999.25, -9999.0)

# Sentinel match tolerance. Tight on purpose: it exists for text-rounding drift
# from a re-export (-999.2500001), not for a fuzzy neighbourhood. "-999.2500"
# and "-999.25" already parse to the same double and need no tolerance at all,
# while -999.2 is 0.05 away and must survive as data. Matches
# tools/las.py NULL_MATCH_RTOL so that curve_inventory's own declared-only path
# and this tool cannot disagree about what "equals the declared NULL" means.
NULL_MATCH_RTOL = 1e-9
NULL_MATCH_ATOL = 1e-9

# HOUSE RULES. Both gate a *report*, never a removal, which is the only reason
# it was acceptable to pick them. Not in the catalog's "Thresholds the corpus
# does not supply" table; if anything downstream ever acts on a suspect, they
# must be entered there with a basis first.
SUSPECT_REPEAT_FRAC = 0.10   # share of surviving finite samples for repeat-extreme
NEAR_SENTINEL_RTOL = 1e-3    # nearness to a named sentinel for near-named-sentinel

_REPEAT_BASIS = (
    "house rule, not from the corpus: most-frequent surviving value occupying "
    ">= {frac:.0%} of finite samples AND sitting at the curve minimum or maximum"
)
_NEAR_BASIS = (
    "house rule, not from the corpus: within {rtol:g} relative of a null value "
    "named at kgs#1 (-999.25, -9999) without equalling it"
)


# ---------------------------------------------------------------------------
# result types. The first three fields of ScrubbedCurve are the contract
# specs/03-curve_inventory.md states for this tool and must not move.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Suspect:
    """A value that looks like a sentinel and was therefore left alone."""

    value: float
    count: int
    fraction: float
    rule: str
    basis: str
    detail: str


@dataclass(frozen=True)
class ScrubbedCurve:
    values: list[float | None]
    sentinels_found: tuple[float, ...]
    n_replaced: int
    n_samples: int = 0
    n_null: int = 0
    null_fraction: Quantity | None = None
    all_null: bool = False
    counts: dict[str, int] = field(default_factory=dict)
    origins: dict[str, str] = field(default_factory=dict)
    suspects: tuple[Suspect, ...] = ()
    mnemonic: str = ""
    method: str = ""
    source: str = KGS_LAS20
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScrubbedFile:
    columns: tuple[list[float | None], ...]
    curves: tuple[ScrubbedCurve, ...]
    mnemonics: tuple[str, ...]
    index_column: int | None
    n_index_nulls: int
    sentinels_found: tuple[float, ...]
    n_replaced: int
    source: str = KGS_LAS20
    method: str = ""
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    @property
    def null_basis(self) -> dict[str, Any]:
        """The provenance packet for `curve_inventory(null_basis=...)`.

        `curve_inventory` passes this straight into its `assumptions`, so a null
        fraction it reports can always be traced back to what was treated as a
        null and on whose authority.
        """
        return {
            "tool": "null_scrub",
            "source": self.source,
            "method": self.method,
            "sentinels_found": self.sentinels_found,
            "sentinel_origins": {
                k: v for c in self.curves for k, v in c.origins.items()
            },
            "n_replaced": self.n_replaced,
            "per_curve": {
                c.mnemonic or f"col{i}": {
                    "n_replaced": c.n_replaced,
                    "n_null": c.n_null,
                    "sentinels_found": c.sentinels_found,
                }
                for i, c in enumerate(self.curves)
            },
            "suspects": tuple(
                {
                    "mnemonic": c.mnemonic or f"col{i}",
                    "value": s.value,
                    "count": s.count,
                    "rule": s.rule,
                    "basis": s.basis,
                }
                for i, c in enumerate(self.curves)
                for s in c.suspects
            ),
            "index_column": self.index_column,
            "n_index_nulls": self.n_index_nulls,
            "assumptions": dict(self.assumptions),
            "flags": self.flags,
        }


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _key(value: float) -> str:
    """Stable dict key for a sentinel. Floats as dict keys read badly in a log."""
    return repr(float(value))


def _coerce(raw: Any) -> tuple[float | None, str]:
    """-> (number or None, kind).

    kind is "none" | "number" | "nan" | "text". The source restricts ~A to
    "floating point or integer (long) values", so text is out-of-spec data
    rather than a value; it is nulled and flagged rather than raising, because
    real files contain it.
    """
    if raw is None:
        return None, "none"
    if isinstance(raw, bool):  # bool is an int subclass; never a log reading
        return None, "text"
    if isinstance(raw, (int, float)):
        v = float(raw)
        return (None, "nan") if math.isnan(v) else (v, "number")
    try:
        v = float(str(raw).strip())
    except (TypeError, ValueError):
        return None, "text"
    return (None, "nan") if math.isnan(v) else (v, "number")


def _build_sentinels(
    declared_null: float | None,
    scrub_common: bool,
    candidate_sentinels: Sequence[float],
) -> tuple[list[float], dict[str, str]]:
    """-> (sentinel values in application order, value-key -> origin)."""
    sentinels: list[float] = []
    origins: dict[str, str] = {}

    def add(value: float, origin: str) -> None:
        v = float(value)
        if any(math.isclose(v, s, rel_tol=NULL_MATCH_RTOL, abs_tol=NULL_MATCH_ATOL)
               for s in sentinels):
            return
        sentinels.append(v)
        origins[_key(v)] = origin

    if declared_null is not None:
        add(declared_null, "declared")
    if scrub_common:
        for s in LAS20_COMMON_NULLS:
            add(s, "common")
    for s in candidate_sentinels:
        add(s, "caller")
    return sentinels, origins


def _suspects(
    survivors: list[float],
    n_finite: int,
    repeat_frac: float,
    near_rtol: float,
) -> tuple[Suspect, ...]:
    """Values that look like sentinels. Reported; never removed."""
    if not survivors or n_finite == 0:
        return ()
    out: list[Suspect] = []
    seen: set[str] = set()
    tally = Counter(survivors)
    lo, hi = min(survivors), max(survivors)

    # near-named-sentinel runs first: where both rules would fire on the same
    # value it is the more specific and more useful diagnosis, because it names
    # the sourced value the suspect resembles.
    for named in LAS20_COMMON_NULLS:
        for v, n in sorted(tally.items()):
            if _key(v) in seen or v == named:
                continue
            if abs(v - named) <= near_rtol * abs(named):
                out.append(Suspect(
                    value=v, count=n, fraction=n / n_finite,
                    rule="near-named-sentinel",
                    basis=_NEAR_BASIS.format(rtol=near_rtol),
                    detail=(
                        f"{v:g} occurs {n} times and sits "
                        f"{abs(v - named) / abs(named):.2g} relative from {named:g}, a null "
                        "value named by the source. It is not that value, so it was NOT "
                        "removed; the source's \"etc.\" is not enumerable from this corpus."
                    ),
                ))
                seen.add(_key(v))

    value, count = tally.most_common(1)[0]
    frac = count / n_finite
    # Both conditions matter. A flatlined caliper sitting on bit size is
    # repeated but mid-range; a sentinel is repeated AND out at an extreme.
    # lo != hi excludes a wholly constant column, where "extreme" carries no
    # information and a legitimate constant curve (bit size) would fire on
    # every file. count >= 2 because a "repeat" must actually repeat: on a short
    # all-distinct column the most frequent value occurs once, and one
    # occurrence of the minimum is a reading, not a sentinel.
    if (_key(value) not in seen and count >= 2 and frac >= repeat_frac
            and (value == lo or value == hi) and lo != hi):
        out.append(Suspect(
            value=value, count=count, fraction=frac, rule="repeat-extreme",
            basis=_REPEAT_BASIS.format(frac=repeat_frac),
            detail=(
                f"{value:g} occurs {count} of {n_finite} finite samples "
                f"({frac:.1%}) and is the curve {'minimum' if value == lo else 'maximum'}; "
                "it may be absent data written as a number. NOT removed - pass it "
                "in candidate_sentinels if it is a null."
            ),
        ))
    return tuple(out)


# ---------------------------------------------------------------------------
# 12_null_scrub
# ---------------------------------------------------------------------------
def null_scrub(
    values: Sequence[Any],
    *,
    declared_null: float | None = None,
    mnemonic: str = "",
    scrub_common: bool = True,
    candidate_sentinels: Sequence[float] = (),
    allow_zero_null: bool = False,
    match_rtol: float = NULL_MATCH_RTOL,
    match_atol: float = NULL_MATCH_ATOL,
    report_suspects: bool = True,
    suspect_repeat_frac: float = SUSPECT_REPEAT_FRAC,
    near_sentinel_rtol: float = NEAR_SENTINEL_RTOL,
) -> ScrubbedCurve | Refusal:
    """Replace null sentinels in one LAS column with `None`, and report the rest.

    Returns a new list; the caller's sequence is never touched. `None` marks a
    null on the way out and nothing else does, which is the property
    `curve_inventory` (#3) depends on.

    Scrubs the declared `~W NULL`, the two values kgs#1 names, and whatever the
    caller supplies. Does **not** detect anything else - see the module
    docstring.
    """
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(
            f"values must be a sequence of numbers, got {type(values).__name__}; "
            "this is a wiring fault at the call site, not a condition of the data"
        )
    for c in candidate_sentinels:
        if isinstance(c, float) and math.isnan(c):
            raise ValueError(
                "NaN in candidate_sentinels; NaN never compares equal to itself "
                "and is already treated as a null"
            )

    if not values:
        return Refusal(
            reason="the column has no samples; a null fraction over zero samples is undefined",
            needed=("a populated ~A column",),
            source=KGS_LAS20,
        )
    if declared_null is not None:
        try:
            declared_null = float(declared_null)
        except (TypeError, ValueError):
            # A ~W NULL of "N/A" is a condition of the file, not a wiring fault,
            # so it is refused rather than raised: kgs#1 gives NULL as a numeric
            # field ("NULL| . | nnnn.nn").
            return Refusal(
                reason=(
                    f"declared NULL {declared_null!r} is not a number, so nothing can be "
                    "matched against it; kgs#1 declares ~W NULL as a numeric field "
                    "(NULL . nnnn.nn)"
                ),
                needed=(
                    "a numeric ~W NULL",
                    "or declared_null=None to scrub only the sentinels kgs#1 names",
                ),
                source=KGS_LAS20,
            )
    if declared_null is not None and not math.isfinite(declared_null):
        return Refusal(
            reason=(
                f"declared NULL is {declared_null!r}, which nothing can be matched "
                "against (a NaN never compares equal to itself)"
            ),
            needed=("a finite ~W NULL", "or declared_null=None to scrub only the sourced sentinels"),
            source=KGS_LAS20,
        )
    if declared_null is not None and declared_null == 0.0 and not allow_zero_null:
        return Refusal(
            reason=(
                "declared NULL is 0.0. Zero is a legitimate reading for gamma ray, SP, "
                "Vsh, porosity and most computed curves, so applying it blindly would "
                "delete real data with no trace - the exact failure this tool exists to "
                "prevent. A ~W field is not the caller's consent to do that."
            ),
            needed=(
                "allow_zero_null=True to apply it anyway",
                "or declared_null=None to ignore the declaration and scrub only the "
                "sentinels kgs#1 names",
                "or a corrected ~W NULL",
            ),
            source=KGS_LAS20,
        )

    sentinels, origins = _build_sentinels(declared_null, scrub_common, candidate_sentinels)

    out: list[float | None] = []
    counts: dict[str, int] = {}
    n_pre_null = 0
    n_nan = 0
    n_text = 0
    n_inf = 0
    survivors: list[float] = []

    for raw in values:
        number, kind = _coerce(raw)
        if kind == "none":
            out.append(None)
            n_pre_null += 1
            continue
        if kind == "nan":
            # Not a sentinel guess: NaN is not a number, so nulling it destroys
            # nothing.
            out.append(None)
            n_nan += 1
            continue
        if kind == "text":
            # kgs#1: ~A holds "floating point or integer (long) values ... Text
            # ... not supported". Out-of-spec data, not a value.
            out.append(None)
            n_text += 1
            continue

        assert number is not None
        hit = None
        for s in sentinels:
            if math.isclose(number, s, rel_tol=match_rtol, abs_tol=match_atol):
                hit = s
                break
        if hit is not None:
            out.append(None)
            counts[_key(hit)] = counts.get(_key(hit), 0) + 1
            continue
        if not math.isfinite(number):
            # Out of spec, but an infinity is not a null and this tool will not
            # decide which it is.
            n_inf += 1
            out.append(number)
            continue
        out.append(number)
        survivors.append(number)

    n_samples = len(out)
    n_null = sum(1 for v in out if v is None)
    n_replaced = n_null - n_pre_null
    sentinels_found = tuple(s for s in sentinels if counts.get(_key(s), 0) > 0)
    all_null = n_null == n_samples

    suspects = ()
    if report_suspects:
        suspects = _suspects(survivors, len(survivors), suspect_repeat_frac, near_sentinel_rtol)

    name = f"{mnemonic} " if mnemonic else ""
    flags: list[str] = []
    if declared_null is not None and not any(
        math.isclose(declared_null, s, rel_tol=match_rtol, abs_tol=match_atol)
        for s in sentinels_found
    ):
        flags.append(
            f"declared-null-absent: {name}never contains the declared NULL "
            f"{declared_null:g}. Either the curve has no nulls or the file used an "
            "undeclared sentinel; read the suspects."
        )
    undeclared_common = [
        s for s in sentinels_found
        if origins.get(_key(s)) == "common"
    ]
    if undeclared_common:
        flags.append(
            "common-sentinel-applied-undeclared: removed "
            + ", ".join(f"{s:g}" for s in undeclared_common)
            + " although the file declared "
            + (f"{declared_null:g}" if declared_null is not None else "no NULL")
            + ". kgs#1 names these as *common* null values, not as reserved, so the "
            "removal is announced rather than assumed free."
        )
    if (allow_zero_null and declared_null is not None and declared_null == 0.0
            and any(s == 0.0 for s in sentinels_found)):
        flags.append(
            f"zero-null-applied: removed {counts.get(_key(0.0), 0)} zero(s) because the "
            "file declared NULL = 0.0 and the caller passed allow_zero_null=True. Zero "
            "is a legitimate reading for gamma ray, SP, Vsh and porosity, so the removal "
            "is announced rather than assumed free."
        )
    caller_applied = [s for s in sentinels_found if origins.get(_key(s)) == "caller"]
    if caller_applied:
        flags.append(
            "caller-sentinel-applied: removed "
            + ", ".join(f"{s:g}" for s in caller_applied)
            + " on the caller's authority; no source names these."
        )
    if all_null:
        flags.append(f"all-null: {name}has no surviving samples")
    if n_nan:
        flags.append(f"{n_nan} NaN values nulled (not a number, not a sentinel guess)")
    if n_text:
        flags.append(
            f"non-numeric-value: {n_text} cells would not parse as numbers; kgs#1 "
            "restricts ~A to floating point or integer values. Nulled."
        )
    if n_inf:
        flags.append(
            f"non-finite-value: {n_inf} infinities kept, not nulled; out of the "
            "source's value domain but not a null"
        )
    for s in suspects:
        flags.append(f"suspected-undeclared-sentinel ({s.rule}): {name}{s.detail}")

    method = (
        "replace declared ~W NULL and the null values named at kgs#1 "
        f"({', '.join(f'{s:g}' for s in LAS20_COMMON_NULLS)}) with None; "
        "undeclared sentinels are reported, never removed"
    )
    fraction = Quantity(
        value=n_null / n_samples,
        unit="v/v",
        method=f"null samples / total samples ({n_null}/{n_samples}), nulls per {method}",
        source=KGS_LAS20,
        inputs={"n_null": n_null, "n_samples": n_samples},
        assumptions={
            "declared_null": declared_null,
            "sentinels_applied": tuple(sentinels),
            "sentinel_origins": dict(origins),
        },
        flags=tuple(flags),
    )

    return ScrubbedCurve(
        values=out,
        sentinels_found=sentinels_found,
        n_replaced=n_replaced,
        n_samples=n_samples,
        n_null=n_null,
        null_fraction=fraction,
        all_null=all_null,
        counts={
            **counts,
            "nan": n_nan,
            "non_numeric": n_text,
            "non_finite_kept": n_inf,
            "already_none": n_pre_null,
        },
        origins=dict(origins),
        suspects=suspects,
        mnemonic=mnemonic,
        method=method,
        source=KGS_LAS20,
        flags=tuple(flags),
        assumptions={
            "declared_null": declared_null,
            "scrub_common": scrub_common,
            "common_sentinels": LAS20_COMMON_NULLS,
            "candidate_sentinels": tuple(float(c) for c in candidate_sentinels),
            "allow_zero_null": allow_zero_null,
            "match_rtol": match_rtol,
            "match_atol": match_atol,
            "suspect_repeat_frac": suspect_repeat_frac,
            "suspect_repeat_frac_basis": "house rule; the corpus supplies no detection threshold",
            "near_sentinel_rtol": near_sentinel_rtol,
            "near_sentinel_rtol_basis": "house rule; the corpus supplies no detection threshold",
            "detection_policy": (
                "sourced sentinels scrubbed, everything else flagged; the source's "
                "\"etc.\" is not enumerable from this corpus"
            ),
        },
    )


def null_scrub_columns(
    columns: Sequence[Sequence[Any]],
    *,
    mnemonics: Sequence[str] = (),
    index_column: int | None = 0,
    **kw: Any,
) -> ScrubbedFile | Refusal:
    """Scrub every column of one `~A` section against one shared sentinel set.

    Column 0 is the index unless told otherwise, per kgs#1: "The index values
    always appear in the first column". A null there is flagged separately and
    loudly, because it corrupts the depth frame rather than one curve - every
    depth range, step and gap downstream is measured against those rows.
    """
    cols = list(columns)
    if not cols:
        return Refusal(
            reason="no columns supplied; there is no ~A data to scrub",
            needed=("a populated ~A section",),
            source=KGS_LAS20,
        )
    names = list(mnemonics)
    if names and len(names) != len(cols):
        raise ValueError(
            f"{len(names)} mnemonics for {len(cols)} columns; the ~C-order join would "
            "label values with the wrong curve"
        )
    if not names:
        names = [f"col{i}" for i in range(len(cols))]
    if index_column is not None and not (0 <= index_column < len(cols)):
        raise IndexError(f"index_column {index_column} outside 0..{len(cols) - 1}")

    curves: list[ScrubbedCurve] = []
    for i, col in enumerate(cols):
        r = null_scrub(col, mnemonic=names[i], **kw)
        if isinstance(r, Refusal):
            return r
        curves.append(r)

    file_flags: list[str] = []
    if len({len(c) for c in cols}) > 1:
        file_flags.append(
            "ragged-columns: the columns are not all the same length. Each was "
            "scrubbed independently; curve_inventory refuses on this, which is the "
            "right place for it."
        )

    n_index_nulls = 0
    if index_column is not None:
        idx = curves[index_column]
        null_rows = [r for r, v in enumerate(idx.values) if v is None]
        n_index_nulls = len(null_rows)
        if null_rows:
            shown = ", ".join(str(r) for r in null_rows[:10])
            more = "" if len(null_rows) <= 10 else f" (+{len(null_rows) - 10} more)"
            file_flags.append(
                f"index-null: {n_index_nulls} null(s) in the index column "
                f"{names[index_column]!r} at row(s) {shown}{more}. This is a hole in the "
                "depth frame, not in one curve: every depth range, step and gap is "
                "measured against these rows."
            )

    seen: list[float] = []
    for c in curves:
        for s in c.sentinels_found:
            if not any(math.isclose(s, t, rel_tol=NULL_MATCH_RTOL, abs_tol=NULL_MATCH_ATOL)
                       for t in seen):
                seen.append(s)

    for c in curves:
        for f in c.flags:
            if f.startswith(("all-null", "suspected-undeclared-sentinel")):
                file_flags.append(f"{c.mnemonic}: {f}")

    return ScrubbedFile(
        columns=tuple(c.values for c in curves),
        curves=tuple(curves),
        mnemonics=tuple(names),
        index_column=index_column,
        n_index_nulls=n_index_nulls,
        sentinels_found=tuple(seen),
        n_replaced=sum(c.n_replaced for c in curves),
        source=KGS_LAS20,
        method=curves[0].method,
        flags=tuple(file_flags),
        assumptions={
            **curves[0].assumptions,
            "index_column": index_column,
            "index_basis": "kgs#1: the index values always appear in the first column",
        },
    )


def null_scrub_las(las_file: Any, **kw: Any) -> ScrubbedFile | Refusal:
    """Scrub a parsed LAS file. Duck-typed; does not import `tools.las`.

    Takes the declared NULL and the `~C` mnemonics off the parsed file so the
    common call is one line:

        s = null_scrub_las(f)
        inv = curve_inventory_from_las(f, scrubbed_columns=s.columns,
                                       null_basis=s.null_basis)
    """
    if isinstance(las_file, Refusal):
        return las_file
    columns = getattr(las_file, "columns", None)
    if columns is None:
        raise TypeError("las_file has no .columns; expected a parsed LAS file")
    curves = getattr(las_file, "curves", ()) or ()
    kw.setdefault("declared_null", getattr(las_file, "null_value", None))
    kw.setdefault("mnemonics", tuple(getattr(c, "mnemonic", "") for c in curves))
    if len(kw["mnemonics"]) != len(columns):
        kw["mnemonics"] = ()
    return null_scrub_columns(columns, **kw)

# ---------------------------------------------------------------------------
# 13_depth_resample
# Curve conditioning: resample curves onto a common depth grid.
# ---------------------------------------------------------------------------

# --- provenance -------------------------------------------------------------

# `tool-catalog.md:223` reads "Source: none - no source in corpus. kind should be
# plumbing; vertical-resolution limits at trieste#1", and `tool-verification.md`
# L84 lists this tool under "no source" while L192 corrects the kind to
# `plumbing`. Quantity refuses to construct without a source string, so the
# honest value names those lines rather than a fabricated corpus anchor.
NO_CITATION = (
    "not applicable - plumbing, no citation owed "
    "(tool-catalog.md:223; kind corrected parse -> plumbing at tool-verification.md:192)"
)

TRIESTE_1 = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#1"
TRIESTE_2 = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#2"
TRIESTE_3 = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#3"

# --- owned numbers, declared as owned ---------------------------------------

# PROVISIONAL, owned. No source in the corpus states a resampling ratio. This is
# a guard against absurd requests (1 ft -> 0.1 ft is a tenfold inflation of the
# array with no new information, and is usually a units mistake), not a
# resolution criterion. Overridable per call; see the spec's "The owned number".
MAX_UPSAMPLE_RATIO = 4.0

# Owned, but not arbitrary: a depth increment above 1.5 nominal steps rounds to
# two or more sample intervals, meaning at least one sample is missing.
GAP_TOLERANCE_RATIO = 1.5

# Grid nodes are rounded here so that 1000 + 3*0.1 is 1000.3, not 1000.3000000004.
_GRID_DECIMALS = 6
# Depth comparison tolerance for "this node sits on an input sample".
_DEPTH_TOL = 1e-6

FT_PER_M = 3.280839895013123  # exact inverse of the international foot, 0.3048 m

INTERP_METHODS = ("linear", "log", "nearest")
DEPTH_UNITS = ("ft", "m")

# Published vertical apertures of the vintage resistivity devices, in feet.
# These are measurements from the corpus, not house numbers - each row quotes
# the segment it came from. `note` carries the limit the prose states beyond the
# bare spacing.
VINTAGE_RESOLUTION_FT: dict[str, dict[str, Any]] = {
    "normal_16in": {
        "value": 16.0 / 12.0,
        "source": TRIESTE_1,
        "basis": "AM spacing 16 in",
        "note": "apparent bed thickness is less than actual by the spacing; "
                "below the spacing the curve reverses and reads a spurious minimum",
    },
    "normal_64in": {
        "value": 64.0 / 12.0,
        "source": TRIESTE_1,
        "basis": "AM spacing 64 in",
        "note": "apparent bed thickness is less than actual by the spacing",
    },
    "lateral_18ft8in": {
        "value": 18.0 + 8.0 / 12.0,
        "source": TRIESTE_1,
        "basis": "AO spacing 18 ft 8 in",
        "note": "a minimum bed thickness of about 50 ft is needed for plateau "
                "readings uninfluenced by surrounding formations; below that, a "
                "blind zone and a spurious reflection peak one AO spacing below the bed",
        "plateau_min_bed_ft": 50.0,
    },
    "ll7": {
        "value": 32.0 / 12.0,
        "source": TRIESTE_1,
        "basis": "i_o current sheet thickness approximately 32 in",
        "note": "sonde length A1A2 is 80 in",
    },
    "ll3": {
        "value": 12.0 / 12.0,
        "source": TRIESTE_2,
        "basis": "i_o current sheet thickness usually about 12 in",
        "note": "better vertical resolution than LL7; shows more detail",
    },
    "dll": {
        "value": 2.0,
        "source": TRIESTE_3,
        "basis": "nominal beam thickness of 2 ft",
        "note": "LLS has the same vertical resolution as LLD (2 ft)",
    },
}


# --- inputs and outputs -----------------------------------------------------


@dataclass(frozen=True)
class CurveSpec:
    """One curve to resample, with the interpolation method it may be read under.

    `method` has no default on purpose. See the module docstring.
    """

    values: Sequence[float | None]
    method: str
    unit: str = ""


@dataclass(frozen=True)
class ResampledCurve:
    """One curve on the output grid, with how much of it is measurement.

    Not a Quantity - Quantity holds one float. It carries the same provenance
    fields alongside the array so nothing here is an orphan number either.
    """

    mnemonic: str
    unit: str
    method: str
    source: str
    values: tuple[float | None, ...]
    n_exact: int
    n_interpolated: int
    n_null: int
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    @property
    def measured_fraction(self) -> float:
        """Share of output nodes that are an input sample verbatim."""
        n = len(self.values)
        return self.n_exact / n if n else 0.0


@dataclass(frozen=True)
class ResampleResult:
    depth: tuple[float, ...]
    depth_unit: str
    curves: dict[str, ResampledCurve | Refusal]
    step: Quantity
    source_step: Quantity
    upsample_ratio: Quantity
    tail_remainder: Quantity
    gaps: tuple[Range, ...] = ()
    method: str = "depth resample onto a uniform grid"
    source: str = NO_CITATION
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    @property
    def n_nodes(self) -> int:
        return len(self.depth)

    @property
    def refused_curves(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.curves.items() if isinstance(v, Refusal))


# --- the cited half ---------------------------------------------------------


def vintage_vertical_resolution(device: str) -> Quantity | Refusal:
    """Published vertical aperture of a named vintage resistivity device, in ft.

    The one cited number this module produces. Refuses an unnamed device rather
    than interpolating between tools it does not have.
    """
    key = device.strip().lower()
    row = VINTAGE_RESOLUTION_FT.get(key)
    if row is None:
        return Refusal(
            reason=f"no published vertical resolution held for device {device!r}",
            needed=(f"one of: {', '.join(sorted(VINTAGE_RESOLUTION_FT))}",
                    "or the aperture stated on the log heading"),
            source=TRIESTE_1,
        )
    assumptions: dict[str, Any] = {"device": key, "basis": row["basis"], "note": row["note"]}
    if "plateau_min_bed_ft" in row:
        assumptions["plateau_min_bed_ft"] = row["plateau_min_bed_ft"]
    return Quantity(
        value=float(row["value"]),
        unit="ft",
        method="published vertical aperture (Trieste, Log Interpretation Ch. 7)",
        source=row["source"],
        inputs={"device": key},
        assumptions=assumptions,
    )


# --- helpers ----------------------------------------------------------------


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _value_at(values: Sequence[float | None], i: int) -> float | None:
    """A sample, with NaN/inf read as a null. Never mutates the caller's array."""
    v = values[i]
    if v is None:
        return None
    if not _finite(v):
        return None
    return float(v)


def _interpolate(method: str, z: float, z0: float, v0: float, z1: float, v1: float
                 ) -> tuple[float | None, str | None]:
    """Value at z between two bracketing samples. Returns (value, problem)."""
    span = z1 - z0
    t = (z - z0) / span
    if method == "linear":
        return v0 + t * (v1 - v0), None
    if method == "log":
        if v0 <= 0.0 or v1 <= 0.0:
            return None, "log-method-nonpositive"
        lv = math.log10(v0) + t * (math.log10(v1) - math.log10(v0))
        return 10.0 ** lv, None
    if method == "nearest":
        # Ties go to the shallower sample. Deterministic, and recorded in
        # assumptions - an averaged tie would synthesise a value, which is
        # exactly what `nearest` exists to avoid.
        return (v0 if (z - z0) <= (z1 - z) else v1), None
    raise ValueError(f"unknown interpolation method {method!r}")  # unreachable


def _bracket(depths: Sequence[float], z: float, hint: int) -> int:
    """Index i with depths[i] <= z <= depths[i+1]. `hint` walks forward."""
    i = hint
    n = len(depths)
    while i + 2 < n and depths[i + 1] < z:
        i += 1
    return i


# --- the tool ---------------------------------------------------------------


def depth_resample(
    depth: Sequence[float],
    curves: Mapping[str, CurveSpec] | None = None,
    *,
    target_step: float,
    depth_unit: str,
    start: float | None = None,
    stop: float | None = None,
    vertical_resolution: float | None = None,
    max_upsample_ratio: float = MAX_UPSAMPLE_RATIO,
    gap_tolerance_ratio: float = GAP_TOLERANCE_RATIO,
) -> ResampleResult | Refusal:
    """Put curves on a uniform depth grid, and say what that cost.

    Every curve must state its interpolation method; gaps and nulls are never
    crossed; upsampling is always flagged and refused past `max_upsample_ratio`.
    See the module docstring for why each of those is not negotiable.
    """
    curves = dict(curves or {})

    # --- programmer error: bad call, not an unanswerable question ---
    if not isinstance(target_step, (int, float)) or not math.isfinite(float(target_step)) \
            or float(target_step) <= 0.0:
        raise ValueError(f"target_step must be a positive finite number, got {target_step!r}")
    if max_upsample_ratio <= 0 or gap_tolerance_ratio <= 0:
        raise ValueError("max_upsample_ratio and gap_tolerance_ratio must be positive")
    for name, spec in curves.items():
        if len(spec.values) != len(depth):
            raise ValueError(
                f"curve {name!r} has {len(spec.values)} values for {len(depth)} depths; "
                "resampling cannot align arrays of different length"
            )

    target_step = float(target_step)
    unit = str(depth_unit).strip().lower()
    if unit not in DEPTH_UNITS:
        return Refusal(
            reason=f"depth unit {depth_unit!r} not recognised; this tool does not guess one",
            needed=(f"depth_unit one of {DEPTH_UNITS}",
                    "normalise the index with unit_convert (#11) first"),
            source=NO_CITATION,
        )

    # --- validate the index ---
    if len(depth) < 2:
        return Refusal(
            reason=f"depth index has {len(depth)} sample(s); a step cannot be established",
            needed=("at least two depth samples",),
            source=NO_CITATION,
        )
    bad = [i for i, z in enumerate(depth) if z is None or not _finite(z)]
    if bad:
        return Refusal(
            reason=(f"depth index carries {len(bad)} non-finite or null value(s) "
                    f"(first at row {bad[0]}); the index itself is not a measurement "
                    "and cannot be repaired by interpolation"),
            needed=("a depth column with a finite value on every row",),
            source=NO_CITATION,
        )

    raw = [float(z) for z in depth]
    diffs = [raw[i + 1] - raw[i] for i in range(len(raw) - 1)]
    if any(d == 0.0 for d in diffs):
        i = next(i for i, d in enumerate(diffs) if d == 0.0)
        return Refusal(
            reason=(f"depth index repeats {raw[i]:.4f} {unit} at rows {i} and {i + 1}; "
                    "which sample governs a grid node is ambiguous"),
            needed=("a de-duplicated depth index",),
            source=NO_CITATION,
        )
    up = all(d > 0 for d in diffs)
    down = all(d < 0 for d in diffs)
    if not (up or down):
        return Refusal(
            reason=("depth index is not monotonic - it changes direction, so it is not a "
                    "single logging run and interpolation order is undefined"),
            needed=("a monotonic depth index",
                    "run curve_splice_detect (#14) to find the run boundaries, "
                    "then resample each run separately"),
            source=NO_CITATION,
        )

    flags: list[str] = []
    reversed_input = False
    order = list(range(len(raw)))
    if down:
        reversed_input = True
        order.reverse()
        raw = [raw[i] for i in order]
        diffs = [raw[i + 1] - raw[i] for i in range(len(raw) - 1)]
        flags.append("input-depth-reversed: index decreased with row number "
                     "(logged upward); reversed for resampling, output is ascending")

    # --- nominal step and gaps ---
    # Median, not mean: a 4 ft data gap must not inflate the nominal step.
    nominal = float(median(diffs))
    gap_threshold = gap_tolerance_ratio * nominal
    gaps = tuple(
        Range(low=raw[i], high=raw[i + 1], unit=unit,
              method=f"depth increment above {gap_tolerance_ratio} x nominal step",
              source=NO_CITATION,
              members={"increment": diffs[i], "nominal_step": nominal,
                       "threshold": gap_threshold})
        for i, d in enumerate(diffs) if d > gap_threshold
    )
    if gaps:
        flags.append(
            f"gaps-not-crossed: {len(gaps)} depth gap(s) wider than "
            f"{gap_tolerance_ratio} x {nominal:g} {unit}; nodes inside them are null, "
            "never interpolated across (curve_splice_detect #14 identifies the cause)"
        )

    # --- upsample check ---
    ratio = nominal / target_step
    if ratio > max_upsample_ratio:
        return Refusal(
            reason=(f"target step {target_step:g} {unit} is {ratio:.3g}x finer than the "
                    f"nominal recorded step {nominal:g} {unit}, above this project's own "
                    f"cap of {max_upsample_ratio:g}. Resampling adds no information: the "
                    f"extra samples would be arithmetic, not log readings, and the "
                    "recording tool's vertical aperture already exceeds either step "
                    "(see trieste#1). The cap is PROVISIONAL and owned by this project, "
                    "not taken from any source"),
            needed=(f"a target step no finer than {nominal / max_upsample_ratio:g} {unit}",
                    "or an explicit max_upsample_ratio= override accepting the invention"),
            source=NO_CITATION,
        )
    if ratio > 1.0:
        flags.append(
            f"upsample: output has {ratio:.3g}x the sample density of the input and "
            "no more information; interpolated nodes are arithmetic, not measurements"
        )
    elif ratio < 1.0:
        flags.append(
            "downsample-decimation: intermediate samples are discarded, not averaged; "
            "a thin bed may survive or vanish depending only on where a node lands. "
            "Block averaging would be a filter, not a resample - see the spec"
        )

    if vertical_resolution is not None:
        vr = float(vertical_resolution)
        if vr > 0 and target_step < vr:
            flags.append(
                f"grid-finer-than-vertical-resolution: target step {target_step:g} {unit} "
                f"is below the stated vertical resolution {vr:g} {unit} of the recording "
                "tool; adjacent output samples are not independent readings of the "
                f"formation ({TRIESTE_1})"
            )

    # --- build the grid ---
    lo, hi = raw[0], raw[-1]
    g0 = lo if start is None else float(start)
    g1 = hi if stop is None else float(stop)
    if g1 < g0:
        raise ValueError(f"stop {g1} is above start {g0}; the grid would be empty")
    n_nodes = int(math.floor((g1 - g0) / target_step + _DEPTH_TOL)) + 1
    grid = tuple(round(g0 + k * target_step, _GRID_DECIMALS) for k in range(n_nodes))
    if not grid or grid[-1] < lo - _DEPTH_TOL or grid[0] > hi + _DEPTH_TOL:
        return Refusal(
            reason=(f"the requested grid {g0:g}..{g1:g} {unit} does not overlap the data "
                    f"{lo:g}..{hi:g} {unit}; no node would carry a measurement"),
            needed=("a start/stop inside the logged interval",),
            source=NO_CITATION,
        )

    remainder = (g1 - grid[-1]) if grid else 0.0
    if remainder > _DEPTH_TOL:
        flags.append(
            f"tail-dropped: {remainder:g} {unit} at the bottom does not fill a whole "
            f"{target_step:g} {unit} cell; the partial interval is dropped, never "
            "stretched and never extrapolated"
        )
    outside = sum(1 for z in grid if z < lo - _DEPTH_TOL or z > hi + _DEPTH_TOL)
    if outside:
        flags.append(
            f"nodes-outside-data: {outside} node(s) fall outside the logged interval "
            f"{lo:g}..{hi:g} {unit} and are null; this tool does not extrapolate"
        )

    assumptions = {
        "max_upsample_ratio": max_upsample_ratio,
        "max_upsample_ratio_status": "PROVISIONAL - owned by this project, no corpus source",
        "gap_tolerance_ratio": gap_tolerance_ratio,
        "nominal_step_estimator": "median of positive first differences",
        "grid_origin": "first input depth" if start is None else "caller-supplied start",
        "nearest_tie_rule": "ties go to the shallower sample",
        "null_rule": "never interpolate across a null or a gap",
        "extrapolation": "none",
        "input_reversed": reversed_input,
    }
    if vertical_resolution is not None:
        assumptions["vertical_resolution"] = float(vertical_resolution)

    # --- per curve ---
    out: dict[str, ResampledCurve | Refusal] = {}
    for name, spec in curves.items():
        out[name] = _resample_one(
            name, spec, raw, order, grid, gaps, lo, hi, unit, assumptions,
        )
    refused = tuple(k for k, v in out.items() if isinstance(v, Refusal))
    if refused:
        flags.append(
            "curves-refused: " + ", ".join(sorted(refused))
            + " (interpolation method not stated or not recognised)"
        )

    q_inputs = {"n_input_rows": len(raw), "depth_first": lo, "depth_last": hi}
    return ResampleResult(
        depth=grid,
        depth_unit=unit,
        curves=out,
        step=Quantity(target_step, unit, "caller-stated target grid step", NO_CITATION,
                      inputs=q_inputs, assumptions=assumptions),
        source_step=Quantity(nominal, unit,
                             "median of positive first differences of the input index",
                             NO_CITATION, inputs=q_inputs),
        upsample_ratio=Quantity(ratio, "dimensionless",
                                "nominal source step / target step", NO_CITATION,
                                inputs={"source_step": nominal, "target_step": target_step},
                                assumptions={"above_1_means": "output invents samples"}),
        tail_remainder=Quantity(max(remainder, 0.0), unit,
                                "interval below the last grid node, dropped", NO_CITATION,
                                inputs={"last_node": grid[-1], "stop": g1}),
        gaps=gaps,
        flags=tuple(flags),
        assumptions=assumptions,
    )


def _resample_one(
    name: str,
    spec: CurveSpec,
    raw: list[float],
    order: list[int],
    grid: Sequence[float],
    gaps: Sequence[Range],
    lo: float,
    hi: float,
    unit: str,
    grid_assumptions: dict[str, Any],
) -> ResampledCurve | Refusal:
    method = (spec.method or "").strip().lower()
    if method not in INTERP_METHODS:
        return Refusal(
            reason=(f"curve {name!r} has no usable interpolation method "
                    f"(given {spec.method!r}). This tool will not pick one: linear "
                    "interpolation of a curve that lives on a log scale (resistivity) is "
                    "wrong by tens of percent, and linear interpolation of a flag or "
                    "lithology code invents a category. Neither is visible downstream"),
            needed=(f"CurveSpec.method one of {INTERP_METHODS}",
                    "'log' for resistivity and anything spanning decades",
                    "'nearest' for flags, indicators and categorical curves",
                    "'linear' for additive curves (GR, RHOB, NPHI, DT, CALI)"),
            source=NO_CITATION,
        )

    # Read the caller's array in ascending-depth order without touching it.
    values = [_value_at(spec.values, i) for i in order]

    out: list[float | None] = []
    n_exact = n_interp = n_null = 0
    problems: set[str] = set()
    hint = 0
    for z in grid:
        if z < lo - _DEPTH_TOL or z > hi + _DEPTH_TOL:
            out.append(None)
            n_null += 1
            continue
        i = _bracket(raw, z, hint)
        hint = i
        # Exact hit on a recorded sample: take it verbatim, whatever the method.
        if abs(z - raw[i]) <= _DEPTH_TOL:
            v = values[i]
        elif abs(z - raw[i + 1]) <= _DEPTH_TOL:
            v = values[i + 1]
        else:
            v = None
            if any(g.low - _DEPTH_TOL <= z <= g.high + _DEPTH_TOL for g in gaps):
                problems.add("gap")
            else:
                v0, v1 = values[i], values[i + 1]
                if v0 is None or v1 is None:
                    problems.add("null-halo")
                else:
                    v, problem = _interpolate(method, z, raw[i], v0, raw[i + 1], v1)
                    if problem:
                        problems.add(problem)
            if v is None:
                out.append(None)
                n_null += 1
                continue
            out.append(v)
            n_interp += 1
            continue
        if v is None:
            out.append(None)
            n_null += 1
        else:
            out.append(v)
            n_exact += 1

    curve_flags: list[str] = []
    if "null-halo" in problems:
        curve_flags.append(
            "null-halo: nodes bracketed by a null are null; this tool never reaches past "
            "a null to the next real sample, because that would fill the gap silently"
        )
    if "gap" in problems:
        curve_flags.append("gap: nodes inside a depth gap are null, never interpolated across")
    if "log-method-nonpositive" in problems:
        curve_flags.append(
            "log-method-nonpositive: a bracketing sample was <= 0 and has no logarithm; "
            "those interpolated nodes are null. A non-positive sample landing on a grid "
            "node is still passed through verbatim - this tool does not edit measurements "
            "(null_scrub #12 should have caught an undeclared sentinel)"
        )
    if n_null:
        curve_flags.append(f"null-nodes: {n_null} of {len(grid)} output nodes carry no value")

    return ResampledCurve(
        mnemonic=name,
        unit=spec.unit,
        method=f"{method} interpolation onto a uniform depth grid",
        source=NO_CITATION,
        values=tuple(out),
        n_exact=n_exact,
        n_interpolated=n_interp,
        n_null=n_null,
        inputs={"n_input_rows": len(raw), "depth_unit": unit},
        assumptions={
            "interpolation_method": method,
            "method_stated_by": "caller - this tool never infers a curve's method",
            **{k: grid_assumptions[k] for k in
               ("nearest_tie_rule", "null_rule", "extrapolation")},
        },
        flags=tuple(curve_flags),
    )

# ---------------------------------------------------------------------------
# 14_curve_splice_detect
# Run-boundary detection and cross-run discontinuity measurement. Tool #14, group B.
# ---------------------------------------------------------------------------

# Single source of truth for the cross-run depth-registry allowance. #8 owns it.

# ---------------------------------------------------------------------------
# Corpus anchors
# ---------------------------------------------------------------------------

ASQUITH_HEADING = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#10"
RRC_REAL_HEADER = "09-gas-deliverability/rrc-section-f-completions-electric-logs#16"
BEG_DATA_PREP = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#36"
BEG_WORKFLOW = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#33"
BEG_TOOL_HISTORY = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#34"
LAS_SECTIONS = "02-las-format/kgs-las-2.0-field-table#1"

# The tool's own citation: runs exist and disagree in depth registry (asquith#64),
# the run table is header data (rrc#16), the practice is a depth shift to the
# nearest foot against the resistivity suite (beg#36/#33).
SOURCE = ASQUITH_RUNS


# ---------------------------------------------------------------------------
# Thresholds. Nothing numeric below appears inline in the procedures.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Threshold:
    """One owned number, with the status the catalog would print for it.

    `status` is one of:
      SOURCED    - the corpus states it
      DERIVED    - a sourced number reused for a second purpose, stated here
      PROVISIONAL- ours, overridable
      CALLER     - the tool refuses to run without being told
      NUMERICAL  - float hygiene, not a domain number
    """

    name: str
    value: float | None
    unit: str
    status: str
    source: str
    basis: str


THRESHOLDS: dict[str, Threshold] = {
    "cross_run_registry_ft": Threshold(
        name="cross-run depth-registry allowance",
        value=CROSS_RUN_REGISTRY_FT,
        unit="ft",
        status="SOURCED",
        source=f"{ASQUITH_RUNS} + {BEG_DATA_PREP} + {BEG_WORKFLOW}",
        basis=(
            "asquith#64: log values 'may be peak or trough values from as much as "
            "1 ft above or below the listed depths ... a suite of logs generally "
            "requires more than one logging run ... some logs differ slightly in "
            "depth-registry of beds'. beg#36: multi-run wells 'were depth-shifted "
            "to match the resistivity suite to the nearest foot'. Two independent "
            "statements of one quantity; imported from tools/raster.py so #8 and "
            "#14 cannot drift. tool-catalog.md widens it to +/-2 ft for "
            "perf-in-zone; that is a different decision and is not applied here."
        ),
    ),
    "registry_lag_step_ft": Threshold(
        name="registry lag search grid",
        value=1.0,
        unit="ft",
        status="SOURCED",
        source=BEG_DATA_PREP,
        basis=(
            "beg#36 depth-shifts runs 'to the nearest foot', so the lag grid is "
            "whole feet, searched only within the registry allowance: {-1, 0, +1}."
        ),
    ),
    "gap_significance_ft": Threshold(
        name="index-gap significance",
        value=CROSS_RUN_REGISTRY_FT,
        unit="ft",
        status="DERIVED",
        source=ASQUITH_RUNS,
        basis=(
            "an index jump exceeding the modal step by less than the registry "
            "allowance is inside the noise the runs are known to carry, so it is "
            "not evidence of an unlogged interval. Reuses the sourced number "
            "rather than inventing a second one."
        ),
    ),
    "cluster_distance_ft": Threshold(
        name="candidate clustering distance",
        value=CROSS_RUN_REGISTRY_FT,
        unit="ft",
        status="DERIVED",
        source=ASQUITH_RUNS,
        basis=(
            "two detectors firing within the depth precision at which runs are "
            "known to disagree are describing one boundary, not two."
        ),
    ),
    "offset_aperture_ft": Threshold(
        name="offset aperture",
        value=None,
        unit="ft",
        status="CALLER",
        source="",
        basis=(
            "no source states how far above and below a splice to average. Too "
            "short and the median is noise; too long and it swallows a bed. The "
            "tool refuses rather than defaulting."
        ),
    ),
    "offset_tolerance": Threshold(
        name="per-curve offset tolerance (calibration verdict)",
        value=None,
        unit="curve units",
        status="CALLER",
        source="",
        basis=(
            "the corpus supplies no magnitude at which a cross-run discontinuity "
            "becomes a calibration problem, and any such number would be per "
            "curve, per vintage and per vendor. The offset is always measured; "
            "the verdict is only reached on request."
        ),
    ),
    "float_rtol": Threshold(
        name="float comparison tolerance",
        value=1e-9,
        unit="relative",
        status="NUMERICAL",
        source="",
        basis="float hygiene for depth equality and modal-step matching; not a domain number.",
    ),
}

_ALLOWANCE_FT: float = float(THRESHOLDS["cross_run_registry_ft"].value)
_LAG_STEP_FT: float = float(THRESHOLDS["registry_lag_step_ft"].value)
_GAP_SIG_FT: float = float(THRESHOLDS["gap_significance_ft"].value)
_CLUSTER_FT: float = float(THRESHOLDS["cluster_distance_ft"].value)
_RTOL: float = float(THRESHOLDS["float_rtol"].value)

# The integer-foot lags searched on an overlap. beg#36 "to the nearest foot",
# bounded by asquith#64's +/-1 ft. Derived, never typed as a literal list.
_LAGS_FT: tuple[float, ...] = tuple(
    _LAG_STEP_FT * k
    for k in range(-int(_ALLOWANCE_FT // _LAG_STEP_FT), int(_ALLOWANCE_FT // _LAG_STEP_FT) + 1)
)


# ---------------------------------------------------------------------------
# Observations. Real corpus numbers that are NOT thresholds, kept separate so
# nothing here can be mistaken for a cutoff.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Observation:
    """A magnitude the corpus reports, for a caller choosing a tolerance."""

    name: str
    value: float | None
    unit: str
    source: str
    quote: str
    is_threshold: bool = False
    caveat: str = ""


CORPUS_OBSERVATIONS: dict[str, Observation] = {
    "normalization_shift_max_pu": Observation(
        name="largest neutron/density normalization shift applied at Boonsville",
        value=10.0,
        unit="porosity units",
        source=BEG_DATA_PREP,
        quote="Some shifts were as high as 10 porosity units.",
        caveat=(
            "This is the largest correction APPLIED in a WELL-TO-WELL "
            "normalization against a standard crossplot. It is not a detection "
            "threshold and it is not run-to-run within one well. Using it as a "
            "cutoff would present a fabricated number as sourced."
        ),
    ),
    "vendor_recalibration_tendency": Observation(
        name="vendor tendency to need recalibration",
        value=None,
        unit="",
        source=BEG_DATA_PREP,
        quote=(
            "Generally Halliburton and Western Atlas logs required more of this "
            "recalibration than did Schlumberger logs."
        ),
        caveat=(
            "A tendency, not a rule. beg#34 states the opposing observation: 'The "
            "differences in the tools of the various vendors are not enough to "
            "make any substantial difference to the water-saturation "
            "calculations.' A service-company change is therefore recorded and "
            "flagged for attention; it never raises a verdict on its own."
        ),
    ),
    "depth_shift_reference_suite": Observation(
        name="the run the others are shifted to match",
        value=None,
        unit="",
        source=BEG_WORKFLOW,
        quote=(
            "depth-shift the various log suites to a common depth (usually on the "
            "basis of the resistivity suite)"
        ),
        caveat="Boonsville practice. This tool detects and measures; it does not shift.",
    ),
}


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunInterval:
    """One logging run's declared coverage, as read off the log header.

    `rrc-section-f#16` shows the real table this comes from: Run Number, Bit
    From / To / Size, casing record. `header_extract` (#4) owns RRC items C
    ("Depths logged") and D ("Bit sizes"); until it returns the per-run form,
    the caller assembles these.
    """

    run_id: str
    top_ft: float
    bottom_ft: float
    bit_size_in: float | None = None
    service_company: str | None = None
    date_logged: str | None = None
    evidence: str = "declared"

    def __post_init__(self) -> None:
        _require_finite("top_ft", self.top_ft)
        _require_finite("bottom_ft", self.bottom_ft)
        if not isinstance(self.run_id, str):
            raise TypeError("RunInterval.run_id must be a string naming the logging run")
        if self.top_ft > self.bottom_ft:
            raise ValueError(
                f"RunInterval {self.run_id!r} is inverted: top_ft {self.top_ft} is "
                f"below bottom_ft {self.bottom_ft}"
            )


@dataclass(frozen=True)
class RunLog:
    """The curve data as it came off ONE logging run, with its own depth index.

    Used for the overlap comparison, where the same rock was logged twice: a
    genuine run overlap, or the "Main Pass and Repeat Pass" of `rrc#16`.
    """

    run_id: str
    depth_ft: Sequence[float]
    curves: Mapping[str, Sequence[Any]]
    bit_size_in: float | None = None
    service_company: str | None = None
    date_logged: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str):
            raise TypeError("RunLog.run_id must be a string naming the logging run")
        n = len(self.depth_ft)
        for name, vals in self.curves.items():
            if len(vals) != n:
                raise ValueError(
                    f"curve {name!r} on run {self.run_id!r} has {len(vals)} samples "
                    f"against {n} depths"
                )


@dataclass(frozen=True)
class SpliceBoundary:
    """One depth at which the curve set is believed to change logging run."""

    depth: Quantity
    kind: str                       # overlap|abutment|gap|sampling-step-change|
                                    # index-reversal|index-duplicate|index-gap|curve-onset|curve-terminus
    evidence: tuple[str, ...]
    above_run: str | None
    below_run: str | None
    overlap: Range | None
    gap: Range | None
    curves: tuple[str, ...]
    corroborated: bool
    registry_allowance: Quantity
    flags: tuple[str, ...] = ()
    source: str = SOURCE


@dataclass(frozen=True)
class SpliceOffset:
    """The measured discontinuity in one curve across one boundary."""

    curve: str
    boundary_depth_ft: float
    basis: str                      # "overlap" | "aperture"
    offset: Quantity
    above_stat: Quantity
    below_stat: Quantity
    n_above: int
    n_below: int
    registry_lag_ft: Quantity | None
    verdict: str                    # within-tolerance|exceeds-tolerance|no-tolerance-supplied
    tolerance: Quantity | None
    flags: tuple[str, ...] = ()
    source: str = SOURCE


@dataclass(frozen=True)
class SpliceReport:
    """Boundaries, and what each curve does across them."""

    boundaries: tuple[SpliceBoundary, ...]
    offsets: tuple[SpliceOffset, ...]
    unmeasurable: tuple[dict[str, Any], ...]
    declared_runs: tuple[RunInterval, ...]
    depth_span: Range
    modal_step: Quantity | None
    verdict_reached: bool
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)
    source: str = SOURCE

    @property
    def boundary_depths_ft(self) -> tuple[float, ...]:
        return tuple(b.depth.value for b in self.boundaries)


# ---------------------------------------------------------------------------
# Small helpers. Programmer error raises; domain limits refuse.
# ---------------------------------------------------------------------------

def _require_finite(name: str, value: float) -> float:
    v = float(value)
    if not math.isfinite(v):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return v


def _is_null(v: Any, null_value: float | None) -> bool:
    if v is None:
        return True
    try:
        f = float(v)
    except (TypeError, ValueError):
        return True
    if not math.isfinite(f):
        return True
    if null_value is not None and math.isclose(f, null_value, rel_tol=_RTOL, abs_tol=1e-12):
        return True
    return False


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=_RTOL, abs_tol=1e-9)


def _modal_step_ft(depths: Sequence[float]) -> float | None:
    """The most common absolute interval, rounded to suppress float noise."""
    diffs = [abs(depths[i + 1] - depths[i]) for i in range(len(depths) - 1)]
    diffs = [d for d in diffs if d > 0.0]
    if not diffs:
        return None
    counts = Counter(round(d, 6) for d in diffs)
    return float(counts.most_common(1)[0][0])


def _nearest(sorted_depths: Sequence[float], target: float) -> tuple[int, float]:
    """Index of the sample nearest `target`, and its distance. Binary search.

    A real LAS index runs to tens of thousands of samples and the lag search
    walks it once per lag, so a linear scan per lookup is quadratic and will
    hang on a full-size file.
    """
    n = len(sorted_depths)
    if n == 0:
        return -1, math.inf
    i = bisect_left(sorted_depths, target)
    best, dist = -1, math.inf
    for k in (i - 1, i, i + 1):
        if 0 <= k < n:
            d = abs(sorted_depths[k] - target)
            if d < dist:
                best, dist = k, d
    return best, dist


def _median(vals: Sequence[float]) -> float:
    return float(statistics.median(vals))


def _residual_dispersion(vals: Sequence[float]) -> float:
    """Mean absolute deviation about the median. Zero iff the series is constant.

    Not the *median* absolute deviation: that stays at zero while up to half the
    residuals disagree, which is exactly the case a depth mis-registry produces
    when the curve has one feature in the window (half the samples land on each
    limb of it). The mean form moves as soon as any residual breaks ranks, which
    is what the lag search needs.
    """
    if not vals:
        return math.inf
    m = _median(vals)
    return sum(abs(v - m) for v in vals) / len(vals)


def _unit_for(curve: str, curve_units: Mapping[str, str] | None) -> tuple[str, bool]:
    if curve_units and curve in curve_units and str(curve_units[curve]).strip():
        return str(curve_units[curve]), True
    return "curve units", False


def _allowance_quantity() -> Quantity:
    t = THRESHOLDS["cross_run_registry_ft"]
    return Quantity(
        value=t.value,
        unit=t.unit,
        method="cross-run depth-registry allowance",
        source=t.source,
        inputs={},
        assumptions={"status": t.status, "basis": t.basis},
    )


def _validate_runs(runs: Sequence[RunInterval]) -> Refusal | None:
    seen: set[str] = set()
    for r in runs:
        if not r.run_id.strip():
            # Mirrors raster_depth_register R2: registry is per run, so an
            # unnamed run cannot be kept apart from another.
            return Refusal(
                reason=(
                    "a declared logging run has no run_id; a log suite generally "
                    "requires more than one logging run and the runs differ in "
                    "depth-registry of beds, so an unnamed run cannot be kept apart"
                ),
                needed=("a run_id on every RunInterval",),
                source=SOURCE,
            )
        if r.run_id in seen:
            return Refusal(
                reason=f"two declared runs share the run_id {r.run_id!r}",
                needed=("a distinct run_id per RunInterval",),
                source=SOURCE,
            )
        seen.add(r.run_id)
    return None


# ---------------------------------------------------------------------------
# Candidate detectors
# ---------------------------------------------------------------------------

@dataclass
class _Candidate:
    depth: float
    kind: str
    evidence: str
    above_run: str | None = None
    below_run: str | None = None
    overlap: tuple[float, float] | None = None
    gap: tuple[float, float] | None = None
    curve: str | None = None
    declared: bool = False
    flags: tuple[str, ...] = ()


def _index_candidates(depths: Sequence[float], modal_step: float | None) -> list[_Candidate]:
    """Reversal, duplicate, gap and persistent sampling-step change.

    `depths` is already oriented increasing. A local decrease against that
    orientation is a re-entry into rock already logged, which is two runs over
    the same interval.
    """
    out: list[_Candidate] = []
    n = len(depths)
    for i in range(n - 1):
        d0, d1 = depths[i], depths[i + 1]
        delta = d1 - d0
        if _close(d0, d1):
            out.append(_Candidate(d1, "index-duplicate", "index-duplicate"))
        elif delta < 0.0:
            out.append(
                _Candidate(
                    depth=0.5 * (d0 + d1),
                    kind="index-reversal",
                    evidence="index-reversal",
                    overlap=(d1, d0),
                )
            )
        elif modal_step is not None and delta > modal_step + _GAP_SIG_FT:
            out.append(
                _Candidate(
                    depth=0.5 * (d0 + d1),
                    kind="index-gap",
                    evidence="index-gap",
                    gap=(d0, d1),
                )
            )

    # Persistent sampling-step change: the modal interval shifts and the new one
    # repeats. A single odd interval is a gap or jitter, not a new acquisition.
    steps = [round(depths[i + 1] - depths[i], 6) for i in range(n - 1)]
    current: float | None = None
    for i, s in enumerate(steps):
        if s <= 0:
            continue
        if current is None:
            current = s
            continue
        if _close(s, current):
            continue
        if i + 1 < len(steps) and _close(steps[i + 1], s):
            out.append(
                _Candidate(
                    depth=depths[i],
                    kind="sampling-step-change",
                    evidence=f"sampling-step-change:{current:g}->{s:g}ft",
                )
            )
            current = s
    return out


def _null_block_candidates(
    depths: Sequence[float],
    curves: Mapping[str, Sequence[Any]],
    null_value: float | None,
) -> list[_Candidate]:
    """Leading / trailing null blocks per curve.

    Only the leading and trailing blocks count. An interior null block is far
    more likely a washout or a bad-hole edit than a run boundary, and no source
    distinguishes them - see the spec's open questions.
    """
    out: list[_Candidate] = []
    if not depths:
        return out
    top, bottom = depths[0], depths[-1]
    for name, vals in curves.items():
        live = [i for i, v in enumerate(vals) if not _is_null(v, null_value)]
        if not live:
            continue
        onset, terminus = depths[live[0]], depths[live[-1]]
        if onset - top > _ALLOWANCE_FT:
            out.append(
                _Candidate(onset, "curve-onset", f"curve-onset:{name}", curve=name)
            )
        if bottom - terminus > _ALLOWANCE_FT:
            out.append(
                _Candidate(terminus, "curve-terminus", f"curve-terminus:{name}", curve=name)
            )
    return out


def _declared_candidates(runs: Sequence[RunInterval]) -> list[_Candidate]:
    """Boundary geometry between consecutive declared runs."""
    out: list[_Candidate] = []
    ordered = sorted(runs, key=lambda r: (r.top_ft, r.bottom_ft))
    for a, b in zip(ordered, ordered[1:]):
        tag = f"declared:{a.run_id}/{b.run_id}"
        if b.top_ft < a.bottom_ft - _ALLOWANCE_FT:
            out.append(
                _Candidate(
                    depth=0.5 * (b.top_ft + a.bottom_ft),
                    kind="overlap",
                    evidence=tag,
                    above_run=a.run_id,
                    below_run=b.run_id,
                    overlap=(b.top_ft, a.bottom_ft),
                    declared=True,
                    flags=(
                        "boundary depth inside an overlap is a convention; the "
                        "overlap Range is the evidence",
                    ),
                )
            )
        elif abs(b.top_ft - a.bottom_ft) <= _ALLOWANCE_FT:
            out.append(
                _Candidate(
                    depth=0.5 * (b.top_ft + a.bottom_ft),
                    kind="abutment",
                    evidence=tag,
                    above_run=a.run_id,
                    below_run=b.run_id,
                    declared=True,
                )
            )
        else:
            out.append(
                _Candidate(
                    depth=0.5 * (b.top_ft + a.bottom_ft),
                    kind="gap",
                    evidence=tag,
                    above_run=a.run_id,
                    below_run=b.run_id,
                    gap=(a.bottom_ft, b.top_ft),
                    declared=True,
                )
            )
        if a.service_company and b.service_company and a.service_company != b.service_company:
            out[-1].flags = out[-1].flags + (
                f"service company changes across this boundary: "
                f"{a.service_company!r} -> {b.service_company!r}; beg#34 states "
                "vendor differences do not materially change Sw, so this is an "
                "attribute for attention, not a verdict",
            )
        if a.bit_size_in is not None and b.bit_size_in is not None and not _close(
            a.bit_size_in, b.bit_size_in
        ):
            out[-1].flags = out[-1].flags + (
                f"bit size changes across this boundary: {a.bit_size_in} in -> "
                f"{b.bit_size_in} in (RRC header item D, per-run table)",
            )
    return out


_KIND_RANK = {
    "overlap": 0,
    "abutment": 1,
    "gap": 2,
    "index-reversal": 3,
    "index-duplicate": 4,
    "index-gap": 5,
    "sampling-step-change": 6,
    "curve-onset": 7,
    "curve-terminus": 8,
}


def _cluster(cands: Sequence[_Candidate]) -> list[SpliceBoundary]:
    """Merge candidates within the registry allowance into single boundaries."""
    if not cands:
        return []
    ordered = sorted(cands, key=lambda c: c.depth)
    groups: list[list[_Candidate]] = [[ordered[0]]]
    for c in ordered[1:]:
        if abs(c.depth - groups[-1][-1].depth) <= _CLUSTER_FT:
            groups[-1].append(c)
        else:
            groups.append([c])

    boundaries: list[SpliceBoundary] = []
    for g in groups:
        declared = [c for c in g if c.declared]
        chosen = min(g, key=lambda c: _KIND_RANK.get(c.kind, 99))
        depth = declared[0].depth if declared else chosen.depth
        kind = declared[0].kind if declared else chosen.kind
        ov = next((c.overlap for c in g if c.overlap), None)
        gp = next((c.gap for c in g if c.gap), None)
        above = next((c.above_run for c in g if c.above_run), None)
        below = next((c.below_run for c in g if c.below_run), None)
        flags: tuple[str, ...] = ()
        for c in g:
            for f in c.flags:
                if f not in flags:
                    flags = flags + (f,)
        if not declared:
            flags = flags + (
                "inferred from the data; no declared run table corroborates it",
            )
        boundaries.append(
            SpliceBoundary(
                depth=Quantity(
                    value=depth,
                    unit="ft",
                    method=f"run boundary, {kind}",
                    source=RRC_REAL_HEADER if declared else SOURCE,
                    inputs={"evidence": sorted({c.evidence for c in g})},
                    assumptions={
                        "registry_allowance_ft": _ALLOWANCE_FT,
                        "depth_reference": "as supplied on the index; datum not resolved here",
                    },
                ),
                kind=kind,
                evidence=tuple(sorted({c.evidence for c in g})),
                above_run=above,
                below_run=below,
                overlap=(
                    Range(
                        low=min(ov),
                        high=max(ov),
                        unit="ft",
                        method="interval logged by both runs",
                        source=RRC_REAL_HEADER,
                    )
                    if ov
                    else None
                ),
                gap=(
                    Range(
                        low=min(gp),
                        high=max(gp),
                        unit="ft",
                        method="interval logged by neither run",
                        source=RRC_REAL_HEADER,
                    )
                    if gp
                    else None
                ),
                curves=tuple(sorted({c.curve for c in g if c.curve})),
                corroborated=bool(declared) and any(not c.declared for c in g),
                registry_allowance=_allowance_quantity(),
                flags=flags,
            )
        )
    return boundaries


# ---------------------------------------------------------------------------
# Stage 1 - boundaries only
# ---------------------------------------------------------------------------

def splice_candidates(
    depth_ft: Sequence[float],
    curves: Mapping[str, Sequence[Any]] | None = None,
    *,
    declared_runs: Sequence[RunInterval] | None = None,
    null_value: float | None = None,
    allow_curve_step_inference: bool = False,
) -> SpliceReport | Refusal:
    """Locate run boundaries from the header, the index, the nulls and the step.

    See `specs/14-curve_splice_detect.md`. Returns a report whose `offsets` is
    empty; `curve_splice_detect` adds the measurement stage on top.
    """
    curves = dict(curves or {})
    runs = tuple(declared_runs or ())

    # R5 - the decision this tool exists to hold.
    if allow_curve_step_inference:
        return Refusal(
            reason=(
                "a step in a curve is a bed boundary until a run boundary is "
                "independently evidenced; inferring run boundaries from curve "
                "shape would nominate every formation top in the well. Boundaries "
                "come from the header run table, the depth index, the null "
                "pattern or the sampling step only"
            ),
            needed=(
                "a declared run table (RRC header item C/D, see rrc-section-f#16), "
                "or a depth overlap, index gap, sampling-step change or null-block "
                "edge in the data",
            ),
            source=SOURCE,
        )

    depths = [_require_finite("depth_ft", d) for d in depth_ft]
    for name, vals in curves.items():
        if len(vals) != len(depths):
            raise ValueError(
                f"curve {name!r} has {len(vals)} samples against {len(depths)} depths"
            )

    # R2
    if len(depths) < 2:
        return Refusal(
            reason=f"a depth index of {len(depths)} sample(s) has no interval to inspect",
            needed=("at least two depth samples",),
            source=LAS_SECTIONS,
        )

    # R4
    bad = _validate_runs(runs)
    if bad is not None:
        return bad

    # R3
    if _close(depths[0], depths[-1]):
        return Refusal(
            reason=(
                "the depth index starts and ends at the same depth, so its "
                "direction cannot be determined and a local reversal cannot be "
                "told from the file's own ordering"
            ),
            needed=("a depth index whose first and last samples differ",),
            source=LAS_SECTIONS,
        )

    descending = depths[-1] < depths[0]
    if descending:
        depths = list(reversed(depths))
        curves = {k: list(reversed(list(v))) for k, v in curves.items()}

    modal_step = _modal_step_ft(depths)
    cands: list[_Candidate] = []
    cands += _declared_candidates(runs)
    cands += _index_candidates(depths, modal_step)
    cands += _null_block_candidates(depths, curves, null_value)

    boundaries = _cluster(cands)

    flags: list[str] = []
    if descending:
        flags.append("depth index was descending; reoriented ascending for detection")
    if null_value is not None:
        flags.append(
            "a declared null value was used; the declared NULL is not sufficient "
            "(undeclared sentinels such as -999.25 and -9999 both occur) - pass "
            "null_scrub (#12) output instead"
        )
    if not boundaries:
        flags.append(
            "no run boundary is evidenced; LAS 2.0 declares no per-run metadata "
            f"({LAS_SECTIONS}), so a cleanly merged multi-run file is "
            "indistinguishable from a single-run file - this is NOT evidence of a "
            "single run"
        )
    if not runs:
        flags.append(
            "no declared run table was supplied; every boundary here is inferred. "
            "The run table is header data (RRC header item C/D, rrc-section-f#16)"
        )

    return SpliceReport(
        boundaries=tuple(boundaries),
        offsets=(),
        unmeasurable=(),
        declared_runs=runs,
        depth_span=Range(
            low=min(depths),
            high=max(depths),
            unit="ft",
            method="depth index span as supplied",
            source=LAS_SECTIONS,
        ),
        modal_step=(
            None
            if modal_step is None
            else Quantity(
                value=modal_step,
                unit="ft",
                method="modal depth interval of the index",
                source=LAS_SECTIONS,
                inputs={"n_samples": len(depths)},
            )
        ),
        verdict_reached=False,
        flags=tuple(flags),
        assumptions={
            "registry_allowance_ft": _ALLOWANCE_FT,
            "thresholds": {k: t.status for k, t in THRESHOLDS.items()},
            "stage": "boundaries only; no curve offsets measured",
        },
    )


# ---------------------------------------------------------------------------
# Stage 2 - the offsets
# ---------------------------------------------------------------------------

def _window(
    depths: Sequence[float],
    vals: Sequence[Any],
    lo: float,
    hi: float,
    null_value: float | None,
) -> list[float]:
    out: list[float] = []
    for d, v in zip(depths, vals):
        if lo <= d <= hi and not _is_null(v, null_value):
            out.append(float(v))
    return out


def curve_splice_detect(
    depth_ft: Sequence[float],
    curves: Mapping[str, Sequence[Any]],
    *,
    aperture_ft: float | None = None,
    declared_runs: Sequence[RunInterval] | None = None,
    offset_tolerance: Mapping[str, float] | None = None,
    curve_units: Mapping[str, str] | None = None,
    null_value: float | None = None,
    allow_curve_step_inference: bool = False,
) -> SpliceReport | Refusal:
    """Locate run boundaries and measure each curve's discontinuity across them.

    See `specs/14-curve_splice_detect.md`. Refuses on: no `aperture_ft` (CALLER),
    fewer than two depths, an index with no direction, an unnamed or duplicated
    run, no curves, and any request to infer boundaries from curve steps.

    The offset is always measured. The calibration verdict is reached only where
    the caller supplied a tolerance for that curve: no source in the corpus
    states how large a cross-run discontinuity has to be to be a problem.
    """
    curves = dict(curves)

    # R6 - measuring is the whole second half of this tool.
    if not curves:
        return Refusal(
            reason="no curves were supplied, so there is nothing to measure across a boundary",
            needed=("at least one curve",),
            source=SOURCE,
        )

    # R1 - CALLER threshold.
    if aperture_ft is None:
        t = THRESHOLDS["offset_aperture_ft"]
        return Refusal(
            reason=(
                "aperture_ft was not supplied. No source in the corpus states how "
                f"far above and below a splice to average: {t.basis}"
            ),
            needed=("aperture_ft, in feet, exceeding the cross-run registry allowance",),
            source=SOURCE,
        )
    aperture = _require_finite("aperture_ft", aperture_ft)
    if aperture <= 0:
        raise ValueError(f"aperture_ft must be positive, got {aperture_ft!r}")
    if aperture <= _ALLOWANCE_FT:
        return Refusal(
            reason=(
                f"an aperture of {aperture:g} ft does not exceed the cross-run "
                f"depth-registry allowance of {_ALLOWANCE_FT:g} ft, so every sample "
                "in it is inside the depth uncertainty of the boundary itself"
            ),
            needed=(f"aperture_ft greater than {_ALLOWANCE_FT:g} ft",),
            source=SOURCE,
        )

    stage1 = splice_candidates(
        depth_ft,
        curves,
        declared_runs=declared_runs,
        null_value=null_value,
        allow_curve_step_inference=allow_curve_step_inference,
    )
    if isinstance(stage1, Refusal):
        return stage1

    depths = [float(d) for d in depth_ft]
    work_curves = {k: list(v) for k, v in curves.items()}
    if depths[-1] < depths[0]:
        depths = list(reversed(depths))
        work_curves = {k: list(reversed(v)) for k, v in work_curves.items()}

    tolerances = dict(offset_tolerance or {})
    offsets: list[SpliceOffset] = []
    unmeasurable: list[dict[str, Any]] = []

    for b in stage1.boundaries:
        d = b.depth.value
        lo_a, hi_a = d - _ALLOWANCE_FT - aperture, d - _ALLOWANCE_FT
        lo_b, hi_b = d + _ALLOWANCE_FT, d + _ALLOWANCE_FT + aperture
        for name in sorted(work_curves):
            vals = work_curves[name]
            above = _window(depths, vals, lo_a, hi_a, null_value)
            below = _window(depths, vals, lo_b, hi_b, null_value)
            if not above or not below:
                unmeasurable.append(
                    {
                        "curve": name,
                        "boundary_depth_ft": d,
                        "n_above": len(above),
                        "n_below": len(below),
                        "reason": (
                            "one side of the boundary has no live sample inside the "
                            "aperture, once the +/- registry allowance exclusion is "
                            "applied"
                        ),
                    }
                )
                continue
            unit, unit_known = _unit_for(name, curve_units)
            m_a, m_b = _median(above), _median(below)
            off = m_b - m_a
            tol = tolerances.get(name)
            if tol is None:
                verdict = "no-tolerance-supplied"
                tol_q = None
            else:
                tol_v = abs(_require_finite("offset_tolerance", tol))
                verdict = "exceeds-tolerance" if abs(off) > tol_v else "within-tolerance"
                tol_q = Quantity(
                    value=tol_v,
                    unit=unit,
                    method="caller-supplied cross-run offset tolerance",
                    source="CALLER - no corpus source states a discontinuity magnitude",
                    inputs={"curve": name},
                )
            flags = [
                "aperture basis: the two windows are different rock, so this offset "
                "is confounded with real geology. An overlap, where both runs logged "
                "the same interval, is the only unconfounded measurement - see "
                "overlap_offset()",
            ]
            if not unit_known:
                flags.append("no unit was declared for this curve")
            if len(above) == 1 or len(below) == 1:
                flags.append("one side of the boundary contributed a single sample")
            if b.overlap is not None:
                flags.append(
                    "this boundary has a declared overlap; measure it with "
                    "overlap_offset() instead of across the aperture"
                )
            common = {
                "unit": unit,
                "source": SOURCE,
                "inputs": {
                    "curve": name,
                    "boundary_depth_ft": d,
                    "aperture_ft": aperture,
                    "exclusion_ft": _ALLOWANCE_FT,
                },
                "assumptions": {
                    "statistic": "median",
                    "above_window_ft": [lo_a, hi_a],
                    "below_window_ft": [lo_b, hi_b],
                    "aperture_status": THRESHOLDS["offset_aperture_ft"].status,
                },
            }
            offsets.append(
                SpliceOffset(
                    curve=name,
                    boundary_depth_ft=d,
                    basis="aperture",
                    offset=Quantity(
                        value=off,
                        method="median below the splice minus median above it",
                        **common,
                    ),
                    above_stat=Quantity(
                        value=m_a, method="median above the splice", **common
                    ),
                    below_stat=Quantity(
                        value=m_b, method="median below the splice", **common
                    ),
                    n_above=len(above),
                    n_below=len(below),
                    registry_lag_ft=None,
                    verdict=verdict,
                    tolerance=tol_q,
                    flags=tuple(flags),
                )
            )

    reached = bool(offsets) and all(o.verdict != "no-tolerance-supplied" for o in offsets)
    flags = list(stage1.flags)
    if offsets and not reached:
        flags.append(
            "no calibration verdict was reached: offset_tolerance was not supplied "
            "for every measured curve. The corpus states no magnitude at which a "
            "cross-run discontinuity becomes a calibration problem - see "
            "CORPUS_OBSERVATIONS for what it does say"
        )
    if unmeasurable:
        flags.append(f"{len(unmeasurable)} boundary/curve pair(s) could not be measured")

    assumptions = dict(stage1.assumptions)
    assumptions.update(
        {
            "aperture_ft": aperture,
            "statistic": "median",
            "stage": "boundaries and aperture offsets",
        }
    )
    return SpliceReport(
        boundaries=stage1.boundaries,
        offsets=tuple(offsets),
        unmeasurable=tuple(unmeasurable),
        declared_runs=stage1.declared_runs,
        depth_span=stage1.depth_span,
        modal_step=stage1.modal_step,
        verdict_reached=reached,
        flags=tuple(flags),
        assumptions=assumptions,
    )


# ---------------------------------------------------------------------------
# The unconfounded measurement: two runs over the same rock
# ---------------------------------------------------------------------------

def overlap_offset(
    above: RunLog,
    below: RunLog,
    *,
    curve: str,
    tolerance: float | None = None,
    unit: str | None = None,
    null_value: float | None = None,
) -> SpliceOffset | Refusal:
    """Offset between two runs over the interval they both logged.

    The same rock measured twice, so the difference is instrument and not
    geology. `beg-boonsville#36` depth-shifts runs "to the nearest foot" before
    comparing values, so the lag is searched over whole feet inside the
    `asquith#64` registry allowance and the lag minimising the scatter (the
    MEAN absolute deviation about the median, never the median form - see
    `_residual_dispersion`) of the paired residuals is chosen first; the reported
    offset is the median residual at that lag. Depth mis-registry inflates the
    scatter, a calibration difference shifts the level, and `beg#36` corrects
    them in that order.

    Refuses on: the same run twice, a curve absent from either run, no shared
    depth interval, and fewer than two paired samples at every lag.
    """
    # R10
    if above.run_id == below.run_id:
        return Refusal(
            reason=f"both arguments carry run_id {above.run_id!r}; there is nothing to compare",
            needed=("two different logging runs",),
            source=SOURCE,
        )
    # R8
    missing = [r.run_id for r in (above, below) if curve not in r.curves]
    if missing:
        return Refusal(
            reason=f"curve {curve!r} is not present on run(s) {missing}",
            needed=(f"{curve} on both runs",),
            source=SOURCE,
        )

    da = [_require_finite("depth_ft", d) for d in above.depth_ft]
    db = [_require_finite("depth_ft", d) for d in below.depth_ft]
    va = list(above.curves[curve])
    vb = list(below.curves[curve])
    if len(da) < 2 or len(db) < 2:
        return Refusal(
            reason="a logging run with fewer than two samples cannot be compared",
            needed=("at least two samples on each run",),
            source=SOURCE,
        )
    if da[-1] < da[0]:
        da, va = list(reversed(da)), list(reversed(va))
    if db[-1] < db[0]:
        db, vb = list(reversed(db)), list(reversed(vb))

    lo = max(min(da), min(db))
    hi = min(max(da), max(db))
    # R7
    if hi <= lo:
        return Refusal(
            reason=(
                f"runs {above.run_id!r} and {below.run_id!r} share no depth "
                "interval, so there is no common rock to compare"
            ),
            needed=("two runs whose logged intervals overlap",),
            source=SOURCE,
        )

    step_b = _modal_step_ft(db) or 0.0
    half_step = 0.5 * step_b if step_b > 0 else _ALLOWANCE_FT

    scored: list[tuple[float, float, list[float]]] = []  # (mad, lag, residuals)
    for lag in _LAGS_FT:
        residuals: list[float] = []
        for z, v in zip(da, va):
            if not (lo <= z <= hi) or _is_null(v, null_value):
                continue
            target = z + lag
            j, dist = _nearest(db, target)
            if j < 0 or dist > half_step or _is_null(vb[j], null_value):
                continue
            residuals.append(float(vb[j]) - float(v))
        if len(residuals) < 2:
            continue
        scored.append((_residual_dispersion(residuals), lag, residuals))

    best: tuple[float, float, list[float]] | None = None
    tied: list[float] = []
    if scored:
        floor = min(s[0] for s in scored)
        # A locally linear curve gives the SAME residual dispersion at every lag:
        # the depth shift is then not resolved by the data. Prefer no shift over
        # an arbitrary one, and say so.
        tied = [s[1] for s in scored if s[0] <= floor + 1e-12]
        preferred = 0.0 if any(_close(t, 0.0) for t in tied) else min(tied, key=abs)
        best = next(s for s in scored if _close(s[0], floor) and _close(s[1], preferred))

    # R9
    if best is None:
        return Refusal(
            reason=(
                f"fewer than two paired samples of {curve!r} were found on the "
                f"overlap {lo:g}-{hi:g} ft at any registry lag in "
                f"{[round(x, 3) for x in _LAGS_FT]} ft"
            ),
            needed=("live samples of the curve on both runs over the shared interval",),
            source=SOURCE,
        )

    dispersion, lag, residuals = best
    off = _median(residuals)
    ua = unit if unit and unit.strip() else "curve units"
    live_a = [float(v) for z, v in zip(da, va) if lo <= z <= hi and not _is_null(v, null_value)]
    live_b = [float(v) for z, v in zip(db, vb) if lo <= z <= hi and not _is_null(v, null_value)]
    tol_q = None
    if tolerance is None:
        verdict = "no-tolerance-supplied"
    else:
        tv = abs(_require_finite("tolerance", tolerance))
        verdict = "exceeds-tolerance" if abs(off) > tv else "within-tolerance"
        tol_q = Quantity(
            value=tv,
            unit=ua,
            method="caller-supplied cross-run offset tolerance",
            source="CALLER - no corpus source states a discontinuity magnitude",
            inputs={"curve": curve},
        )

    common = {
        "unit": ua,
        "source": f"{BEG_DATA_PREP} + {ASQUITH_RUNS}",
        "inputs": {
            "curve": curve,
            "above_run": above.run_id,
            "below_run": below.run_id,
            "overlap_ft": [lo, hi],
            "n_pairs": len(residuals),
        },
        "assumptions": {
            "statistic": "median of paired residuals",
            "lag_grid_ft": list(_LAGS_FT),
            "lag_chosen_by": "minimum mean absolute deviation of the residuals about their median",
            "lags_tied_at_minimum": tied,
            "residual_dispersion": dispersion,
            "pair_window_ft": half_step,
            "lag_status": THRESHOLDS["registry_lag_step_ft"].status,
        },
    }
    flags = [
        "overlap basis: the same rock logged twice, so this offset is not "
        "confounded with geology",
    ]
    if len(tied) > 1:
        flags.append(
            f"the depth registry lag is not resolved by these data: lags "
            f"{[round(t, 3) for t in tied]} ft all give the same residual "
            "dispersion, which happens where the curve is locally linear. No "
            "shift was preferred over an arbitrary one"
        )
    if abs(lag) > 0:
        flags.append(
            f"a depth registry lag of {lag:+g} ft was applied before comparing "
            "values, per beg#36 'depth-shifted ... to the nearest foot'"
        )
    if unit is None:
        flags.append("no unit was declared for this curve")
    if above.service_company and below.service_company and (
        above.service_company != below.service_company
    ):
        flags.append(
            f"service company differs across the overlap: "
            f"{above.service_company!r} -> {below.service_company!r}; beg#34 states "
            "vendor differences do not materially change Sw, so this is an "
            "attribute for attention, not a verdict"
        )

    return SpliceOffset(
        curve=curve,
        boundary_depth_ft=0.5 * (lo + hi),
        basis="overlap",
        offset=Quantity(
            value=off, method="median of (below-run minus above-run) over the overlap", **common
        ),
        above_stat=Quantity(
            value=_median(live_a), method="median of the above run over the overlap", **common
        ),
        below_stat=Quantity(
            value=_median(live_b), method="median of the below run over the overlap", **common
        ),
        n_above=len(live_a),
        n_below=len(live_b),
        registry_lag_ft=Quantity(
            value=lag,
            unit="ft",
            method="whole-foot depth registry lag, chosen by minimum residual MAD",
            source=BEG_DATA_PREP,
            inputs={"lag_grid_ft": list(_LAGS_FT)},
            assumptions={"status": THRESHOLDS["registry_lag_step_ft"].status},
        ),
        verdict=verdict,
        tolerance=tol_q,
        flags=tuple(flags),
    )


def cross_run_registry_allowance() -> Quantity:
    """The allowance this tool clusters, excludes and searches lags with.

    Deliberately the same number `tools.raster.cross_run_depth_allowance()`
    returns: one published quantity, one constant.
    """
    return _allowance_quantity()
