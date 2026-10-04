"""Tool #90 `perf_config_evaluate` — score a proposed gun configuration end to end.

Merge target: `tools/perforation.py`. Spec: `specs/90-perf_config_evaluate.md`.

The non-obvious decisions, all of them forced by what the source does and does not
publish:

*   **There is no scoring formula.** `slb-choosing-a-perforation-strategy#4` ranks
    four geometrical factors 1-4 by relative importance and says only that "the
    optimum perforation design establishes the proper tradeoff of these factors".
    Both equations sidecars for these documents recover nothing usable (SLB's is
    empty; the manual's four fragments are a truncated penetration ratio and three
    pressure-regime inequalities). Turning ranks into a desirability number needs
    weights nobody published, so none are invented. `Quantity.value` is the **count
    of source-stated design rules the configuration violates** — arithmetic over
    sourced booleans, every unit of it a quoted sentence in `inputs["violations"]`.
    Zero means "nothing published objects", not "good". `not-a-merit-score` is on
    every result.

*   **Two tables, and they conflict.** The upper table is conditioned on completion
    type, the lower on reservoir condition, and the lower is captioned "common
    considerations for perforating natural completions". Under natural fractures
    the lower table puts shot density at rank 3 where the upper table's Natural
    column allows only "1 or 2". The same gun therefore ranks differently depending
    on which is entered, so the conditioning variable is a required input and its
    absence is a refusal rather than a default.

*   **Two temperature tables, only one of which is a service rating.** The manual's
    "Explosive specifications" table gives RDX a 180 degC "temperature limit" with
    no duration; SLB rates RDX at 166 degC for one hour. The manual's column tracks
    material decomposition, not a job rating. The refusal is computed from SLB's
    time-at-temperature points; the manual's table is reproduced verbatim below,
    reported in `assumptions`, and never used as a limit.
"""
from __future__ import annotations

from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------

SRC_TABLES = "10-perforating/slb-choosing-a-perforation-strategy#4"          # p. 58
SRC_GLOSSARY = "10-perforating/slb-choosing-a-perforation-strategy#3"        # p. 57
SRC_GUNS = "10-perforating/slb-choosing-a-perforation-strategy#2"            # p. 56
SRC_NATURAL = "10-perforating/slb-choosing-a-perforation-strategy#5"         # p. 60
SRC_STIMULATED = "10-perforating/slb-choosing-a-perforation-strategy#8"      # p. 65
SRC_SANDCONTROL = "10-perforating/slb-choosing-a-perforation-strategy#9"     # p. 66
SRC_THERMAL = "10-perforating/slb-choosing-a-perforation-strategy#9"         # p. 66
SRC_CHARGES = "10-perforating/fundamentals-of-well-perforating-manual#1"     # Module 3

SOURCE = f"{SRC_TABLES}; {SRC_THERMAL}; {SRC_CHARGES}"

METHOD = (
    "SLB 1992 perforation-factor ranking + stated design rules "
    "(no published scoring formula)"
)

FACTORS = (
    "shot_density",
    "perforation_diameter",
    "perforation_phasing",
    "perforation_length",
)

# --------------------------------------------------------------------------
# Table 1 — "Relative importance of four main geometrical factors in the three
# completion types, where 1 is greatest and 4 is least."  slb#4, p. 58.
#
# Printed verbatim:
#   |  Perforation Geometry | Completion Type  |   |   |
#   |   |  Consolidated |   | Unconsolidated  |
#   |   |  Natural | Stimulated | Sand Control  |
#   |  Shot density         | 1 or 2 | 2 | 2  |
#   |  Perforation diameter | 3 or 4 | 3 | 1  |
#   |  Perforation phasing  | 3 or 4 | 1 | 3  |
#   |  Perforation length   | 1 or 2 | 4 | 4  |
#
# "1 or 2" is stored as the tuple (1, 2) — the source prints a band, not a value.
# --------------------------------------------------------------------------

FACTOR_RANKING_BY_COMPLETION_TYPE: dict[str, dict[str, Any]] = {
    "natural": {
        "shot_density": (1, 2),
        "perforation_diameter": (3, 4),
        "perforation_phasing": (3, 4),
        "perforation_length": (1, 2),
    },
    "stimulated": {
        "shot_density": 2,
        "perforation_diameter": 3,
        "perforation_phasing": 1,
        "perforation_length": 4,
    },
    "sand_control": {
        "shot_density": 2,
        "perforation_diameter": 1,
        "perforation_phasing": 3,
        "perforation_length": 4,
    },
}

COMPLETION_TYPE_CONSOLIDATION = {
    "natural": "Consolidated",
    "stimulated": "Consolidated",
    "sand_control": "Unconsolidated",
}

COMPLETION_TYPE_LABEL = {
    "natural": "Natural",
    "stimulated": "Stimulated",
    "sand_control": "Sand Control",
}

# --------------------------------------------------------------------------
# Table 2 — same figure, lower part.  slb#4, p. 58.  Caption: "The lower part of
# the figure shows common considerations for perforating natural completions."
#
# Printed verbatim:
#   |  Perforation Geometry | Isotropic Permeability | Anisotropy |   | Natural Fractures | Wellbore Damage  |
#   |   |   |  Of Any Cause | Laminar Shale  |   |   |
#   |  Shot density         | 2 | 1 | 1 | 3 | 2  |
#   |  Perforation diameter | 4 | 3 | 4 | 4 | 4  |
#   |  Perforation phasing  | 3 | 4 | 3 | 2 | 3  |
#   |  Perforation length   | 1 | 2 | 2 | 1 | 1  |
# --------------------------------------------------------------------------

FACTOR_RANKING_BY_RESERVOIR_CONDITION: dict[str, dict[str, int]] = {
    "isotropic_permeability": {
        "shot_density": 2,
        "perforation_diameter": 4,
        "perforation_phasing": 3,
        "perforation_length": 1,
    },
    "anisotropy_any_cause": {
        "shot_density": 1,
        "perforation_diameter": 3,
        "perforation_phasing": 4,
        "perforation_length": 2,
    },
    "laminar_shale": {
        "shot_density": 1,
        "perforation_diameter": 4,
        "perforation_phasing": 3,
        "perforation_length": 2,
    },
    "natural_fractures": {
        "shot_density": 3,
        "perforation_diameter": 4,
        "perforation_phasing": 2,
        "perforation_length": 1,
    },
    "wellbore_damage": {
        "shot_density": 2,
        "perforation_diameter": 4,
        "perforation_phasing": 3,
        "perforation_length": 1,
    },
}

RESERVOIR_CONDITION_LABEL = {
    "isotropic_permeability": "Isotropic Permeability",
    "anisotropy_any_cause": "Anisotropy — Of Any Cause",
    "laminar_shale": "Anisotropy — Laminar Shale",
    "natural_fractures": "Natural Fractures",
    "wellbore_damage": "Wellbore Damage",
}

RANKING_TABLE_CAPTION = (
    "Relative importance of four main geometrical factors in the three completion "
    "types, where 1 is greatest and 4 is least. The optimum perforation design "
    "establishes the proper tradeoff of these factors. The lower part of the figure "
    "shows common considerations for perforating natural completions. When natural "
    "fractures are present, phasing becomes more important than density to improve "
    "communication between fractures and perforations."
)

# --------------------------------------------------------------------------
# Explosive specifications — fundamentals-of-well-perforating-manual#1, Module 3.
# Reproduced verbatim.  NOT used as a downhole limit: the column carries no
# exposure duration and its values track material decomposition, not a service
# rating.  See TIME_AT_TEMPERATURE_RATINGS for the ratings that are applied.
#
# The chemical-formulation row is partly OCR-corrupt (RDX is C3H6N6O6, printed
# C6H6N6; HNS is C14H6N6O12, printed C2H2N6O12; PSF's "SN6O14" is not a formula).
# Stored verbatim, marked, used for nothing.
# --------------------------------------------------------------------------

EXPLOSIVE_SPECIFICATIONS: dict[str, dict[str, Any]] = {
    "lead_azide": {
        "name": "Lead Azide",
        "class_as_printed": "PRIMARY",
        "chemical_formulation_as_printed": "PbN_{6}",
        "ocr_suspect_formula": False,
        "temperature_limit_degc": 329,
        "density_kg_m3": None,
        "detonation_velocity_m_s": None,
        "remarks": "",
    },
    "tacot": {
        "name": "Tacot",
        "class_as_printed": "PRIMARY",
        "chemical_formulation_as_printed": "C_{12}H_{8}O_{12}N_{4}",
        "ocr_suspect_formula": False,
        "temperature_limit_degc": 378,
        "density_kg_m3": None,
        "detonation_velocity_m_s": None,
        "remarks": "",
    },
    "hns": {
        "name": "HNS",
        "class_as_printed": "SECONDARY",
        "chemical_formulation_as_printed": "C_{2}H_{2}N_{6}O_{12}",
        "ocr_suspect_formula": True,
        "temperature_limit_degc": 320,
        "density_kg_m3": 1740,
        "detonation_velocity_m_s": 7000,
        "remarks": "For HT charges",
    },
    "rdx": {
        "name": "RDX",
        "class_as_printed": "SECONDARY",
        "chemical_formulation_as_printed": "C_{6}H_{6}N_{6}",
        "ocr_suspect_formula": True,
        "temperature_limit_degc": 180,
        "density_kg_m3": 1820,
        "detonation_velocity_m_s": 8400,
        "remarks": "Most common",
    },
    "psf": {
        "name": "PSF",
        "class_as_printed": "SECONDARY",
        "chemical_formulation_as_printed": "SN_{6}O_{14}",
        "ocr_suspect_formula": True,
        "temperature_limit_degc": 307,
        "density_kg_m3": None,
        "detonation_velocity_m_s": None,
        "remarks": "For HT charges",
    },
    "hmx": {
        "name": "HMX",
        "class_as_printed": "SECONDARY",
        "chemical_formulation_as_printed": "C_{4}H_{8}N_{8}O_{8}",
        "ocr_suspect_formula": False,
        "temperature_limit_degc": 327,
        "density_kg_m3": 1900,
        "detonation_velocity_m_s": 9124,
        "remarks": ">T than RDX",
    },
}

# PYX is named at slb#9 alongside HNS as a high-temperature explosive but does not
# appear in the manual's specification table.
KNOWN_CHARGE_TYPES = tuple(EXPLOSIVE_SPECIFICATIONS) + ("pyx",)

# --------------------------------------------------------------------------
# Time-at-temperature ratings — slb#9, p. 66, quoted:
#
#   "When conveyed by wireline, RDX is limited to exposure of 1 hour at 330 degF
#   [166 degC], or when tubing conveyed, to 100 hours at 200 degF [93 degC].
#   Similarly, HMX survives 1 hour at 400 degF [204 degC], and 100 hours at
#   300 degF [149 degC]."
#
# HMX's conveyance mapping is an inference from "Similarly" — flagged on use.
# --------------------------------------------------------------------------

_RDX_QUOTE = (
    "When conveyed by wireline, RDX is limited to exposure of 1 hour at 330°F "
    "[166°C], or when tubing conveyed, to 100 hours at 200°F [93°C]."
)
_HMX_QUOTE = (
    "Similarly, HMX survives 1 hour at 400°F [204°C], and 100 hours at "
    "300°F [149°C]."
)

TIME_AT_TEMPERATURE_RATINGS: dict[str, tuple[dict[str, Any], ...]] = {
    "rdx": (
        {
            "exposure_hours": 1.0,
            "limit_degf": 330.0,
            "limit_degc": 166.0,
            "conveyance_as_printed": "wireline",
            "conveyance_inferred": False,
            "quote": _RDX_QUOTE,
            "anchor": SRC_THERMAL,
        },
        {
            "exposure_hours": 100.0,
            "limit_degf": 200.0,
            "limit_degc": 93.0,
            "conveyance_as_printed": "tubing_conveyed",
            "conveyance_inferred": False,
            "quote": _RDX_QUOTE,
            "anchor": SRC_THERMAL,
        },
    ),
    "hmx": (
        {
            "exposure_hours": 1.0,
            "limit_degf": 400.0,
            "limit_degc": 204.0,
            "conveyance_as_printed": "wireline",
            "conveyance_inferred": True,
            "quote": _HMX_QUOTE,
            "anchor": SRC_THERMAL,
        },
        {
            "exposure_hours": 100.0,
            "limit_degf": 300.0,
            "limit_degc": 149.0,
            "conveyance_as_printed": "tubing_conveyed",
            "conveyance_inferred": True,
            "quote": _HMX_QUOTE,
            "anchor": SRC_THERMAL,
        },
    ),
}

# "At higher temperatures or longer exposures, explosives and special elastomers
# and lubricants are available to perforate reliably at up to 500 degF [260 degC]
# for wireline-conveyed applications and up to 460 degF [238 degC] for TCP.
# Explosives for high temperatures, called HNS and PYX ..."  slb#9, p. 66.
# A ceiling with NO published duration.
_HT_QUOTE = (
    "At higher temperatures or longer exposures, explosives and special elastomers "
    "and lubricants are available to perforate reliably at up to 500°F "
    "[260°C] for wireline-conveyed applications and up to 460°F "
    "[238°C] for TCP. Explosives for high temperatures, called HNS and PYX, "
    "are much more expensive and generally stocked only in areas where "
    "high-temperature wells are common."
)

HT_EXPLOSIVE_CEILINGS: dict[str, dict[str, Any]] = {
    "wireline": {
        "limit_degf": 500.0,
        "limit_degc": 260.0,
        "exposure_hours": None,
        "quote": _HT_QUOTE,
        "anchor": SRC_THERMAL,
    },
    "tubing_conveyed": {
        "limit_degf": 460.0,
        "limit_degc": 238.0,
        "exposure_hours": None,
        "quote": _HT_QUOTE,
        "anchor": SRC_THERMAL,
    },
}

HT_EXPLOSIVES = ("hns", "pyx")

# No time-at-temperature *service* rating is published for these anywhere in the
# corpus; the manual gives only a material temperature limit.
NO_SERVICE_RATING = ("tacot", "psf")

THERMAL_DEGRADATION_CONSEQUENCE = (
    "This degradation results in a loss of sensitivity—leading to a potential "
    "misfire—and loss of strength—leading to reduced charge performance."
)

CONVEYANCES = ("wireline", "tubing_conveyed")

# --------------------------------------------------------------------------
# Discrete phasing set and covered geometry ranges.  These are the values the
# source names; it does not publish a complete standard set, so membership is
# derived from the text and each member's citation is carried.
# --------------------------------------------------------------------------

PHASING_SET_DEG: dict[int, str] = {
    0: f"'Phasing of 0° has all shots in one line, meaning the angle between "
       f"shots is actually 360°.' ({SRC_GUNS}, footnote 2, p. 56)",
    45: f"'The 135°/45° designation means the angle between successive "
        f"shots is 135°, resulting in an overall phasing of 45°.' "
        f"({SRC_NATURAL}, p. 60)",
    60: f"'A 60° phasing means one shot every 60° azimuthally' "
        f"({SRC_GUNS}, footnote 2, p. 56)",
    90: f"'a 3-in. [8-cm] perforation of 90° phasing' ({SRC_TABLES}, p. 58)",
    180: "'the Pivot Gun system, which delivers casing gun performance with "
         "180° phasing' "
         "(10-perforating/slb-choosing-a-perforation-strategy#6, p. 62)",
}

SHOT_DENSITY_BAND_SPF = (4.0, 12.0)
SHOT_DENSITY_BAND_CITATION = (
    f"'4 shot-per-foot (spf) density' ({SRC_GUNS}, p. 56) and 'There is 1 vertical "
    f"inch [2.5 cm] between shots, making 12 shots per foot' ({SRC_NATURAL}, p. 60)"
)

PENETRATION_BAND_IN = (3.0, 30.0)
PENETRATION_BAND_CITATION = (
    f"'a 3-in. [8-cm] perforation of 90° phasing' and 'a large charge that "
    f"penetrates 30 in. [76 cm] into the standard API test target' ({SRC_TABLES}, p. 58)"
)

# "Big hole charge ... A 'big hole' has an entrance diameter of 0.5 to 1.2 in.
# [13 to 30 mm] ... Conventional deep penetrators have an entrance hole diameter
# of 0.3 to 0.5 in. [8 to 13 mm]."  slb#3, p. 57.
ENTRANCE_HOLE_CLASSES_IN: dict[str, tuple[float, float]] = {
    "deep_penetrator": (0.30, 0.50),
    "big_hole": (0.50, 1.20),
}
ENTRANCE_HOLE_MAX_IN = 1.20
ENTRANCE_HOLE_CLASS_CITATION = (
    "\"**Big hole charge**: A shaped charge that gives priority to entrance hole "
    "over depth of penetration, used exclusively in sand control completions. A "
    "'big hole' has an entrance diameter of 0.5 to 1.2 in. [13 to 30 mm], usually "
    "about twice that of a deep penetrator charge of similar size. Conventional "
    "deep penetrators have an entrance hole diameter of 0.3 to 0.5 in. "
    f"[8 to 13 mm].\" ({SRC_GLOSSARY}, p. 57)"
)

PENETRATION_PROVENANCE_NOTE = (
    "'Penetration in surface tests is different than under stress in the well.' "
    "'Unconfined compressive strength of test targets is a minimum of 3300 psi, "
    "representing only low-strength reservoir rock (reservoir rock strength ranges "
    f"from 0 to 25,000 psi).' ({SRC_TABLES}, p. 58)"
)

# --------------------------------------------------------------------------
# The design rules that are actually checked.  Each is one quoted sentence.
# --------------------------------------------------------------------------

DESIGN_RULES: dict[str, dict[str, Any]] = {
    "R1_stimulated_phasing_le_60": {
        "applies_to": "stimulated",
        "quote": (
            "This indicates the phase angle should be 60° or less so the "
            "perforation is always within 30° of a fracture."
        ),
        "anchor": SRC_STIMULATED,
        "page": 65,
    },
    "R2_natural_entrance_hole_gt_0p25in": {
        "applies_to": "natural",
        "quote": (
            "Under typical flow conditions, perforation diameter does not adversely "
            "affect flow once it exceeds 0.25 in. [6 mm], which today is provided by "
            "nearly all guns used in natural completions."
        ),
        "anchor": SRC_NATURAL,
        "page": 60,
    },
    "R3_sand_control_big_hole": {
        "applies_to": "sand_control",
        "quote": (
            "A 'big hole' has an entrance diameter of 0.5 to 1.2 in. [13 to 30 mm] "
            "... used exclusively in sand control completions."
        ),
        "anchor": SRC_GLOSSARY,
        "page": 57,
    },
    "R4_penetration_1p5x_damage": {
        "applies_to": "natural/wellbore_damage",
        "quote": (
            "In the context of well productivity, a deep penetrator shoots to a "
            "depth 1.5 times that of the wellbore damage."
        ),
        "anchor": SRC_NATURAL,
        "page": 60,
        "needs_input": "damage_depth_in",
    },
    "R5_stimulated_proppant_bridging": {
        "applies_to": "stimulated",
        "quote": (
            "They found that the perforation must always be at least twice the "
            "proppant diameter. When perforation diameter is at least six times "
            "proppant diameter, proppant concentrations can increase without risk "
            "of bridging."
        ),
        "anchor": SRC_STIMULATED,
        "page": 65,
        "needs_input": "proppant_diameter_in",
    },
}

PENETRATION_1P5X_FACTOR = 1.5
PROPPANT_MIN_RATIO = 2.0
PROPPANT_NO_BRIDGING_RATIO = 6.0
# Both ratios are inclusive published boundaries -- "at least twice the proppant
# diameter", "at least six times proppant diameter" -- so a design sitting exactly
# on one meets it. Binary floating point puts 1.2/0.2 and 0.6/0.1 one ulp *below*
# 6.0, which made the tool tell an operator that a 6.00x design "is below the 6x"
# threshold. Compared with a relative tolerance so the boundary is the source's
# and not IEEE-754's.
RATIO_BOUNDARY_TOL = 1e-9
STIMULATED_MAX_PHASING_DEG = 60.0
NATURAL_MIN_ENTRANCE_HOLE_IN = 0.25

FRACTURED_POPULAR_CONFIG = {
    "phasing_deg": 60,
    "shot_density_spf": 5,
    "quote": (
        "In fractured formations, a popular gun configuration uses 60° phasing "
        "with 5 spf."
    ),
    "anchor": SRC_TABLES,
}

HSD_CASING_STRENGTH_ADVISORY = {
    "quote": (
        "The 135°/45° phased HSD guns achieve the greatest area open to "
        "flow while maintaining maximum casing strength."
    ),
    "anchor": SRC_SANDCONTROL,
    "note": (
        "The casing-strength relationship itself is an image (img-27.jpeg); no "
        "numeric casing-strength check is possible and none is attempted."
    ),
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _rank_key(rank: Any) -> tuple[float, float]:
    """Sort key for a rank that may be an int or a printed band such as (1, 2)."""
    if isinstance(rank, tuple):
        return (float(rank[0]), float(rank[1]))
    return (float(rank), float(rank))


def _priority_groups(ranking: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    """Factors most- to least-important, grouped where the source ties them.

    Table 1's Natural column prints bands ("1 or 2", "3 or 4"), so two factors can
    share a band and the source does not order within it. Returning groups keeps
    that ambiguity visible instead of breaking the tie arbitrarily.
    """
    groups: dict[tuple[float, float], list[str]] = {}
    for factor in FACTORS:
        groups.setdefault(_rank_key(ranking[factor]), []).append(factor)
    return tuple(tuple(groups[k]) for k in sorted(groups))


def _rank_within(band_or_rank: Any, rank: int) -> bool:
    if isinstance(band_or_rank, tuple):
        return band_or_rank[0] <= rank <= band_or_rank[1]
    return band_or_rank == rank


def _classify_entrance_hole(d_in: float) -> str | None:
    if ENTRANCE_HOLE_CLASSES_IN["big_hole"][0] <= d_in <= ENTRANCE_HOLE_CLASSES_IN["big_hole"][1]:
        return "big_hole"
    if ENTRANCE_HOLE_CLASSES_IN["deep_penetrator"][0] <= d_in < ENTRANCE_HOLE_CLASSES_IN["deep_penetrator"][1]:
        return "deep_penetrator"
    return None


def _select_rating(charge_type: str, exposure_hours: float) -> dict[str, Any] | None:
    """Smallest published duration >= the requested exposure.

    Monotone-conservative: degradation grows with both temperature and time, so a
    shorter exposure is covered by a longer-duration rating at the same temperature.
    No interpolation between the two published points — no such curve is published.
    """
    for point in TIME_AT_TEMPERATURE_RATINGS[charge_type]:
        if exposure_hours <= point["exposure_hours"]:
            return point
    return None


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------

def perf_config_evaluate(
    *,
    completion_type: str | None,
    shot_density_spf: float,
    phasing_deg: float,
    penetration_in: float,
    entrance_hole_in: float,
    charge_type: str | None,
    bht_degf: float,
    exposure_hours: float,
    conveyance: str | None,
    reservoir_condition: str | None = None,
    damage_depth_in: float | None = None,
    proppant_diameter_in: float | None = None,
) -> Quantity | Refusal:
    """Assess a proposed perforating gun configuration against the SLB 1992 tables.

    Returns a `Quantity` whose value is the **count of source-stated design rules
    the configuration violates** (unit "violations"), with the applied factor
    ranking, the reason that ranking was chosen, the per-factor assessment and every
    violation quote on `inputs`. Not a merit score — see the module docstring.

    Returns a `Refusal` when the source cannot support an answer: a missing or
    unrecognised conditioning variable, a charge outside its published
    time-at-temperature rating, a phasing the source does not name, or a geometry
    value outside the range the tables were drawn for.
    """
    # ---- programmer error, not refusal -----------------------------------
    if shot_density_spf <= 0:
        raise ValueError("shot_density_spf must be positive")
    if penetration_in <= 0:
        raise ValueError("penetration_in must be positive")
    if entrance_hole_in <= 0:
        raise ValueError("entrance_hole_in must be positive")
    if exposure_hours < 0:
        raise ValueError("exposure_hours must not be negative")
    if not 0 <= phasing_deg <= 360:
        raise ValueError("phasing_deg must lie between 0 and 360 degrees")
    if damage_depth_in is not None and damage_depth_in <= 0:
        raise ValueError("damage_depth_in must be positive when supplied")
    if proppant_diameter_in is not None and proppant_diameter_in <= 0:
        raise ValueError("proppant_diameter_in must be positive when supplied")

    flags: list[str] = ["not-a-merit-score"]
    advisories: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    # ---- 1. conditioning variable: completion type ------------------------
    if completion_type not in FACTOR_RANKING_BY_COMPLETION_TYPE:
        return Refusal(
            reason=(
                "completion_type is the conditioning variable for the upper ranking "
                f"table and must be one of "
                f"{sorted(FACTOR_RANKING_BY_COMPLETION_TYPE)} "
                "(the three columns of 'Relative importance of four main geometrical "
                f"factors in the three completion types'); got {completion_type!r}."
            ),
            needed=("completion_type",),
            source=SRC_TABLES,
        )

    # ---- 2. conditioning variable: reservoir condition (natural only) -----
    if reservoir_condition is not None and reservoir_condition not in FACTOR_RANKING_BY_RESERVOIR_CONDITION:
        return Refusal(
            reason=(
                "reservoir_condition must be one of "
                f"{sorted(FACTOR_RANKING_BY_RESERVOIR_CONDITION)} "
                "(the five columns of the lower ranking table); "
                f"got {reservoir_condition!r}."
            ),
            needed=("reservoir_condition",),
            source=SRC_TABLES,
        )

    if completion_type == "natural" and reservoir_condition is None:
        return Refusal(
            reason=(
                "A natural completion is ranked by both tables and they disagree, so "
                "the tool will not pick one silently. The upper table's Natural "
                "column gives shot density rank '1 or 2' and phasing '3 or 4'; the "
                "lower table's Natural Fractures column gives shot density 3 and "
                "phasing 2. Caption: '"
                + RANKING_TABLE_CAPTION
                + "' Supply reservoir_condition, one of "
                f"{sorted(FACTOR_RANKING_BY_RESERVOIR_CONDITION)}."
            ),
            needed=("reservoir_condition",),
            source=SRC_TABLES,
        )

    # ---- 3. conveyance ----------------------------------------------------
    if conveyance not in CONVEYANCES:
        return Refusal(
            reason=(
                "The time-at-temperature ratings are printed per conveyance method "
                f"({_RDX_QUOTE}), so conveyance must be one of {list(CONVEYANCES)}; "
                f"got {conveyance!r}."
            ),
            needed=("conveyance",),
            source=SRC_THERMAL,
        )

    # ---- 4. charge type ---------------------------------------------------
    if charge_type not in KNOWN_CHARGE_TYPES:
        return Refusal(
            reason=(
                "charge_type must be one of the explosives the corpus documents: "
                f"{list(KNOWN_CHARGE_TYPES)}; got {charge_type!r}."
            ),
            needed=("charge_type",),
            source=SRC_CHARGES,
        )

    if charge_type == "lead_azide":
        return Refusal(
            reason=(
                "Lead azide is a primary explosive: 'A primary explosive, used in the "
                "detonator, detonates from heat (applied by electric power) or impact "
                "... A secondary explosive, used in detonating cord, shaped charges "
                "and boosters, is detonated only by another detonation.' It is a "
                "detonator explosive, not a shaped-charge explosive, so it is not a "
                "gun-configuration input."
            ),
            needed=("charge_type (a secondary explosive: rdx, hmx, hns or pyx)",),
            source=SRC_GLOSSARY,
        )

    if charge_type in NO_SERVICE_RATING:
        spec = EXPLOSIVE_SPECIFICATIONS[charge_type]
        return Refusal(
            reason=(
                f"No time-at-temperature service rating is published for "
                f"{spec['name']} anywhere in the corpus. The only figure available is "
                f"the manual's 'Temperature limit [°C] = {spec['temperature_limit_degc']}', "
                "which carries no exposure duration and is a material limit rather "
                "than a downhole rating (the same table gives RDX 180 °C where "
                "the service rating is 166 °C for one hour). Refusing rather "
                "than treating a material limit as a job rating."
            ),
            needed=(
                f"a published time-at-temperature rating for {spec['name']} "
                "(manufacturer datasheet or API 19B qualification)",
            ),
            source=f"{SRC_CHARGES}; {SRC_THERMAL}",
        )

    # ---- 5. the thermal / exposure-time refusal ---------------------------
    charge_rating: dict[str, Any]
    if charge_type in HT_EXPLOSIVES:
        ceiling = HT_EXPLOSIVE_CEILINGS[conveyance]
        charge_rating = {
            "charge": charge_type.upper(),
            "kind": "high-temperature ceiling (no exposure duration published)",
            "limit_degf": ceiling["limit_degf"],
            "limit_degc": ceiling["limit_degc"],
            "rated_exposure_hours": None,
            "conveyance": conveyance,
            "quote": ceiling["quote"],
            "anchor": ceiling["anchor"],
        }
        flags.append("no-duration-published-for-ht-explosive")
        if bht_degf > ceiling["limit_degf"]:
            return Refusal(
                reason=(
                    f"{charge_type.upper()} is not rated for {bht_degf:g} °F "
                    f"{conveyance.replace('_', '-')}-conveyed. The source's ceiling "
                    f"is {ceiling['limit_degf']:g} °F "
                    f"[{ceiling['limit_degc']:g} °C]: \"{ceiling['quote']}\" "
                    f"{THERMAL_DEGRADATION_CONSEQUENCE}"
                ),
                needed=(
                    "a bottomhole temperature at or below the published ceiling, "
                    "or a charge with a higher published rating",
                ),
                source=SRC_THERMAL,
            )
    else:
        point = _select_rating(charge_type, exposure_hours)
        if point is None:
            longest = TIME_AT_TEMPERATURE_RATINGS[charge_type][-1]
            return Refusal(
                reason=(
                    f"Exposure of {exposure_hours:g} h is beyond the longest "
                    f"time-at-temperature rating published for "
                    f"{charge_type.upper()}: "
                    f"{longest['exposure_hours']:g} hours at "
                    f"{longest['limit_degf']:g} °F "
                    f"[{longest['limit_degc']:g} °C]. "
                    f"\"{longest['quote']}\" No rating is published past that point "
                    "and none is extrapolated."
                ),
                needed=(
                    "an exposure time within the published rating, or a manufacturer "
                    "time-temperature derating curve",
                ),
                source=SRC_THERMAL,
            )
        charge_rating = {
            "charge": charge_type.upper(),
            "kind": "published time-at-temperature point",
            "limit_degf": point["limit_degf"],
            "limit_degc": point["limit_degc"],
            "rated_exposure_hours": point["exposure_hours"],
            "conveyance_as_printed": point["conveyance_as_printed"],
            "conveyance_inferred": point["conveyance_inferred"],
            "quote": point["quote"],
            "anchor": point["anchor"],
            "selection_rule": (
                "smallest published duration >= the requested exposure "
                f"({exposure_hours:g} h -> the {point['exposure_hours']:g} h point)"
            ),
        }
        if bht_degf > point["limit_degf"]:
            return Refusal(
                reason=(
                    f"{charge_type.upper()} is rated "
                    f"{point['exposure_hours']:g} hour(s) at "
                    f"{point['limit_degf']:g} °F [{point['limit_degc']:g} °C]; "
                    f"the expected bottomhole temperature is {bht_degf:g} °F, "
                    f"{bht_degf - point['limit_degf']:g} °F above it for an "
                    f"exposure of {exposure_hours:g} h. \"{point['quote']}\" "
                    f"{THERMAL_DEGRADATION_CONSEQUENCE}"
                ),
                needed=(
                    "a charge rated for this temperature and exposure "
                    "(HNS or PYX reach 500 °F wireline / 460 °F TCP), "
                    "or a shorter exposure, or a lower bottomhole temperature",
                ),
                source=SRC_THERMAL,
            )
        if bht_degf == point["limit_degf"]:
            flags.append("at-published-temperature-limit")
        if point["conveyance_as_printed"] != conveyance:
            flags.append("conveyance-mismatch-with-published-rating")
        if point["conveyance_inferred"]:
            flags.append("charge-rating-conveyance-inferred")

    if charge_type in EXPLOSIVE_SPECIFICATIONS:
        flags.append("material-limit-table-not-a-service-rating")

    # ---- 6. phasing must be one the source names --------------------------
    phasing_key = int(phasing_deg) if float(phasing_deg).is_integer() else None
    if phasing_key not in PHASING_SET_DEG:
        return Refusal(
            reason=(
                f"{phasing_deg:g}° is not a phasing this source names. The "
                f"discrete set it uses is {sorted(PHASING_SET_DEG)}°: "
                + "; ".join(f"{k}° — {v}" for k, v in sorted(PHASING_SET_DEG.items()))
                + ". The ranking tables are not drawn for other phasings and none is "
                "interpolated."
            ),
            needed=(f"phasing_deg in {sorted(PHASING_SET_DEG)}",),
            source=SRC_TABLES,
        )

    # ---- 7. geometry inside the ranges the tables cover -------------------
    if not SHOT_DENSITY_BAND_SPF[0] <= shot_density_spf <= SHOT_DENSITY_BAND_SPF[1]:
        return Refusal(
            reason=(
                f"{shot_density_spf:g} spf is outside the shot-density range this "
                f"source covers, {SHOT_DENSITY_BAND_SPF[0]:g} to "
                f"{SHOT_DENSITY_BAND_SPF[1]:g} spf: {SHOT_DENSITY_BAND_CITATION}. "
                "The 1992 tables are not drawn for densities outside that band and "
                "the ranking is not extrapolated to them."
            ),
            needed=(
                "a shot density within the covered band, or a newer source covering "
                "modern high-shot-density guns",
            ),
            source=SRC_TABLES,
        )

    if not PENETRATION_BAND_IN[0] <= penetration_in <= PENETRATION_BAND_IN[1]:
        return Refusal(
            reason=(
                f"{penetration_in:g} in. of penetration is outside the range this "
                f"source covers, {PENETRATION_BAND_IN[0]:g} to "
                f"{PENETRATION_BAND_IN[1]:g} in.: {PENETRATION_BAND_CITATION}. "
                "The ranking is not extrapolated to penetrations the article does "
                "not describe."
            ),
            needed=(
                "a penetration within the covered band, or a newer source covering "
                "modern deep-penetrating charges",
            ),
            source=SRC_TABLES,
        )

    if entrance_hole_in > ENTRANCE_HOLE_MAX_IN:
        return Refusal(
            reason=(
                f"{entrance_hole_in:g} in. is larger than any entrance hole this "
                f"source describes; the biggest is the big-hole charge at "
                f"{ENTRANCE_HOLE_MAX_IN:g} in. {ENTRANCE_HOLE_CLASS_CITATION}"
            ),
            needed=("an entrance hole diameter within the documented charge classes",),
            source=SRC_GLOSSARY,
        )

    # ---- 8. select the ranking table --------------------------------------
    completion_ranking = FACTOR_RANKING_BY_COMPLETION_TYPE[completion_type]

    if completion_type == "natural":
        ranking_table = "Table 2 — natural completion, reservoir condition"
        ranking = dict(FACTOR_RANKING_BY_RESERVOIR_CONDITION[reservoir_condition])
        ranking_table_reason = (
            f"completion_type='natural' and reservoir_condition="
            f"'{reservoir_condition}'. The lower table is captioned 'The lower part "
            "of the figure shows common considerations for perforating natural "
            "completions', so for a natural completion it is the more specific "
            "conditioning and it governs. The upper table's Natural column is "
            "reported alongside as completion_type_ranking."
        )
        conflicts = [
            f for f in FACTORS
            if not _rank_within(completion_ranking[f], ranking[f])
        ]
        if conflicts:
            flags.append("ranking-tables-conflict")
    else:
        ranking_table = "Table 1 — completion type"
        ranking = dict(completion_ranking)
        ranking_table_reason = (
            f"completion_type='{completion_type}' "
            f"({COMPLETION_TYPE_LABEL[completion_type]}, "
            f"{COMPLETION_TYPE_CONSOLIDATION[completion_type]}). The lower table is "
            "captioned for natural completions only, so it does not apply here and "
            "the upper table governs."
        )
        conflicts = []
        if reservoir_condition is not None:
            flags.append("reservoir-condition-not-applied")

    # ---- 9. the sourced design rules --------------------------------------
    if completion_type == "stimulated":
        rule = DESIGN_RULES["R1_stimulated_phasing_le_60"]
        # Footnote 2: 0 deg phasing is 360 deg between shots, so it is the widest
        # spacing, not the narrowest -- "a 0 deg phasing could place the perforation
        # far from the fracture" (slb#8).
        effective_phasing = 360.0 if phasing_key == 0 else float(phasing_key)
        if effective_phasing > STIMULATED_MAX_PHASING_DEG:
            violations.append({
                "rule": "R1_stimulated_phasing_le_60",
                "quote": rule["quote"],
                "anchor": rule["anchor"],
                "detail": (
                    f"phasing {phasing_key}°"
                    + (
                        " (0° phasing puts all shots in one line, i.e. 360° "
                        "between shots — footnote 2)"
                        if phasing_key == 0 else ""
                    )
                    + f" exceeds the {STIMULATED_MAX_PHASING_DEG:g}° maximum."
                ),
            })

        rule5 = DESIGN_RULES["R5_stimulated_proppant_bridging"]
        if proppant_diameter_in is None:
            advisories.append({
                "rule": "R5_stimulated_proppant_bridging",
                "quote": rule5["quote"],
                "anchor": rule5["anchor"],
                "detail": (
                    "Not checked: proppant_diameter_in was not supplied. Supply it to "
                    "check the bridging ratio."
                ),
            })
            flags.append("rule-uncheckable-missing-input")
        else:
            ratio = entrance_hole_in / proppant_diameter_in
            if ratio < PROPPANT_MIN_RATIO * (1.0 - RATIO_BOUNDARY_TOL):
                violations.append({
                    "rule": "R5_stimulated_proppant_bridging",
                    "quote": rule5["quote"],
                    "anchor": rule5["anchor"],
                    "detail": (
                        f"entrance hole {entrance_hole_in:g} in. is "
                        f"{ratio:.2f}x the proppant diameter "
                        f"{proppant_diameter_in:g} in.; the source requires at least "
                        f"{PROPPANT_MIN_RATIO:g}x."
                    ),
                })
            elif ratio < PROPPANT_NO_BRIDGING_RATIO * (1.0 - RATIO_BOUNDARY_TOL):
                advisories.append({
                    "rule": "R5_stimulated_proppant_bridging",
                    "quote": rule5["quote"],
                    "anchor": rule5["anchor"],
                    "detail": (
                        f"ratio {ratio:.2f}x clears the {PROPPANT_MIN_RATIO:g}x "
                        f"minimum but is below the {PROPPANT_NO_BRIDGING_RATIO:g}x at "
                        "which proppant concentration can be raised without bridging "
                        "risk."
                    ),
                })

    if completion_type == "natural":
        rule = DESIGN_RULES["R2_natural_entrance_hole_gt_0p25in"]
        if entrance_hole_in <= NATURAL_MIN_ENTRANCE_HOLE_IN:
            violations.append({
                "rule": "R2_natural_entrance_hole_gt_0p25in",
                "quote": rule["quote"],
                "anchor": rule["anchor"],
                "detail": (
                    f"entrance hole {entrance_hole_in:g} in. does not exceed the "
                    f"{NATURAL_MIN_ENTRANCE_HOLE_IN:g} in. above which the source "
                    "says diameter stops adversely affecting flow."
                ),
            })

        rule4 = DESIGN_RULES["R4_penetration_1p5x_damage"]
        if reservoir_condition == "wellbore_damage":
            if damage_depth_in is None:
                advisories.append({
                    "rule": "R4_penetration_1p5x_damage",
                    "quote": rule4["quote"],
                    "anchor": rule4["anchor"],
                    "detail": (
                        "Not checked: damage_depth_in was not supplied, and "
                        "reservoir_condition='wellbore_damage' is exactly the case "
                        "the rule governs. Supply it to check the 1.5x rule."
                    ),
                })
                flags.append("rule-uncheckable-missing-input")
            else:
                required = PENETRATION_1P5X_FACTOR * damage_depth_in
                if penetration_in < required:
                    violations.append({
                        "rule": "R4_penetration_1p5x_damage",
                        "quote": rule4["quote"],
                        "anchor": rule4["anchor"],
                        "detail": (
                            f"penetration {penetration_in:g} in. is short of "
                            f"{PENETRATION_1P5X_FACTOR:g} x {damage_depth_in:g} = "
                            f"{required:g} in."
                        ),
                    })

        if reservoir_condition == "natural_fractures":
            if not (
                phasing_key == FRACTURED_POPULAR_CONFIG["phasing_deg"]
                and shot_density_spf == FRACTURED_POPULAR_CONFIG["shot_density_spf"]
            ):
                advisories.append({
                    "rule": "fractured_popular_configuration",
                    "quote": FRACTURED_POPULAR_CONFIG["quote"],
                    "anchor": FRACTURED_POPULAR_CONFIG["anchor"],
                    "detail": (
                        f"this configuration is {phasing_key}° / "
                        f"{shot_density_spf:g} spf. A preference in the source, not a "
                        "threshold."
                    ),
                })

    if completion_type == "sand_control":
        rule = DESIGN_RULES["R3_sand_control_big_hole"]
        if entrance_hole_in < ENTRANCE_HOLE_CLASSES_IN["big_hole"][0]:
            violations.append({
                "rule": "R3_sand_control_big_hole",
                "quote": rule["quote"],
                "anchor": rule["anchor"],
                "detail": (
                    f"entrance hole {entrance_hole_in:g} in. is below the "
                    f"{ENTRANCE_HOLE_CLASSES_IN['big_hole'][0]:g} in. floor of the "
                    "big-hole class that sand control completions use exclusively."
                ),
            })
        if phasing_key != 45:
            advisories.append({
                "rule": "hsd_135_45_casing_strength",
                "quote": HSD_CASING_STRENGTH_ADVISORY["quote"],
                "anchor": HSD_CASING_STRENGTH_ADVISORY["anchor"],
                "detail": HSD_CASING_STRENGTH_ADVISORY["note"],
            })

    # ---- 10. per-factor assessment ----------------------------------------
    hole_class = _classify_entrance_hole(entrance_hole_in)
    if hole_class is None and entrance_hole_in < ENTRANCE_HOLE_CLASSES_IN["deep_penetrator"][0]:
        flags.append("entrance-hole-below-deep-penetrator-class")
    flags.append("penetration-is-surface-test")

    factor_assessment = {
        "shot_density": {
            "rank": ranking["shot_density"],
            "value": shot_density_spf,
            "unit": "shots/ft",
            "note": (
                "'In most formations, vertical permeability is lower than "
                "horizontal. In all these cases, productivity is improved by use of "
                f"guns with high shot densities.' ({SRC_TABLES}, p. 58)"
            ),
        },
        "perforation_diameter": {
            "rank": ranking["perforation_diameter"],
            "value": entrance_hole_in,
            "unit": "in",
            "charge_class": hole_class,
            "note": ENTRANCE_HOLE_CLASS_CITATION,
        },
        "perforation_phasing": {
            "rank": ranking["perforation_phasing"],
            "value": phasing_key,
            "unit": "deg",
            "note": PHASING_SET_DEG[phasing_key],
        },
        "perforation_length": {
            "rank": ranking["perforation_length"],
            "value": penetration_in,
            "unit": "in",
            "note": PENETRATION_PROVENANCE_NOTE,
        },
    }

    inputs: dict[str, Any] = {
        "completion_type": completion_type,
        "reservoir_condition": reservoir_condition,
        "shot_density_spf": shot_density_spf,
        "phasing_deg": phasing_key,
        "penetration_in": penetration_in,
        "entrance_hole_in": entrance_hole_in,
        "charge_type": charge_type,
        "bht_degf": bht_degf,
        "exposure_hours": exposure_hours,
        "conveyance": conveyance,
        "damage_depth_in": damage_depth_in,
        "proppant_diameter_in": proppant_diameter_in,
        "ranking_table": ranking_table,
        "ranking_table_reason": ranking_table_reason,
        "ranking_table_caption": RANKING_TABLE_CAPTION,
        "factor_ranking": ranking,
        "factor_priority_order": _priority_groups(ranking),
        "completion_type_ranking": dict(completion_ranking),
        "ranking_conflicts": tuple(conflicts),
        "factor_assessment": factor_assessment,
        "violations": tuple(violations),
        "advisories": tuple(advisories),
        "charge_rating": charge_rating,
    }

    assumptions: dict[str, Any] = {
        "no_published_scoring_formula": (
            "The source ranks the four factors 1-4 by relative importance and "
            "publishes no weights and no scoring formula — 'The optimum "
            "perforation design establishes the proper tradeoff of these factors.' "
            "The returned value is therefore a count of violated source-stated "
            "rules, not a composite desirability score, and configurations cannot "
            "be ordered by it."
        ),
        "rating_selection_rule": (
            "Time-at-temperature is checked against the published point whose "
            "duration is the smallest >= the requested exposure (<=1 h -> the 1-hour "
            "point, 1-100 h -> the 100-hour point, >100 h -> refusal). "
            "Monotone-conservative; no interpolation, because no time-temperature "
            "curve is published."
        ),
        "hmx_conveyance_inferred": (
            "The source gives RDX's two points with explicit conveyance and HMX's "
            "with only the word 'Similarly'. The parallel wireline/TCP mapping for "
            "HMX is an inference and is flagged when applied."
        ),
        "material_limit_table_not_used": {
            "note": (
                "The manual's 'Temperature limit [°C]' column carries no "
                "exposure duration and its values track material decomposition "
                "(RDX 180 °C against a 166 °C one-hour service rating). It "
                "is reproduced for reference and is never used as a limit."
            ),
            "table": (
                EXPLOSIVE_SPECIFICATIONS.get(charge_type)
                if charge_type in EXPLOSIVE_SPECIFICATIONS else None
            ),
            "anchor": SRC_CHARGES,
        },
        "phasing_set_derivation": (
            "The source names 0, 45, 60, 90 and 180 degree phasings and no others; "
            "it does not publish a complete standard set. Membership and its "
            "citations are in PHASING_SET_DEG."
        ),
        "covered_ranges": {
            "shot_density_spf": SHOT_DENSITY_BAND_SPF,
            "shot_density_citation": SHOT_DENSITY_BAND_CITATION,
            "penetration_in": PENETRATION_BAND_IN,
            "penetration_citation": PENETRATION_BAND_CITATION,
            "entrance_hole_max_in": ENTRANCE_HOLE_MAX_IN,
            "note": (
                "1992 values. Modern HSD guns run 16-21 spf and charges exceed 40 in. "
                "of API section 1 penetration; the tool refuses outside the band "
                "rather than extrapolating a ranking the tables were not drawn for."
            ),
        },
    }

    return Quantity(
        value=float(len(violations)),
        unit="violations",
        method=METHOD,
        source=SOURCE,
        inputs=inputs,
        assumptions=assumptions,
        flags=tuple(flags),
    )
