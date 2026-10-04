"""Tool #100 — porosity_from_formation_factor (group J, §14 vintage electric logs).

Fragment for merge into `tools/petrophysics.py`. Nothing here duplicates what is
already in that module; `ASQUITH_T11`/`ASQUITH_FPHI` are new anchors and
`archie_sw` is untouched.

Why `a` and `m` have no defaults, when `archie_sw` in the same module lets them
default to 1.0/2.0: in Archie the pair sits under a 1/n root and moves Sw
modestly; here it *is* the answer. At F = 20 the three pairs Asquith marks "most
commonly used" give 0.1988, 0.2012 and 0.2236 — 2.5 porosity units apart on a 20%
rock. Asquith's reconnaissance advice (a = 1.0, m = n = 2.0, Table 1.1 preamble)
is explicitly offered for "an initial estimate of water saturation", not for
inverting F, so it is not wired in as a default here.

The other reason this tool is unusually strict: its output looks exactly like a
density porosity and is not one. It is an arithmetic consequence of a resistivity
ratio, and it is only valid where the interval is water-bearing. A
hydrocarbon-bearing interval reads high resistivity, hence high F, hence a
porosity that is too low — with nothing in the number to show it. Hence the
permanent flags and the water-bearing gate.
"""
from __future__ import annotations

from ..result import Quantity, Range, Refusal

# Asquith & Krygowski (2004) Table 1.1 + Eq. 1.6, book p. 4-5.
ASQUITH_T11 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#8"
# Ch. 5 INTERPRETATION, "Resistivity-derived Porosity", Eqs. 5.4-5.7.
# Catalog cites p. 90 (PDF); the corpus running heads put it on book pp. 82-83.
ASQUITH_FPHI = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#33"

# Asquith Table 1.1, "Different coefficients and exponents used to calculate
# formation factor (F)" (modified after Asquith, 1980), ASQUITH_T11, book p. 5.
# Every pair the table prints, with the lithology it belongs to. `common` marks
# the three rows carrying the table's footnote 1, "Most commonly used".
ARCHIE_AM_PAIRS: dict[str, dict] = {
    "carbonate": {
        "a": 1.0, "m": 2.0, "common": True,
        "comment": "Carbonates (Asquith Table 1.1, most commonly used)"},
    "consolidated_sandstone": {
        "a": 0.81, "m": 2.0, "common": True,
        "comment": "Consolidated sandstones (Asquith Table 1.1, most commonly used)"},
    "unconsolidated_sand": {
        "a": 0.62, "m": 2.15, "common": True,
        "comment": "Unconsolidated sands, Humble formula (Asquith Table 1.1, most commonly used)"},
    "average_sand": {
        "a": 1.45, "m": 1.54, "common": False,
        "comment": "Average sands (after Carothers, 1968)"},
    "shaly_sand": {
        "a": 1.65, "m": 1.33, "common": False,
        "comment": "Shaly sands (after Carothers, 1968)"},
    "calcareous_sand": {
        "a": 1.45, "m": 1.70, "common": False,
        "comment": "Calcareous sands (after Carothers, 1968)"},
    "carbonate_carothers": {
        "a": 0.85, "m": 2.14, "common": False,
        "comment": "Carbonates (after Carothers, 1968)"},
    "pliocene_sand_socal": {
        "a": 2.45, "m": 1.08, "common": False,
        "comment": "Pliocene sands, southern California (after Carothers and Porter, 1970)"},
    "miocene_sand_gulf_coast": {
        "a": 1.97, "m": 1.29, "common": False,
        "comment": "Miocene sands, Texas-Louisiana Gulf Coast (after Carothers and Porter, 1970)"},
}

# Table 1.1's tenth row, Sethi (1979) "Clean granular formations", prints its
# cementation exponent as phi^(2.05-phi). That is ambiguous between m = 2.05 - phi
# and the literal power, the corpus has no prose to settle it, and both readings
# make the inversion implicit in phi rather than closed-form. It is named here so
# a caller who asks for it gets a Refusal that says why, rather than silence.
SETHI_ROW_KEY = "clean_granular_sethi"
SETHI_ROW_NOTE = (
    "Sethi (1979), clean granular formations: Asquith Table 1.1 prints a = 1.0 with the "
    "cementation exponent as phi^(2.05-phi). The corpus does not resolve whether that means "
    "m = 2.05 - phi or the literal power, and either reading is implicit in phi, so F cannot "
    "be inverted in closed form."
)

# Not from the corpus. The corpus states no upper bound on porosity anywhere (see
# tool-catalog.md, "Thresholds the corpus does not supply"), so this drives a
# flag that says it is a house heuristic - never a refusal.
IMPLAUSIBLE_POROSITY = 0.5


def _published_pairs_text(common_only: bool = False) -> str:
    rows = [
        f"a={r['a']}, m={r['m']} ({name}: {r['comment']})"
        for name, r in ARCHIE_AM_PAIRS.items()
        if r["common"] or not common_only
    ]
    return "; ".join(rows)


def lithology_am_pair(lithology: str) -> dict[str, float]:
    """Look up an (a, m) pair from Asquith Table 1.1 by lithology name.

    Deliberately a separate call from the porosity tool rather than a `lithology=`
    argument on it. The caller has to choose the pair and pass it explicitly, so
    the choice is visible in the transcript and in the result's `inputs`, which
    is the whole point of refusing to default it.
    """
    key = lithology.strip().lower()
    if key == SETHI_ROW_KEY:
        raise ValueError(SETHI_ROW_NOTE)
    if key not in ARCHIE_AM_PAIRS:
        raise ValueError(
            f"unknown lithology {lithology!r}; Asquith Table 1.1 rows: "
            f"{sorted(ARCHIE_AM_PAIRS)}. This tool does not guess a and m."
        )
    row = ARCHIE_AM_PAIRS[key]
    return {"a": row["a"], "m": row["m"], "comment": row["comment"]}


def _f_value(f) -> float:
    """Accept F as a float or as a Quantity from formation_factor_field (#99)."""
    value = f.value if isinstance(f, (Quantity, Refusal)) else f
    if value is None:
        raise ValueError("F is None; formation_factor_field returned a Refusal, not a factor")
    value = float(value)
    if value <= 0:
        raise ValueError(
            f"formation factor must be positive, got {value}; F is a resistivity ratio"
        )
    return value


def _pair_carried_by_f(f) -> dict[str, float]:
    """Any a/m the upstream F already assumed, from its inputs or assumptions.

    Constants baked into F upstream are part of F's definition. Overriding them
    with a different pair here would break the round trip phi -> F, so they win
    and the disagreement is reported rather than resolved.
    """
    carried: dict[str, float] = {}
    if not isinstance(f, Quantity):
        return carried
    for bag in (f.inputs, f.assumptions):
        for key in ("a", "m"):
            if key not in carried and isinstance(bag.get(key), (int, float)):
                carried[key] = float(bag[key])
    return carried


def porosity_from_formation_factor(
    f,
    a: float | None = None,
    m: float | None = None,
    water_bearing: bool | None = None,
    lithology: str | None = None,
    f_source: str | None = None,
):
    """phi = (a/F)^(1/m).  Asquith Eq. 1.6 inverted, the step Eq. 5.6 performs.

    Porosity when the well has no porosity tool at all - a vintage ES suite with
    SP and resistivity and nothing else. The anchor derives Eq. 5.6 by setting
    S_xo = 1 in Eq. 5.4, "remembering that F = a/phi^m, and solving for porosity";
    with F = R_xo/R_mf that is term-for-term this function. F is taken as an
    argument so it can come from either published wet-zone route, R_o/R_w
    (Eq. 1.5) or R_xo/R_mf (Eq. 5.5).

    Refuses without a and m, and without a water-bearing certification. Refuses a
    porosity outside 0-1 rather than reporting one, because at that point the
    arithmetic is right and the inputs are wrong.
    """
    f_value = _f_value(f)
    if lithology is not None and lithology.strip().lower() == SETHI_ROW_KEY:
        return Refusal(reason=SETHI_ROW_NOTE,
                       needed=("an (a, m) pair with a numeric cementation exponent",),
                       source=ASQUITH_T11)

    carried = _pair_carried_by_f(f)
    # Which route produced F. #99's `formation_factor_from_porosity` stamps
    # route="porosity" and a circularity note; spec 99 ("What must travel with F
    # for #100") requires this tool to refuse or flag hard on that route,
    # because inverting a computed F returns the porosity it was built from.
    f_route = f.assumptions.get("route") if isinstance(f, Quantity) else None
    supplied = {"a": a, "m": m}
    conflicts = [
        f"{k}: caller {supplied[k]}, F carries {carried[k]}"
        for k in ("a", "m")
        if k in carried and supplied[k] is not None and supplied[k] != carried[k]
    ]
    a_used = carried.get("a", a)
    m_used = carried.get("m", m)

    if a_used is None or m_used is None:
        missing = [n for n, v in (("a", a_used), ("m", m_used)) if v is None]
        return Refusal(
            reason=(
                f"{' and '.join(missing)} not supplied; this tool does not pick the tortuosity "
                "factor or the cementation exponent. m is an exponent, so the choice moves "
                "porosity substantially and the operator must own it. Published pairs "
                f"(Asquith Table 1.1): {_published_pairs_text()}"
            ),
            needed=tuple(missing),
            source=ASQUITH_T11,
        )
    a_used, m_used = float(a_used), float(m_used)
    if a_used <= 0:
        raise ValueError(f"tortuosity factor a must be positive, got {a_used}")
    if m_used <= 0:
        raise ValueError(f"cementation exponent m must be positive, got {m_used}")

    if water_bearing is None:
        return Refusal(
            reason=(
                "the interval has not been certified water-bearing; F is a formation factor "
                "only where Sw = 1 (Asquith Eq. 5.5 sets S_xo = 1.0 to get here)"
            ),
            needed=("water_bearing=True, certified from the interval F was measured over",),
            source=ASQUITH_FPHI,
        )
    if water_bearing is False:
        return Refusal(
            reason=(
                "interval declared not water-bearing; residual hydrocarbons raise the shallow "
                "resistivity, so F is too high and the resistivity porosity comes out too low. "
                "Asquith's correction (Eq. 5.7) needs S_xo and works on R_mf/R_xo, not on F"
            ),
            needed=("a water-bearing interval", "or S_xo and R_mf/R_xo for Asquith Eq. 5.7"),
            source=ASQUITH_FPHI,
        )

    phi = (a_used / f_value) ** (1.0 / m_used)

    if not 0.0 < phi < 1.0:
        return Refusal(
            reason=(
                f"F = {f_value:g} with a = {a_used:g}, m = {m_used:g} implies porosity "
                f"{phi:.4f}, which is not physical. F below a always does this; on a vintage "
                "log it usually means Ro was read in a thin resistive bed without a departure "
                "correction, or Rw is too high. Returning the number would be worse than "
                "declining"
            ),
            needed=("a corrected F", "or the (a, m) pair for this rock"),
            source=ASQUITH_FPHI,
        )

    # What the other most-common Table 1.1 pairs would have given from this same
    # F. Computed rather than described, so the spread cannot drift from the value.
    alternatives = {
        name: (row["a"] / f_value) ** (1.0 / row["m"])
        for name, row in ARCHIE_AM_PAIRS.items() if row["common"]
    }
    lo, hi = min(alternatives.values()), max(alternatives.values())

    flags = [
        "resistivity-derived porosity: an arithmetic consequence of F, a and m, not a measurement",
        "valid only if the interval F came from is water-bearing; a hydrocarbon-bearing "
        "interval gives a high F, hence a porosity that is too low, with no outward sign",
        f"Asquith Table 1.1 most-common pairs span phi {lo:.4f}-{hi:.4f} "
        f"({(hi - lo) * 100:.1f} porosity units) at F = {f_value:g}",
    ]
    if not f_source:
        flags.append("F has no stated route (Ro/Rw or Rxo/Rmf); phi inherits assumptions "
                     "that were not declared")
    if f_route == "porosity":
        flags.append("circular: F was computed as a/phi^m from a porosity, not measured "
                     "from a resistivity ratio, so this inversion returns that same "
                     "porosity dressed as a measurement. Only Ro/Rw (Eq. 1.5) or "
                     "Rxo/Rmf (Eq. 5.5) make phi independent of its own input")
    if conflicts:
        flags.append("a/m conflict, F's own pair used: " + "; ".join(conflicts))
    if phi > IMPLAUSIBLE_POROSITY:
        flags.append(f"phi {phi:.3f} exceeds {IMPLAUSIBLE_POROSITY} - implausible for a "
                     "consolidated rock. House heuristic, not a corpus threshold; flagged, "
                     "not refused")

    return Quantity(
        value=phi, unit="v/v",
        method="porosity from formation factor, phi = (a/F)^(1/m) "
               "(Asquith Eq. 1.6 inverted; the step taken at Eq. 5.6)",
        source=ASQUITH_FPHI,
        inputs={"F": f_value, "a": a_used, "m": m_used},
        assumptions={
            "lithology": lithology,
            "F_source": f_source,
            "a_m_from": "F's own assumptions" if carried else "caller",
            "n": 2.0,  # anchor: "The saturation exponent (n) is assumed to be 2."
            "water_bearing": True,
            "alternative_pairs": alternatives,
            "constants_source": ASQUITH_T11,
        },
        flags=tuple(flags),
    )


def porosity_spread_from_formation_factor(
    f,
    water_bearing: bool | None = None,
    pairs: str = "most_common",
    f_source: str | None = None,
):
    """The honest band when no (a, m) has been chosen: phi under every Table 1.1 pair.

    The only path in this tool that answers without a stated a and m - and it
    answers with a Range explicitly labelled as a band, never a point. The point
    call stays a Quantity because the caller stated the pair and downstream tools
    need a scalar.
    """
    f_value = _f_value(f)
    if water_bearing is None:
        return Refusal(
            reason="the interval has not been certified water-bearing; F is a formation "
                   "factor only where Sw = 1",
            needed=("water_bearing=True",),
            source=ASQUITH_FPHI,
        )
    if water_bearing is False:
        return Refusal(
            reason="interval declared not water-bearing; F is too high and every porosity "
                   "in the band would be too low",
            needed=("a water-bearing interval",),
            source=ASQUITH_FPHI,
        )
    if pairs not in ("most_common", "all"):
        raise ValueError(f"pairs must be 'most_common' or 'all', got {pairs!r}")

    members = {
        name: (row["a"] / f_value) ** (1.0 / row["m"])
        for name, row in ARCHIE_AM_PAIRS.items()
        if pairs == "all" or row["common"]
    }
    physical = {k: v for k, v in members.items() if 0.0 < v < 1.0}
    if not physical:
        return Refusal(
            reason=f"F = {f_value:g} gives a porosity of 1.0 or more under every "
                   f"Asquith Table 1.1 pair ({pairs}); F or the constants are wrong",
            needed=("a corrected F",),
            source=ASQUITH_FPHI,
        )

    dropped = sorted(set(members) - set(physical))
    note = f"; {len(dropped)} pair(s) gave phi >= 1 and were excluded: {dropped}" if dropped else ""
    return Range(
        low=min(physical.values()), high=max(physical.values()), unit="v/v",
        method=f"porosity from formation factor across Asquith Table 1.1 pairs ({pairs}); "
               f"phi = (a/F)^(1/m){note}",
        source=ASQUITH_T11,
        members=physical,
    )
