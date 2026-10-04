"""Tool #91 — `nacl_equivalent` (group J, section 13 formation water).

Convert a multi-ion water analysis to equivalent NaCl ppm, which is what the
NaCl-only resistivity charts (and therefore `rw_from_tds` #92 and
`salinity_from_rw` #94) actually take on their salinity axis.

WHY THIS TOOL REFUSES ALMOST EVERYTHING
---------------------------------------
The source states the procedure but reads the per-ion multipliers off a chart:

    "From chart (Fig-3), enter the x-axis at 7000 ppm and read the multiplier
     value for each of the solids curves from the y-axis: k -> (cl) = 1 ,
     k -> (Mg) = 1.32"
    -- 11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties, p. 2|8

Fig-3 is not in the corpus. It is not even present as an image: the conversion
carries img-0..img-5 and none of them is Fig-1..Fig-4. No other document in the
corpus prints ion-to-NaCl multipliers. So the only multipliers with provenance
are the two printed in that one worked example, at one total-solids value
(7,000 ppm) -- and they are confirmed by division on the example's own table
(3168/2400 = 1.32, 4600/4600 = 1.00), which is arithmetic on published numbers
rather than chart reading.

A multiplier read at one salinity is a point on a curve, not the curve: Fig-3's
x-axis IS total solids. So this module interpolates nothing, extrapolates
nothing, and supplies nothing from memory. The Dunlap / Desai-Moore multiplier
families are widely known, and writing them in from training knowledge is
precisely the move this layer exists to make impossible: a number without
provenance is indistinguishable downstream from a right one.

MULTIPLIER_POINTS is therefore a table of (total_solids_ppm, k) POINTS per ion.
Digitizing Fig-3 later is a data-only change -- add rows, add an interpolation
rule with the digitizer's stated uncertainty -- with no edit to the procedure.

Spec: specs/91-nacl_equivalent.md
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

SOURCE = "11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties"
SOURCE_PAGE = f"{SOURCE} p. 2|7-2|8 ('Equivalent NaCl Salinity of Salts')"

# The one worked example in the source, used both as the multiplier provenance
# and as this tool's oracle.
_EXAMPLE = "worked example, MgCl2 water, p. 2|8 (total solids 7,000 ppm)"

#: Per-ion Fig-3 multiplier POINTS: ion -> ((total_solids_ppm, k, provenance), ...)
#:
#: Two entries only. Both are printed in the source's worked example prose
#: ("k -> (cl) = 1 , k -> (Mg) = 1.32") AND independently recoverable by dividing
#: that example's printed equivalent concentrations by its printed ionic
#: concentrations (Mg: 3168/2400 = 1.32; Cl: 4600/4600 = 1.00). The two routes
#: agree, which is the only cross-check available on the OCR of this section.
#:
#: Each is a POINT READ at total solids = 7,000 ppm, not a whole curve. Nothing
#: here licenses use at any other total-solids value -- see _refuse_off_curve.
MULTIPLIER_POINTS: dict[str, tuple[tuple[float, float, str], ...]] = {
    "Cl": ((7000.0, 1.00, _EXAMPLE),),
    "Mg": ((7000.0, 1.32, _EXAMPLE),),
}

#: Ions the source names as present in formation waters (line 250 salts list and
#: the unsolved exercise table on p. 2|9) but for which it prints NO multiplier.
#: Listed so a refusal can say "the source names this ion and gives no number"
#: rather than "unknown label".
IONS_NAMED_WITHOUT_MULTIPLIER: tuple[str, ...] = (
    "Na", "Ca", "K", "SO4", "CO3", "HCO3",
)

#: Float-representation tolerance ONLY. This is not a physical tolerance on the
#: total-solids match and must never be widened to become one: the source gives
#: one x-value per curve and no tolerance of any kind.
_TOTAL_SOLIDS_REL_EPS = 1e-9

#: The unit this tool emits. #92 / #94 consume `Quantity.value` as ppm NaCl.
UNIT = "ppm NaCl equivalent"

_METHOD = (
    "Equivalent NaCl = sum(k_i * C0_i), per-ion multiplier k read from Fig-3 at "
    "the sample's total solids concentration (Mosul lec-2, p. 2|8)"
)

# Charge-notation suffixes: "+2", "2+", "++", "-", "^2-", "(2+)" ... but NOT the
# bare digit in "SO4"/"CO3"/"HCO3", which carries no sign.
_CHARGE_SUFFIX = re.compile(r"[\s^]*(?:\([^)]*\)|[+-]{1,3}\d?|\d{1,2}[+-]{1,2})\s*$")

#: Canonical species labels, keyed by upper-cased formula with the charge stripped.
_CANONICAL: dict[str, str] = {
    "CL": "Cl", "MG": "Mg", "NA": "Na", "K": "K", "CA": "Ca",
    "SO4": "SO4", "CO3": "CO3", "HCO3": "HCO3", "NO3": "NO3",
    "FE": "Fe", "BA": "Ba", "SR": "Sr", "LI": "Li", "BR": "Br",
    "I": "I", "F": "F", "OH": "OH", "SIO2": "SiO2", "B": "B",
}


def normalize_ion(label: str) -> str:
    """`'Mg+2'`, `'Mg2+'`, `'mg++'`, `'MG'` -> `'Mg'`; `'SO4^2-'` -> `'SO4'`.

    An unrecognized formula is returned upper-cased and unchanged; the caller
    refuses on it (no printed multiplier) rather than raising, because an ion the
    source does not cover is a refusal, not a bad argument.
    """
    if not isinstance(label, str):
        raise ValueError(f"ion label must be a string, got {type(label).__name__}")
    base = _CHARGE_SUFFIX.sub("", label.strip())
    base = base.strip().replace(" ", "")
    if not base:
        raise ValueError(f"ion label {label!r} has no formula")
    if base.upper() not in _CANONICAL:
        # "HCO3-" / "NO3-": the trailing digit is stoichiometric, not the charge
        # magnitude, so the general "<digits><sign>" rule (which "Mg2+" needs)
        # eats it and yields "HCO" / "NO". Retry with a sign-only strip and keep
        # it only when it names a species the table knows.
        sign_only = re.sub(r"[\s^]*[+-]{1,3}\s*$", "", label.strip()).replace(" ", "")
        if sign_only.upper() in _CANONICAL:
            base = sign_only
    return _CANONICAL.get(base.upper(), base.upper())


def _multiplier_at(ion: str, total_solids_ppm: float) -> tuple[float, str] | None:
    """The digitized k for `ion` at exactly `total_solids_ppm`, or None.

    Exact match only. One point per curve supports no interpolation: picking
    between linear-in-ppm and linear-in-log(ppm) is a decision that must arrive
    WITH the digitized chart, not be guessed here.
    """
    for x, k, prov in MULTIPLIER_POINTS.get(ion, ()):
        if math.isclose(x, total_solids_ppm, rel_tol=_TOTAL_SOLIDS_REL_EPS, abs_tol=0.0):
            return k, prov
    return None


def _digitized_points_for(ion: str) -> str:
    pts = MULTIPLIER_POINTS.get(ion, ())
    if not pts:
        return f"{ion}: no digitized point"
    return f"{ion}: k={pts[0][1]:g} at total solids {pts[0][0]:,.0f} ppm" + (
        "" if len(pts) == 1 else f" (+{len(pts) - 1} more)"
    )


def nacl_equivalent(
    ions_ppm: Mapping[str, float],
    total_solids_ppm: float | None = None,
    concentration_unit: str = "ppm",
    analysis_is_complete: bool = True,
    require_charge_balance: bool = False,
) -> Quantity | Refusal:
    """Total equivalent NaCl concentration, in ppm, of a multi-ion water analysis.

    Procedure (`{SOURCE}`, p. 2|7-2|8):
      1. total solids S = sum of the ion concentrations,
      2. k_i = Fig-3(ion i, S)   <- the chart read this corpus cannot perform,
      3. Eq_i = k_i * C0_i,
      4. equivalent NaCl = sum(Eq_i).

    Steps 1, 3 and 4 are implemented exactly. Step 2 is a table lookup restricted
    to the two multipliers the source prints, at the one total-solids value it
    prints them for; everything else refuses.

    Returns `Quantity` (ppm NaCl equivalent) or `Refusal`.
    Raises `ValueError` for programmer error: empty analysis, negative or
    non-numeric concentration, negative total solids.
    """
    # ---- programmer errors -------------------------------------------------
    if not ions_ppm:
        raise ValueError("ions_ppm is empty: an analysis needs at least one ion")
    clean: dict[str, float] = {}
    for raw_label, raw_c in ions_ppm.items():
        ion = normalize_ion(raw_label)
        if isinstance(raw_c, bool) or not isinstance(raw_c, (int, float)):
            raise ValueError(f"concentration for {raw_label!r} is not a number: {raw_c!r}")
        c = float(raw_c)
        if math.isnan(c) or math.isinf(c):
            raise ValueError(f"concentration for {raw_label!r} is not finite: {c!r}")
        if c < 0.0:
            raise ValueError(f"concentration for {raw_label!r} is negative: {c}")
        clean[ion] = clean.get(ion, 0.0) + c
    if total_solids_ppm is not None:
        if isinstance(total_solids_ppm, bool) or not isinstance(total_solids_ppm, (int, float)):
            raise ValueError("total_solids_ppm must be a number or None")
        total_solids_ppm = float(total_solids_ppm)
        if total_solids_ppm < 0.0:
            raise ValueError(f"total_solids_ppm is negative: {total_solids_ppm}")

    # ---- R5: units ---------------------------------------------------------
    # The source is ppm-only ("Formation water salinity unit represented in part
    # per million of NaCl ppm NaCl", p. 2|4) and gives no density and no ppm<->mg/L
    # relation. mg/L and ppm diverge with brine density -- under 1% here, well
    # above 10% near saturation -- so a silent conversion would be an invented
    # number in the one place this layer refuses to have one.
    if concentration_unit != "ppm":
        return Refusal(
            reason=(
                f"concentrations were given in {concentration_unit!r}; the procedure and its "
                "chart family are stated in ppm only, and the source gives neither a brine "
                "density nor any ppm<->mg/L relation. mg/L and ppm differ by density and the "
                "difference is material at high salinity, so no conversion is applied."
            ),
            needed=(
                "concentrations in ppm",
                "or a source stating the ppm<->mg/L convention used by the Fig-2/Fig-3 chart family",
            ),
            source=SOURCE_PAGE,
        )

    # ---- R6: charge balance ------------------------------------------------
    # Deliberate. The source never mentions charge balance, milliequivalents, or
    # cation/anion sums; its own exercise table lists seven ions with no balance
    # commentary, and its worked example does not balance (2400 ppm Mg2+ ~ 197
    # meq/L vs 4600 ppm Cl- ~ 130 meq/L) yet is treated as unremarkable. So there
    # is no tolerance to apply and inventing one is forbidden. A caller who asks
    # for the check is told that, with the anchor.
    if require_charge_balance:
        return Refusal(
            reason=(
                "a charge-balance check was requested, but this source states no charge-balance "
                "or ion-balance criterion of any kind -- no milliequivalent sums, no tolerance, "
                "no analysis-quality test. Its own worked example does not balance (2400 ppm Mg2+ "
                "vs 4600 ppm Cl-) and is used regardless. This tool will not invent a tolerance."
            ),
            needed=(
                "a source stating a water-analysis charge-balance criterion and its tolerance",
            ),
            source=SOURCE_PAGE,
        )

    ion_sum = sum(clean.values())

    # ---- R4 / R7: what total solids enters the chart -----------------------
    if total_solids_ppm is None:
        if not analysis_is_complete:
            return Refusal(
                reason=(
                    "the ion list was declared partial, so its sum is not the total solids "
                    "concentration; step 1 of the procedure ('calculate the total solids "
                    "concentration') has no value to produce, and the Fig-3 x-axis entry is "
                    "therefore unknown."
                ),
                needed=("total_solids_ppm",),
                source=SOURCE_PAGE,
            )
        total_solids_ppm = ion_sum
        total_solids_basis = "sum of supplied ions"
    else:
        total_solids_basis = "caller-supplied"
        if analysis_is_complete and not math.isclose(
            total_solids_ppm, ion_sum, rel_tol=_TOTAL_SOLIDS_REL_EPS, abs_tol=0.0
        ):
            return Refusal(
                reason=(
                    f"total_solids_ppm = {total_solids_ppm:,.6g} does not equal the sum of the "
                    f"ion concentrations ({ion_sum:,.6g} ppm), a difference of "
                    f"{total_solids_ppm - ion_sum:,.6g} ppm, on an analysis declared complete. "
                    "The source forms total solids as exactly that sum (2400 + 4600 = 7000 ppm) "
                    "and states no tolerance for a mismatch, so none is assumed. Pass "
                    "analysis_is_complete=False if the ion list is deliberately partial."
                ),
                needed=(
                    "a total_solids_ppm equal to the sum of the ions supplied",
                    "or analysis_is_complete=False",
                ),
                source=SOURCE_PAGE,
            )

    # ---- R1 / R3: ions with no printed multiplier --------------------------
    # Zero-concentration ions are admitted: 0 * k = 0 for every k, so they are
    # determinate without a multiplier. That is arithmetic, not an assumption.
    flags: list[str] = []
    missing: list[str] = []
    zero_admitted: list[str] = []
    for ion, c in clean.items():
        if ion in MULTIPLIER_POINTS:
            continue
        if c == 0.0:
            zero_admitted.append(ion)
        else:
            missing.append(ion)
    if missing:
        missing.sort()
        named = [i for i in missing if i in IONS_NAMED_WITHOUT_MULTIPLIER]
        unknown = [i for i in missing if i not in IONS_NAMED_WITHOUT_MULTIPLIER]
        detail = []
        if named:
            detail.append(
                "the source names " + ", ".join(named) + " among formation-water salts but "
                "prints no multiplier for them"
            )
        if unknown:
            detail.append("no multiplier is printed for " + ", ".join(unknown))
        return Refusal(
            reason=(
                "no Fig-3 multiplier is available for: " + ", ".join(missing) + ". "
                + "; ".join(detail)
                + ". The only multipliers this source prints are k(Cl)=1.00 and k(Mg)=1.32, "
                "read off Fig-3 at total solids = 7,000 ppm in its one worked example. Fig-3 "
                "itself is not in the corpus (the document references Fig-1..Fig-4 and carries "
                "none of them as images), so the curves cannot be read and no value is supplied "
                "from outside the source."
            ),
            needed=tuple(
                f"Fig-3 multiplier curve for {ion}, digitized, evaluated at total solids "
                f"= {total_solids_ppm:,.6g} ppm"
                for ion in missing
            ),
            source=SOURCE_PAGE,
        )

    # ---- R2: off the one digitized point -----------------------------------
    multipliers: dict[str, dict[str, Any]] = {}
    off_curve: list[str] = []
    for ion in clean:
        if ion in zero_admitted:
            continue
        hit = _multiplier_at(ion, total_solids_ppm)
        if hit is None:
            off_curve.append(ion)
        else:
            k, prov = hit
            multipliers[ion] = {
                "k": k,
                "read_at_total_solids_ppm": total_solids_ppm,
                "provenance": f"{SOURCE_PAGE}, {prov}",
            }
    if off_curve:
        off_curve.sort()
        return Refusal(
            reason=(
                f"total solids = {total_solids_ppm:,.6g} ppm, but the multiplier for "
                + ", ".join(off_curve)
                + " is a single point read off Fig-3 at 7,000 ppm ("
                + "; ".join(_digitized_points_for(i) for i in off_curve)
                + "). The Fig-3 x-axis is total solids, so k varies along it; one point per "
                "curve supports neither interpolation nor extrapolation, and the source gives "
                "no functional form and no second point."
            ),
            needed=tuple(
                f"Fig-3 multiplier curve for {ion}, digitized, evaluated at total solids "
                f"= {total_solids_ppm:,.6g} ppm"
                for ion in off_curve
            ),
            source=SOURCE_PAGE,
        )

    # ---- steps 3 and 4 -----------------------------------------------------
    by_ion: dict[str, float] = {}
    for ion, c in clean.items():
        k = multipliers[ion]["k"] if ion in multipliers else 0.0
        by_ion[ion] = k * c  # zero-concentration ions contribute exactly 0.0
    equivalent_nacl_ppm = sum(by_ion.values())

    flags.append(
        "MULTIPLIERS ARE SINGLE-POINT READS: k(Cl)=1.00 and k(Mg)=1.32 come from one worked "
        "example at total solids = 7,000 ppm. They are points on the Fig-3 curves, not the "
        "curves; k varies with total solids and this result is valid at that total solids only."
    )
    if total_solids_basis == "sum of supplied ions":
        flags.append(
            f"total solids ({total_solids_ppm:,.6g} ppm) derived by summing the ions supplied, "
            "as the source's worked example does (2400 + 4600 = 7000 ppm)."
        )
    for ion in sorted(zero_admitted):
        flags.append(
            f"{ion} was reported at 0 ppm and admitted with no multiplier: 0 x k = 0 for every "
            "k, so its contribution is determinate. No multiplier was assumed for it."
        )
    flags.append(
        "charge balance NOT checked: this source states no ion-balance criterion "
        "(see specs/91-nacl_equivalent.md section 5)."
    )

    return Quantity(
        value=equivalent_nacl_ppm,
        unit=UNIT,
        method=_METHOD,
        source=SOURCE_PAGE,
        inputs={
            "ions_ppm": dict(sorted(clean.items())),
            "total_solids_ppm": total_solids_ppm,
            "equivalent_nacl_ppm_by_ion": dict(sorted(by_ion.items())),
        },
        assumptions={
            "multipliers": multipliers,
            "total_solids_basis": total_solids_basis,
            "concentration_unit": "ppm",
            "charge_balance_checked": False,
        },
        flags=tuple(flags),
    )
