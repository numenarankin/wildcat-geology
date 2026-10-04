"""The value type every tool returns.

`well-log-agent.md` requires that every computed value carry its inputs, its
method, and its provenance — "no orphan numbers" — and that the agent never
produce a number that is not already in `computed`. That contract is enforced
here rather than by convention: a tool cannot return a bare float, because the
only constructor takes a method and a source alongside the value.

`Refusal` is the other half. Several tools are specified to refuse rather than
estimate: Archie without Rw provenance, subsea conversion against an unresolved
datum, porosity through a washout. A refusal is a returned value, not an
exception, because the caller needs to render the reason to the operator and the
harness needs to log it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    method: str
    source: str
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.method or not self.source:
            raise ValueError("a Quantity must carry both a method and a source")

    def __repr__(self) -> str:  # keeps test failures readable
        return f"Quantity({self.value:.6g} {self.unit}, {self.method})"


@dataclass(frozen=True)
class Refusal:
    """A tool declining to answer, with the reason and what would unblock it."""

    reason: str
    needed: tuple[str, ...] = ()
    source: str = ""

    @property
    def value(self) -> None:
        return None


@dataclass(frozen=True)
class Range:
    """A band, for tools specified to report a spread rather than a point.

    `inputs`, `assumptions` and `flags` mirror `Quantity` deliberately. Without
    them a spread was a second-class result: `coning_rate_schedule` had to put a
    caller-supplied contact-rise velocity into its `method` string because there
    was nowhere else for it, and `provenance_audit` reported a correctly-sourced
    `coning_critical_rate` spread as carrying no inputs, because it looked for a
    field this class did not have. Two tools reached the same gap independently,
    which is what makes it the contract's problem rather than theirs.

    `members` stays as it was — the per-member values behind the band, one entry
    per correlation — and is not a substitute for `inputs`: members are what the
    band is made of, inputs are what it was computed from.
    """

    low: float
    high: float
    unit: str
    method: str
    source: str
    members: dict[str, float] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.method or not self.source:
            raise ValueError("a Range must carry both a method and a source")

    @property
    def spread(self) -> float:
        return self.high - self.low
