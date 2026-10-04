"""Group C, tools #24 / #26 / #29 — staged replacement for the matching parts of
`tools/petrophysics.py`.

MERGE NOTE. This file is the complete revised text of everything group C owns in
that module. It replaces, wholesale:

  * the constant tables `MATRIX`, `FLUID` and `DRHO_SUSPECT`
  * the anchors `ASQUITH_T41`, `ASQUITH_T42`, `ASQUITH_SONIC`
  * `matrix_constant_lookup`   (#24)
  * `density_porosity`         (#26)
  * `sonic_porosity`           (#29)

and adds `MatrixConstants`, `MATRIX_AAPG`, `FLUID_AAPG`, `MATRIX_TABLES`,
`AAPG_DN`, `HILCHIE_GAS_DENSITY`, `HYDROCARBON_FACTORS` and `GATE_BASIS`.

It does **not** touch `ASQUITH_VSH` / `ASQUITH_SW` / `ASQUITH_TEMP`,
`gamma_ray_index`, `vshale`, `archie_sw`, `formation_temperature` or
`resistivity_at_temperature` — those are group D's and stay as they are.
Downstream importers keep working: `tools/quality.py` imports `DRHO_SUSPECT`,
`tools/state_checks.py` imports `ASQUITH_T42`, both unchanged.

--- the three decisions worth explaining -------------------------------------

**#24 no longer returns a bare dict.** It was the one place in this module where
numbers escaped without provenance. It now returns `MatrixConstants`, a frozen
record whose every numeric field is itself a `Quantity`, `Range` or `Refusal`,
and which names the table that answered. Consumers read `.rho_ma.value` and
`.dt_ma_point()`; see `specs/24-matrix_constant_lookup.md`.

**Two constants in the shipped table were not in the source.** Asquith Table 4.1
prints sandstone Wyllie Δt_ma as the *range* "55.5 to 51.0", and leaves the RHG
column *blank* for anhydrite and salt. The shipped table stored a point 55.5 and
carried the Wyllie values across into the RHG column for the two evaporites —
a fabricated constant with a real citation on it. The range is now a `Range`,
collapsed to its published-first endpoint (55.5) only at the point of use, with
a flag; the blank cells are now a `Refusal`.

**The porosity gates are not all equal.** DRHO > 0.20 g/cm³ is SOURCED
(`asquith#18`); the caliper and rugosity cutoffs are PROVISIONAL house rules
(`tool-catalog.md:88`, :112). `density_porosity` therefore names the gate and its
status in the refusal, because one is defensible in front of an operator and the
other is ours. An unreadable hole-quality verdict fails closed.
"""
from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .result import Quantity, Range, Refusal
# Asquith Table 1.1's nine (a, m) pairs, held once, by #100. See
# FORMATION_FACTOR_SETS below for why this is an import and not a second copy.
from .vintage_logs.porosity_from_f import ARCHIE_AM_PAIRS as _ARCHIE_AM_PAIRS

# --- corpus anchors -----------------------------------------------------------

ASQUITH_T41 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#17"
ASQUITH_T42 = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#18"
ASQUITH_SONIC = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#16"
AAPG_DN = "01-curve-reading/aapg-density-neutron-log-porosity#0"

# --- the matrix tables --------------------------------------------------------
#
# Asquith Table 4.2 (rho_ma and Pe, p. 40, asquith#18) merged with Table 4.1
# (Dt_ma, p. 39, asquith#17). Dt_ma is keyed by *equation variant* because
# Table 4.1 prints a separate Raymer-Hunt-Gardner column, which the AAPG page
# does not do at all — that pairing is one of the two reasons the catalog makes
# Asquith the source of truth (tool-catalog.md:274, "Reconcile - RESOLVED").
#
# Two cells are not scalars, and both are faithful to what Table 4.1 prints:
#   * sandstone Wyllie is the tuple (55.5, 51.0), the published range, in
#     published order. It is the reciprocal pair of the printed velocity range
#     18,000-19,500 ft/sec (1e6/18000 = 55.56, 1e6/19500 = 51.28).
#   * anhydrite and salt have no RHG entry. The cell is blank in the table, so
#     it is None here, and #24 refuses rather than substituting the Wyllie value.

MATRIX: dict[str, dict[str, Any]] = {
    "sandstone": {"rho_ma": 2.644, "pe": 1.81, "dt_ma_wyllie": (55.5, 51.0), "dt_ma_rhg": 56.0},
    "limestone": {"rho_ma": 2.710, "pe": 5.08, "dt_ma_wyllie": 47.6, "dt_ma_rhg": 49.0},
    "dolomite": {"rho_ma": 2.877, "pe": 3.14, "dt_ma_wyllie": 43.5, "dt_ma_rhg": 44.0},
    "anhydrite": {"rho_ma": 2.960, "pe": 5.05, "dt_ma_wyllie": 50.0, "dt_ma_rhg": None},
    "salt": {"rho_ma": 2.040, "pe": 4.65, "dt_ma_wyllie": 66.7, "dt_ma_rhg": None},
}

# The documented alternate: `aapg-density-neutron-log-porosity#0`, Hartmann &
# Beaumont, AAPG Treatise. Carried so a caller can ask for it and see which table
# answered; NEVER averaged with Asquith (tool-catalog.md:274). The page publishes
# no travel times at all, so every Dt_ma from this table is a Refusal.
MATRIX_AAPG: dict[str, dict[str, Any]] = {
    "sandstone": {"rho_ma": 2.65, "pe": 1.8, "dt_ma_wyllie": None, "dt_ma_rhg": None},
    "limestone": {"rho_ma": 2.71, "pe": 4.8, "dt_ma_wyllie": None, "dt_ma_rhg": None},
    "dolomite": {"rho_ma": 2.876, "pe": 3.0, "dt_ma_wyllie": None, "dt_ma_rhg": None},
    "anhydrite": {"rho_ma": 2.977, "pe": 5.05, "dt_ma_wyllie": None, "dt_ma_rhg": None},
    "salt": {"rho_ma": 2.032, "pe": 4.6, "dt_ma_wyllie": None, "dt_ma_rhg": None},
}

MATRIX_TABLES: dict[str, dict[str, dict[str, Any]]] = {
    "asquith": MATRIX,
    "aapg": MATRIX_AAPG,
}
TABLE_SOURCES: dict[str, str] = {"asquith": ASQUITH_T42, "aapg": AAPG_DN}
TABLE_LABELS: dict[str, str] = {
    "asquith": "Asquith Table 4.2 / 4.1",
    "aapg": "AAPG density-neutron page (documented alternate)",
}

# Fluid column of Asquith Table 4.2 (rho_fl) and Table 4.1 (Dt_fl).
FLUID: dict[str, dict[str, float]] = {
    "fresh": {"rho_fl": 1.0, "dt_fl": 189.0},
    "salt": {"rho_fl": 1.15, "dt_fl": 185.0},
}
# The AAPG page says "use 1.0 for freshwater and 1.1 for saltwater mud" — a third
# disagreement, kept table-scoped so an AAPG matrix is never paired with an
# Asquith fluid. It publishes no travel times, hence no dt_fl.
FLUID_AAPG: dict[str, dict[str, float]] = {
    "fresh": {"rho_fl": 1.0},
    "salt": {"rho_fl": 1.1},
}
FLUID_TABLES: dict[str, dict[str, dict[str, float]]] = {
    "asquith": FLUID,
    "aapg": FLUID_AAPG,
}

# What each rho_fl actually IS, per table, in the source's own words. The two
# saltwater numbers are not the same quantity: Table 4.2's row is labelled "Salt
# water" (formation brine, 1.15), while Asquith's own prose on the same page
# works a "saltwater-filled formation" at 1.1 and the AAPG page says outright
# "use 1.0 for freshwater and 1.1 for saltwater mud" — mud *filtrate*, which is
# what occupies the pore space within the density tool's shallow depth of
# investigation. Calling 1.15 a filtrate value attributes to Table 4.2 a row it
# does not have, so the basis string names the row that supplied the number and
# the disagreement it sits inside.
FLUID_BASIS: dict[str, dict[str, str]] = {
    "asquith": {
        "fresh": "Asquith Table 4.2 'Fresh water' 1.0 g/cm3 (asquith#18)",
        "salt": ("Asquith Table 4.2 'Salt water' 1.15 g/cm3, formation brine (asquith#18); "
                 "Asquith's own prose on the same page and the AAPG page use 1.1 g/cm3 for "
                 "saltwater mud filtrate, which is what the shallow-reading density tool sees. "
                 "Pass table='aapg' for that value; the two are never averaged"),
    },
    "aapg": {
        "fresh": "AAPG 'use 1.0 for freshwater' (aapg-density-neutron-log-porosity#0)",
        "salt": ("AAPG 'use 1.1 for saltwater mud', i.e. mud filtrate "
                 "(aapg-density-neutron-log-porosity#0); Asquith Table 4.2 lists formation "
                 "salt water at 1.15 instead"),
    },
}

# Asquith #18: "Whenever the correction curve (DRHO) exceeds 0.20 g/cm3, the
# value of the bulk density ... should be considered suspect and possibly
# invalid." The only quantitative log-quality threshold in the corpus, and the
# only SOURCED one of the three porosity gates. Imported by tools/quality.py and
# tools/state_checks.py — one constant, one home.
DRHO_SUSPECT = 0.20

# Asquith #18, "Hydrocarbon Effects": Hilchie (1978) suggests a gas density of
# 0.7 g/cm3 for rho_fl where gas density is unknown. Note the source states no
# oil equivalent for the density log — "oil does not significantly affect
# density porosity" — which is why #26 has a gas switch and no oil switch.
HILCHIE_GAS_DENSITY = 0.7

# Asquith #17, Eqs. 4.5/4.6: Hilchie (1978) hydrocarbon corrections to *sonic*
# porosity. Both are published here, unlike the density case.
HYDROCARBON_FACTORS: dict[str, tuple[float, str]] = {
    "gas": (0.7, "Eq. 4.5"),
    "oil": (0.9, "Eq. 4.6"),
}

# Asquith #17, Eq. 4.4: "C = a constant which is normally 1.0 (Hilchie, 1978)".
# "Normally", not "definitionally" — so it is a documented default, not a
# hard-coded constant, and #29 takes it as an argument.
COMPACTION_C_DEFAULT = 1.0

# The three gates that govern whether a bulk density is usable, and the status of
# each (tool-catalog.md:88 and :112). A refusal must name which one fired: one is
# defensible in front of an operator and the others are house rules.
GATE_BASIS: dict[str, str] = {
    "drho": f"SOURCED (asquith#18: DRHO > {DRHO_SUSPECT} g/cm3)",
    "caliper": "PROVISIONAL house rule (tool-catalog.md:88: DiffCal = caliper - bit > +1.0 in)",
    "rugosity": "PROVISIONAL house rule (tool-catalog.md:88: |d(CAL)/dz| > 0.5 in/ft over 2 ft)",
    "unnamed": ("gate not named by hole_quality (#25); tool-catalog.md:112 requires it, "
                "because a sourced gate and a house rule are not the same refusal"),
}

# The reconcile is a number, so it is carried as one. Divergence between the two
# tables is quoted at the catalog's own reference point.
DIVERGENCE_RHO_B = 2.40
DIVERGENCE_RHO_FL = 1.0


def _divergence_pu(key: str) -> float:
    """|phi_asquith - phi_aapg| in porosity units at rho_b=2.40, rho_fl=1.0.

    Reproduces tool-catalog.md:274 exactly: sandstone 0.31, anhydrite 0.61,
    salt 1.04 — small for sandstone, not negligible for evaporites.
    """
    a = MATRIX[key]["rho_ma"]
    b = MATRIX_AAPG[key]["rho_ma"]
    phi_a = (a - DIVERGENCE_RHO_B) / (a - DIVERGENCE_RHO_FL)
    phi_b = (b - DIVERGENCE_RHO_B) / (b - DIVERGENCE_RHO_FL)
    return abs(phi_a - phi_b) * 100.0


# --- #24 matrix_constant_lookup ----------------------------------------------

@dataclass(frozen=True)
class MatrixConstants:
    """What #24 returns. Not a number: a record of which table answered.

    Every numeric field is a `Quantity`, `Range` or `Refusal`, so nothing escapes
    without provenance. `dt_ma` is a `Range` for sandstone under Wyllie (the
    table prints "55.5 to 51.0"), and a `Refusal` where the table has no cell.
    """

    lithology: str
    table: str
    variant: str
    source: str
    rho_ma: Quantity
    dt_ma: Quantity | Range | Refusal
    pe: Quantity | None
    alternate_rho_ma: Quantity
    divergence_pu: Quantity

    def __getitem__(self, key: str) -> Any:
        """Mapping access, kept because #24 used to return a bare dict.

        Callers written against the old contract read `consts["rho_ma"]` and
        `consts["dt_ma"]` and expect **floats**, so that is what this returns —
        `tools/formation_water/hingle.py` is one such caller. New code should use
        the attributes, which carry the provenance the dict could not. A `dt_ma`
        that is a published range yields its published-first endpoint here, the
        same value `dt_ma_point()` gives, and one that is a `Refusal` raises
        rather than handing back a number the table does not contain.
        """
        if key == "rho_ma":
            return self.rho_ma.value
        if key == "dt_ma":
            point = self.dt_ma_point()
            if isinstance(point, Refusal):
                raise KeyError(
                    f"dt_ma is not available for {self.lithology!r} under "
                    f"{self.variant!r}: {point.reason}")
            return point.value
        if key == "pe":
            return None if self.pe is None else self.pe.value
        raise KeyError(key)

    def dt_ma_point(self) -> Quantity | Refusal:
        """A scalar Dt_ma, or the refusal that stopped one existing.

        A published range is collapsed to its **published-first** endpoint and
        flagged. It is never averaged: a midpoint appears in no source, and
        averaging published values is the exact failure the catalog's reconcile
        note forbids. See specs/24-matrix_constant_lookup.md, "The sandstone
        range", for why the first endpoint and not the second.
        """
        if isinstance(self.dt_ma, Refusal):
            return self.dt_ma
        if isinstance(self.dt_ma, Quantity):
            return self.dt_ma
        rng: Range = self.dt_ma
        point = rng.members["published_first"]
        return Quantity(
            value=point, unit="usec/ft",
            method=f"matrix interval transit time, {rng.method}",
            source=rng.source,
            inputs={"lithology": self.lithology},
            assumptions={"table": self.table, "variant": self.variant,
                         "dt_ma_range": (rng.low, rng.high),
                         "endpoint": "published-first"},
            flags=(f"dt_ma collapsed from the published range {rng.low}-{rng.high} usec/ft "
                   f"to {point} (published-first endpoint, the conservative end); "
                   "pass dt_ma explicitly to choose another",),
        )

    def rho_fl(self, fluid: str) -> Quantity:
        """Fluid density from the *same* table, so tables are never mixed."""
        key = _fluid_key(fluid, self.table)
        value = FLUID_TABLES[self.table][key]["rho_fl"]
        return Quantity(
            value=value, unit="g/cm3",
            method=f"fluid density, {TABLE_LABELS[self.table]}",
            source=TABLE_SOURCES[self.table],
            inputs={"fluid": key}, assumptions={"table": self.table},
        )

    def dt_fl(self, fluid: str) -> Quantity | Refusal:
        """Fluid interval transit time. Table 4.1 only; the AAPG page has none."""
        if self.table != "asquith":
            return Refusal(
                reason=(f"the {TABLE_LABELS[self.table]} publishes no interval transit times, "
                        "so no fluid travel time is available from it"),
                needed=("table='asquith' for Table 4.1", "or an explicit dt_fl"),
                source=AAPG_DN,
            )
        key = _fluid_key(fluid, self.table)
        return Quantity(
            value=FLUID[key]["dt_fl"], unit="usec/ft",
            method="fluid interval transit time, Asquith Table 4.1",
            source=ASQUITH_T41, inputs={"fluid": key},
        )


def _lithology_key(lithology: str) -> str:
    key = str(lithology).strip().lower()
    if key not in MATRIX:
        raise ValueError(
            f"unknown lithology {lithology!r}; known: {sorted(MATRIX)}. "
            "This tool does not guess a matrix."
        )
    return key


def _table_key(table: str) -> str:
    key = str(table).strip().lower()
    if key not in MATRIX_TABLES:
        raise ValueError(
            f"unknown matrix table {table!r}; known: {sorted(MATRIX_TABLES)}. "
            "'asquith' is the source of truth (tool-catalog.md:274); 'aapg' is the "
            "documented alternate. This tool does not average them."
        )
    return key


def _variant_key(variant: str) -> str:
    key = str(variant).strip().lower()
    if key not in ("wyllie", "rhg"):
        raise ValueError(
            f"unknown equation variant {variant!r}; known: ['rhg', 'wyllie']. "
            "Table 4.1 prints a separate matrix travel time per variant."
        )
    return key


def _fluid_key(fluid: str, table: str = "asquith") -> str:
    key = str(fluid).strip().lower()
    if key not in FLUID_TABLES[table]:
        raise ValueError(
            f"unknown fluid {fluid!r} for table {table!r}; "
            f"known: {sorted(FLUID_TABLES[table])}"
        )
    return key


def matrix_constant_lookup(lithology: str, variant: str = "wyllie",
                           table: str = "asquith") -> MatrixConstants:
    """Matrix constants for a stated lithology. Never defaults a lithology.

    Asquith Table 4.2 (rho_ma, Pe) and Table 4.1 (Dt_ma, with its own RHG
    column) are the source of truth; `table="aapg"` returns the documented
    alternate and says so on the result, so a caller can always tell which table
    answered. An unknown lithology raises rather than refusing: guessing a matrix
    is programmer error, and every porosity in this layer rests on it.
    """
    key = _lithology_key(lithology)
    tkey = _table_key(table)
    vkey = _variant_key(variant)
    row = MATRIX_TABLES[tkey][key]
    label = TABLE_LABELS[tkey]
    src = TABLE_SOURCES[tkey]
    other = "aapg" if tkey == "asquith" else "asquith"

    rho_ma = Quantity(
        value=row["rho_ma"], unit="g/cm3",
        method=f"matrix density, {label}", source=src,
        inputs={"lithology": key}, assumptions={"table": tkey},
        flags=() if tkey == "asquith" else
        ("documented alternate table; Asquith Table 4.2 is the source of truth "
         "(tool-catalog.md:274)",),
    )

    dt_ma: Quantity | Range | Refusal
    raw = row[f"dt_ma_{vkey}"]
    if tkey != "asquith":
        dt_ma = Refusal(
            reason=(f"the {label} publishes matrix densities only; it carries no matrix "
                    "interval transit times, for either equation variant"),
            needed=("matrix_constant_lookup(..., table='asquith') for Table 4.1",
                    "or an explicit dt_ma"),
            source=AAPG_DN,
        )
    elif raw is None:
        dt_ma = Refusal(
            reason=(f"Asquith Table 4.1 leaves the Raymer-Hunt-Gardner matrix travel-time "
                    f"cell blank for {key}; no RHG Dt_ma is published for it"),
            needed=(f"a published RHG matrix travel time for {key}",
                    "or variant='wyllie' (Table 4.1 does print a Wyllie value)",
                    "or an explicit dt_ma"),
            source=ASQUITH_T41,
        )
    elif isinstance(raw, tuple):
        first, second = raw
        dt_ma = Range(
            low=min(first, second), high=max(first, second), unit="usec/ft",
            method=f"matrix interval transit time ({vkey.upper()} column), Asquith Table 4.1",
            source=ASQUITH_T41,
            members={"published_first": float(first), "published_second": float(second)},
        )
    else:
        dt_ma = Quantity(
            value=float(raw), unit="usec/ft",
            method=f"matrix interval transit time ({vkey.upper()} column), Asquith Table 4.1",
            source=ASQUITH_T41,
            inputs={"lithology": key}, assumptions={"variant": vkey, "table": tkey},
        )

    pe_raw = row.get("pe")
    pe = None if pe_raw is None else Quantity(
        value=pe_raw, unit="b/e", method=f"photoelectric effect, {label}", source=src,
        inputs={"lithology": key}, assumptions={"table": tkey},
    )

    alt_row = MATRIX_TABLES[other][key]
    alternate = Quantity(
        value=alt_row["rho_ma"], unit="g/cm3",
        method=f"matrix density, {TABLE_LABELS[other]} (the alternate table)",
        source=TABLE_SOURCES[other],
        inputs={"lithology": key}, assumptions={"table": other},
        flags=("carried for comparison; the two tables are never averaged "
               "(tool-catalog.md:274)",),
    )
    divergence = Quantity(
        value=_divergence_pu(key), unit="pu",
        method=(f"|phi_asquith - phi_aapg| at rho_b={DIVERGENCE_RHO_B}, "
                f"rho_fl={DIVERGENCE_RHO_FL} (Eq. 4.7)"),
        source=f"{ASQUITH_T42} vs {AAPG_DN}",
        inputs={"rho_ma_asquith": MATRIX[key]["rho_ma"],
                "rho_ma_aapg": MATRIX_AAPG[key]["rho_ma"],
                "rho_b": DIVERGENCE_RHO_B, "rho_fl": DIVERGENCE_RHO_FL},
        assumptions={"reconcile": "tool-catalog.md:274 - Asquith wins, AAPG is the alternate"},
    )

    return MatrixConstants(
        lithology=key, table=tkey, variant=vkey, source=src,
        rho_ma=rho_ma, dt_ma=dt_ma, pe=pe,
        alternate_rho_ma=alternate, divergence_pu=divergence,
    )


# --- the hole-quality verdict reader (#25's output, consumed by #26) ----------
#
# #25 is being written concurrently and its spec had not landed when this was
# written, so the reader is deliberately permissive about shape and strict about
# meaning. It accepts a mapping, an object with the same attributes, a list of
# depth intervals (selected by depth_md), a Quantity, or a Refusal. What it will
# NOT do is treat an unrecognisable verdict as good hole: unreadable fails
# closed, because the failure mode this layer exists to prevent is a porosity
# quietly reported from a washed-out interval.

_HQ_KEYS = ("flag", "status", "quality", "verdict", "washout", "bad_hole", "rugose",
            "gate", "basis", "drho", "diffcal", "diff_cal", "caliper_in", "bit_size_in",
            "top_md", "base_md", "depth_md")
_HQ_BAD_TOKENS = ("washout", "wash-out", "bad", "rugose", "rugosity", "enlarge",
                  "suspect", "undergauge", "under-gauge", "caving", "cave", "invalid")
_HQ_GOOD_TOKENS = ("in-gauge", "in gauge", "ingauge", "good", "ok", "pass", "nominal",
                   "clean", "valid")


def _hq_as_dict(entry: Any) -> dict[str, Any] | None:
    if isinstance(entry, Mapping):
        return {str(k): v for k, v in entry.items()}
    if isinstance(entry, Quantity):
        out: dict[str, Any] = {}
        out.update({str(k): v for k, v in entry.inputs.items()})
        out.update({str(k): v for k, v in entry.assumptions.items()})
        if entry.flags:
            out.setdefault("flag", "; ".join(entry.flags))
        return out or None
    if hasattr(entry, "__dict__") or hasattr(entry, "__slots__"):
        out = {k: getattr(entry, k) for k in _HQ_KEYS if hasattr(entry, k)}
        # #25 (tools/borehole.py) reports *which* gate fired, per sample, on
        # `.hits`: (gate, status, bad, observed, cutoff, source, detail). That is
        # the only place the SOURCED/PROVISIONAL distinction the catalog demands
        # (tool-catalog.md:112) actually exists, so read it rather than guessing
        # a gate from whichever numbers happen to be on the record.
        hits = getattr(entry, "hits", None)
        if isinstance(hits, Sequence) and not isinstance(hits, (str, bytes)):
            fired = [h for h in hits if getattr(h, "bad", False)]
            if fired:
                out["gate"] = "+".join(dict.fromkeys(
                    str(getattr(h, "gate", "") or "") for h in fired))
                out["basis"] = "; ".join(
                    f"{getattr(h, 'gate', '?')}: {getattr(h, 'status', 'UNSTATED')} "
                    f"({getattr(h, 'source', '') or 'no source'})" for h in fired)
                out["gate_detail"] = "; ".join(
                    str(getattr(h, "detail", "") or "") for h in fired)
        return out or None
    return None


def _hq_gate(record: Mapping[str, Any]) -> str:
    text = str(record.get("gate") or "").strip().lower()
    if "drho" in text:
        return "drho"
    if "rug" in text:
        return "rugosity"
    if "cal" in text or "washout" in text or "gauge" in text or "bit" in text:
        return "caliper"
    if text:
        return "unnamed"
    # No gate named: infer only where the record itself carries the evidence.
    # A DRHO *value* is not evidence that the DRHO gate fired - asquith#18 gates
    # on DRHO **exceeding** 0.20 g/cm3. Claiming "drho - SOURCED" for a record
    # whose DRHO is in tolerance dresses a PROVISIONAL house rule in the corpus's
    # only sourced threshold, which is the exact confusion tool-catalog.md:112
    # forbids.
    drho = _numeric(record.get("drho"))
    if drho is not None and drho > DRHO_SUSPECT:
        return "drho"
    if any(_numeric(record.get(k)) is not None
           for k in ("diffcal", "diff_cal", "caliper_in")):
        return "caliper"
    if drho is not None:
        return "drho"
    return "unnamed"


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _hq_verdict(record: Mapping[str, Any]) -> tuple[str, str, str]:
    """-> (verdict, gate, detail). verdict is 'bad', 'ok' or 'unreadable'."""
    drho = _numeric(record.get("drho"))
    if drho is not None and drho > DRHO_SUSPECT:
        return ("bad", "drho", f"DRHO {drho:.2f} g/cm3 exceeds {DRHO_SUSPECT} g/cm3")
    gate = _hq_gate(record)
    if record.get("washout") is True or record.get("bad_hole") is True \
            or record.get("rugose") is True:
        flagged = [k for k in ("washout", "bad_hole", "rugose") if record.get(k) is True]
        return ("bad", "caliper" if gate == "unnamed" else gate,
                f"hole_quality reports {' and '.join(flagged)}")
    text = " ".join(str(record.get(k)) for k in ("flag", "status", "quality", "verdict")
                    if record.get(k) is not None).strip().lower()
    if text:
        hit = next((t for t in _HQ_BAD_TOKENS if t in text), None)
        if hit is not None:
            if gate == "unnamed":
                # Infer the gate from the verdict word rather than reporting
                # "gate not named" when the verdict itself names it.
                if "rugos" in hit:
                    gate = "rugosity"
                elif hit in ("washout", "wash-out", "enlarge", "undergauge",
                             "under-gauge", "caving", "cave"):
                    gate = "caliper"
            named = str(record.get("gate_detail") or "").strip()
            return ("bad", gate,
                    named or f"hole_quality verdict {text!r}")
        if any(t in text for t in _HQ_GOOD_TOKENS):
            return ("ok", gate, f"hole_quality verdict {text!r}")
    if drho is not None:
        return ("ok", "drho", f"DRHO {drho:.2f} g/cm3 is within {DRHO_SUSPECT} g/cm3")
    return ("unreadable", gate, "no washout/rugosity verdict field found on the record")


def _hq_select(hole_quality: Any, depth_md: float | None) -> tuple[str, Any]:
    """-> ('none'|'refusal'|'record'|'unreadable'|'needs_depth', payload)."""
    if hole_quality is None:
        return ("none", None)
    if isinstance(hole_quality, Refusal):
        return ("refusal", hole_quality)
    if isinstance(hole_quality, (str, bytes)):
        return ("unreadable", hole_quality)
    # #25's own return type (tools/borehole.py HoleQuality) publishes
    # `verdict_at(depth_ft)` as "the contract density_porosity (#26) codes
    # against". Use it, rather than refusing the whole object as unreadable:
    # a false refusal on every depth is not fail-closed, it is unusable.
    selector = getattr(hole_quality, "verdict_at", None)
    if callable(selector) and not isinstance(hole_quality, Mapping):
        if depth_md is None:
            return ("needs_depth", tuple(getattr(hole_quality, "samples", ()) or ()))
        sample = selector(float(depth_md))
        if sample is None:
            return ("none", None)  # #25 evaluated no sample at this depth
        return _hq_select(sample, depth_md)
    if isinstance(hole_quality, Sequence) and not isinstance(hole_quality, Mapping):
        entries = [e for e in hole_quality]
        if not entries:
            return ("unreadable", hole_quality)
        if depth_md is None:
            if len(entries) == 1:
                return _hq_select(entries[0], None)
            return ("needs_depth", entries)
        for entry in entries:
            rec = _hq_as_dict(entry)
            if rec is None:
                continue
            top, base = _numeric(rec.get("top_md")), _numeric(rec.get("base_md"))
            if top is None or base is None:
                # An entry with no depth bounds is a whole-hole verdict only if it
                # is the only one; otherwise it cannot be placed against depth_md.
                if len(entries) == 1:
                    return ("record", rec)
                continue
            if min(top, base) <= depth_md <= max(top, base):
                return ("record", rec)
        return ("none", None)  # no interval covers this depth: #25 said nothing here
    rec = _hq_as_dict(hole_quality)
    if rec is None:
        return ("unreadable", hole_quality)
    return ("record", rec)


# --- #26 density_porosity -----------------------------------------------------

def density_porosity(rho_b: float, lithology: str, fluid: str = "fresh",
                     drho: float | None = None, gas_bearing: bool = False, *,
                     hole_quality: Any = None, depth_md: float | None = None,
                     table: str = "asquith",
                     rho_ma: float | None = None,
                     rho_ma_source: str | None = None) -> Quantity | Refusal:
    """phi_D = (rho_ma - rho_b) / (rho_ma - rho_fl).  Asquith Eq. 4.7 (#18, p. 40).

    Negative results are returned, not clipped: Asquith notes a negative density
    porosity is diagnostic of anhydrite or other heavy minerals, so suppressing
    it would discard a real lithology signal.

    Two gates can stop it. DRHO > 0.20 g/cm3 is the source's own quality rule and
    is SOURCED; a washout or rugosity verdict from `hole_quality` (#25) is a
    PROVISIONAL house rule. The refusal names which fired and its status, because
    an operator can argue with one and not the other.

    `rho_ma` overrides the matrix density the lithology would supply, and lands in
    `assumptions` where `assumption_registry` (#68) can see it. It exists because
    the catalog's flagship contested-constant sweep - Asquith 2.644 against AAPG
    2.65, and 1.04 porosity units apart on salt - was otherwise unreachable
    through this tool's public surface: `sensitivity_sweep` (#69) had to swap the
    entry in the module-level MATRIX table and restore it afterwards, which
    mutates shared state and is neither thread-safe nor re-entrant. An override
    still requires `lithology`, because the travel time, the alternate-table
    comparison and the flags all come from it; it replaces one constant, not the
    lookup. Supplying it without `rho_ma_source` is answered but flagged - a
    matrix density with no stated origin is exactly the orphan number this layer
    exists to prevent.
    """
    consts = matrix_constant_lookup(lithology, table=table)
    rho_ma_override = rho_ma
    rho_ma = consts.rho_ma.value if rho_ma_override is None else float(rho_ma_override)
    if rho_ma_override is not None and not _finite(rho_ma_override):
        raise ValueError(f"rho_ma override must be a finite density, got {rho_ma_override!r}")
    if gas_bearing:
        rho_fl = HILCHIE_GAS_DENSITY
        fluid_note = "Hilchie (1978) gas density 0.7 g/cm3"
    else:
        rho_fl = consts.rho_fl(fluid).value
        fkey = _fluid_key(fluid, consts.table)
        fluid_note = FLUID_BASIS[consts.table][fkey]

    # Gate 1, SOURCED: the caller's own DRHO reading outranks everything.
    if drho is not None and drho > DRHO_SUSPECT:
        return Refusal(
            reason=(f"DRHO {drho:.2f} g/cm3 exceeds {DRHO_SUSPECT}; bulk density is suspect. "
                    f"Gate: DRHO - {GATE_BASIS['drho']}"),
            needed=("a bulk density from an in-gauge interval",
                    "or a porosity that does not depend on the density curve"),
            source=ASQUITH_T42,
        )

    # Gate 2, the #25 verdict. Unreadable fails closed.
    kind, payload = _hq_select(hole_quality, depth_md)
    hq_note: str | None = None
    if kind == "refusal":
        return Refusal(
            reason=("hole_quality (#25) could not establish the hole condition, so the "
                    "bulk density cannot be cleared for use: " + payload.reason),
            needed=tuple(payload.needed) or ("a hole-quality verdict at this depth",),
            source=payload.source or ASQUITH_T42,
        )
    if kind == "needs_depth":
        return Refusal(
            reason=(f"hole_quality supplied {len(payload)} depth intervals but no depth_md "
                    "to select among them; picking one would be a guess about where this "
                    "bulk density was read"),
            needed=("depth_md for this rho_b", "or a single hole_quality verdict"),
            source=ASQUITH_T42,
        )
    if kind == "unreadable":
        return Refusal(
            reason=(f"hole_quality verdict of type {type(payload).__name__} carries no "
                    "readable washout/rugosity flag; an unreadable verdict is refused "
                    "rather than treated as good hole"),
            needed=("a hole_quality record with a flag/status field, or washout/bad_hole "
                    "booleans, or a DRHO value",),
            source=ASQUITH_T42,
        )
    if kind == "record":
        verdict, gate, detail = _hq_verdict(payload)
        basis = str(payload.get("basis") or GATE_BASIS.get(gate, GATE_BASIS["unnamed"]))
        if verdict == "bad":
            return Refusal(
                reason=(f"hole_quality (#25) flags this depth as bad hole: {detail}. "
                        f"Gate: {gate} - {basis}"),
                needed=("a bulk density from an in-gauge interval",
                        "or an explicit override if the house-rule cutoff is wrong for this well"
                        if gate != "drho" else
                        "or a porosity that does not depend on the density curve"),
                source=ASQUITH_T42 if gate == "drho" else "tool-catalog.md:112",
            )
        if verdict == "unreadable":
            return Refusal(
                reason=("hole_quality supplied a record with no washout/rugosity verdict "
                        "field; an unreadable verdict is refused rather than treated as "
                        "good hole"),
                needed=("a flag/status field, or washout/bad_hole booleans, or a DRHO value",),
                source=ASQUITH_T42,
            )
        hq_note = f"{gate}: {detail} ({basis})"

    if rho_ma == rho_fl:
        raise ValueError(
            f"rho_ma and rho_fl are both {rho_ma}; Eq. 4.7 is undefined. "
            "No published table pair produces this."
        )

    phi = (rho_ma - rho_b) / (rho_ma - rho_fl)
    flags: list[str] = []
    if phi < 0:
        flags.append("negative porosity - possible anhydrite or heavy minerals")
    if consts.table != "asquith":
        flags.append(
            f"matrix from the documented alternate table ({TABLE_LABELS[consts.table]}); "
            f"Asquith is the source of truth and the two differ by "
            f"{consts.divergence_pu.value:.2f} pu for {consts.lithology} at "
            f"rho_b={DIVERGENCE_RHO_B}, rho_fl={DIVERGENCE_RHO_FL}"
        )
    assumptions: dict[str, Any] = {
        "lithology": consts.lithology, "fluid": fluid, "gas_bearing": gas_bearing,
        "matrix_table": consts.table, "matrix_source": consts.source,
        "fluid_basis": fluid_note,
    }
    if rho_ma_override is not None:
        # The override replaced the table value, so the table is no longer what
        # produced this number and `matrix_source` must not read as though it did.
        assumptions["rho_ma_override"] = float(rho_ma_override)
        assumptions["rho_ma_override_source"] = rho_ma_source
        assumptions["matrix_source"] = rho_ma_source or "caller override, no source stated"
        table_value = consts.rho_ma.value
        flags.append(
            f"rho_ma overridden: {float(rho_ma_override)} g/cm3 in place of "
            f"{table_value} g/cm3 from {TABLE_LABELS[consts.table]} for "
            f"{consts.lithology}")
        if not rho_ma_source:
            flags.append(
                "rho_ma override carries no stated source; a matrix density with no "
                "origin is the orphan number this layer exists to prevent")
    if hq_note is not None:
        assumptions["hole_quality_gate"] = hq_note
    inputs: dict[str, Any] = {"rho_b": rho_b, "rho_ma": rho_ma, "rho_fl": rho_fl}
    if drho is not None:
        inputs["drho"] = drho
    return Quantity(
        value=phi, unit="v/v", method="density porosity (Asquith Eq. 4.7)",
        source=consts.source, inputs=inputs, assumptions=assumptions,
        flags=tuple(flags),
    )


# --- #29 sonic_porosity -------------------------------------------------------

def sonic_porosity(dt_log: float, lithology: str, fluid: str = "fresh",
                   method: str = "wyllie", dt_shale: float | None = None, *,
                   c_constant: float = COMPACTION_C_DEFAULT,
                   hydrocarbon: str | None = None,
                   dt_ma: float | None = None,
                   table: str = "asquith") -> Quantity | Refusal:
    """Sonic porosity, with every correction Asquith #16-#17 attaches to it.

    Wyllie time-average (Eq. 4.1) or Raymer-Hunt-Gardner (Eq. 4.2); then the
    compaction correction of Eqs. 4.3/4.4 when an adjacent-shale transit time is
    supplied; then Hilchie's hydrocarbon corrections, Eq. 4.5 (gas, x0.7) and
    Eq. 4.6 (oil, x0.9).

    Each correction is applied only where the source publishes it. Eq. 4.3 is
    stated for *unconsolidated sands* and as an addition to *the Wyllie
    equation*, so it refuses on a carbonate and refuses under RHG rather than
    quietly generalising. C in Eq. 4.4 is "normally 1.0 (Hilchie, 1978)" — a
    documented default, so it is an argument, not a hard-coded constant.
    """
    if not dt_log > 0:
        raise ValueError(f"dt_log must be positive, got {dt_log!r}")
    variant = _variant_key(method)
    if hydrocarbon is not None:
        hc_key = str(hydrocarbon).strip().lower()
        if hc_key not in HYDROCARBON_FACTORS:
            raise ValueError(
                f"unknown hydrocarbon {hydrocarbon!r}; known: "
                f"{sorted(HYDROCARBON_FACTORS)}. Asquith #17 publishes Eq. 4.5 (gas) "
                "and Eq. 4.6 (oil) and nothing else."
            )
    else:
        hc_key = None
    consts = matrix_constant_lookup(lithology, variant, table)
    fkey = _fluid_key(fluid, "asquith")

    # Compaction is gated by what Eq. 4.3 is published for, before anything is
    # computed, so a caller who asked for an unsupported correction gets a
    # refusal rather than a number with the correction quietly dropped.
    if dt_shale is not None:
        if variant != "wyllie":
            return Refusal(
                reason=("Asquith Eq. 4.3 adds the compaction factor to 'the Wyllie et al. "
                        "(1958) equation'; no compaction form is published for "
                        "Raymer-Hunt-Gardner"),
                needed=("method='wyllie'", "or a published RHG compaction correction"),
                source=ASQUITH_T41,
            )
        if consts.lithology != "sandstone":
            return Refusal(
                reason=(f"Asquith Eq. 4.3 is published for unconsolidated *sands*; no "
                        f"compaction factor is published for {consts.lithology}"),
                needed=(f"a published compaction correction for {consts.lithology}",
                        "or omit dt_shale"),
                source=ASQUITH_T41,
            )
        if not dt_shale > 0:
            raise ValueError(f"dt_shale must be positive, got {dt_shale!r}")
        if not c_constant > 0:
            raise ValueError(
                f"c_constant must be positive, got {c_constant!r}; Eq. 4.4 would give a "
                "zero or negative compaction factor"
            )

    # Matrix travel time: an explicit override, else Table 4.1 (which may refuse,
    # or may be a range that has to be collapsed in the open).
    dt_ma_range: tuple[float, float] | None = None
    range_flag: str | None = None
    if dt_ma is not None:
        if not dt_ma > 0:
            raise ValueError(f"dt_ma must be positive, got {dt_ma!r}")
        dt_ma_value = float(dt_ma)
        dt_ma_basis = "caller override"
        dt_ma_source = "caller"
    else:
        point = consts.dt_ma_point()
        if isinstance(point, Refusal):
            return point
        dt_ma_value = point.value
        dt_ma_basis = f"Asquith Table 4.1 ({variant.upper()} column)"
        dt_ma_source = point.source
        rng = consts.dt_ma
        if isinstance(rng, Range):
            dt_ma_range = (rng.low, rng.high)
            range_flag = point.flags[0] if point.flags else None

    dt_fl_value: float | None = FLUID[fkey]["dt_fl"] if variant == "wyllie" else None

    def _phi(matrix_dt: float) -> tuple[float, float | None, float]:
        """-> (final, after_compaction, uncorrected) for one matrix travel time."""
        if variant == "rhg":
            base = 0.625 * (dt_log - matrix_dt) / dt_log
        else:
            if dt_fl_value == matrix_dt:
                raise ValueError(
                    f"dt_fl and dt_ma are both {matrix_dt}; Eq. 4.1 is undefined"
                )
            base = (dt_log - matrix_dt) / (dt_fl_value - matrix_dt)
        after_cp = None
        value = base
        if dt_shale is not None:
            cp = (dt_shale * c_constant) / 100.0
            value = value / cp
            after_cp = value
        if hc_key is not None:
            value = value * HYDROCARBON_FACTORS[hc_key][0]
        return (value, after_cp, base)

    phi, phi_after_cp, phi_base = _phi(dt_ma_value)

    # Provenance ---------------------------------------------------------------
    if variant == "rhg":
        label = "Raymer-Hunt-Gardner (Asquith Eq. 4.2)"
    else:
        label = "Wyllie time-average (Asquith Eq. 4.1)"
    corrections: list[str] = []
    assumptions: dict[str, Any] = {
        "lithology": consts.lithology,
        "equation_variant": variant,
        "matrix_table": consts.table,
        "matrix_source": consts.source,   # the rho_ma table (#18), for the record
        "dt_ma_source": dt_ma_source,     # Table 4.1 (#17) is what THIS tool used
        "dt_ma_basis": dt_ma_basis,
        "phi_uncorrected": phi_base,
    }
    if variant == "wyllie":
        assumptions["fluid"] = fkey
    if dt_ma_range is not None:
        assumptions["dt_ma_range"] = dt_ma_range
    if dt_shale is not None:
        cp = (dt_shale * c_constant) / 100.0
        assumptions["compaction_factor_Cp"] = cp
        assumptions["C"] = c_constant
        assumptions["dt_shale"] = dt_shale
        assumptions["phi_after_compaction"] = phi_after_cp
        corrections.append("compaction (Eq. 4.3/4.4)")
    if hc_key is not None:
        factor, eq = HYDROCARBON_FACTORS[hc_key]
        assumptions["hydrocarbon"] = hc_key
        assumptions["hydrocarbon_factor"] = factor
        corrections.append(f"{hc_key} ({eq})")
    if corrections:
        assumptions["correction_order"] = ["base equation", *corrections]
        assumptions["correction_source"] = ASQUITH_T41
        label = label + " + " + " + ".join(corrections)

    flags: list[str] = []
    if range_flag is not None:
        low, high = dt_ma_range  # type: ignore[misc]
        phi_low = _phi(low)[0]
        phi_high = _phi(high)[0]
        flags.append(
            f"{range_flag}; the published range spans "
            f"{abs(phi_low - phi_high) * 100:.2f} pu here "
            f"(phi {min(phi_low, phi_high):.6f} to {max(phi_low, phi_high):.6f})"
        )
    if consts.lithology in ("limestone", "dolomite"):
        flags.append(
            "sonic reads matrix porosity only; vuggy or fracture secondary porosity is not "
            "seen and the value reads too low in such carbonates (Asquith #17). Compute "
            "SPI = total porosity (nuclear) - sonic porosity."
        )
    if dt_shale is not None:
        cp = (dt_shale * c_constant) / 100.0
        if cp < 1.0:
            flags.append(
                f"compaction factor Cp = {cp:.4f} < 1.0, so Eq. 4.3 raises porosity rather "
                "than lowering it; Asquith states no floor and does not discuss this case, "
                "so the value is returned unclamped"
            )
    if phi < 0:
        flags.append("negative porosity - dt_log is below the matrix travel time; "
                     "check the lithology assumption")
    if consts.table != "asquith":
        # Reachable ONLY with an explicit dt_ma: without one, the alternate
        # table's Dt_ma is a Refusal and this function has already returned. So
        # the travel times in play came from anywhere except the named table,
        # and a flag saying "matrix from the alternate table" would be false in
        # the only case it can fire.
        note = (f"the named matrix table ({TABLE_LABELS[consts.table]}) publishes no "
                f"interval transit times; dt_ma {dt_ma_value} usec/ft came from the "
                "caller, not from it")
        if dt_fl_value is not None:
            note += (f", and dt_fl {dt_fl_value} usec/ft is Asquith Table 4.1 "
                     f"({ASQUITH_T41}) — the only published source of one")
        flags.append(note)

    inputs: dict[str, Any] = {"dt_log": dt_log, "dt_ma": dt_ma_value}
    if dt_fl_value is not None:
        inputs["dt_fl"] = dt_fl_value

    return Quantity(
        value=phi, unit="v/v", method=label, source=ASQUITH_SONIC,
        inputs=inputs, assumptions=assumptions, flags=tuple(flags),
    )


# ---------------------------------------------------------------------------
# Group D — #31 vshale, #32 temperature_gradient, #35 archie_sw
#
# Specs: specs/31-vshale.md, specs/32-temperature_gradient.md,
#        specs/35-archie_sw.md. Read those for the quoted equations; what
#        follows explains only the decisions a reader would otherwise query.
#
# Three of them change returned values.
#
# **Asquith's Clavier equation is printed wrong and is corrected here.** #15
# prints Eq. 3.4 as `1.7 - [3.38 - (I_GR - 0.7)^2]^0.5`. At I_GR = 1 — pure
# shale, where the answer is known independently — that returns Vsh = -0.1138, a
# negative shale volume. With `(I_GR + 0.7)` it returns exactly 1.0, and at
# I_GR = 0 both forms give exactly 0. The corrected form is used and the printed
# one is pinned in CLAVIER_PRINTED_IS_WRONG so it cannot drift back. Same class
# of defect as the dogleg equation in the directional-drilling thesis
# (petrophysics-tool-build.md, Part 5).
#
# **Sw > 1 is now a refusal, not a flagged number.** Rewriting Eq. 7.1 with
# Eq. 7.16 gives Sw = (Rw/Rwa)^(1/n), and asquith#44 states Rwa >= Rw in every
# case the model admits. Above unity the arithmetic still works and the physics
# does not, and a flag does not survive into BVW, a net-pay cutoff or a report.
# The refusal carries the uncapped Sw, Rwa, Ro and which of the source's named
# causes the inputs fit — it is the wet verdict, not the loss of one.
#
# **The Arps constant is unit-bound and the gradient needs TD.** 6.77 in degF,
# 21.0 in degC, and Asquith ties the second to "for depth in meters"; Celsius
# temperatures with the Fahrenheit constant is a wrong answer with no symptom.
# `temperature_gradient` is new, and is what tool-verification.md's "needs TD as
# an input" was asking for. No BHT correction is applied anywhere here: the
# corpus supports a linear gradient and nothing more (see BHT_UNCORRECTED).
# ---------------------------------------------------------------------------

ASQUITH_VSH = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#15"
ASQUITH_SW = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#42"
ASQUITH_TEMP = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9"
#: Apparent water resistivity (Eq. 7.16) and its "Interpretation pitfalls",
#: pp. 118-119. The only place the corpus says what an Sw above 1.0 means.
ASQUITH_RWA = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#44"
#: The invasion profiles, and the one sentence that licenses "deep reading = Rt".
#: The same segment as ASQUITH_TEMP; named separately so citations read honestly.
ASQUITH_INVASION = ASQUITH_TEMP


# --- #31 vshale ---------------------------------------------------------------
#
# Coefficients of Eqs. 3.2-3.5, `asquith#15`. Tabulated rather than inlined so
# the Clavier sign correction has somewhere to live beside the value it fixes.

LARIONOV_TERTIARY = (0.083, 3.7)      # Eq. 3.2
STEIBER = (3.0, 2.0)                  # Eq. 3.3
CLAVIER = (1.7, 3.38, 0.7)            # Eq. 3.4, sign corrected
LARIONOV_OLDER = (0.33, 2.0)          # Eq. 3.5

#: What `asquith#15` actually prints for Eq. 3.4, kept so the defect stays
#: visible and a test can assert we do not return it.
CLAVIER_PRINTED_IS_WRONG = (
    "asquith#15 prints Eq. 3.4 as 1.7 - [3.38 - (I_GR - 0.7)^2]^0.5, which returns "
    "Vsh = -0.1138 at I_GR = 1.0 (pure shale). The (I_GR + 0.7) form, used here, "
    "returns exactly 1.0 there and exactly 0.0 at I_GR = 0"
)

#: Above this I_GR the Clavier radicand 3.38 - (I_GR + 0.7)^2 goes negative and
#: there is no real Vsh: sqrt(3.38) - 0.7 = 1.1384776...
CLAVIER_IGR_MAX = math.sqrt(CLAVIER[1]) - CLAVIER[2]

#: Steiber's pole, 3 - 2*I_GR = 0.
STEIBER_IGR_POLE = STEIBER[0] / STEIBER[1]

#: Total-GR curves versus uranium-free ones. `asquith#15` (Dewan, 1983) suggests
#: thorium and potassium instead of total GR where uranium salts are present,
#: because uranium is soluble and post-depositional, so a total-GR Vsh reads too
#: shaly there.
GR_TOTAL_CURVES = frozenset({"GR", "SGR", "GRD", "GRR", "GRT"})
GR_URANIUM_FREE_CURVES = frozenset({"CGR", "THOR", "TH", "KTH"})

#: `asquith#15` lists the nonlinear forms "in increasing optimism" as
#: 3.2, 3.3, 3.4, 3.5 — which would make Larionov-older the most optimistic. Its
#: own Figure 3.2 table contradicts that at I_GR = 0.35 (Steiber 0.15,
#: Larionov-older 0.21), and so do the equations: there the four give
#: 0.1206 < 0.1522 < 0.1909 < 0.2061, i.e. the printed order is *decreasing*
#: optimism. Equations and worked example agree with each other, so the sentence
#: loses. Reported, never acted on.
VSHALE_RANKING_DISPUTE = (
    "asquith#15's sentence orders the nonlinear forms 3.2, 3.3, 3.4, 3.5 'in "
    "increasing optimism', but its own Figure 3.2 table prints Steiber 0.15 below "
    "Larionov-older 0.21 at I_GR = 0.35, and the equations agree with the table. "
    "The order is decreasing optimism; assumptions['optimism_rank'] is computed "
    "from the equations at this I_GR, not from the sentence"
)

#: The claim that IS true across I_GR in [0, 1], and the reason all five forms
#: are offered rather than one.
VSHALE_OPTIMISM = (
    "nonlinear forms read lower (more optimistic) than linear: asquith#15, 'all "
    "nonlinear relationships are more optimistic; that is, they produce a shale "
    "volume value lower than that from the linear equation'"
)

VSHALE_METHODS = ("linear", "larionov_tertiary", "steiber", "clavier",
                  "larionov_older")


def _vshale_form(key: str, igr: float):
    """One published form at one I_GR.  -> (value | None, label, why_none).

    Evaluated **lazily, one form at a time**. Building all five eagerly evaluated
    Clavier's sqrt(3.38 - (I_GR + 0.7)^2) even for a caller who asked for linear,
    so a `math domain error` escaped from a call that should have returned a
    linear Vsh — and I_GR beyond 1.138 is routine on a real curve, because no
    clean/shale pair brackets every sample. Out of domain is a `None` here and
    becomes a Refusal only if it is the form actually requested.
    """
    if key == "linear":
        return (igr, "linear I_GR (Asquith Eq. 3.1)", None)
    if key == "larionov_tertiary":
        coeff, expo = LARIONOV_TERTIARY
        label = "Larionov (1969) tertiary rocks (Asquith Eq. 3.2)"
    elif key == "larionov_older":
        coeff, expo = LARIONOV_OLDER
        label = "Larionov (1969) older rocks (Asquith Eq. 3.5)"
    elif key == "steiber":
        num, den_coeff = STEIBER
        label = "Steiber (1970) (Asquith Eq. 3.3)"
        den = num - den_coeff * igr
        if den == 0:
            return (None, label,
                    f"I_GR = {igr:.6f} is Steiber's pole: Eq. 3.3's denominator "
                    f"3 - 2*I_GR is zero at I_GR = {STEIBER_IGR_POLE}")
        return (igr / den, label, None)
    elif key == "clavier":
        offset, under, shift = CLAVIER
        label = "Clavier (1971) (Asquith Eq. 3.4, sign corrected)"
        radicand = under - (igr + shift) ** 2
        if radicand < 0:
            return (None, label,
                    f"I_GR = {igr:.6f} is outside Clavier's real domain: Eq. 3.4's "
                    f"radicand 3.38 - (I_GR + 0.7)^2 is negative above I_GR = "
                    f"{CLAVIER_IGR_MAX:.6f}, so there is no real shale volume. "
                    "Returning a complex or clipped value would be inventing one")
        return (offset - math.sqrt(radicand), label, None)
    else:  # pragma: no cover - guarded by the caller
        raise ValueError(f"unknown vshale method {key!r}")
    try:
        return (coeff * (2.0 ** (expo * igr) - 1.0), label, None)
    except OverflowError:
        return (None, label,
                f"I_GR = {igr:.6f} overflows 2^({expo}*I_GR); the equation is drawn "
                "for I_GR in [0, 1] and this is far outside it")


def _vshale_forms(igr: float) -> dict:
    """Every form with a real value at this I_GR. Informational; never raises."""
    out = {}
    for key in VSHALE_METHODS:
        value, _, _ = _vshale_form(key, igr)
        if value is not None:
            out[key] = value
    return out


def gamma_ray_index(gr_log: float, gr_clean: float, gr_shale: float) -> float:
    """I_GR = (GR_log - GR_min) / (GR_max - GR_min).  Asquith Eq. 3.1.

    Returns a bare float. That predates the Quantity contract and is kept because
    the name is public; `vshale` records I_GR in `inputs`, which is where the
    provenance actually lands. See specs/31-vshale.md, open question 1.

    Identical picks raise rather than refuse: the picks are declarations by the
    caller, not measurements, and declaring the clean line and the shale line to
    be the same line is a self-contradictory argument.
    """
    if not (_finite(gr_log) and _finite(gr_clean) and _finite(gr_shale)):
        raise ValueError(
            f"gamma ray values must be finite; got gr_log={gr_log!r}, "
            f"gr_clean={gr_clean!r}, gr_shale={gr_shale!r}. Run null_scrub (#12) first."
        )
    if gr_shale == gr_clean:
        raise ValueError(
            f"clean and shale picks are identical ({gr_clean}); Eq. 3.1's denominator "
            "is zero and I_GR is undefined. The picks are this tool's whole "
            "calibration and it will not invent a spread between them."
        )
    return (gr_log - gr_clean) / (gr_shale - gr_clean)


def vshale(gr_log: float, gr_clean: float, gr_shale: float, method: str = "linear",
           *, gr_curve=None, pick_source=None, depth_ft=None):
    """Shale volume from gamma ray. Asquith Eqs. 3.1-3.5 (`asquith#15`, pp. 31-35).

    All five published forms. The nonlinear ones are uniformly lower than linear
    — the source's own words — so reporting one without saying which would hide
    that; every result carries the whole set in `assumptions["forms"]` and the
    ranking they actually produce at this I_GR in `assumptions["optimism_rank"]`.

    The default is `linear` because the source says so: "For a first-order
    estimation of shale volume, the linear response ... should be used." Which
    nonlinear form applies is "based on geographic area or formation age", which
    is external information this tool does not have and will not guess.

    Nothing is clipped. An I_GR outside [0, 1] means the picks do not bracket the
    reading, and hiding that behind a clamp would bury a bad pick a whole zone
    rests on. Only the requested form is evaluated, so one form being out of its
    domain cannot break a call that asked for another.
    """
    key = str(method).strip().lower()
    if key not in VSHALE_METHODS:
        raise ValueError(
            f"unknown vshale method {method!r}; known: {sorted(VSHALE_METHODS)}. "
            "asquith#15 publishes Eqs. 3.1-3.5 and this tool adds none."
        )

    # R1: inverted picks. Arithmetically fine, which is exactly the problem — it
    # returns a mirrored I_GR that still reads like a shale volume.
    if _finite(gr_clean) and _finite(gr_shale) and gr_shale < gr_clean:
        return Refusal(
            reason=(f"the shale pick ({gr_shale}) is below the clean pick ({gr_clean}); "
                    "Eq. 3.1 names GR_min the clean sand or carbonate and GR_max the "
                    "shale, and asquith#15's premise is that shale reads high. Swapped "
                    "picks give a mirrored I_GR that still looks like a shale volume"),
            needed=("gr_clean = the minimum (clean) gamma ray reading",
                    "gr_shale = the maximum (shale) gamma ray reading"),
            source=ASQUITH_VSH,
        )

    igr = gamma_ray_index(gr_log, gr_clean, gr_shale)

    # R2: the requested form has no real value here. Only this form is evaluated,
    # so a Clavier domain limit cannot reach a caller who asked for linear.
    value, label, why_none = _vshale_form(key, igr)
    if value is None:
        return Refusal(
            reason=why_none,
            needed=("clean and shale picks that bracket this reading",
                    "or another form: "
                    + ", ".join(sorted(set(VSHALE_METHODS) - {key}))),
            source=ASQUITH_VSH,
        )

    real_forms = _vshale_forms(igr)
    ranked = [k for k, _ in sorted(real_forms.items(), key=lambda kv: kv[1])]

    curve = None if gr_curve is None else str(gr_curve).strip().upper()
    flags = []
    if key != "linear":
        flags.append(VSHALE_OPTIMISM)
        flags.append(VSHALE_RANKING_DISPUTE)
    if not 0.0 <= igr <= 1.0:
        side = "cleaner than the clean pick" if igr < 0 else "shalier than the shale pick"
        flags.append(
            f"I_GR = {igr:.6f} is outside [0, 1]: this reading is {side}, so the picks "
            f"({gr_clean} clean, {gr_shale} shale) do not bracket it. Asquith picks "
            "GR_min and GR_max as the observed extremes of the interval he then "
            "evaluates, so his procedure never produces this and the corpus has no rule "
            "for it. Not clipped - a clamp would hide the bad pick"
        )
    if not 0.0 <= value <= 1.0:
        flags.append(
            f"V_shale = {value:.6f} is outside [0, 1] and is a fraction of bulk volume; "
            "returned unclipped so the pick can be corrected rather than papered over"
        )
    if curve is None:
        flags.append(
            "the gamma ray curve was not declared. asquith#15 (Dewan, 1983) recommends "
            "thorium and potassium instead of total GR where uranium salts, potassium "
            "feldspar, mica or glauconite are present; pass gr_curve to get that check"
        )
    elif curve in GR_TOTAL_CURVES:
        flags.append(
            f"{curve} is a total gamma ray. asquith#15 (Dewan, 1983): use only the "
            "thorium and potassium components 'because uranium salts are soluble and "
            "can be transported and precipitated in the formation after deposition'. "
            "In uranium-bearing rock this V_shale reads too high"
        )
    elif curve in GR_URANIUM_FREE_CURVES:
        flags.append(f"{curve} excludes uranium, which is what asquith#15 recommends "
                     "for V_shale in rock carrying uranium salts")
    if not pick_source:
        flags.append("the clean and shale picks were asserted with no stated source; "
                     "a pick that cannot be traced to a curve and a depth is not evidence")

    return Quantity(
        value=value, unit="v/v", method=label, source=ASQUITH_VSH,
        inputs={"gr_log": gr_log, "gr_clean": gr_clean, "gr_shale": gr_shale,
                "I_GR": igr, "depth_ft": depth_ft},
        assumptions={"method": key, "forms": real_forms, "optimism_rank": ranked,
                     "gr_curve": curve, "pick_source": pick_source,
                     "clavier_sign": CLAVIER_PRINTED_IS_WRONG if key == "clavier" else None},
        flags=tuple(flags),
    )


# --- #32 temperature_gradient -------------------------------------------------
#
# The unit binding IS the tool. `asquith#9` prints the Arps constant as 6.77 and,
# parenthetically, 21.0 "for depth in meters", and notes the temperatures are
# "usually Fahrenheit for depth in feet, Celsius for depth in meters". Passing
# Celsius with 6.77 is a plausible wrong answer with no symptom: at 20 -> 80 the
# two constants give 0.3085 and 0.4059, a 24% error.

TEMPERATURE_UNITS = {
    "degF": {"depth_unit": "ft", "arps_x": 6.77, "source": ASQUITH_TEMP,
             "note": "Asquith Eq. 1.10 (Arps), Fahrenheit form; depth in feet"},
    "degC": {"depth_unit": "m", "arps_x": 21.0, "source": ASQUITH_TEMP,
             "note": "Asquith Eq. 1.10 (Arps), Celsius form, printed 'for depth in meters'"},
}

#: The Arps constants alone, by unit. The Celsius value is disputed in the corpus
#: — Mosul #1 Eq. 10 prints 21.5 where Asquith prints 21.0 — and
#: `tools/formation_water/rw_tds.py` takes it as an argument. This copy uses
#: Asquith's, which is its cited source. They are never averaged.
ARPS_X = {u: c["arps_x"] for u, c in TEMPERATURE_UNITS.items()}

#: The most consequential caveat in this module, and it goes on every temperature.
#: A BHT is one reading taken at the end of a run in a hole that circulating mud
#: has been cooling: it reads low, so Tf reads low, so Rw corrected to Tf reads
#: high, so Sw reads low — optimistic, in the direction that costs money.
#: `asquith#9` supplies no correction for it and neither does anything else in
#: this corpus, so none is applied.
BHT_UNCORRECTED = (
    "BHT is uncorrected for circulation cooling. asquith#9 supports a linear "
    "gradient between the mean annual surface temperature and BHT at TD and "
    "nothing more - it prints no Horner or static-temperature correction, and "
    "neither does anything else in this corpus. An uncorrected BHT reads low, so "
    "Tf reads low, so Rw at Tf reads high, so Sw reads low"
)


def _temperature_units(units):
    """-> (key, was_declared). Never guesses; None means 'defaulted, and say so'."""
    if units is None:
        return ("degF", False)
    key = str(units)
    if key not in TEMPERATURE_UNITS:
        raise ValueError(
            f"units must be one of {sorted(TEMPERATURE_UNITS)}, got {units!r}. "
            "The Arps constant is unit-bound (6.77 degF / 21.0 degC) and the "
            "geothermal gradient's depth unit follows it; this tool does not infer "
            "a unit system from the magnitude of a temperature."
        )
    return (key, True)


def _unit_flags(unit_key: str, declared: bool) -> list:
    if declared:
        return []
    return [f"unit system was not declared and defaulted to {unit_key} "
            f"({TEMPERATURE_UNITS[unit_key]['depth_unit']}); the Arps constant and the "
            "gradient's depth unit are both unit-bound, and Celsius temperatures "
            "against the Fahrenheit constant is a wrong answer with no symptom"]


def temperature_gradient(surface_temp: float, bht: float, total_depth: float,
                         units=None, *, surface_temp_source=None, bht_source=None):
    """The geothermal gradient m = (BHT - AMST) / TD.  Asquith #9, p. 17.

    The source's worked example: (250 - 70) / 15,000 = 0.012 degF/ft, printed
    both ways as "0.012 degree/ft or 1.2 degree/100 ft".

    TD is the input this tool was missing (tool-verification.md, "Missing
    required inputs"). The two TDs on a real header disagree — both fixtures
    carry a driller's TDD and a logger's TDL, 4 ft and 2 ft apart and in opposite
    senses — so whichever is passed is recorded in `inputs` and the tool does not
    choose between them.

    There is no default surface temperature. It is not on a LAS header, this
    corpus has no table of mean annual surface temperature, and Asquith's 70 degF
    is an example value, not a constant.
    """
    unit_key, declared = _temperature_units(units)
    depth_unit = TEMPERATURE_UNITS[unit_key]["depth_unit"]
    if not (_finite(surface_temp) and _finite(bht) and _finite(total_depth)):
        raise ValueError(
            f"surface_temp, bht and total_depth must be finite numbers; got "
            f"{surface_temp!r}, {bht!r}, {total_depth!r}. LAS header values arrive as "
            "strings - parse them (header_extract, #4) rather than passing them through.")
    if total_depth <= 0:
        raise ValueError("total depth must be positive")

    # R1. The line runs from the surface temperature to BHT at TD, and the earth
    # is warmer with depth. A BHT at or below the surface temperature is a header
    # error — most often BHT in degC against a surface temperature in degF, or a
    # missing BHT defaulted to the surface value — and the line it produces cools
    # every formation with depth. The arithmetic is fine; the physics is not.
    if bht <= surface_temp:
        return Refusal(
            reason=(f"BHT {bht} {unit_key} is not above the mean annual surface "
                    f"temperature {surface_temp} {unit_key}, so the gradient is "
                    f"{'zero' if bht == surface_temp else 'negative'} and the formation "
                    "would cool with depth. asquith#9 fits a line from the surface "
                    "temperature to BHT at TD; this pair does not describe a well"),
            needed=("a BHT above the mean annual surface temperature",
                    f"both temperatures in the same unit system (declared here as "
                    f"{unit_key})"),
            source=ASQUITH_TEMP,
        )

    m = (bht - surface_temp) / total_depth
    flags = [BHT_UNCORRECTED] + _unit_flags(unit_key, declared)
    if not surface_temp_source:
        flags.append("the mean annual surface temperature was asserted with no stated "
                     "source; it is not on a LAS header and this corpus has no table of it")
    if not bht_source:
        flags.append("BHT was asserted with no stated source; the log header's ~P BHT "
                     "is the usual one")
    return Quantity(
        value=m, unit=f"{unit_key}/{depth_unit}",
        method="linear geothermal gradient m = (BHT - AMST)/TD (Asquith #9, Eq. 1.10)",
        source=ASQUITH_TEMP,
        inputs={"surface_temp": surface_temp, "BHT": bht, "total_depth": total_depth},
        assumptions={"units": unit_key, "depth_unit": depth_unit,
                     "gradient_per_100_depth_units": m * 100.0,
                     "surface_temp_source": surface_temp_source,
                     "bht_source": bht_source,
                     "gradient": "linear; BHT uncorrected for circulation cooling"},
        flags=tuple(flags),
    )


def formation_temperature(surface_temp: float, bht: float, total_depth: float,
                          depth: float, units=None, *,
                          surface_temp_source=None, bht_source=None):
    """Tf = m*depth + AMST, m from `temperature_gradient`.  Asquith #9, p. 17.

    Eq. 1.10, y = mx + c, with x = formation depth, y = temperature, m = the
    geothermal gradient and c = the mean annual surface temperature. The source's
    worked example: (0.012 x 8,000) + 70 = 166 degF.

    The gradient is not recomputed here — it comes from `temperature_gradient`,
    so there is one implementation of the slope and the two cannot disagree.
    """
    unit_key, declared = _temperature_units(units)
    if not _finite(depth):
        raise ValueError(f"depth must be finite, got {depth!r}")
    if depth < 0:
        raise ValueError(f"depth must not be negative, got {depth!r}")

    slope = temperature_gradient(
        surface_temp, bht, total_depth, unit_key if declared else None,
        surface_temp_source=surface_temp_source, bht_source=bht_source)
    if isinstance(slope, Refusal):
        return slope

    tf = slope.value * depth + surface_temp
    flags = list(slope.flags)
    if depth > total_depth:
        flags.append(
            f"depth {depth} is below total depth {total_depth}: this is extrapolation "
            "past the deeper of the two points the line was fitted through. Routine on "
            "a real log - repass-2 logs to 4218 ft against a driller's TD of 4200 - so "
            "it is flagged, not refused"
        )
    return Quantity(
        value=tf, unit=unit_key,
        method="linear geothermal gradient, Tf = m*depth + AMST (Asquith #9, Eq. 1.10)",
        source=ASQUITH_TEMP,
        inputs={"surface_temp": surface_temp, "BHT": bht,
                "total_depth": total_depth, "depth": depth,
                "gradient": slope.value},
        assumptions={"units": unit_key,
                     "depth_unit": TEMPERATURE_UNITS[unit_key]["depth_unit"],
                     "gradient_per_100_depth_units":
                         slope.assumptions["gradient_per_100_depth_units"],
                     "gradient_method": slope.method,
                     "surface_temp_source": surface_temp_source,
                     "bht_source": bht_source,
                     "gradient": "linear; BHT uncorrected for circulation cooling"},
        flags=tuple(flags),
    )


def resistivity_at_temperature(r_known: float, t_known: float, t_target: float,
                               units="degF"):
    """Arps: R2 = R1 * (T1 + X) / (T2 + X), X = 6.77 degF or 21.0 degC.

    Asquith #9, Eq. 1.10, introduced as an approximation to a chart: "Figure 1.11
    is a chart that is used for correcting fluid resistivities to the formation
    temperature. This chart is closely approximated by the Arp's formula". Worked
    example: 0.04 ohm-m at 70 degF becomes 0.04 x (70+6.77)/(166+6.77) = 0.01777
    at 166 degF, which the source prints as 0.018.

    The constant is unit-bound. Passing Celsius temperatures with the Fahrenheit
    constant is a several-percent-to-24% error that looks entirely plausible, so
    the unit system is an explicit argument, an unknown token raises rather than
    silently defaulting, and `units=None` is answered but flagged.

    `tools/formation_water/rw_tds.py` carries a richer copy of this function
    (quantity_kind, the disputed Mosul 21.5 Celsius constant); merging them is
    group J's call. `tests/group_j/j91_j92.py` pins the two to identical values,
    so nothing here may change a returned number.
    """
    unit_key, declared = _temperature_units(units)
    if not (_finite(r_known) and _finite(t_known) and _finite(t_target)):
        raise ValueError(
            f"resistivity and temperatures must be finite; got r={r_known!r}, "
            f"T1={t_known!r}, T2={t_target!r}")
    if r_known <= 0:
        raise ValueError(f"resistivity must be positive, got {r_known!r}")

    x = TEMPERATURE_UNITS[unit_key]["arps_x"]
    # The correlation's pole: past it Arps returns a negative or infinite
    # resistivity, which no source supports at any confidence.
    if (t_known + x) <= 0 or (t_target + x) <= 0:
        return Refusal(
            reason=(f"temperature at or below the Arps pole: the correlation divides by "
                    f"(T + {x}) in {unit_key}, so T <= {-x} {unit_key} yields a negative "
                    f"or infinite resistivity. Got T1={t_known}, T2={t_target} {unit_key}"),
            needed=(f"both temperatures above {-x} {unit_key}",
                    "or the correct unit system - the constant is unit-bound"),
            source=ASQUITH_TEMP,
        )

    r2 = r_known * (t_known + x) / (t_target + x)
    return Quantity(
        value=r2, unit="ohm-m",
        method=f"Arps temperature correction ({unit_key})", source=ASQUITH_TEMP,
        inputs={"R1": r_known, "T1": t_known, "T2": t_target},
        assumptions={"constant": x, "units": unit_key,
                     "depth_unit": TEMPERATURE_UNITS[unit_key]["depth_unit"],
                     "basis": TEMPERATURE_UNITS[unit_key]["note"]},
        flags=tuple(_unit_flags(unit_key, declared)),
    )


# --- #35 archie_sw ------------------------------------------------------------
#
# Reading #37's verdict. `tools/invasion.py` did not exist when this was written
# — only `specs/37-invasion_profile.md` — so this does not import it: importing a
# module that is not there yet would break the whole layer at import time. The
# reader is permissive about type and strict about meaning, the same shape as
# #26's hole-quality reader and for the same reason. What it will NOT do is treat
# an unreadable verdict as a clearance.
#
# Assumed of #37, from specs/37-invasion_profile.md "Output":
#   .rt          Quantity | Refusal  - "the contract"
#   .rt_status   "usable" | "corrected" | "not_usable"
#   .rt_usable   bool property
#   .profile / .fluid_indication / .mud_regime / .flags
# and, from its l. 294-297, that #35 must PROPAGATE an rt refusal rather than
# downgrade it to a flag.

_INVASION_FIELDS = ("rt", "rt_status", "rt_usable", "profile", "fluid_indication",
                    "mud_regime", "flags", "annulus_effect")


def _invasion_field(invasion, name):
    if isinstance(invasion, Mapping):
        return invasion.get(name)
    return getattr(invasion, name, None)


def _invasion_rt(invasion):
    """-> (kind, payload).

    kind is 'none' (nothing supplied), 'refusal' (propagate payload), 'rt'
    (payload is a Quantity carrying the Rt to use), 'cleared' (the verdict clears
    the caller's Rt without substituting one), or 'unreadable'.
    """
    if invasion is None:
        return ("none", None)
    if isinstance(invasion, Refusal):
        return ("refusal", invasion)
    if isinstance(invasion, (str, bytes, int, float, bool)):
        return ("unreadable", invasion)

    rt = _invasion_field(invasion, "rt")
    if isinstance(rt, Refusal):
        return ("refusal", rt)
    if isinstance(rt, Quantity):
        return ("rt", rt)

    status = _invasion_field(invasion, "rt_status")
    usable = _invasion_field(invasion, "rt_usable")
    if isinstance(status, str) and status.strip().lower() == "not_usable":
        return ("refusal", Refusal(
            reason=("invasion_profile (#37) reports rt_status='not_usable': the deep "
                    "reading is not Rt. asquith#9 licenses 'deep reading = Rt' only "
                    "under a step profile"),
            needed=("an invasion-corrected Rt", "or a declared step profile"),
            source=ASQUITH_INVASION))
    if usable is False:
        return ("refusal", Refusal(
            reason="invasion_profile (#37) reports the deep reading is not usable as Rt",
            needed=("an invasion-corrected Rt",), source=ASQUITH_INVASION))
    if usable is True or (isinstance(status, str)
                          and status.strip().lower() in ("usable", "corrected")):
        return ("cleared", invasion)
    return ("unreadable", invasion)


#: asquith#44, "Interpretation pitfalls": "In low-porosity zones (less than about
#: 10% porosity), the R_wa value is lower than the actual R_w value" — the
#: technique itself pushes Sw up there. SOURCED, with the source's own "about".
RWA_LOW_POROSITY = 0.10

#: The published (a, m) sets, echoed on results so a caller can see whether the
#: pair they passed is one of them.
#:
#: **Read from #100's table, not restated here.** Asquith Table 1.1 (`asquith#8`,
#: book p. 5, "Different coefficients and exponents used to calculate formation
#: factor (F)") prints nine (a, m) pairs, and `tools/vintage_logs/porosity_from_f.py`
#: already holds all nine with their attributions. This module previously carried
#: a three-row copy of the same table under a wrong citation — "Table 1.2
#: (`asquith#9`)", which is a different table entirely (Table 1.2 is "Common
#: equations of well-log interpretation") — and the copy's six missing rows made
#: `archie_sw` tell a caller who passed Carothers' shaly-sand pair (a = 1.65,
#: m = 1.33) that it "is not one of the sets Asquith prints", when Table 1.1
#: prints exactly it. One table, one anchor: duplicated lookup tables are how the
#: Fig. 7-9 error survived this build.
FORMATION_FACTOR_SETS = {
    name: (row["a"], row["m"]) for name, row in _ARCHIE_AM_PAIRS.items()
}


def archie_sw(rt: float, phi: float, rw: float, rw_source=None,
              a: float = 1.0, m: float = 2.0, n: float = 2.0,
              rt_invasion_corrected: bool = False, *,
              invasion=None, rw_at_formation_temperature=None,
              depth_ft=None):
    """Sw = (a*Rw / (Rt * phi^m))^(1/n).  Asquith Eq. 7.1 (`asquith#42`, p. 121).

    Refuses a point value without Rw provenance. That is a harness rule from
    well-log-agent.md, not a published one, and it is the gate that stops a
    guessed Rw from becoming a saturation the operator acts on.

    Two clauses in Eq. 7.1's own variable list drive the rest: Rt is "deep
    induction or deep laterolog **corrected for invasion**", and Rw is "at
    formation temperature". Pass `invasion=` the #37 verdict and this tool acts on
    it — clearing the reading, substituting a corrected Rt, or propagating #37's
    refusal. With no verdict it flags rather than refuses, because specs/37's own
    step-versus-transition reconciliation needs a provisional Sw computed off an
    uncorrected deep reading, and refusing here would make that uncomputable.

    Sw above 1.0 refuses. See specs/35-archie_sw.md, "What Sw > 1 means".
    """
    # R1b: the provenance must be an Rw, not something Rw-shaped.
    #
    # A bare truthy string satisfied R1 while saying nothing about *what* the
    # number is, and the two upstream tools both hand back quantities that are
    # not Rw:
    #   * `rw_from_sp` (#33) returns an **Rwe** until the Bateman-Konen step
    #     runs. Asquith commits this error himself - Chapter 2 works the upper
    #     Morrow bed to Rw = 0.10, Chapter 10's shortcut works the same bed to
    #     0.140 and calls it Rw, 47% high.
    #   * `rw_pickett` (#34) returns the intercept **a*Rw**, not Rw. Feeding it
    #     in undivided understates Sw by exactly sqrt(a): on a real fit it came
    #     back a clean Quantity with no flag, 21% optimistic (0.337 against
    #     0.428).
    #
    # `tools/rw.py:rw_provenance()` already knew how to catch both, but it was
    # opt-in and nothing here called it. When `rw` arrives as a Quantity its
    # declared kind is checked; a bare float with a string provenance cannot be
    # checked and is flagged instead, since the corpus gives no way to tell.
    _rw_kind = (rw.assumptions.get("quantity_kind")
                if isinstance(rw, Quantity) else None)
    if _rw_kind is not None and _rw_kind != "Rw":
        return Refusal(
            reason=(f"the Rw supplied is declared {_rw_kind!r}, not 'Rw'. "
                    + ("Rwe is an equivalent resistivity and is not Rw until the "
                       "Rwe->Rw conversion runs; Asquith's own Chapter 10 shortcut "
                       "makes this error and reads 47% high against his Chapter 2 "
                       "answer on the same bed."
                       if _rw_kind == "Rwe" else
                       "a*Rw is the Pickett intercept and is not Rw until it is "
                       "divided by the tortuosity factor a; used undivided it "
                       "understates Sw by sqrt(a)."
                       if _rw_kind == "a*Rw" else
                       "Eq. 7.1 takes the formation-water resistivity itself.")),
            needed=(f"an Rw Quantity, or the {_rw_kind} converted first "
                    "(rwe_to_rw for Rwe; divide by a for a*Rw)",),
            source=ASQUITH_SW,
        )

    if isinstance(rw, Quantity):
        rw = rw.value

    # Programmer error and bad units, before anything is computed.
    if not (_finite(rt) and _finite(phi) and _finite(rw)
            and _finite(a) and _finite(m) and _finite(n)):
        raise ValueError(
            f"Archie needs finite arguments; got Rt={rt!r}, phi={phi!r}, Rw={rw!r}, "
            f"a={a!r}, m={m!r}, n={n!r}. Run null_scrub (#12) over the curves first.")
    if phi <= 0:
        raise ValueError("porosity must be positive for Archie")
    if phi > 1.0:
        raise ValueError(
            f"porosity {phi!r} is not a fraction. Archie takes phi in v/v, so {phi!r} is "
            "almost certainly a percentage; it moves Sw by a factor of 10^(m/n) in the "
            "optimistic direction with no other symptom. Use unit_convert (#11).")
    if rt <= 0:
        raise ValueError(f"Rt must be positive, got {rt!r}")
    if rw <= 0:
        raise ValueError(f"Rw must be positive, got {rw!r}")
    if a <= 0:
        raise ValueError(f"tortuosity factor a must be positive, got {a!r}")
    if n == 0:
        raise ValueError("saturation exponent n must not be zero; Eq. 7.1 raises to 1/n")

    # R1: the gate this tool exists for.
    if not rw_source:
        return Refusal(
            reason="Rw has no stated provenance; Archie will not return a point saturation",
            needed=("Rw from rw_from_sp, rw_pickett, or a measured water analysis",),
            source=ASQUITH_SW,
        )

    # R5: Eq. 7.1 defines Rw at formation temperature.
    if rw_at_formation_temperature is False:
        return Refusal(
            reason=("Rw is declared as NOT being at formation temperature. Eq. 7.1's own "
                    "variable list reads 'Rw = resistivity of formation water at "
                    "formation temperature'; an Rw left at surface temperature is several "
                    "times too high and Sw comes out correspondingly optimistic"),
            needed=("resistivity_at_temperature (#32, Arps) applied to Rw, with a "
                    "formation temperature from formation_temperature (#32)",),
            source=ASQUITH_SW,
        )

    # The Rt gate. A #37 verdict outranks the bare boolean.
    kind, payload = _invasion_rt(invasion)
    rt_used = float(rt)
    rt_raw = None
    rt_basis = "caller's Rt; invasion correction not established"
    flags = []

    if kind == "refusal":
        return Refusal(
            reason=("invasion_profile (#37) will not clear the deep reading as Rt, and "
                    "Eq. 7.1 is defined on 'deep induction or deep laterolog corrected "
                    "for invasion': " + payload.reason),
            needed=tuple(payload.needed) or ("an invasion-corrected Rt",),
            source=payload.source or ASQUITH_INVASION,
        )
    if kind == "unreadable":
        return Refusal(
            reason=(f"the invasion verdict of type {type(payload).__name__} carries no "
                    "readable rt, rt_status or rt_usable field; an unreadable verdict is "
                    "refused rather than treated as a clearance"),
            needed=("an invasion_profile (#37) result",
                    "or omit invasion= and accept the uncorrected-Rt flag"),
            source=ASQUITH_INVASION,
        )
    if kind == "rt":
        rt_used = float(payload.value)
        if not _finite(rt_used) or rt_used <= 0:
            raise ValueError(
                f"invasion_profile supplied a non-positive Rt: {payload.value!r}")
        rt_basis = f"invasion_profile (#37): {payload.method}"
        if rt_used != float(rt):
            rt_raw = float(rt)
            flags.append(
                f"Rt substituted by invasion_profile (#37): {rt_used} ohm-m used, the "
                f"caller's {rt} ohm-m recorded as Rt_raw. Eq. 7.1 is defined on the "
                "corrected value")
    elif kind == "cleared":
        rt_basis = "deep reading cleared as Rt by invasion_profile (#37)"
    elif rt_invasion_corrected:
        rt_basis = "caller asserts Rt is invasion-corrected (no #37 verdict supplied)"
        flags.append(
            "Rt was asserted invasion-corrected by the caller with no invasion_profile "
            "(#37) verdict behind it; the assertion is recorded, not verified")
    else:
        # F1. Deliberately a flag and not a refusal — see the docstring and
        # specs/35-archie_sw.md, F1.
        flags.append(
            "Rt not declared invasion-corrected; deep readings are not Rt. Eq. 7.1 "
            "defines Rt as 'deep induction or deep laterolog corrected for invasion', "
            "and asquith#9 licenses 'deep = Rt' only under a step profile. Run "
            "invasion_profile (#37) and pass invasion=. This value is provisional: it "
            "is the Swa that specs/37's Swa/Swr reconciliation consumes, not a "
            "saturation to act on")

    profile = _invasion_field(invasion, "profile") if invasion is not None else None
    fluid = _invasion_field(invasion, "fluid_indication") if invasion is not None else None
    if profile == "annulus":
        flags.append(
            "invasion_profile (#37) reports an annulus profile: asquith#9 says it 'can "
            "only occur in zones that bear hydrocarbons', and the annular ring of "
            "displaced formation water inflates the deep reading")
    if fluid == "hydrocarbon":
        flags.append("invasion_profile (#37) reports a hydrocarbon fluid indication")

    rwa = rt_used * phi ** m / a           # Eq. 7.16
    ro = a * rw / phi ** m                 # Ro = F * Rw, Eqs. 7.13/7.14
    sw = ((a * rw) / (rt_used * phi ** m)) ** (1.0 / n)

    # R4. Above unity Sw is arithmetically available and physically impossible.
    # asquith#44: "If the zone contains hydrocarbons, Rt is greater than Ro, and
    # Rwa is greater than Rw" — Rwa < Rw is outside the model, and the source
    # names what produces it anyway.
    if sw > 1.0:
        causes = []
        if phi < RWA_LOW_POROSITY:
            causes.append(
                f"porosity {phi:.4f} is below the {RWA_LOW_POROSITY:.0%} asquith#44 names "
                "as an interpretation pitfall - 'in low-porosity zones (less than about "
                "10% porosity), the R_wa value is lower than the actual R_w value'")
        causes.append(
            f"Rw {rw} may be too high for this zone: the R_wa method takes the LOWEST "
            f"R_wa as the best estimate of Rw, and this zone's R_wa is {rwa:.6g}")
        if kind == "none" and not rt_invasion_corrected:
            causes.append(
                "Rt was never established as invasion-corrected; an uncorrected deep "
                "reading in an invaded zone reads below Rt (asquith#9), and asquith#43 "
                "case 3 makes the same diagnosis from the saturation side")
        return Refusal(
            reason=(f"Archie gives Sw = {sw:.6f}, above 1.0. A saturation is a fraction of "
                    f"pore volume, so this is not a number to act on - the interval reads "
                    f"at or beyond fully wet (R_wa {rwa:.6g} < Rw {rw}; Ro {ro:.6g} > Rt "
                    f"{rt_used}). It is neither clipped nor returned with a flag, because "
                    f"it would propagate into BVW = phi*Sw, into the net-pay Sw cutoff, "
                    f"and into a report reading '{sw * 100:.0f}% water'. Candidate "
                    "causes: " + "; ".join(causes)),
            needed=("an Rw low enough to be the minimum R_wa over the zones compared "
                    "(rw_pickett #34, rw_from_sp #33, or a water analysis)",
                    "an invasion-corrected Rt (invasion_profile #37)",
                    "a porosity above the ~10% R_wa pitfall, or a method that does not "
                    "rest on R_wa",
                    "or read the interval as wet, which is what this arithmetic says"),
            source=ASQUITH_RWA,
        )

    if sw == 1.0:
        flags.append("Sw is exactly 1.0: R_wa equals Rw and the interval reads fully wet")
    if phi < RWA_LOW_POROSITY:
        flags.append(
            f"porosity {phi:.4f} is below {RWA_LOW_POROSITY:.0%}, where asquith#44 states "
            "the R_wa value reads lower than the actual Rw; Sw from this range is biased "
            "high")
    if rw_at_formation_temperature is None:
        flags.append(
            "it was not declared whether Rw is at formation temperature; Eq. 7.1 requires "
            "that it is, and resistivity_at_temperature (#32) is the fix")
    named = [k for k, v in FORMATION_FACTOR_SETS.items() if v == (a, m)]
    if not named:
        flags.append(
            f"a={a}, m={m} is not one of the sets Asquith Table 1.1 prints "
            f"({FORMATION_FACTOR_SETS}); the pair is the caller's")

    # What goes where matters downstream, not only stylistically. `assumption_registry`
    # (#68) is fed from `assumptions` and nothing else, and renders every row as
    # something "the user never stated". So `assumptions` carries only what a caller
    # could actually have declared and that changes the answer: a, m, n, the Rw
    # provenance, which route established Rt, and whether Rw is at formation
    # temperature. R_wa and R_o are *computed* and #37's verdict is an *observation*;
    # filing either under assumptions would tell an operator that a derived number was
    # a silent default. They ride on `inputs`, where #30 already puts its computed
    # `separation`. There is deliberately no `lithology` argument: Archie depends on
    # lithology only through `a` and `m`, which are already arguments, and a parameter
    # that changes no answer invites a caller to believe it did.
    return Quantity(
        value=sw, unit="v/v", method="Archie (Asquith Eq. 7.1)", source=ASQUITH_SW,
        inputs={"Rt": rt_used, "phi": phi, "Rw": rw, "Rt_raw": rt_raw,
                "Rwa": rwa, "Ro": ro, "depth_ft": depth_ft,
                "formation_factor_set": named[0] if named else None,
                "invasion_profile": profile, "fluid_indication": fluid},
        assumptions={"a": a, "m": m, "n": n, "Rw_source": rw_source,
                     "rt_basis": rt_basis,
                     "rw_at_formation_temperature": rw_at_formation_temperature},
        flags=tuple(flags),
    )


# ---------------------------------------------------------------------------
# Neutron-density tools (#27, #28, #30)
#
# All three stand on one fact: a porosity curve carries a *matrix reference*,
# and that reference is a choice the logging program made, not a property of the
# rock. `asquith#19` says a neutron curve is "in units referenced to a specific
# lithology (usually either limestone or sandstone, depending on the geologic
# environment)" and `asquith#20` says the same of the density curve. So the
# comparison these tools exist to make is only meaningful once both curves are on
# one reference, and that reference is the formation's own lithology.
#
# Everything else follows. Comparing a limestone-referenced NPHI against a
# sandstone-matrix DPHI produces several porosity units of apparent crossover
# with no gas present at all, so #30 refuses rather than subtracting. And the
# corrections that would put two curves onto one reference live in vendor
# chartbooks that are not in this corpus, so #27's product is a refusal naming
# the chart rather than a number.
#
# The one number the corpus does give for the crossover regime is Asquith
# Eq. 4.8 — and it prints two expressions as if they were equal:
#
#     phi_NDgas = sqrt((phi_N^2 + phi_D^2)/2) = (1/3) phi_N + (2/3) phi_D
#
# They are not. At phi_N = 0.15, phi_D = 0.25 the radical gives 0.2061553 and the
# weighted form 0.2166667, a full porosity unit apart. The radical is what the
# equation is named for and is what these tools return; the weighted value rides
# along on `assumptions` with the difference, so the disagreement travels with
# the number instead of being resolved silently in the source's favour.
# ---------------------------------------------------------------------------

AAPG_CROSSPLOT = "01-curve-reading/aapg-density-neutron-log-porosity#0"
AAPG_GAS = "01-curve-reading/aapg-density-neutron-log-porosity#1"
ASQUITH_XPLOT = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#20"
ASQUITH_NEUTRON = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#19"
ASQUITH_FALSE_XOVER = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#28"
ASQUITH_SHALE_CORR = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#75"

#: The three references `asquith#19` enumerates for a porosity curve. There is no
#: fourth, and there is no default — the catalog's "limestone unless the header
#: says otherwise" is drift, settled against in `specs/11-unit_convert.md`.
NEUTRON_MATRICES: tuple[str, ...] = ("limestone", "sandstone", "dolomite")

#: Asquith's quick-look average carries a stated +/- tolerance. Unit-bound, so it
#: is looked up rather than written into the arithmetic.
QUICKLOOK_TOLERANCE: dict[str, float] = {"v/v": 0.02, "pct": 2.0}

POROSITY_UNITS: tuple[str, ...] = ("v/v", "pct")

ASQUITH_CHART_TABLES = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#22"
ASQUITH_CHART_CAPTIONS = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#27"

#: Eleven (NPHI in limestone units, -> dolomite, -> sandstone) rows read off
#: Asquith Table 4.10 (`asquith#22`), for **one** Halliburton tool. `None` is the
#: table's "< 0".
#:
#: **This is not a correction table and nothing may treat it as one.** It is
#: never interpolated, never fitted, and no code path returns a number derived
#: from it. It exists so the refusal below can state how large the correction it
#: declines to make would have been. Table 4.11 in the same segment reads 0.080
#: where this tool's chart reads 0.135 for the same 0.160 input — 5.5 porosity
#: units between two vendors' charts — which is precisely why a curve fitted
#: through these points would be one vendor's chart published as universal.
_CHART_SAMPLE_ASQUITH_T410: tuple[tuple[float, float | None, float | None], ...] = (
    (0.005, None, 0.015),
    (0.090, 0.070, 0.140),
    (0.130, 0.105, 0.185),
    (-0.010, None, None),
    (0.000, None, 0.015),
    (0.290, 0.250, 0.365),
    (0.140, 0.115, 0.200),
    (0.160, 0.135, 0.220),
    (0.010, None, 0.030),
)

#: Largest shift Table 4.10 publishes, in porosity units: 0.290 limestone units
#: becomes 0.365 sandstone, +7.5 pu, while the same reading becomes 0.250
#: dolomite, -4.0 pu. The correction is neither small nor signed one way.
_T410_MAX_SHIFT_PU = 100.0 * max(
    abs(target - nphi)
    for nphi, dolo, sand in _CHART_SAMPLE_ASQUITH_T410
    for target in (dolo, sand) if target is not None)

_MAGNITUDE_CAVEAT = (
    "the separation is qualitative: aapg#1 ranks its crossover points 2 > 3 > 4 "
    "but publishes no scale from separation to gas saturation"
)

#: The tool is named after the quantity, not after a chart it does not have.
#: `aapg#0`'s preferred method is "Plot the porosities on a density-neutron
#: crossplot from a log interpretation chartbook"; Asquith Figure 4.11 is an
#: un-OCR'd image and no vendor chartbook is in the corpus. Every result says so,
#: per specs/28 ("This tool implements only the *chartbook-free* paths the two
#: sources publish as equations, and says so on every result").
_CHARTBOOK_UNAVAILABLE = (
    "chartbook crossplot not available; this is the published chartbook-free form "
    "(aapg#0: the preferred method is to plot the pair on a vendor density-neutron "
    "crossplot, which is not in this corpus)"
)

#: Always flown by #30. The test consumes phi_D as a number and therefore cannot
#: see the gate that decides whether that number is real: DRHO > 0.20 g/cm3
#: (`asquith#18`, the one SOURCED log-quality threshold in the corpus), or a
#: washed-out hole - `asquith#20` Table 4.3 itself says "Watch for washed out
#: hole (large caliper values) and bad density data". A washout inflates density
#: porosity, which is the crossover direction, so an unchecked hole manufactures
#: gas.
_BOREHOLE_UNCHECKED = (
    "borehole condition is not tested here: this tool takes phi_D as a number "
    "and cannot see DRHO or the caliper, and a washed-out hole inflates density "
    "porosity in the crossover direction (asquith#18 DRHO > 0.20 g/cm3; "
    "asquith#20 Table 4.3 'watch for washed out hole ... and bad density data') "
    "- clear the interval with hole_quality (#25), or compute phi_D through "
    "density_porosity(..., drho=..., hole_quality=...), before reading this as gas"
)


def _porosity_unit(unit: str) -> str:
    key = str(unit).strip().lower()
    if key not in POROSITY_UNITS:
        raise ValueError(
            f"unknown porosity unit {unit!r}; known: {POROSITY_UNITS}. "
            "This tool does not guess a porosity convention.")
    return key


def _matrix_name(value: Any, argument: str) -> str | None:
    """Normalize a declared matrix reference, or None if it was not declared."""
    if value is None:
        return None
    key = str(value).strip().lower()
    if key not in NEUTRON_MATRICES:
        raise ValueError(
            f"{argument}={value!r} is not one of {NEUTRON_MATRICES}; "
            f"asquith#19 enumerates these three and this tool adds none.")
    return key


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(float(value))


def _asserted(source: Any, what: str) -> tuple[str, ...]:
    return () if source else (
        f"{what} was asserted by the caller with no stated source; "
        "a reference that cannot be traced to a log heading is not evidence",)


def gas_effect_flag(phi_n: float, phi_d: float, *, phi_n_matrix: Any,
                    phi_d_matrix: Any, formation_lithology: Any,
                    unit: str = "v/v", phi_n_matrix_source: str | None = None,
                    phi_d_matrix_source: str | None = None,
                    lithology_source: str | None = None,
                    overlay_tolerance: float = 0.0, clean: bool | None = None,
                    v_shale: float | None = None, depth_ft: float | None = None):
    """Neutron-density crossover, the gas indicator.  `aapg#1`, `asquith#20`.

    `aapg#1` defines it exactly: "Crossover occurs when the density log reads
    higher than the neutron log **in a zone of the same lithology as the log
    matrix lithology**". That qualifier is the tool. Without it the same
    comparison flags a scaling artefact as gas, so the matrix references are
    required, must agree with each other, and must agree with the formation.

    Sign convention, pinned: **positive = crossover = density above neutron =
    the gas direction.** Nothing downstream should re-derive it.
    """
    unit_key = _porosity_unit(unit)
    n_matrix = _matrix_name(phi_n_matrix, "phi_n_matrix")
    d_matrix = _matrix_name(phi_d_matrix, "phi_d_matrix")
    litho = _matrix_name(formation_lithology, "formation_lithology") \
        if formation_lithology not in (None, "shale") else formation_lithology
    if not isinstance(overlay_tolerance, (int, float)) or isinstance(overlay_tolerance, bool) \
            or not math.isfinite(float(overlay_tolerance)) or overlay_tolerance < 0:
        raise ValueError(
            f"overlay_tolerance={overlay_tolerance!r} is not a finite, non-negative "
            "number. A negative tolerance has no meaning and taking its magnitude "
            "would silently narrow what counts as crossover.")

    if not _finite(phi_n) or not _finite(phi_d):
        return Refusal(
            reason="a porosity is null or non-finite; nothing can be compared",
            needed=("null_scrub (#12) over both curves before this comparison",),
            source=AAPG_GAS)
    if n_matrix is None:
        return Refusal(
            reason="the neutron curve's matrix reference was not declared; "
                   "asquith#19 records neutron porosity 'in units referenced to a "
                   "specific lithology', and a value stripped of that reference "
                   "cannot be compared with anything",
            needed=("phi_n_matrix - limestone, sandstone or dolomite, from the log "
                    "heading or mnemonic_normalize (#9)",),
            source=ASQUITH_NEUTRON)
    if d_matrix is None:
        return Refusal(
            reason="the density curve's matrix reference was not declared; the "
                   "rho_ma the porosity was computed on is a choice the logging "
                   "program made, not a property of the rock",
            needed=("phi_d_matrix - the matrix density_porosity (#26) used",),
            source=ASQUITH_XPLOT)
    if n_matrix != d_matrix:
        return Refusal(
            reason=(f"the two curves are on different matrix references "
                    f"(neutron {n_matrix}, density {d_matrix}); their difference is "
                    "a scaling artefact and reads as crossover with no gas present"),
            needed=("neutron_porosity_correct (#27) to re-reference the neutron curve",
                    "or density_porosity (#26) recomputed on the neutron's matrix"),
            source=ASQUITH_FALSE_XOVER)
    if litho is None:
        return Refusal(
            reason="the formation's actual lithology was not declared; asquith#20 "
                   "requires knowing it 'as well as' the reference before predicting "
                   "gas from the log patterns",
            needed=("formation_lithology for the zone",),
            source=ASQUITH_XPLOT)
    if litho != n_matrix:
        return Refusal(
            reason=(f"the curves are referenced to {n_matrix} but the formation is "
                    f"{litho}; aapg#1 defines crossover only 'in a zone of the same "
                    "lithology as the log matrix lithology', and outside it the "
                    "separation is the false crossover of asquith#28"),
            needed=("neutron_porosity_correct (#27) to bring the neutron onto the "
                    f"{litho} reference",
                    f"or density_porosity (#26) recomputed on {litho}"),
            source=ASQUITH_FALSE_XOVER)
    if unit_key == "v/v" and (abs(phi_n) > 1.0 or abs(phi_d) > 1.0):
        return Refusal(
            reason=f"unit declared v/v but a porosity exceeds 1.0 "
                   f"(phi_n={phi_n}, phi_d={phi_d}); these are not fractions",
            needed=("null_scrub (#12) if this is a null sentinel",
                    "unit_convert (#11), or the correct unit token",),
            source=ASQUITH_XPLOT)

    separation = float(phi_d) - float(phi_n)
    tol = float(overlay_tolerance)
    if separation > tol:
        pattern, verdict = "crossover", "gas_indicated"
    elif separation < -tol:
        pattern, verdict = "shale_direction", "gas_not_indicated"
    else:
        pattern, verdict = "overlay", "gas_not_indicated"

    flags = [_MAGNITUDE_CAVEAT, _BOREHOLE_UNCHECKED]
    if pattern == "crossover":
        flags.append(
            "density porosity is inflated by gas here - recompute it with "
            "density_porosity(..., gas_bearing=True) (aapg#0)")
        if clean is False or (v_shale is not None and v_shale > 0):
            flags.append(
                "gas and clay are not separable from this test: aapg#1 notes clay "
                "drives a point toward the shale reference while gas makes the same "
                "sand look clean")
    if pattern == "shale_direction":
        flags.append(
            "neutron above density is the shale direction; density porosity is the "
            "reasonable approximation of formation porosity here (aapg#0)")
    if pattern != "crossover" and (clean is False or (v_shale is not None and v_shale > 0)):
        # The dangerous verdict, and the one the source works an example of. In
        # Case Study 5 the Pictured Cliffs is a shaly sandstone that produces gas
        # and shows no crossover: asquith#76 - "the response of the neutron and
        # density logs to abundant shale has masked any response to gas".
        # asquith#20 is the mechanism: clay drives the neutron up while gas drives
        # it down. So "gas not indicated" on a declared-shaly interval is not
        # evidence of no gas, and must never leave this tool sounding like it is.
        flags.append(
            "gas is NOT ruled out: the interval is declared shaly, and clay drives "
            "the neutron up while gas drives it down (asquith#20), so shale can "
            "mask crossover entirely - asquith#76 records exactly that in a "
            "gas-producing shaly sandstone, where 'response of the neutron and "
            "density logs to abundant shale has masked any response to gas'")
    if tol:
        flags.append(
            f"overlay tolerance {tol:g} {unit_key} is the caller's; no source "
            "supplies one, and a non-zero value narrows what counts as crossover")
    for value, what in ((phi_n_matrix_source, "the neutron matrix reference"),
                        (phi_d_matrix_source, "the density matrix reference"),
                        (lithology_source, "the formation lithology")):
        flags.extend(_asserted(value, what))

    return Quantity(
        separation, unit_key, "neutron-density crossover test (aapg#1; asquith#20)",
        AAPG_GAS,
        inputs={"phi_n": float(phi_n), "phi_d": float(phi_d),
                "separation": separation, "depth_ft": depth_ft},
        assumptions={"verdict": verdict, "pattern": pattern,
                     "phi_n_matrix": n_matrix, "phi_d_matrix": d_matrix,
                     "formation_lithology": litho,
                     "phi_n_matrix_source": phi_n_matrix_source,
                     "phi_d_matrix_source": phi_d_matrix_source,
                     "lithology_source": lithology_source,
                     "overlay_tolerance": tol, "unit": unit_key},
        flags=tuple(flags))


def crossplot_porosity(phi_n: float, phi_d: float, *, phi_n_matrix: Any,
                       phi_d_matrix: Any, formation_lithology: Any,
                       unit: str = "v/v", form: str = "auto",
                       clean: bool | None = None, gas_free: bool | None = None,
                       v_shale: float | None = None,
                       phi_n_matrix_source: str | None = None,
                       phi_d_matrix_source: str | None = None,
                       lithology_source: str | None = None,
                       overlay_tolerance: float = 0.0,
                       depth_ft: float | None = None):
    """Neutron-density crossplot porosity, with gas identified rather than averaged.

    The route is chosen by `gas_effect_flag` (#30) and **the crossover test is
    not repeated here** — `phi_d > phi_n` appears once in this module, inside #30,
    so the two tools cannot come to disagree about whether a zone shows gas.

    In the crossover regime the answer is Asquith Eq. 4.8's radical. The equation
    also prints a 1/3-2/3 weighted form as an equality; it is not one, so the
    weighted value and the difference ride on `assumptions`.
    """
    unit_key = _porosity_unit(unit)
    if form not in ("auto", "rms", "average", "density"):
        raise ValueError(f"unknown form {form!r}; known: auto, rms, average, density")

    verdict = gas_effect_flag(
        phi_n, phi_d, phi_n_matrix=phi_n_matrix, phi_d_matrix=phi_d_matrix,
        formation_lithology=formation_lithology, unit=unit_key,
        phi_n_matrix_source=phi_n_matrix_source,
        phi_d_matrix_source=phi_d_matrix_source, lithology_source=lithology_source,
        overlay_tolerance=overlay_tolerance, clean=clean, v_shale=v_shale,
        depth_ft=depth_ft)

    n_matrix = _matrix_name(phi_n_matrix, "phi_n_matrix")
    tolerance = QUICKLOOK_TOLERANCE[unit_key]

    def _quicklook():
        """Asquith's quick-look average, under his own three constraints."""
        if unit_key == "v/v" and (abs(float(phi_n)) > 1.0 or abs(float(phi_d)) > 1.0):
            # #30 makes this check last, after the reference gates, so the one
            # route that survives its R5 refusal has to make it for itself.
            return Refusal(
                reason=f"unit declared v/v but a porosity exceeds 1.0 "
                       f"(phi_n={phi_n}, phi_d={phi_d}); these are not fractions",
                needed=("unit_convert (#11), or the correct unit token",),
                source=ASQUITH_XPLOT)
        if n_matrix != "limestone":
            return Refusal(
                reason=(f"the quick-look average is stated for limestone-referenced "
                        f"curves; these are referenced to {n_matrix}"),
                needed=("limestone-referenced curves, or form='rms'",),
                source=ASQUITH_XPLOT)
        if clean is not True or gas_free is not True:
            return Refusal(
                reason=("the quick-look average is stated for clean, gas-free "
                        "intervals; averaging an interval whose gas status is "
                        "undeclared is what 'gas is identified, not averaged away' "
                        "forbids"),
                needed=("clean=True and gas_free=True, both caller declarations",
                        "or form='rms', which does not average"),
                source=ASQUITH_XPLOT)
        avg = (float(phi_n) + float(phi_d)) / 2.0
        return Range(avg - tolerance, avg + tolerance, unit_key,
                     "neutron-density quick-look average (Asquith), "
                     f"+/-{tolerance:g} {unit_key}; limestone-referenced curves, "
                     "caller-declared clean and gas-free", ASQUITH_XPLOT,
                     members={"phi_n": float(phi_n), "phi_d": float(phi_d),
                              "average": avg, "tolerance": tolerance},
                     inputs={"phi_n": float(phi_n), "phi_d": float(phi_d),
                             "depth_ft": depth_ft},
                     # The three constraints asquith#20 puts on the quick-look are
                     # what makes the answer admissible, so they are recorded as
                     # data, not only narrated in `method`. `Range` gained
                     # `inputs`/`assumptions`/`flags` for exactly this.
                     assumptions={"phi_n_matrix": n_matrix,
                                  "phi_d_matrix": _matrix_name(phi_d_matrix,
                                                               "phi_d_matrix"),
                                  "phi_n_matrix_source": phi_n_matrix_source,
                                  "phi_d_matrix_source": phi_d_matrix_source,
                                  "formation_lithology": formation_lithology,
                                  "lithology_source": lithology_source,
                                  "clean": clean, "gas_free": gas_free,
                                  "average": avg, "tolerance": tolerance,
                                  "form": form, "form_forced": form != "auto",
                                  "unit": unit_key},
                     flags=(_CHARTBOOK_UNAVAILABLE,
                            "quick-look reconnaissance estimate, good to about "
                            f"{tolerance:g} {unit_key} (asquith#20); clean and gas-free "
                            "are caller declarations, not measurements",
                            *_asserted(phi_n_matrix_source, "the neutron matrix reference"),
                            *_asserted(phi_d_matrix_source, "the density matrix reference"),
                            *_asserted(lithology_source, "the formation lithology")))

    # #30's R5 — curves referenced off the formation's lithology — is the one
    # condition it declines to interpret for which a source still supplies a
    # method, and only under the quick-look constraints. Every other refusal is a
    # gate on this call too and propagates untouched, `form` notwithstanding: the
    # quick-look average of a limestone-referenced neutron and a
    # sandstone-referenced density is not an average of anything, and neither is
    # the average of a null.
    _false_crossover = (isinstance(verdict, Refusal)
                        and "aapg#1 defines crossover" in verdict.reason)

    if form == "average":
        if isinstance(verdict, Refusal) and not _false_crossover:
            return verdict
        return _quicklook()

    if isinstance(verdict, Refusal):
        if form == "auto" and _false_crossover:
            got = _quicklook()
            if not isinstance(got, Refusal):
                return got
            # R7: propagate #30's refusal, but say what the one remaining route
            # would need, so the caller is not left to rediscover it.
            return Refusal(reason=verdict.reason,
                           needed=tuple(verdict.needed) + tuple(got.needed),
                           source=verdict.source)
        if form in ("rms", "density") and "different matrix references" not in verdict.reason \
                and "was not declared" not in verdict.reason \
                and "null or non-finite" not in verdict.reason \
                and "not fractions" not in verdict.reason:
            pass  # a forced form may still answer where #30 only declined to judge
        else:
            return verdict

    pattern = verdict.assumptions["pattern"] if not isinstance(verdict, Refusal) else None
    # A forced form that reaches here past a #30 refusal has answered a question
    # #30 declined to judge. specs/28 Procedure 5: "Every forced form records that
    # it was forced and flags where the source scopes it differently from the
    # call." Without this the caller cannot tell a routed answer from an overridden
    # one, because `gas_effect_pattern` is None in both the overlay-free cases.
    _overridden = verdict.reason if isinstance(verdict, Refusal) else None
    rms = math.sqrt((float(phi_n) ** 2 + float(phi_d) ** 2) / 2.0)
    weighted = float(phi_n) / 3.0 + 2.0 * float(phi_d) / 3.0

    shared_assumptions = {
        "phi_n_matrix": n_matrix,
        "phi_d_matrix": _matrix_name(phi_d_matrix, "phi_d_matrix"),
        "phi_n_matrix_source": phi_n_matrix_source,
        "phi_d_matrix_source": phi_d_matrix_source,
        "formation_lithology": formation_lithology,
        "lithology_source": lithology_source,
        "gas_effect_pattern": pattern,
        "gas_effect_verdict": None if pattern is None else
        verdict.assumptions["verdict"],
        # phi_D - phi_N, taken from #30's own returned value rather than recomputed,
        # so the two tools cannot report different separations for one depth. The
        # magnitude is diagnostic (asquith#20: "qualitatively related to the gas
        # saturation") and is what an operator reads the crossplot to see, so it
        # travels with the porosity instead of being left to be re-derived.
        "gas_effect_separation": None if pattern is None else verdict.value,
        "form": form, "form_forced": form != "auto", "unit": unit_key,
    }
    eq48_note = {
        "alternate_weighted_form": weighted,
        "alternate_form_difference": weighted - rms,
        "alternate_form_note": (
            "Asquith Eq. 4.8 prints sqrt((phiN^2+phiD^2)/2) and (1/3)phiN+(2/3)phiD "
            "as equal; they are not. The radical is returned and the weighted value "
            "is carried so the disagreement is visible."),
    }

    # `form="rms"` forces Eq. 4.8 **in any regime** (specs/28, Procedure 5). It
    # must outrank the shale-direction route, because the corpus's own worked RMS
    # in that direction is Case Study 5 (`asquith#75`, Eq. 10.41, Table 10.9),
    # where NPHIc 0.226 > DPHIc 0.158 and the published PHI is 0.195 — a value no
    # other route here can produce. Routing that call to phi_D returned 0.158 and
    # made a published oracle unreachable.
    if form == "density" or (pattern == "shale_direction" and form != "rms"):
        flags = [_CHARTBOOK_UNAVAILABLE]
        # The method must not claim a basis the result's own pattern contradicts.
        # `aapg#0` prescribes phi_D as the formation porosity *in the shale
        # direction*; forced anywhere else it is the caller's choice, and in the
        # crossover regime aapg#0's own instruction is the opposite one.
        if pattern == "shale_direction":
            method = ("density porosity as formation porosity, "
                      "shale direction (aapg#0)")
            flags.append(
                "neutron above density is the shale direction; a fuller treatment "
                "shale-corrects both curves first and then applies the same RMS "
                "(neutron_shale_correct, asquith#75), which is not this tool")
        else:
            method = "density porosity returned as formation porosity, forced (aapg#0)"
            if pattern == "crossover":
                flags.append(
                    "form='density' was forced in the crossover regime, where "
                    "aapg#0's answer is to RECOMPUTE density porosity with gas "
                    "density - density_porosity(..., gas_bearing=True) - not to "
                    "take the water-filled phi_D as the formation porosity; gas "
                    "has inflated this number")
        if form == "density":
            flags.append("form='density' was forced by the caller")
        if _overridden:
            flags.append("this form was forced past a gas_effect_flag (#30) refusal: "
                         + _overridden)
        return Quantity(float(phi_d), unit_key, method,
                        AAPG_CROSSPLOT,
                        inputs={"phi_n": float(phi_n), "phi_d": float(phi_d),
                                "depth_ft": depth_ft},
                        assumptions=shared_assumptions, flags=tuple(flags))

    if pattern == "overlay" and form == "auto":
        return Quantity(float(phi_d), unit_key,
                        "neutron and density agree; porosity read directly",
                        ASQUITH_XPLOT,
                        inputs={"phi_n": float(phi_n), "phi_d": float(phi_d),
                                "depth_ft": depth_ft},
                        assumptions=shared_assumptions,
                        flags=(_CHARTBOOK_UNAVAILABLE,
                               "neutron and density overlay within the tolerance; "
                               "the RMS and the arithmetic mean coincide here",))

    flags = [
        _CHARTBOOK_UNAVAILABLE,
        "gas inflates density porosity: the chartbook crossplot, and recomputing "
        "phi_D with density_porosity(..., gas_bearing=True) (#26), are the two "
        "methods the sources prefer over this closed form",
    ]
    if form == "rms":
        flags.append("form='rms' was forced by the caller")
        if pattern == "shale_direction":
            # Forced against the direction aapg#0 scopes its own answer to, so say
            # where the source disagrees with the call (specs/28, Procedure 5).
            flags.append(
                "form='rms' was forced in the shale direction (neutron above "
                "density), where aapg#0's own answer is phi_D; asquith#75 applies "
                "this RMS there only to inputs already shale-corrected by "
                "Eqs. 10.39-10.40, which this tool does not do")
    if _overridden:
        flags.append("this form was forced past a gas_effect_flag (#30) refusal: "
                     + _overridden)
    method = ("neutron-density gas porosity, RMS form (Asquith Eq. 4.8)"
              if pattern == "crossover"
              else "neutron-density porosity, chartbook-free RMS (aapg#0; Asquith Eq. 4.8)")
    return Quantity(rms, unit_key, method,
                    ASQUITH_XPLOT if pattern == "crossover" else AAPG_CROSSPLOT,
                    inputs={"phi_n": float(phi_n), "phi_d": float(phi_d),
                            "depth_ft": depth_ft},
                    assumptions={**shared_assumptions, **eq48_note},
                    flags=tuple(flags))


def neutron_porosity_correct(phi_n: float, *, log_matrix: Any,
                             formation_lithology: Any, unit: str = "v/v",
                             log_matrix_source: str | None = None,
                             lithology_source: str | None = None,
                             tool_vendor: str | None = None,
                             tool_model: str | None = None,
                             apply_environmental: bool = False,
                             fallback: str | None = None,
                             phi_d: float | None = None,
                             phi_d_matrix: Any = None,
                             v_shale: float | None = None,
                             depth_ft: float | None = None):
    """Correct a neutron porosity to a stated matrix — or refuse, which is usual.

    Where the curve's reference already is the formation's lithology there is
    nothing to correct and the value is returned as read. Where it is not, the
    correction lives in the **vendor's chartbook for that specific tool**, and no
    chartbook is in this corpus. So the tool refuses and names the chart.

    There is deliberately no `chart=` argument. A caller- or model-supplied
    correction curve is the exact hole this tool exists to close.
    """
    unit_key = _porosity_unit(unit)
    log_ref = _matrix_name(log_matrix, "log_matrix")
    litho = _matrix_name(formation_lithology, "formation_lithology") \
        if formation_lithology not in (None, "shale") else formation_lithology
    if fallback not in (None, "crossplot"):
        raise ValueError(f"unknown fallback {fallback!r}; known: None, 'crossplot'")

    if not _finite(phi_n):
        return Refusal(
            reason="the neutron porosity is null or non-finite",
            needed=("null_scrub (#12) over the curve",), source=AAPG_CROSSPLOT)
    if unit_key == "v/v" and abs(float(phi_n)) > 1.0:
        # Same guard, same wording as gas_effect_flag above: within one module the
        # two tools must not disagree about what "v/v" admits. A raw LAS column
        # still carrying -999.25, or a percent-scaled curve labelled v/v, both
        # land here rather than being passed through as a porosity.
        return Refusal(
            reason=f"unit declared v/v but the neutron porosity is {phi_n} - that is "
                   "not a fraction; it is a percent-scaled reading, a null sentinel, "
                   "or the wrong unit token",
            needed=("null_scrub (#12) if this is a null sentinel",
                    "unit_convert (#11), or the correct unit token: "
                    f"{POROSITY_UNITS}"),
            source=ASQUITH_NEUTRON)
    if log_ref is None:
        return Refusal(
            reason="the neutron curve's matrix reference was not declared, and no "
                   "default is sourced: asquith#19 says the reference is 'usually "
                   "either limestone or sandstone, depending on the geologic "
                   "environment', which is not a default",
            needed=("log_matrix from the log heading, the ~P section, or "
                    "mnemonic_normalize (#9)",),
            source=ASQUITH_NEUTRON)
    if litho is None:
        return Refusal(
            reason="the formation's lithology was not declared, so whether any "
                   "correction is needed cannot be determined",
            needed=("formation_lithology for the zone",), source=AAPG_CROSSPLOT)
    if apply_environmental:
        return Refusal(
            reason="environmental corrections (borehole size, mud weight, salinity, "
                   "standoff, temperature) are chartbook-only and tool-specific; no "
                   "chartbook is held in this corpus",
            needed=(f"the environmental correction charts for "
                    f"{tool_vendor or 'the logging vendor'} "
                    f"{tool_model or '(tool model not stated)'}",),
            source=AAPG_CROSSPLOT)

    if log_ref == litho:
        flags = [
            "no environmental correction applied and none is available in this corpus",
            "no shale correction applied; clay-bound hydrogen makes the neutron read "
            "above true porosity (asquith#19, 'shale effect'), the opposite direction "
            "to gas - correcting it is neutron_shale_correct (asquith#75, Eq. 10.39), "
            "which needs V_shale and NPHI_shale and neither has a default",
            "gas drives neutron porosity below true porosity (asquith#19) - run "
            "gas_effect_flag (#30) before treating this as formation porosity",
        ]
        for value, what in ((log_matrix_source, "the log matrix reference"),
                            (lithology_source, "the formation lithology")):
            flags.extend(_asserted(value, what))
        return Quantity(
            float(phi_n), unit_key,
            "neutron porosity read directly; log matrix reference matches formation "
            "lithology (aapg#0; asquith#19)", AAPG_CROSSPLOT,
            inputs={"phi_n": float(phi_n), "depth_ft": depth_ft},
            assumptions={"log_matrix": log_ref, "log_matrix_source": log_matrix_source,
                         "formation_lithology": litho,
                         "lithology_source": lithology_source,
                         "correction_applied": "none", "tool_vendor": tool_vendor,
                         "tool_model": tool_model, "unit": unit_key},
            flags=tuple(flags))

    if fallback == "crossplot":
        if phi_d is None or phi_d_matrix is None:
            return Refusal(
                reason="the crossplot fallback needs the density porosity and its "
                       "matrix reference",
                needed=("phi_d", "phi_d_matrix"), source=AAPG_CROSSPLOT)
        got = crossplot_porosity(
            phi_n, phi_d, phi_n_matrix=log_ref, phi_d_matrix=phi_d_matrix,
            formation_lithology=litho, unit=unit_key, form="rms",
            phi_n_matrix_source=log_matrix_source, lithology_source=lithology_source,
            v_shale=v_shale, depth_ft=depth_ft)
        if isinstance(got, Refusal):
            return got
        return Quantity(
            got.value, got.unit, got.method, got.source, inputs=got.inputs,
            assumptions={**got.assumptions, "substituted_for": "chartbook lithology "
                         "correction (#27)"},
            flags=got.flags + (
                "this is the chartbook-free crossplot standing in for a lithology "
                f"correction from {log_ref} to {litho}; it is not that correction, "
                "and the two do not have to agree",))

    if litho == "shale":
        # A lithology chart does not correct for shale and no chart is asked for
        # here. asquith#19's "shale effect" is bound hydrogen counted as pore
        # hydrogen, and the published remedy is an equation, not a chart.
        return Refusal(
            reason=("the formation is shale, and neutron porosity reads above true "
                    "porosity there because the hydrogen in the clay structure and "
                    "in clay-bound water is sensed as porosity (asquith#19, 'shale "
                    "effect'). No lithology chart corrects that: the published "
                    "remedy is NPHIc = NPHI - Vshale x NPHI_shale (asquith#75, "
                    "Eq. 10.39), which is neutron_shale_correct and not this tool. "
                    "Neither Vshale nor NPHI_shale has a default - Asquith's own "
                    "Case Study 5 takes NPHI_shale = 0.4 from a nearby shale pick "
                    "on that well, not from a table"),
            needed=("V_shale for the zone, from vshale (#31)",
                    "NPHI_shale, the neutron porosity read in a nearby shale on "
                    "this same log",
                    "neutron_shale_correct (asquith#75, Eq. 10.39), which is where "
                    "that correction lives"),
            source=ASQUITH_SHALE_CORR)

    return Refusal(
        reason=(f"the curve is referenced to {log_ref} and the formation is {litho}; "
                "correcting between them requires the neutron chartbook for the "
                "specific tool that recorded the curve, and no chartbook is held in "
                "this corpus. asquith#19: 'the responses of different neutron logs "
                "differ from each other (unlike all other logs) and must be "
                "interpreted from the specific chart designed for a specific log'. "
                f"The correction is not small and is not signed one way: Table 4.10 "
                f"(asquith#22) takes NPHI 0.290 limestone units to 0.365 sandstone "
                f"(+{_T410_MAX_SHIFT_PU:.1f} porosity units) but to 0.250 dolomite "
                "(-4.0), and Table 4.11 has a second vendor's chart reading 0.080 "
                "where the right one reads 0.135 on the same 0.160 input - 5.5 "
                "porosity units of disagreement between two charts"),
        needed=("Asquith & Krygowski (2004) Figure 4.6, 'Chart for correcting "
                "Halliburton DSN-II neutron-porosity curve for lithology' - its "
                "caption survives at asquith#27 but the chart is an image and was "
                "not extracted, so it is not held; digitising it is the cheapest "
                "unblock",
                "or Asquith & Krygowski (2004) Figure 4.7, 'Chart for correcting "
                "Schlumberger CNL thermal-neutron curves (NPHI and TNPH) for "
                "lithology' - caption at asquith#27, image likewise not held",
                f"or the vendor chartbook matched to the specific tool for any log "
                f"those two do not cover: "
                f"{tool_vendor or 'the logging vendor'} "
                f"{tool_model or '(tool model not stated)'} - Schlumberger Log "
                "Interpretation Charts (Por-13 family) or the Halliburton / Baker "
                "Atlas equivalent, matched to tool model and mud type",
                "or fallback='crossplot' with phi_d and phi_d_matrix, which "
                "substitutes a different method and says so",
                "or density_porosity (#26) recomputed on the formation matrix"),
        source=AAPG_CROSSPLOT)
