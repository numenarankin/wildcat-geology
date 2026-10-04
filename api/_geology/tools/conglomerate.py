"""#109 `matrix_density_sensitivity` — group K, catalog §16.

Density porosity is not measured, it is chosen: the same RHOB curve reports a
different porosity depending on which matrix density and which pore-fluid
density somebody put into Eq. 4.7. This tool sweeps both and reports the band.

Two axes, not one. `asquith#18` names rho_ma and rho_fl as co-errors in the same
passage and works its saltwater example at 1.1 g/cm3, and
`aapg-density-neutron-log-porosity#0` says outright "use 1.0 for freshwater and
1.1 for saltwater mud". A sweep that varies the matrix and silently defaults the
fluid to 1.0 commits the second half of the error it was built to expose, so
both candidate lists are required inputs with no defaults.

The equation is not reimplemented here in any meaningful sense: every pair goes
through one helper, and any pair that the existing `density_porosity` can
express by name is also run through *it* and compared, so the two cannot drift.

MERGE NOTE for the coordinator: the `from .petrophysics import ...` line below
exists only because this ships as a standalone fragment. Merging into
`tools/petrophysics.py` drops it. The better end state is to give
`density_porosity` optional `rho_ma` / `rho_fl` overrides delegating to
`_phi_eq_4_7`, after which `_crosscheck_against_density_porosity` can go.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .result import Quantity, Range, Refusal  # noqa: F401  (Quantity: merge parity)
from .petrophysics import (
    DRHO_SUSPECT, FLUID, FLUID_AAPG, MATRIX, MATRIX_AAPG, density_porosity,
)

# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------
ASQUITH_RHO_MA_FL = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#18"
ASQUITH_TABLE_4_8 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#22"
AAPG_DENSITY = "01-curve-reading/aapg-density-neutron-log-porosity#0"

# --------------------------------------------------------------------------
# Constant tables — both published sets, side by side, never averaged
# --------------------------------------------------------------------------
# The catalog's RESOLVED reconcile note on `matrix_constant_lookup` makes
# Asquith Table 4.2 the source of truth and carries the AAPG page as a
# documented alternate. The disagreement is about one porosity unit on salt, so
# it is exactly the sort of thing this tool exists to put a number on: the
# caller names which candidates to sweep and the result records the choice.
#
# The AAPG table is read out of `petrophysics.MATRIX_AAPG`, not restated here.
#
# This module used to declare its own copy, justified by a comment saying the
# AAPG values "cannot live in MATRIX alongside Asquith's" because that table
# carries Dt_ma columns the AAPG page does not publish. #24 has since added
# `MATRIX_AAPG` as a separate table whose Dt_ma cells are None, so the
# justification is stale and the copy was pure drift risk - the same pattern
# that let a transcription error survive in Fig. 7-9, two copies each looking
# corroborated by the other. They agreed on every value when this was
# reconciled; sharing is what keeps it that way.
AAPG_RHO_MA: dict[str, float] = {
    lith: row["rho_ma"] for lith, row in MATRIX_AAPG.items()
}

# Candidate matrices, keyed for the caller. Asquith entries are read out of the
# existing MATRIX table rather than restated, so the numbers exist once.
MATRIX_DENSITY_CANDIDATES: dict[str, tuple[float, str]] = {
    **{k: (v["rho_ma"], f"Asquith Table 4.2 ({ASQUITH_RHO_MA_FL})") for k, v in MATRIX.items()},
    **{f"{k}_aapg": (v, f"AAPG wiki density table ({AAPG_DENSITY})") for k, v in AAPG_RHO_MA.items()},
}

# Candidate pore fluids. `fresh` and `salt_water` come from the existing FLUID
# table; the other two are new here and carry their own citation.
#
# The corpus disagrees with itself on saltwater, and the disagreement is real
# rather than a typo: Asquith Table 4.2 lists formation salt water at 1.15,
# while both Asquith's own worked example and the AAPG page use 1.1 for
# saltwater *mud filtrate* — which is what occupies the pore space within the
# density tool's shallow depth of investigation ("usually mud filtrate",
# aapg#0). Both are offered. The tool does not choose and does not average.
FLUID_DENSITY_CANDIDATES: dict[str, tuple[float, str]] = {
    "fresh": (
        FLUID["fresh"]["rho_fl"],
        f"Asquith Table 4.2 fresh water; AAPG 'use 1.0 for freshwater' ({AAPG_DENSITY})",
    ),
    "salt_mud_filtrate": (
        # Read from FLUID_AAPG rather than hardcoded, same reason as the
        # matrix table above.
        FLUID_AAPG["salt"]["rho_fl"],
        f"AAPG 'use 1.1 for saltwater mud' ({AAPG_DENSITY}); Asquith #18 worked example",
    ),
    "salt_water": (
        FLUID["salt"]["rho_fl"],
        f"Asquith Table 4.2 salt water ({ASQUITH_RHO_MA_FL})",
    ),
    "gas": (
        0.7,
        f"Hilchie (1978) via Asquith #18, where gas density is unknown ({ASQUITH_RHO_MA_FL})",
    ),
}

# Unit-slip guard, NOT a sourced threshold. Table 4.2 prints densities in both
# g/cm3 and kg/m3, so passing 2440 where 2.44 was meant is the realistic
# programmer error and it is caught here. The bounds bracket the corpus's own
# extremes (lowest fluid 0.7, highest listed solid 2.977) with room to spare.
RHO_B_PHYSICAL_G_CC = (1.0, 4.0)

_CROSSCHECK_TOL = 1e-12


@dataclass(frozen=True)
class _Candidate:
    label: str
    rho: float
    source: str
    table_key: str | None  # set only for a bare Asquith lithology in MATRIX


# --------------------------------------------------------------------------
# Eq. 4.7, evaluated once, guarded by the existing tool
# --------------------------------------------------------------------------
def _phi_eq_4_7(rho_b: float, rho_ma: float, rho_fl: float) -> float:
    """phi_D = (rho_ma - rho_b) / (rho_ma - rho_fl). Asquith Eq. 4.7, #18.

    Identical to the core of `density_porosity`; see the merge note in the
    module docstring. Callers must have already rejected rho_fl >= rho_ma.
    """
    return (rho_ma - rho_b) / (rho_ma - rho_fl)


def _crosscheck_against_density_porosity(
    rho_b: float, matrix: _Candidate, fluid: _Candidate, phi: float
) -> bool:
    """Re-run the pair through the shipped `density_porosity` where it can express it.

    Returns True if the check ran. Raises RuntimeError on disagreement, because
    two copies of Eq. 4.7 returning different numbers is a defect in this
    module, not a condition the operator can act on.
    """
    if matrix.table_key is None or matrix.table_key not in MATRIX:
        return False
    fluid_name = next(
        (name for name, row in FLUID.items() if row["rho_fl"] == fluid.rho), None
    )
    if fluid_name is None:
        return False
    reference = density_porosity(rho_b, lithology=matrix.table_key, fluid=fluid_name)
    if isinstance(reference, Refusal):  # only reachable via drho, gated earlier
        return False
    if abs(reference.value - phi) > _CROSSCHECK_TOL:
        raise RuntimeError(
            "matrix_density_sensitivity disagrees with density_porosity on "
            f"{matrix.label}/{fluid_name}: {phi!r} vs {reference.value!r}. "
            "One of the two implementations of Asquith Eq. 4.7 is wrong."
        )
    return True


def _resolve(candidate: object, table: dict[str, tuple[float, str]], axis: str) -> _Candidate:
    """Turn a candidate into a labelled density, or raise. Never defaults."""
    if isinstance(candidate, str):
        key = candidate.strip().lower()
        if key not in table:
            raise ValueError(
                f"unknown {axis} candidate {candidate!r}; known: {sorted(table)}. "
                f"For a measured value pass a (density_g_cc, source) pair instead."
            )
        rho, source = table[key]
        return _Candidate(
            label=key,
            rho=float(rho),
            source=source,
            table_key=key if (axis == "matrix" and key in MATRIX) else None,
        )
    if isinstance(candidate, tuple) and len(candidate) == 2:
        rho, source = candidate
        if isinstance(rho, bool) or not isinstance(rho, (int, float)):
            raise ValueError(f"{axis} candidate density must be a number, got {rho!r}")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                f"{axis} candidate {rho!r} arrived without a source. Matrix and fluid "
                "constants are recorded, never anonymous — pass (density_g_cc, source)."
            )
        if rho <= 0:
            raise ValueError(f"{axis} candidate density must be positive, got {rho!r}")
        return _Candidate(
            label=f"measured:{source.strip()}", rho=float(rho), source=source.strip(),
            table_key=None,
        )
    raise ValueError(
        f"{axis} candidate {candidate!r} is neither a table key nor a "
        "(density_g_cc, source) pair. A bare number is rejected: the constant "
        "has to carry its provenance."
    )


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
def matrix_density_sensitivity(
    rho_b: float,
    matrix_candidates: Sequence[object] | None = None,
    fluid_candidates: Sequence[object] | None = None,
    drho: float | None = None,
) -> Range | Refusal:
    """Sweep density porosity across candidate matrix AND fluid densities.

    Returns a `Range` whose `members` carry the porosity of every (rho_ma,
    rho_fl) pair, so a reviewer can see which combination produced each end. A
    point estimate would defeat the tool; `density_porosity` is the right call
    when the constants are known.

    Both candidate lists are required. Nothing here defaults a matrix density,
    and nothing defaults the fluid to 1.0 — per `asquith#18`, that assumption is
    itself half of the error being measured.

    Args:
        rho_b: bulk density from the log (RHOB), g/cm3.
        matrix_candidates: keys into `MATRIX_DENSITY_CANDIDATES` and/or
            `(rho_ma_g_cc, source)` pairs for measured grain densities.
        fluid_candidates: keys into `FLUID_DENSITY_CANDIDATES` and/or
            `(rho_fl_g_cc, source)` pairs.
        drho: the density-correction curve at this depth, g/cm3. Optional, but
            omitting it means the one sourced log-quality gate did not run and
            the result says so.
    """
    lo_b, hi_b = RHO_B_PHYSICAL_G_CC
    if isinstance(rho_b, bool) or not isinstance(rho_b, (int, float)):
        raise ValueError(f"rho_b must be a number in g/cm3, got {rho_b!r}")
    if not lo_b <= rho_b <= hi_b:
        raise ValueError(
            f"rho_b {rho_b!r} is outside {lo_b}-{hi_b} g/cm3 and is not a formation "
            "bulk density. Asquith Table 4.2 prints densities in g/cm3 and kg/m3 — "
            "check for a unit slip (2440 kg/m3 is 2.44 g/cm3)."
        )
    if drho is not None and (isinstance(drho, bool) or not isinstance(drho, (int, float))):
        raise ValueError(f"drho must be a number in g/cm3 or None, got {drho!r}")
    for name, arg in (("matrix_candidates", matrix_candidates), ("fluid_candidates", fluid_candidates)):
        if isinstance(arg, str):
            # Iterating it would silently sweep its letters.
            raise ValueError(f"{name} must be a sequence of candidates, not the string {arg!r}")

    if not matrix_candidates:
        return Refusal(
            reason=(
                "no candidate matrix densities supplied. This tool never defaults a "
                "matrix density — choosing one silently is the error it exists to "
                "measure (Asquith #18, 'Importance of Correct rho_ma and rho_fl')."
            ),
            needed=(
                "a list of candidate matrix densities: table keys such as "
                "'sandstone' / 'sandstone_aapg', or (rho_ma_g_cc, source) pairs",
            ),
            source=ASQUITH_RHO_MA_FL,
        )
    if not fluid_candidates:
        return Refusal(
            reason=(
                "no candidate fluid densities supplied. Asquith #18 names rho_fl a "
                "co-error with rho_ma, and both it and the AAPG page work saltwater "
                "at 1.1 g/cm3, so defaulting rho_fl to 1.0 would commit the very "
                "error this sweep is meant to expose."
            ),
            needed=(
                "a list of candidate fluid densities: table keys such as 'fresh' / "
                "'salt_mud_filtrate' / 'salt_water' / 'gas', or (rho_fl_g_cc, source) pairs",
            ),
            source=ASQUITH_RHO_MA_FL,
        )

    if drho is not None and drho > DRHO_SUSPECT:
        return Refusal(
            reason=(
                f"DRHO {drho:.2f} g/cm3 exceeds {DRHO_SUSPECT}; Asquith #18 calls the "
                "bulk density suspect and possibly invalid above that. A porosity band "
                "swept across matrix values on a suspect RHOB is a band around a bad "
                "number, and it looks like diligence."
            ),
            needed=("a bulk density from an interval where DRHO is within tolerance",),
            source=ASQUITH_RHO_MA_FL,
        )

    matrices = [_resolve(c, MATRIX_DENSITY_CANDIDATES, "matrix") for c in matrix_candidates]
    fluids = [_resolve(c, FLUID_DENSITY_CANDIDATES, "fluid") for c in fluid_candidates]

    if len(matrices) == 1 and len(fluids) == 1:
        return Refusal(
            reason=(
                f"one matrix ({matrices[0].label}) and one fluid ({fluids[0].label}) is "
                "a point estimate, not a sensitivity: low and high would be equal and "
                "the result would read as 'the constants do not matter', which is the "
                "opposite of what Asquith #18 says. Call density_porosity for a stated "
                "pair, or add a candidate to either axis."
            ),
            needed=("a second candidate on the matrix axis, the fluid axis, or both",),
            source=ASQUITH_RHO_MA_FL,
        )

    for m in matrices:
        for f in fluids:
            if f.rho >= m.rho:
                return Refusal(
                    reason=(
                        f"fluid density {f.rho:g} g/cm3 ({f.label}) is not below matrix "
                        f"density {m.rho:g} g/cm3 ({m.label}); the denominator of "
                        "Asquith Eq. 4.7 collapses or inverts. Refusing the whole sweep "
                        "rather than dropping the pair — a band computed from a "
                        "silently reduced candidate set is worse than no band."
                    ),
                    needed=("a candidate set where every rho_fl is below its rho_ma",),
                    source=ASQUITH_RHO_MA_FL,
                )

    members: dict[str, float] = {}
    lowest = highest = None
    low_label = high_label = ""
    crosschecked = 0
    for m in matrices:
        for f in fluids:
            phi = _phi_eq_4_7(rho_b, m.rho, f.rho)
            if _crosscheck_against_density_porosity(rho_b, m, f, phi):
                crosschecked += 1
            label = f"{m.label}({m.rho:.3f}) / {f.label}({f.rho:.3f})"
            members[f"phi: {label}"] = phi
            if lowest is None or phi < lowest:
                lowest, low_label = phi, label
            if highest is None or phi > highest:
                highest, high_label = phi, label

    members["input: rho_b (g/cm3)"] = float(rho_b)
    if drho is not None:
        members["input: drho (g/cm3)"] = float(drho)

    flags: list[str] = []
    if len(matrices) == 1:
        flags.append(
            "SINGLE-AXIS: rho_ma not varied; Asquith #18 names rho_ma and rho_fl "
            "co-errors and calls rho_ma the larger of the two"
        )
    if len(fluids) == 1:
        flags.append(
            "SINGLE-AXIS: rho_fl not varied; Asquith #18 names it a co-error and "
            "works its saltwater example at 1.1, not 1.0"
        )
    if drho is None:
        flags.append(
            f"DRHO NOT SUPPLIED: the sourced quality gate (DRHO > {DRHO_SUSPECT} g/cm3 "
            "means RHOB is suspect, Asquith #18) was not applied"
        )
    elif drho <= -DRHO_SUSPECT:
        flags.append(
            f"DRHO {drho:.2f} g/cm3 is a large negative correction; the source states "
            f"the gate only on exceeding +{DRHO_SUSPECT}, so this is a flag, not a "
            "refusal — no symmetric threshold is invented here"
        )
    if lowest is not None and lowest < 0:
        flags.append(
            "NEGATIVE POROSITY in the band: Asquith #18 ('Heavy Minerals') reads this "
            "as anhydrite or another heavy mineral, or a matrix denser than assumed, "
            "not as a low-porosity reservoir. Values are not clipped"
        )
    if any(m.label.endswith("_aapg") for m in matrices):
        flags.append(f"AAPG alternate matrix values used alongside Asquith ({AAPG_DENSITY})")

    # Range carries no flags/inputs field, so `method` and the `members` keys are
    # the only place this can go. Recorded as an open question in the spec.
    method = (
        f"matrix/fluid density sensitivity, Asquith Eq. 4.7 swept over "
        f"{len(matrices)}x{len(fluids)}={len(matrices) * len(fluids)} pairs "
        f"({crosschecked} cross-checked against density_porosity); "
        f"low={low_label}; high={high_label}"
    )
    if flags:
        method += " | " + " | ".join(flags)

    return Range(
        low=lowest,
        high=highest,
        unit="v/v",
        method=method,
        source=ASQUITH_RHO_MA_FL,
        members=members,
    )
