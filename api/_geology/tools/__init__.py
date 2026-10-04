"""Deterministic tool layer for the well-log agent.

Every equation is cited to a corpus segment, every returned value carries its
inputs and provenance, and tools refuse rather than estimate where the source
does not support an answer. See tool-catalog.md for the specifications and
tool-verification.md for how the citations were checked.
"""
from .result import Quantity, Range, Refusal  # noqa: F401
