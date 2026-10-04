"""Quality tools: `range_sanity` (#72) and `confidence_score` (#71).

Two decisions here are load-bearing and neither is obvious from the code.

**`range_sanity` never changes a value.** Asquith and Krygowski (#18, p. 40) on
a negative density porosity: "the logging tool is operating properly, but the
assumptions made in the conversion ... are incorrect ... the log still yields
good information. Negative density porosity is often a good indication of the
presence of anhydrite or other heavy minerals." A clip would have turned an
anhydrite pick into a tight limestone. So an out-of-range value is a *finding*,
carried forward intact with a flag saying what it may mean and what would
resolve it. The no-mutation rule is enforced three ways rather than promised:
`Quantity` is frozen, every return is built by the single `_annotate` path which
is not given a value to write, and `_assert_value_identical` fails loudly on any
future edit that breaks it.

**`confidence_score` returns an ordinal level, not a number.** A continuous 0-1
score would need weights, and `well-log-agent.md` §5 requires every band in this
system to be swept against a validation set rather than chosen by intuition.
There is no validation set, so a weight would be a guess with decimal places -
the orphan number this layer exists to prevent. The level is instead the minimum
over five caps, each read off a fact the state object already adjudicates
(evidence kind, assumption source, corpus anchor vs house rule, flags fired).
A minimum has no coefficients, so there is nothing in it to invent, and the
binding cap is always reported so the score explains itself.

Bounds obey `tool-catalog.md`'s SOURCED / PROVISIONAL / CALLER marking. This
module carries only *definitional* bounds (what the quantity is: a saturation
is a fraction of pore volume, an absolute scale has no negative region) plus the
one SOURCED gate the corpus states, `DRHO > 0.20`, imported from
`petrophysics.DRHO_SUSPECT` rather than restated. A rock judgement - "porosity
too high", "Rw implausible" - is absent unless the caller supplies it with a
status and a source. See `specs/72-range_sanity.md` and
`specs/71-confidence_score.md`.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from typing import Any, Iterable, Sequence

from .petrophysics import DRHO_SUSPECT
from .result import Quantity, Range, Refusal

ASQUITH_DENSITY = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#18"
SPEC_72 = "specs/72-range_sanity.md (house contract - plumbing, no corpus citation owed)"

#: The confidence scale is a number the corpus does not publish, so it is
#: sourced the way `las_validate`'s quality score and `unit_convert`'s exact
#: factors are - `owned: <spec> ... not from the corpus` - and never to an
#: anchor. Saying only "no corpus citation owed" would claim nothing is
#: outstanding, when `well-log-agent.md` §5 requires every band in this system,
#: "and the confidence bands", to be swept against a validation set that does
#: not exist yet. What is owed is stated rather than waived.
SPEC_71 = (
    "owned: specs/71-confidence_score.md - the five-level ordinal scale and the "
    "weakest-link (min) rule are this project's house contract, not from the corpus; "
    "no source scores a result, and the calibration sweep well-log-agent.md §5 "
    "requires has not been run"
)

#: The four things a bound may claim about itself. `definitional` means it
#: follows from what the quantity is and owes no citation; the other three are
#: `tool-catalog.md`'s markings.
BOUND_STATUSES = ("definitional", "SOURCED", "PROVISIONAL", "CALLER")


@dataclass(frozen=True)
class Bound:
    """One side of a range, with where it came from and what crossing it means.

    A bound with no `status`/`source` is refused rather than applied. That is
    the mechanism that keeps an invented number out of this tool.
    """

    status: str
    source: str
    low: float | None = None
    high: float | None = None
    low_strict: bool = False   # True => violation at value <= low
    high_strict: bool = False  # True => violation at value >= high
    meaning_low: str = ""
    meaning_high: str = ""
    resolution_low: str = ""
    resolution_high: str = ""
    label: str = ""

    def __post_init__(self) -> None:
        if self.low is None and self.high is None:
            raise ValueError("a Bound must set at least one of low/high")


# --------------------------------------------------------------------------
# Definitional bounds. No citation is owed for these and none is claimed: they
# follow from what the quantity IS. Nothing here is a judgement about rock.
# --------------------------------------------------------------------------
_FRACTION_UNITS = frozenset({"v/v", "frac", "fraction", "dec", "decimal"})
_DENSITY_UNITS = frozenset({"g/cm3", "g/cc", "gm/cc"})

_DEF = "definitional"
_DEF_SRC = "definitional - follows from the definition of the quantity, not from a source"

DEFINITIONAL_BOUNDS: dict[str, tuple[Bound, ...]] = {
    "porosity": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, high=1.0, label="porosity 0..1",
            meaning_low=(
                "bulk density exceeds the assumed matrix density. Per asquith#18 the "
                "logging tool is operating properly and the conversion assumption is "
                "wrong; negative density porosity is often a good indication of "
                "anhydrite or other heavy minerals - this is a lithology signal, not "
                "a tool error"
            ),
            resolution_low=(
                "recompute with rho_ma = 2.96 g/cm3 (anhydrite, Asquith Table 4.2) and "
                "confirm the lithology from the raw bulk density. Not from PE: Table 4.2 "
                "gives anhydrite 5.05 b/e against limestone 5.08 b/e, so PE cannot "
                "separate the two"
            ),
            meaning_high=(
                "pore volume cannot exceed bulk volume; the matrix or fluid density "
                "used in the conversion is wrong, or the value is in percent"
            ),
            resolution_high="check rho_ma / rho_fl and the units (see unit_convert, #11)",
        ),
    ),
    "saturation": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, high=1.0, label="saturation 0..1",
            meaning_low="a saturation is a fraction of pore volume and cannot be negative",
            resolution_low="check the inputs to the saturation equation",
            meaning_high=(
                "the pore volume cannot hold more fluid than it has. Sw > 1 usually "
                "means Rw is too high, a/m/n are wrong for this rock, or porosity is "
                "understated - it can also mean the zone is simply wet and the "
                "parameters are off"
            ),
            resolution_high=(
                "supply a measured Rw (SP-derived or a produced-water sample) and "
                "confirm a, m, n for the formation"
            ),
        ),
    ),
    "volume_fraction": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, high=1.0, label="volume fraction 0..1",
            meaning_low="a volume fraction cannot be negative",
            resolution_low="check the clean and shale endpoints used to normalise it",
            meaning_high="a volume fraction cannot exceed the whole",
            resolution_high="check the clean and shale endpoints used to normalise it",
        ),
    ),
    "bulk_density": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, low_strict=True, label="density > 0",
            meaning_low="matter has positive mass density; a non-positive rho_b is a null or a parse artifact",
            resolution_low="check null handling (null_scrub) on the RHOB curve",
        ),
    ),
    "matrix_density": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="density > 0",
              meaning_low="matter has positive mass density",
              resolution_low="check the matrix constant lookup"),
    ),
    "fluid_density": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="density > 0",
              meaning_low="matter has positive mass density",
              resolution_low="check the fluid density used"),
    ),
    "resistivity": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, low_strict=True, label="resistivity > 0",
            meaning_low=(
                "resistivity is a positive-definite material property; zero or "
                "negative is a short, a null sentinel, or a digitisation artifact"
            ),
            resolution_low="check null handling and the raw curve on the log",
        ),
    ),
    "pressure_absolute": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, label="psia >= 0",
            meaning_low=(
                "an absolute pressure scale has no negative region. NOTE: a negative "
                "GAUGE pressure is a real vacuum reading - psig is not this kind"
            ),
            resolution_low="confirm the pressure base (psia vs psig) at the source",
        ),
    ),
    "temperature_absolute": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, label="absolute T >= 0",
            meaning_low="an absolute temperature scale has no negative region (degF/degC are not this kind)",
            resolution_low="confirm the temperature scale at the source",
        ),
    ),
    "transit_time": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="dt > 0",
              meaning_low="an interval transit time is a time and must be positive",
              resolution_low="check null handling on the DT curve"),
    ),
    "z_factor": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="z > 0",
              meaning_low="z = pV/nRT with p, V and T all positive",
              resolution_low="check the pseudo-reduced inputs to the z correlation"),
    ),
    "viscosity": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="viscosity > 0",
              meaning_low="viscosity is positive-definite",
              resolution_low="check the correlation inputs"),
    ),
    "permeability": (
        Bound(_DEF, _DEF_SRC, low=0.0, low_strict=True, label="k > 0",
              meaning_low="permeability is positive-definite",
              resolution_low="check the correlation inputs"),
    ),
    "depth_md": (
        Bound(
            _DEF, _DEF_SRC, low=0.0, label="MD >= 0",
            meaning_low=(
                "measured depth runs along hole from the reference and cannot be "
                "negative. NOTE: subsea depth (TVDSS) is signed - negative means above "
                "sea level - and is deliberately not this kind"
            ),
            resolution_low="confirm the depth reference (see datum resolution, Stage 0)",
        ),
    ),
}

# --------------------------------------------------------------------------
# The one SOURCED gate. asquith#18: "Whenever the correction curve (DRHO)
# exceeds 0.20 g/cm3, the value of the bulk density obtained from the
# bulk-density curve (RHOB) should be considered suspect and possibly invalid."
# The threshold is imported from petrophysics, never restated.
# --------------------------------------------------------------------------
SOURCED_BOUNDS: dict[str, tuple[Bound, ...]] = {
    # `high_strict=False`, so the violation is at DRHO > 0.20 and not at
    # DRHO >= 0.20. The source says "exceeds", and #25's gate (`relation=">"`)
    # and #26's refusal (`drho > DRHO_SUSPECT`) both read it that way; firing at
    # exactly 0.20 here would have made this the one tool of the three that
    # called a bulk density suspect on Asquith's authority for something Asquith
    # does not say.
    "drho": (
        Bound(
            "SOURCED", ASQUITH_DENSITY, high=DRHO_SUSPECT, high_strict=False,
            label=f"DRHO > {DRHO_SUSPECT} g/cm3",
            meaning_high=(
                "asquith#18: whenever DRHO exceeds 0.20 g/cm3 the bulk density should "
                "be considered suspect and possibly invalid - the tool applied a large "
                "borehole correction, usually mudcake or bad hole"
            ),
            resolution_high="take the bulk density from an in-gauge interval, or refuse the porosity",
        ),
    ),
}

#: Which units a kind's bounds are stated in. A value in any other unit is
#: reported `unchecked` rather than converted: converting is touching the value.
KIND_UNITS: dict[str, frozenset[str]] = {
    "porosity": _FRACTION_UNITS,
    "saturation": _FRACTION_UNITS,
    "volume_fraction": _FRACTION_UNITS,
    "bulk_density": _DENSITY_UNITS,
    "matrix_density": _DENSITY_UNITS,
    "fluid_density": _DENSITY_UNITS,
    "drho": _DENSITY_UNITS,
    "resistivity": frozenset({"ohm-m", "ohmm", "ohm.m", "ohm_m"}),
    "pressure_absolute": frozenset({"psia"}),
    "temperature_absolute": frozenset({"degR", "R", "K", "degK"}),
    "transit_time": frozenset({"usec/ft", "us/ft", "usec/m", "us/m"}),
    "z_factor": frozenset({"-", "", "dimensionless", "frac"}),
    "viscosity": frozenset({"cp", "cP"}),
    "permeability": frozenset({"md", "mD", "millidarcy"}),
    "depth_md": frozenset({"ft", "m"}),
}

#: Units that name exactly one kind. `v/v` is absent on purpose: porosity,
#: saturation and Vsh all wear it, so it must never be inferred.
UNAMBIGUOUS_UNITS: dict[str, str] = {
    "psia": "pressure_absolute",
    "ohm-m": "resistivity",
    "ohmm": "resistivity",
    "usec/ft": "transit_time",
    "us/ft": "transit_time",
    "cp": "viscosity",
    "cP": "viscosity",
    "md": "permeability",
    "mD": "permeability",
}

KNOWN_KINDS = frozenset(DEFINITIONAL_BOUNDS) | frozenset(SOURCED_BOUNDS)


# --------------------------------------------------------------------------
# range_sanity
# --------------------------------------------------------------------------
def _flag(kind: str, value: float, unit: str, relation: str, bound_text: str,
          status: str, meaning: str, resolution: str, basis: str) -> str:
    """One flag string: what fired, what it may mean, what would resolve it."""
    return (
        f"{kind}={value:.6g} {unit} {relation} {bound_text} [{status}]"
        f" | means: {meaning or 'not characterised'}"
        f" | resolve: {resolution or 'not characterised'}"
        f" | basis: {basis}"
    )


def _endpoints(q: Quantity | Range) -> tuple[tuple[str, float], ...]:
    """The value(s) a result carries, each with the label it is flagged under.

    A `Range` is a first-class computed field - `well-log-agent.md`:230 routes
    an Sw with no Rw provenance to one rather than to a point number - so the
    physical-plausibility gate has to reach both of its ends, or the layer's
    least-certain values are the ones that go unchecked. A `Quantity` carries
    one value and is flagged under the bare kind.
    """
    if isinstance(q, Range):
        return (("low", q.low), ("high", q.high))
    return (("", q.value),)


def _carried(q: Quantity | Range) -> tuple[Any, ...]:
    """Everything `range_sanity` is forbidden to touch."""
    return tuple(v for _, v in _endpoints(q)) + (q.unit, q.method, q.source)


def _assert_value_identical(before: Quantity | Range, after: Quantity | Range) -> None:
    """Post-condition: range_sanity is not permitted to change a value.

    NaN counts as preserved (NaN != NaN), which is why this is not a bare `==`.
    An AssertionError here means a future edit introduced a clip.
    """
    a, b = _carried(before), _carried(after)
    same = len(a) == len(b) and all(
        (x == y) or (x != x and y != y) for x, y in zip(a, b))
    if not same:
        raise AssertionError(
            "range_sanity mutated a value - it is specified never to clip, clamp or "
            f"substitute ({a!r} -> {b!r})"
        )


def _annotate(q: Quantity | Range, flags: Sequence[str],
              extra_assumptions: dict[str, Any]) -> Quantity | Range:
    """The ONLY construction path in this module's range checks.

    It is handed flags and assumptions and nothing else, so no code path can
    write a different value: `value` (or `low`/`high`), `unit`, `method`,
    `source` and `inputs` ride through from `q` untouched.
    """
    out = replace(
        q,
        flags=tuple(q.flags) + tuple(flags),
        assumptions={**q.assumptions, **extra_assumptions},
    )
    _assert_value_identical(q, out)
    return out


def _violations(value: float, bound: Bound, kind: str, unit: str) -> list[str]:
    """Flags for one bound, low side first. Never touches `value`."""
    fired: list[str] = []
    basis = bound.source
    if bound.low is not None:
        hit = value <= bound.low if bound.low_strict else value < bound.low
        if hit:
            rel = "at or below" if bound.low_strict else "below"
            fired.append(_flag(kind, value, unit, rel, f"{bound.low:g}", bound.status,
                               bound.meaning_low, bound.resolution_low, basis))
    if bound.high is not None:
        hit = value >= bound.high if bound.high_strict else value > bound.high
        if hit:
            rel = "at or above" if bound.high_strict else "above"
            fired.append(_flag(kind, value, unit, rel, f"{bound.high:g}", bound.status,
                               bound.meaning_high, bound.resolution_high, basis))
    return fired


def _validate_caller_bounds(extra_bounds: dict[str, Bound] | None) -> Refusal | None:
    if not extra_bounds:
        return None
    for kind in sorted(extra_bounds):
        b = extra_bounds[kind]
        if not isinstance(b, Bound):
            raise ValueError(f"extra_bounds[{kind!r}] must be a Bound")
        if not b.status.strip() or not b.source.strip():
            return Refusal(
                reason=(
                    f"the caller bound for {kind!r} carries no status and/or no source; "
                    "a bound without one is an invented bound, and this tool does not "
                    "apply invented bounds"
                ),
                needed=("status (one of %s)" % ", ".join(BOUND_STATUSES), "source"),
                source=SPEC_72,
            )
        if b.status not in BOUND_STATUSES:
            return Refusal(
                reason=f"unknown bound status {b.status!r} on the caller bound for {kind!r}",
                needed=tuple(BOUND_STATUSES),
                source=SPEC_72,
            )
    return None


def range_sanity(q: Any, kind: str | None = None,
                 extra_bounds: dict[str, Bound] | None = None
                 ) -> Quantity | Range | Refusal:
    """Check a computed value against physical bounds. Never changes the value.

    Returns the same value with flags attached and a verdict in `assumptions`:
    `in_range` | `out_of_range` | `invalid` | `unchecked`. `out_of_range` is not
    a rejection - Asquith's negative density porosity is an anhydrite indicator,
    and clipping it would destroy the lithology signal. Blocking is `gate_check`'s
    job (#66), not this tool's.

    Check order, fixed so output is stable: provenance -> finiteness -> kind ->
    unit -> definitional -> SOURCED -> caller bounds.
    """
    # 1. Provenance precondition. A `Range` is provenanced (method, source,
    #    inputs, assumptions, flags) and is checked at both ends; only a value
    #    with no provenance at all is refused.
    if isinstance(q, Refusal):
        return q
    if not isinstance(q, (Quantity, Range)):
        return Refusal(
            reason=(
                "an orphan number cannot be range-checked; range_sanity does not invent "
                f"provenance for a bare {type(q).__name__}"
            ),
            needed=("the value as a Quantity or Range carrying its method, source "
                    "and inputs",),
            source=SPEC_72,
        )

    bad_bounds = _validate_caller_bounds(extra_bounds)
    if bad_bounds is not None:
        return bad_bounds

    flags: list[str] = []
    checks: list[str] = []
    applied: list[dict[str, Any]] = []
    ends = _endpoints(q)
    value = ends[0][1]
    unit = (q.unit or "").strip()

    def _named(side: str, base: str | None = None) -> str:
        """`porosity` for a point value, `porosity.low` for a band's end."""
        base = base or kind or "value"
        return f"{base}.{side}" if side else base

    # 2. Finiteness.
    checks.append("finiteness")
    if not all(math.isfinite(v) for _, v in ends):
        for side, v in ends:
            if math.isfinite(v):
                continue
            flags.append(
                f"{_named(side)}={v!r} is not finite [definitional]"
                " | means: a NaN or infinity reached the state object - usually an undeclared"
                " null sentinel that survived null_scrub, or a division by zero in the method"
                " | resolve: check null handling on the source curve and the method's inputs"
                f" | basis: {_DEF_SRC}"
            )
        return _annotate(q, flags, {
            "range_sanity_verdict": "invalid",
            "range_sanity_kind": kind,
            "range_sanity_bounds": applied,
            "range_sanity_checks": checks,
        })

    # 3. Kind resolution. `v/v` never infers - it is worn by porosity,
    #    saturation and Vsh alike.
    checks.append("kind_resolution")
    resolved = kind
    inferred = False
    if resolved is None:
        resolved = UNAMBIGUOUS_UNITS.get(unit)
        inferred = resolved is not None
    shown = " to ".join(f"{v:.6g}" for _, v in ends)
    if resolved is None:
        flags.append(
            f"value={shown} {unit or '(no unit)'} was not range-checked [{_DEF}]"
            " | means: no kind was stated and the unit does not name exactly one"
            " quantity (v/v is worn by porosity, saturation and Vsh alike)"
            " | resolve: pass kind= explicitly, or supply extra_bounds for it"
            f" | basis: {SPEC_72}"
        )
        return _annotate(q, flags, {
            "range_sanity_verdict": "unchecked",
            "range_sanity_kind": None,
            "range_sanity_bounds": applied,
            "range_sanity_checks": checks,
        })
    if resolved not in KNOWN_KINDS and not (extra_bounds and resolved in extra_bounds):
        return Refusal(
            reason=(
                f"no bounds exist for kind {resolved!r}; this tool holds only "
                "definitional bounds plus the one SOURCED gate (DRHO), and it will not "
                "invent one"
            ),
            needed=(f"extra_bounds[{resolved!r}] with a status and a source",
                    "or one of: " + ", ".join(sorted(KNOWN_KINDS))),
            source=SPEC_72,
        )

    # 4. Unit compatibility. No conversion: converting is touching the value.
    checks.append("unit_compatibility")
    expected = KIND_UNITS.get(resolved)
    if expected is not None and unit not in expected:
        flags.append(
            f"{resolved}={shown} {unit or '(no unit)'} was not range-checked [{_DEF}]"
            f" | means: the bounds for {resolved} are stated in {sorted(expected)} and this"
            " value is not in one of them, so no comparison is meaningful (a porosity in"
            " percent would otherwise read as 'above 1.0')"
            " | resolve: convert with unit_convert (#11) before checking, or state the"
            " correct kind"
            f" | basis: {SPEC_72}"
        )
        return _annotate(q, flags, {
            "range_sanity_verdict": "unchecked",
            "range_sanity_kind": resolved,
            "range_sanity_bounds": applied,
            "range_sanity_checks": checks,
        })

    # 5-7. Bounds, in a fixed order: definitional, then SOURCED, then caller.
    ordered: list[Bound] = []
    ordered.extend(DEFINITIONAL_BOUNDS.get(resolved, ()))
    ordered.extend(SOURCED_BOUNDS.get(resolved, ()))
    if extra_bounds and resolved in extra_bounds:
        ordered.append(extra_bounds[resolved])
    checks.extend(["definitional_bounds", "sourced_bounds", "caller_bounds"])

    for bound in ordered:
        applied.append({
            "label": bound.label or resolved,
            "low": bound.low,
            "high": bound.high,
            "status": bound.status,
            "source": bound.source,
        })
        for side, v in ends:
            flags.extend(_violations(v, bound, _named(side, resolved),
                                     unit or "(no unit)"))

    verdict = "out_of_range" if flags else ("in_range" if applied else "unchecked")
    return _annotate(q, flags, {
        "range_sanity_verdict": verdict,
        "range_sanity_kind": resolved,
        "range_sanity_kind_inferred_from_unit": inferred,
        "range_sanity_bounds": applied,
        "range_sanity_checks": checks,
    })


def range_sanity_all(items: Iterable[tuple[str | None, Any]],
                     extra_bounds: dict[str, Bound] | None = None
                     ) -> tuple[Quantity | Range | Refusal, ...]:
    """Annotate a whole `computed[]` pass. Input order is preserved."""
    return tuple(range_sanity(q, kind, extra_bounds) for kind, q in items)


# --------------------------------------------------------------------------
# confidence_score
# --------------------------------------------------------------------------
#: Named ordinal levels. The digits are ranks, not magnitudes: rank 4 is not
#: twice rank 2, and averaging them is meaningless.
LEVELS: dict[str, int] = {
    "UNSUPPORTED": 0,
    "QUALIFIED": 1,
    "ASSUMED": 2,
    "DERIVED": 3,
    "MEASURED": 4,
}
LEVEL_NAMES: dict[int, str] = {v: k for k, v in LEVELS.items()}

#: `ZoneEvaluation.evidence[].kind` (well-log-agent.md:262). `stated` can never
#: be promoted to `measured` by any code path (harness-implementation.md,
#: Phase 1), which is why it caps here rather than being inferred.
EVIDENCE_CAPS: dict[str, int] = {
    "measured": LEVELS["MEASURED"],
    "documented": LEVELS["DERIVED"],
    "stated": LEVELS["ASSUMED"],
}

#: `ZoneEvaluation.assumptions[].source` (well-log-agent.md:260).
ASSUMPTION_CAPS: dict[str, int] = {
    "user": LEVELS["MEASURED"],
    "derived": LEVELS["DERIVED"],
    "default": LEVELS["DERIVED"],
}

#: A corpus anchor looks like `NN-section/slug` with an optional `#N`.
_ANCHOR = re.compile(r"\d{2}-[a-z0-9][a-z0-9\-]*/[A-Za-z0-9._\-]+(?:#\d+)?")

CONFIDENCE_UNIT = "ordinal-level"
CONFIDENCE_METHOD = "confidence_score v1 - minimum over five determinant caps (weakest link)"
SCALE_WARNING = "ordinal - do not average, subtract, or read as a probability"


def _cap_flag(det: str, trigger: str, meaning: str, resolution: str, cap: int) -> str:
    return (f"{det} {trigger} | means: {meaning} | resolve: {resolution}"
            f" | cap: {LEVEL_NAMES[cap]}({cap})")


def confidence_score(q: Quantity | Range | Refusal | Any,
                     input_evidence: dict[str, str] | None = None,
                     assumption_status: dict[str, str] | None = None
                     ) -> Quantity | Refusal:
    """An ordinal confidence level for one computed field, with its reason.

    `level = min(cap(D1..D5))`: provenance completeness, weakest input evidence
    kind, method standing (corpus anchor vs house rule), flags fired, assumption
    registration. A minimum has no coefficients, so nothing in it is invented,
    and the binding determinant is always named.

    Refuses rather than guessing an evidence kind: inferring one would be the
    `stated` -> `measured` promotion the harness forbids.
    """
    if input_evidence:
        for k, v in input_evidence.items():
            if v not in EVIDENCE_CAPS:
                raise ValueError(
                    f"unknown evidence kind {v!r} for {k!r}; expected one of "
                    f"{sorted(EVIDENCE_CAPS)} (ZoneEvaluation.evidence[].kind)"
                )
    if assumption_status:
        for k, v in assumption_status.items():
            if v not in ASSUMPTION_CAPS:
                raise ValueError(
                    f"unknown assumption status {v!r} for {k!r}; expected one of "
                    f"{sorted(ASSUMPTION_CAPS)} (ZoneEvaluation.assumptions[].source)"
                )

    caps: dict[str, dict[str, Any]] = {}
    flags: list[str] = []

    # D1 - provenance completeness.
    if isinstance(q, Refusal):
        level = LEVELS["UNSUPPORTED"]
        flags.append(_cap_flag(
            "D1 provenance:", "the computation refused",
            f"there is no value to trust - {q.reason}",
            "supply " + (", ".join(q.needed) if q.needed else "what the refusal names"),
            level))
        return Quantity(
            value=float(level), unit=CONFIDENCE_UNIT, method=CONFIDENCE_METHOD, source=SPEC_71,
            inputs={"refusal_reason": q.reason, "refusal_needed": list(q.needed)},
            assumptions={
                "level_name": LEVEL_NAMES[level],
                "scale": SCALE_WARNING,
                "caps": {"D1_provenance": {"cap": level, "fact": "input is a Refusal"}},
                "binding": ["D1_provenance"],
            },
            flags=tuple(flags),
        )
    # A `Range` carries the same five determinants a `Quantity` does - inputs,
    # source, flags, assumptions - so it is scored, not refused. Refusing it
    # would leave the layer's least-certain fields (well-log-agent.md:230 sends
    # an Sw with no Rw provenance to a band rather than a point) as the only
    # ones with no confidence attached.
    if not isinstance(q, (Quantity, Range)):
        return Refusal(
            reason=(
                "confidence is a property of a provenanced value; there is nothing to "
                f"score in a bare {type(q).__name__}"
            ),
            needed=("the value as a Quantity or Range carrying its method, source "
                    "and inputs",),
            source=SPEC_71,
        )

    if q.inputs:
        caps["D1_provenance"] = {"cap": LEVELS["MEASURED"], "fact": f"{len(q.inputs)} inputs recorded"}
    else:
        caps["D1_provenance"] = {"cap": LEVELS["ASSUMED"], "fact": "no inputs recorded"}
        flags.append(_cap_flag(
            "D1 provenance:", "the value records no inputs",
            "it cannot be re-derived from what it carries",
            "record the arguments in Quantity.inputs (see provenance_audit, #67)",
            LEVELS["ASSUMED"]))

    # D2 - weakest input evidence kind. Refuses rather than inferring.
    if q.inputs:
        evidence = input_evidence or {}
        missing = sorted(k for k in q.inputs if k not in evidence)
        if missing:
            return Refusal(
                reason=(
                    "confidence cannot be scored without the evidence kind of every "
                    f"input; uncovered: {', '.join(missing)}. Inferring a kind would be "
                    "the stated -> measured promotion the state object forbids"
                ),
                needed=tuple(f"evidence kind (measured|documented|stated) for {k}" for k in missing),
                source=SPEC_71,
            )
        weakest_key = min(sorted(q.inputs), key=lambda k: EVIDENCE_CAPS[evidence[k]])
        cap = EVIDENCE_CAPS[evidence[weakest_key]]
        caps["D2_input_evidence"] = {
            "cap": cap,
            "fact": f"weakest input {weakest_key!r} is {evidence[weakest_key]}",
        }
        if cap < LEVELS["MEASURED"]:
            flags.append(_cap_flag(
                "D2 input evidence:", f"{weakest_key!r} is {evidence[weakest_key]}",
                ("the value rests on an operator statement, which can never be promoted "
                 "to a measurement"
                 if evidence[weakest_key] == "stated" else
                 "the value rests on a documented rather than measured input"),
                f"supply a log reading or a document for {weakest_key}",
                cap))
    else:
        caps["D2_input_evidence"] = {"cap": LEVELS["MEASURED"], "fact": "no inputs to weigh"}

    # D3 - method standing, read off the result's own source.
    source = q.source or ""
    if "PROVISIONAL" in source.upper():
        caps["D3_method"] = {"cap": LEVELS["QUALIFIED"], "fact": "source is marked PROVISIONAL"}
        flags.append(_cap_flag(
            "D3 method:", "the source is a PROVISIONAL house rule",
            "the threshold or method behind this number is ours, not the corpus's",
            "add a source to the corpus for it, or have the caller state the threshold",
            LEVELS["QUALIFIED"]))
    elif _ANCHOR.search(source):
        caps["D3_method"] = {"cap": LEVELS["MEASURED"], "fact": "source carries a corpus anchor"}
    else:
        caps["D3_method"] = {"cap": LEVELS["QUALIFIED"], "fact": "source is not a corpus anchor"}
        flags.append(_cap_flag(
            "D3 method:", f"source {source!r} carries no corpus anchor",
            "the method behind this number is not traceable to the corpus",
            "cite the corpus segment the method comes from",
            LEVELS["QUALIFIED"]))

    # D4 - flags on the value. Blunt on purpose: under-flagging ships a bad
    # number, over-flagging costs one line of explanation.
    if q.flags:
        caps["D4_flags"] = {"cap": LEVELS["QUALIFIED"], "fact": f"{len(q.flags)} flag(s) attached"}
        flags.append(_cap_flag(
            "D4 flags:", f"{len(q.flags)} flag(s) attached, first: {q.flags[0]!r}",
            "the value stands but carries a caveat a reader must act on",
            "read the attached flag; it names what would resolve it",
            LEVELS["QUALIFIED"]))
    else:
        caps["D4_flags"] = {"cap": LEVELS["MEASURED"], "fact": "no flags"}

    # D5 - assumption registration. Caps rather than refuses: an unregistered
    # assumption is itself a reportable finding.
    if q.assumptions:
        status = assumption_status or {}
        unregistered = sorted(k for k in q.assumptions if k not in status)
        if unregistered:
            caps["D5_assumptions"] = {
                "cap": LEVELS["ASSUMED"],
                "fact": f"unregistered assumptions: {', '.join(unregistered)}",
            }
            flags.append(_cap_flag(
                "D5 assumptions:", f"{', '.join(unregistered)} not in the registry",
                "the value rests on something nobody logged",
                "register them with assumption_registry (#68), or have the user set them",
                LEVELS["ASSUMED"]))
        else:
            weakest_key = min(sorted(q.assumptions), key=lambda k: ASSUMPTION_CAPS[status[k]])
            cap = ASSUMPTION_CAPS[status[weakest_key]]
            caps["D5_assumptions"] = {
                "cap": cap,
                "fact": f"weakest assumption {weakest_key!r} is {status[weakest_key]}",
            }
            if cap < LEVELS["MEASURED"]:
                flags.append(_cap_flag(
                    "D5 assumptions:", f"{weakest_key!r} is a {status[weakest_key]}",
                    "a default or derived value is in play, so this is not a measurement",
                    f"have the operator confirm or override {weakest_key}",
                    cap))
    else:
        caps["D5_assumptions"] = {"cap": LEVELS["MEASURED"], "fact": "nothing assumed"}

    level = min(c["cap"] for c in caps.values())
    binding = [name for name in ("D1_provenance", "D2_input_evidence", "D3_method",
                                 "D4_flags", "D5_assumptions")
               if caps[name]["cap"] == level]

    return Quantity(
        value=float(level), unit=CONFIDENCE_UNIT, method=CONFIDENCE_METHOD, source=SPEC_71,
        inputs={
            "scored_method": q.method,
            "scored_source": q.source,
            "scored_unit": q.unit,
            "input_evidence": dict(sorted((input_evidence or {}).items())),
            "assumption_status": dict(sorted((assumption_status or {}).items())),
        },
        assumptions={
            "level_name": LEVEL_NAMES[level],
            "scale": SCALE_WARNING,
            "rule": "level = min(cap(D1..D5)); no weights exist to invent",
            "caps": caps,
            "binding": binding,
        },
        flags=tuple(flags),
    )


def confidence_trend(field: str, scores: Sequence[Any]) -> Quantity | Refusal:
    """Trend one field's confidence across a session.

    well-log-agent.md:464: "Monotonic increase across a session is a flag on its
    face" - a confidence that only ever rises is describing the agent's growing
    comfort, not the well. Returns a Quantity rather than a Range because the
    flag is the product here and Range carries no flags; the band is in `inputs`.
    """
    if not scores:
        return Refusal(
            reason=f"no confidence observations recorded for {field!r}; there is no trend",
            needed=("at least one confidence_score result for this field",),
            source=SPEC_71,
        )
    levels: list[int] = []
    for s in scores:
        if not isinstance(s, Quantity) or s.unit != CONFIDENCE_UNIT:
            raise ValueError(
                "confidence_trend takes confidence_score results only; got "
                f"{getattr(s, 'unit', type(s).__name__)!r}"
            )
        levels.append(int(s.value))

    flags: list[str] = []
    rises = [i for i in range(1, len(levels)) if levels[i] > levels[i - 1]]
    falls = [i for i in range(1, len(levels)) if levels[i] < levels[i - 1]]
    if rises and not falls and len(levels) >= 3:
        flags.append(
            f"trend {field}: monotonic increase across {len(levels)} observations"
            " | means: confidence rose and was never revised down, which is what an agent"
            " talking itself into an answer looks like"
            " | resolve: check each rise against the trajectory log for the new measured or"
            " documented input that justified it"
            f" | basis: {SPEC_71} (well-log-agent.md:464)"
        )
    for i in falls:
        flags.append(
            f"trend {field}: level fell from {LEVEL_NAMES[levels[i - 1]]} to "
            f"{LEVEL_NAMES[levels[i]]} at observation {i}"
            " | means: evidence for this field weakened or a flag was attached"
            " | resolve: informational - the trajectory log holds what changed"
            f" | basis: {SPEC_71}"
        )
    if not rises and not falls:
        flags.append(
            f"trend {field}: no movement across {len(levels)} observations"
            " | means: confidence never changed - recorded so a flat trend is"
            " distinguishable from an unmonitored one"
            " | resolve: none needed"
            f" | basis: {SPEC_71}"
        )

    latest = levels[-1]
    return Quantity(
        value=float(latest), unit=CONFIDENCE_UNIT,
        method="confidence_trend v1 - ordinal sequence over one field's session history",
        source=SPEC_71,
        inputs={
            "field": field,
            "levels": levels,
            "level_names": [LEVEL_NAMES[v] for v in levels],
            "first": levels[0],
            "last": latest,
            "min": min(levels),
            "max": max(levels),
            "n": len(levels),
        },
        assumptions={
            "level_name": LEVEL_NAMES[latest],
            "scale": SCALE_WARNING,
        },
        flags=tuple(flags),
    )
