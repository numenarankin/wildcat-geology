"""Group Q, pay that has already been drilled through and logged as wet.

The plan predicted this whole group was blocked on new source material. That was
checked segment by segment rather than taken on trust, and it is two thirds
right. What the corpus actually holds:

  * NO laminated sand-shale resistivity model. The only bed-thickness material
    here is `trieste#5`, and it is a different correction: charts Rcor-5 through
    Rcor-9 correct a TOOL's reading for the thickness of the bed it is in, and
    Eq. 7-6 mixes conductivities by the tool's geometrical factors over mud,
    invaded zone and virgin zone. Neither one splits a bed into sand and shale
    laminae, which is the whole of the thin-bed pay problem. `thin_bed_correction`
    refuses.
  * NO flow zone indicator, no reservoir quality index, no Amaefule, no hydraulic
    unit, anywhere in the corpus. The only "Kozeny" in it is the coning
    partial-penetration rate equation, which is a different quantity entirely.
    `rock_typing` refuses.
  * The irreducible-saturation half of the low-resistivity problem IS sourced,
    and it is sourced well. `asquith#45` states, in the book's own words, that
    constant BVW means the zone is at irreducible water saturation and that
    "hydrocarbon production from a zone at irreducible water saturation should be
    water free". So a fine-grained interval whose Archie Sw reads wet, but whose
    BVW is constant, is by the source's own reasoning expected to produce water
    free. `low_resistivity_screen` is built on exactly that sentence and nothing
    more, and says so.

--- the two decisions worth explaining ----------------------------------------

**The screen is scoped to one mechanism and admits it.** Low-resistivity pay has
several causes: laminated thin beds, conductive minerals, fresh formation water,
and high irreducible saturation from fine grain size or microporosity. Only the
last is supported here. Every result flags the ones it did not test, because a
screen silently covering one cause of four reads as clearance for all four.

**It returns candidates and never a conclusion, and the wording is load-bearing.**
The verdict string says so literally. An interval that reads wet and has constant
BVW is worth a second look at the resistivity, the Rw and the grain size; it is
not a pay flag, and nothing here should be quotable as one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .classic import ASQUITH_BUCKLES_FIGURES, BUCKLES_SPREAD_TOLERANCE, BulkVolumeWater
# Aliased private for the same reason as in `tools/classic.py`: a re-exported
# public name enters the registry from whichever module sorts first.
from .classic import bulk_volume_water as _bulk_volume_water
from .result import Quantity, Refusal

# --- corpus anchors -----------------------------------------------------------

#: Bed-thickness and shoulder-bed corrections for induction and laterolog, as
#: charts, plus the geometrical-factor response Eqs. 7-6 to 7-8. The nearest
#: thing this corpus has to a thin-bed correction, and not the same correction.
TRIESTE_BED_THICKNESS = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#5"
#: Wyllie-Rose, Timur and Coates-Dumanoir log-derived permeability. Where a
#: caller asking for rock types should go instead.
ASQUITH_PERMEABILITY = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#48"

# --- house rules --------------------------------------------------------------

#: The Sw above which an interval "reads wet" to a conventional Archie cutoff.
#: PROVISIONAL: no cutoff of this kind is published anywhere in this corpus, it
#: is an argument for exactly that reason, and every result flags it.
SW_WET_CUTOFF_DEFAULT = 0.5

#: What this screen does NOT look at. Stated on every result.
UNTESTED_MECHANISMS = (
    "laminated sand-shale thin beds (see thin_bed_correction, which refuses: no "
    "laminated resistivity model is in this corpus)",
    "conductive minerals such as pyrite or glauconite",
    "fresh or unknown formation water, where Rw itself is the error",
)


# --- #Q1 thin_bed_correction --------------------------------------------------


def thin_bed_correction(rt: float | None = None, rsand: float | None = None,
                        rshale: float | None = None, *,
                        vshale: float | None = None,
                        bed_thickness_ft: float | None = None,
                        ) -> Refusal:
    """Always refuses. No laminated sand-shale resistivity model is in this corpus.

    Arguments are accepted and ignored so a caller's call site does not have to
    change to get the honest answer.

    The failure this tool would fix is real and is exactly the pay a stripper
    operator has already drilled through: in laminated sand and shale below the
    tool's vertical resolution, a deep resistivity averages the conductive shale
    laminae in with the resistive sand, the interval reads wet, and the sand
    laminae are pay. Correcting it needs the laminated model, which parallels the
    sand and shale conductivities by their volume fractions. That model is not
    printed here, and writing it from memory would produce a corrected Rt with a
    citation pointing at a segment that does not contain it.
    """
    return Refusal(
        reason=(
            "No thin-bed resistivity correction is available from this corpus. The "
            "only bed-thickness material here is a different correction: trieste#5 "
            "corrects a tool's reading for the thickness of the bed it sits in, via "
            "charts Rcor-5 to Rcor-9, and its Eq. 7-6 mixes conductivities by the "
            "tool's geometrical factors over the mud, invaded and virgin zones. "
            "Neither splits a bed into sand and shale laminae, which is what the "
            "low-resistivity thin-bed miss requires, and the charts are images so "
            "even the correction they do describe cannot be evaluated here. "
            "low_resistivity_screen covers the one low-resistivity mechanism this "
            "corpus does support, and names this one as untested."
        ),
        needed=(
            "a source printing the laminated sand-shale resistivity model, for "
            "example Poupon, Loy and Tixier (1954), or an SPWLA low-resistivity-pay "
            "paper carrying the laminated formulation",
            "or a resistivity anisotropy (Rh, Rv) measurement, which the laminated "
            "model can be solved against",
        ),
        source=TRIESTE_BED_THICKNESS,
    )


# --- #Q2 low_resistivity_screen -----------------------------------------------


@dataclass(frozen=True)
class LowResistivityCandidates:
    """A CANDIDATE list, and the record that produced it. Never a conclusion.

    `candidates` holds the BVW `Quantity` of each flagged depth, so every entry
    carries the phi and Sw it came from and the equation that produced it. An
    empty tuple with `at_irreducible` True means the interval is at irreducible
    saturation but nothing in it reads wet, which is the ordinary case and is not
    a failure of the screen.
    """

    candidates: tuple[Quantity, ...]
    at_irreducible: bool | None
    bvw: BulkVolumeWater
    verdict: str
    sw_wet_cutoff: float
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)


def low_resistivity_screen(samples: Sequence[Mapping[str, Any]], *,
                           sw_wet_cutoff: float = SW_WET_CUTOFF_DEFAULT,
                           tolerance: float = BUCKLES_SPREAD_TOLERANCE,
                           rock_class: str | None = None
                           ) -> LowResistivityCandidates | Refusal:
    """Depths that read wet but whose BVW says irreducible. Candidates, not pay.

    Each `samples` record needs `phi` and `sw` and may carry `depth_ft`, `name`
    and `vshale`. The screen is one sentence of `asquith#45` turned into code: if
    BVW is constant across the interval the zone is at irreducible water
    saturation, and hydrocarbon production from such a zone "should be water
    free" whatever the Archie Sw reads. So a depth whose Sw is above
    `sw_wet_cutoff` inside a constant-BVW interval is a candidate for a second
    look, and that is all it is.

    Both thresholds are house rules and both are arguments: `tolerance` is the
    Buckles constancy tolerance (see `bulk_volume_water`), and `sw_wet_cutoff`
    has no published basis in this corpus at all.

    This tests ONE of the several causes of low-resistivity pay. The others are
    listed in `UNTESTED_MECHANISMS` and flagged on every result.
    """
    record = _bulk_volume_water(samples, tolerance=tolerance, rock_class=rock_class)
    if isinstance(record, Refusal):
        return record
    sw_wet_cutoff = float(sw_wet_cutoff)

    flags: list[str] = list(record.flags)
    flags.append(
        f"sw_wet_cutoff {sw_wet_cutoff} is a PROVISIONAL house rule; no Sw cutoff of "
        "this kind is published in this corpus")
    flags.append(
        "this screen tests only the irreducible-saturation mechanism that asquith#45 "
        "supports. Untested here: " + "; ".join(UNTESTED_MECHANISMS))

    supplied_vsh = [float(row["vshale"]) for row in samples
                    if isinstance(row, Mapping) and row.get("vshale") is not None]
    assumptions: dict[str, Any] = {
        "rule": "asquith#45: a zone at irreducible water saturation produces water "
                "free, whatever the Archie Sw reads",
        "tolerance_basis": ASQUITH_BUCKLES_FIGURES,
        "result_status": "CANDIDATES for review, not a pay determination",
        "untested_mechanisms": UNTESTED_MECHANISMS,
    }
    if supplied_vsh:
        assumptions["vshale_max"] = max(supplied_vsh)
        flags.append(
            f"vshale up to {max(supplied_vsh):.3f} was supplied but not acted on: "
            "shale conductivity is a separate low-resistivity mechanism, and "
            "shaly_sand_sw is the tool that models it")

    if record.at_irreducible is not True:
        if record.at_irreducible is None:
            verdict = ("no candidates: the Buckles constancy test needs BVW at several "
                       "depths, so this interval could not be screened. That is not a "
                       "conclusion either way")
        else:
            verdict = ("no candidates: BVW varies across the interval, so by asquith#45 "
                       "the zone is not at irreducible water saturation and a wet-looking "
                       "resistivity is most simply explained by movable water. That is a "
                       "screening outcome, not a conclusion")
        return LowResistivityCandidates(
            candidates=(), at_irreducible=record.at_irreducible, bvw=record,
            verdict=verdict, sw_wet_cutoff=sw_wet_cutoff,
            flags=tuple(flags), assumptions=assumptions,
        )

    candidates = tuple(q for q in record.bvw if q.inputs["Sw"] >= sw_wet_cutoff)
    if candidates:
        verdict = (
            f"{len(candidates)} of {len(record.bvw)} depths are CANDIDATES for "
            "low-resistivity pay: BVW is constant across the interval, so asquith#45 "
            "puts the zone at irreducible water saturation and its production should "
            f"be water free, yet their Archie Sw is at or above {sw_wet_cutoff} and "
            "would read wet against a conventional cutoff. This is a candidate list "
            "for review, not a conclusion and not a pay determination: confirm the "
            "grain size against Table 7.1, the Rw, and the resistivity itself before "
            "anything is perforated on it")
    else:
        verdict = (
            "no candidates: the interval is at irreducible water saturation by the "
            f"asquith#45 BVW test, but no depth reads wet against the {sw_wet_cutoff} "
            "cutoff, so there is nothing here that a conventional Sw screen would "
            "have thrown away. That is a screening outcome, not a conclusion")

    return LowResistivityCandidates(
        candidates=candidates, at_irreducible=True, bvw=record, verdict=verdict,
        sw_wet_cutoff=sw_wet_cutoff, flags=tuple(flags), assumptions=assumptions,
    )


# --- #Q3 rock_typing ----------------------------------------------------------


def rock_typing(samples: Sequence[Mapping[str, Any]] | None = None, *,
                k_md: float | None = None, phi: float | None = None,
                n_groups: int | None = None) -> Refusal:
    """Always refuses. No flow zone indicator or reservoir quality index exists here.

    Arguments are accepted and ignored so a caller's call site does not have to
    change to get the honest answer.

    The corpus was searched for "flow zone indicator", "FZI", "reservoir quality
    index", "RQI", "Amaefule", "hydraulic unit" and "flow unit". The only hits
    are a passing mention of flow units recognised from borehole images
    (asquith#60, narrative, no equation) and the Kozeny partial-penetration
    equation in the coning documents, which is a production rate and not a rock
    type. Neither supports RQI = 0.0314 sqrt(k/phi), the normalised porosity
    index, or the FZI grouping built on them.
    """
    return Refusal(
        reason=(
            "No flow zone indicator or reservoir quality index is available from this "
            "corpus: neither Amaefule's RQI and FZI nor any other hydraulic-unit "
            "grouping appears in any document here, in equation form or otherwise. "
            "Grouping intervals by flow behaviour therefore has no citable basis, and "
            "a plausible-looking FZI written from memory would carry a citation to a "
            "segment that does not contain it. Asquith's log-derived permeability "
            "correlations (Wyllie-Rose, Timur, Coates-Dumanoir, asquith#48) are the "
            "corpus-backed way to say something about flow capacity, and "
            "bulk_volume_water is the corpus-backed way to say whether they are even "
            "valid here: asquith#48 requires a zone at irreducible water saturation "
            "before any of them may be applied."
        ),
        needed=(
            "Amaefule et al., 1993, SPE 26436, for RQI, the normalised porosity index "
            "and FZI",
            "or core-measured permeability and porosity pairs, plus a source for the "
            "grouping method",
        ),
        source=ASQUITH_PERMEABILITY,
    )
