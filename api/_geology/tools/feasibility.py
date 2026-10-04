# 101_analysis_feasibility
# `analysis_feasibility` (#101, group K) — staged for merge into `tools/feasibility.py`.
# ---------------------------------------------------------------------------
"""Which published log analyses this well's curves can actually support.

The gate the catalog calls "probably the most important tool on this list". Its
whole job is to answer *before* any computation is attempted, and the product is
not the verdict but the missing list: "Archie is blocked" is useless to an
operator, "Archie is blocked, it needs porosity, no RHOB / DT / NPHI resolves in
this file" is a work order.

Three decisions in here are not obvious.

**An all-null curve is absent.** A `RHOB` declared in `~C` and null in every row
of `~A` is present to a file lister and absent to a petrophysicist. A gate that
counted it sends the agent down a path with no data, and the failure then
surfaces as a wrong saturation rather than as a missing curve. So it fills no
role — but its mnemonic is still named in the explanation, because "RHOB is
present and entirely null" and "there is no density log" have different fixes.

**Blocked is not a refusal.** This module refuses three times only: an empty
inventory, an inventory nothing in which resolves, and a request for an analysis
the corpus does not describe. Every other negative outcome is a verdict — the
tool working, not declining. The harness treats them differently: a refusal
stops the plan, a block redirects it.

**No mnemonic dictionary lives here.** `mnemonic_normalize` (#9) owns that, and a
second divergent copy is exactly what it exists to prevent. This module maps
*canonical* names to measurement roles and takes #9's output as an argument;
without it, it accepts a raw mnemonic only when it is already canonical, and says
so in a flag. Likewise `curve_inventory` (#3) and `es_curve_identify` (#96) are
arguments, never imports.

Source: Asquith and Krygowski, *Basic Well Log Analysis* (2004), Table 1.2
"Common equations of well-log interpretation" and "Basic information needed in
log interpretation", `01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9`,
pp. 7-10. Four rows Table 1.2 does not carry cite their own anchors below.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .result import Quantity, Range, Refusal  # noqa: F401  (Range re-exported for the module)


# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------
ASQ = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004"

# Table 1.2 "Common equations of well-log interpretation" + "BASIC INFORMATION
# NEEDED IN LOG INTERPRETATION" (Lithology; Formation Temperature). The primary
# anchor: every requirement in this module is read off one of its rows.
TABLE_1_2 = f"{ASQ}#9"

ASQ_SP = f"{ASQ}#12"        # "The spontaneous potential (SP) log ... millivolts (mV)"
ASQ_VSH = f"{ASQ}#15"       # Eq. 3.1 gamma ray index
ASQ_SONIC = f"{ASQ}#16"     # DT, SPHI, "microseconds per foot"
ASQ_DENSITY = f"{ASQ}#18"   # RHOB, DRHO, DPHI
ASQ_NEUTRON = f"{ASQ}#19"   # "liquid-filled porosity (phi_N, PHIN, or NPHI)"
ASQ_ND = f"{ASQ}#20"        # "normally recorded in limestone porosity units"
ASQ_CURVES = f"{ASQ}#11"    # the ILD / ILM / SFLU / LLD / LLS / RXO glossary
ASQ_TRACKS = f"{ASQ}#27"    # "the caliper measures the borehole diameter"
ASQ_RESTAB = f"{ASQ}#30"    # Table 5.1, classification of resistivity logs
ASQ_SHALLOW = f"{ASQ}#32"   # "The shallow-reading laterolog may be either a LL8 or an SFL"
ASQ_MICRO = f"{ASQ}#33"     # the microlog is a poor Rxo estimator
ASQ_RATIO = f"{ASQ}#43"     # Eqs. 7.4 / 7.7, and the porosity-free statement
ASQ_SHALY = f"{ASQ}#50"     # Eq. 7.48 Simandoux

BEG_IES = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#38"
BEG_TIMELINE = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#34"
RT_LONG_NORMAL = "12-vintage-logs/trieste-log-interpretation-ch7-resistivity#1"

# The statement that stops "no porosity log" being treated as fatal.
POROSITY_FREE_STATEMENT = (
    'asquith#43: "from the ratio (R_xo/R_t)/(R_mf/R_w), the geologist can '
    "determine a value for both the moveable hydrocarbon index (S_w/S_xo) and "
    "water saturation by the ratio method without knowing porosity. Therefore, a "
    "geologist can still derive useful formation evaluation log parameters even "
    'though porosity logs are unavailable."'
)

LITHOLOGY_STATEMENT = (
    'asquith#9: "Porosity logs require a lithology or a matrix constant before '
    "the porosity (phi) of the zone can be calculated. The formation factor (F), a "
    "variable used in the Archie water-saturation equation, also varies with "
    'lithology."'
)


# --------------------------------------------------------------------------
# House rules. Neither is in the corpus, so both are arguments, both land in
# `assumptions`, and the degradation rule announces itself in a flag. Same
# treatment `curve_inventory` (#3) gives its gap_factor = 1.5.
# --------------------------------------------------------------------------
DEFAULT_DEGRADED_NULL_FRACTION = 0.5

# Not a house rule: a curve with no samples at all cannot support anything, and
# that needs no threshold.
ALL_NULL_FRACTION = 1.0

STATUS_POSSIBLE = "possible"
STATUS_CONDITIONAL = "conditional"
STATUS_BLOCKED = "blocked"

KIND_CURVE = "curve"
KIND_PRODUCT = "product"
KIND_PARAMETER = "parameter"


# --------------------------------------------------------------------------
# Measurement roles. Canonical curve name -> what it measures.
#
# These are `mnemonic_normalize` (#9) canonical names, not raw mnemonics. The
# raw -> canonical step belongs to #9; duplicating it here would create a second
# answer to the same question.
#
# `ML` is deliberately absent from `rxo`: asquith#33, p. 90 warns the microlog is
# a poor Rxo estimator, and the catalog repeats it on microlog_permeability_flag
# (#38) - "Nothing downstream should consume its resistivities."
# --------------------------------------------------------------------------
ROLE_RT = "rt"
ROLE_RI = "ri"
ROLE_RXO = "rxo"
ROLE_RHO_B = "rho_b"
ROLE_DT = "dt"
ROLE_PHI_N_CURVE = "phi_n_curve"
ROLE_PHI_D_CURVE = "phi_d_curve"
ROLE_PHI_S_CURVE = "phi_s_curve"
ROLE_GR = "gr"
ROLE_SP = "sp"
ROLE_CALI = "cali"

ROLE_LABEL: dict[str, str] = {
    ROLE_RT: "true resistivity of the uninvaded zone (R_t)",
    ROLE_RI: "resistivity of the invaded zone (R_i)",
    ROLE_RXO: "resistivity of the flushed zone (R_xo)",
    ROLE_RHO_B: "formation bulk density (rho_bulk)",
    ROLE_DT: "interval transit time (delta t)",
    ROLE_PHI_N_CURVE: "recorded neutron porosity (phi_N)",
    ROLE_PHI_D_CURVE: "recorded density porosity (phi_D)",
    ROLE_PHI_S_CURVE: "recorded sonic porosity (phi_S)",
    ROLE_GR: "natural gamma radioactivity (GR)",
    ROLE_SP: "spontaneous potential (SP)",
    ROLE_CALI: "borehole diameter (caliper)",
}

# The R_i / R_xo split, which the corpus does not settle.
#
# The SYSTEMATIC device classification puts the dual induction's shallow focused
# curve in the INVADED zone, twice, in one segment:
#
#   asquith#32, prose: the dual induction "also has a third resistivity curve, a
#   shallow-reading, focused, laterolog-type measurement that is similar in depth
#   of investigation to the short normal. The shallow-reading laterolog may be
#   either a laterolog-8 (LL8) or a spherically focused log (SFL)."
#
#   asquith#32, symbol list: "R_i = resistivity tool measuring in the invaded
#   zone, usually laterolog-8 or spherically focused log"
#
# and asquith#33 reserves R_xo for the pad-type micro devices: "The microlaterolog
# (MLL), the proximity log (PL) ... and the microspherically focused log (MSFL)
# are pad-type, focused, electrode logs designed to measure the resistivity in the
# flushed zone (R_xo)."
#
# Against that, two VARIABLE GLOSSES read a shallow focused curve as R_xo:
# asquith#11's SFLU caption, and asquith#43's nomenclature inside the ratio
# equation ("R_xo = formation's shallow resistivity from a measurement such as
# laterolog-8, microspherically focused log, or microlaterolog").
#
# The corpus is genuinely split, so neither reading is asserted. SFL / LL8 / RFOC
# fill R_i unconditionally - that is what the systematic text says, and it is the
# reading that keeps them consistent with SN, the curve asquith#32 calls their
# equal in depth of investigation - and they fill R_xo only CONDITIONALLY, so a
# verdict reaching R_xo through one of them comes back `conditional` with the
# conflict attached. asquith#43 licenses the ratio method reaching them, so they
# must not become unusable; the systematic text denies an unconditional R_xo, so
# the tool must stop claiming one.
SHALLOW_FOCUSED_RXO_CONDITION = (
    "R_xo here is a shallow focused laterolog-type curve, and the corpus does not agree that "
    "it reads the flushed zone. asquith#32 puts it in the INVADED zone twice - the dual "
    'induction\'s third curve is "similar in depth of investigation to the short normal", and '
    'its symbol list reads "R_i = resistivity tool measuring in the invaded zone, usually '
    'laterolog-8 or spherically focused log" - and asquith#33 reserves R_xo for the pad-type '
    "micro devices (MLL, PL, MSFL). Only asquith#11's SFLU caption and asquith#43's "
    "ratio-equation gloss read it as R_xo. Clear this by using a pad-type micro device "
    "(MSFL/MLL/PL/RXO) where one was run, or accept an R_xo that may be reading the invaded "
    "zone and will bias S_xo and the ratio method."
)

# canonical name -> claims of (role, basis sentence, condition or None). A curve
# may claim more than one role; each claim carries its own source sentence.
ROLE_BY_CANONICAL: dict[str, tuple[tuple[str, str, str | None], ...]] = {
    "ILD": ((ROLE_RT, 'asquith#11: "Log curve ILD: Deep induction log resistivity curves '
                      'usually measure true formation resistivity (R_t)."', None),),
    "LLD": ((ROLE_RT, 'asquith#11: "Log curve LLD: Deep laterolog resistivity curves usually '
                      'measure true formation resistivity (R_t)."', None),),
    "LN":  ((ROLE_RT, "asquith#30 Table 5.1 places the 64-inch Long Normal (LN) in the "
                      "uninvaded-zone column.", None),),
    "ILM": ((ROLE_RI, 'asquith#11: "Log curve ILM: Medium induction log resistivity curves '
                      'measure the resistivity of the invaded zone (R_i)."', None),),
    "LLS": ((ROLE_RI, 'asquith#11: "Log curve LLS: Shallow laterolog resistivity curves '
                      'measure the resistivity in the invaded zone (R_i)."', None),),
    "SN":  ((ROLE_RI, "asquith#30 Table 5.1 places the 16-inch Short Normal (SN) in the "
                      "invaded-zone column.", None),),
    # ---- pad-type micro devices: R_xo unconditionally, asquith#33 -------
    "RXO": ((ROLE_RXO, 'asquith#11: "Log curve RXO: Microresistivity curves measure the '
                       'resistivity of the flushed zone (R_xo)."', None),),
    "MSFL": ((ROLE_RXO, 'asquith#33: the microspherically focused log is a "pad-type, focused, '
                        'electrode log designed to measure the resistivity in the flushed zone '
                        '(R_xo)", and tools of its design "seem to generally be very good at '
                        'determining flushed-zone resistivity (R_xo)".', None),),
    "MLL": ((ROLE_RXO, 'asquith#33: the microlaterolog is a "pad-type, focused, electrode log '
                       'designed to measure the resistivity in the flushed zone (R_xo)".', None),),
    "PL":  ((ROLE_RXO, 'asquith#33: the proximity log is a "pad-type, focused, electrode log '
                       'designed to measure the resistivity in the flushed zone (R_xo)".', None),),
    # ---- shallow focused laterolog-type: R_i asserted, R_xo conditional --
    "SFL": ((ROLE_RI, 'asquith#32: "R_i = resistivity tool measuring in the invaded zone, '
                      'usually laterolog-8 or spherically focused log", and the dual '
                      'induction\'s shallow focused curve is "similar in depth of investigation '
                      'to the short normal".', None),
            (ROLE_RXO, 'asquith#11: "Log curve SFLU: Spherically focused log resistivity curves '
                       'measure the resistivity of the flushed zone (R_xo)"; asquith#43 names '
                       "the same device class in its R_xo gloss.", SHALLOW_FOCUSED_RXO_CONDITION)),
    "LL8": ((ROLE_RI, 'asquith#32: "R_i = resistivity tool measuring in the invaded zone, '
                      'usually laterolog-8 or spherically focused log"; asquith#30 Table 5.1 '
                      "places Laterolog-8 in the invaded-zone column.", None),
            (ROLE_RXO, 'asquith#43: "R_xo = formation\'s shallow resistivity from a measurement '
                       'such as laterolog-8, microspherically focused log, or microlaterolog."',
             SHALLOW_FOCUSED_RXO_CONDITION)),
    "RFOC": ((ROLE_RI, "mnemonic_normalize (#9), OWNED: RFOC is the third curve of a dual "
                       'induction, which asquith#32 calls "similar in depth of investigation to '
                       'the short normal" and lists under R_i.', None),
             (ROLE_RXO, "mnemonic_normalize (#9) leaves RFOC's zone deliberately undetermined - "
                        '"Consumers must treat the zone as undetermined rather than assume '
                        'R_xo" - so it reaches R_xo only under the same unresolved conflict as '
                        "SFL and LL8.", SHALLOW_FOCUSED_RXO_CONDITION)),
    # ---- everything else -------------------------------------------------
    "RHOB": ((ROLE_RHO_B, 'asquith#18: "the bulk density (rho_b or RHOB)".', None),),
    "DT":  ((ROLE_DT, 'asquith#16: "interval transit time (delta t, delta t, or DT)".', None),),
    "NPHI": ((ROLE_PHI_N_CURVE, 'asquith#19: "the neutron log measures liquid-filled porosity '
                                '(phi_N, PHIN, or NPHI)".', None),),
    "DPHI": ((ROLE_PHI_D_CURVE, 'asquith#18: "A density-derived porosity curve (DPHI) is '
                                'sometimes present in tracks 2 and 3".', None),),
    "SPHI": ((ROLE_PHI_S_CURVE, 'asquith#16: "A sonic-derived porosity curve (SPHI) is sometimes '
                                'displayed in tracks 2 and 3, along with the DT curve."', None),),
    "GR":  ((ROLE_GR, 'asquith#15: "The gamma ray log (GR) ... ranges from 0 to 150 API gamma '
                      'ray units."', None),),
    "SP":  ((ROLE_SP, 'asquith#12: "The spontaneous potential (SP) log ... It is measured in '
                      'millivolts (mV)."', None),),
    "CALI": ((ROLE_CALI, 'asquith#20: "a caliper (CALI) and gamma ray (GR) in track 1".', None),),
}

# Canonical curves that are real measurements but appear in no row of Table 1.2
# and in none of the four secondary rows. Reported apart from `unidentified`,
# because the two have different fixes: an unidentified mnemonic wants a sourced
# entry in `mnemonic_normalize` (#9), and one of these wants nothing at all.
NO_ANALYSIS_ROLE: dict[str, str] = {
    "DRHO": 'asquith#18: "A correction curve (DRHO in g/cm3 or Kg/m3)" - a quality-control '
            "indicator, not a formation measurement. It gates density porosity in hole_quality "
            "(#25) at DRHO > 0.20 g/cm3; it is not rho_bulk and cannot stand in for it.",
    "PEF": 'asquith#18: "the photoelectric-effect measurement (P_e, PE, or PEF)" - a lithology '
           "indicator. Table 1.2 has no PEF row; it informs the `lithology` parameter rather "
           "than filling a requirement.",
    "ML": "asquith#33, p. 90: the microlog is a poor R_xo estimator, so it deliberately does "
          "NOT fill the flushed-zone role - see the module header and "
          "microlog_permeability_flag (#38).",
    "DEPT": "the depth index.",
}

# `es_curve_identify` (#96) role -> (role here, condition, basis). The ES layer
# exists because #96 resolves spelling variants (LN64, LGN, SHN) that nothing in
# this module does.
ROLE_BY_ES_ROLE: dict[str, tuple[str, str | None, str]] = {
    "sp": (ROLE_SP, None,
           "es_curve_identify (#96) classified this curve as the ES spontaneous potential."),
    "short_normal_16in": (
        ROLE_RI, None,
        "es_curve_identify (#96): 16-inch short normal; asquith#30 Table 5.1 puts it in the "
        "invaded-zone column."),
    "long_normal_64in": (
        ROLE_RT,
        "R_t from an ES long normal must go through rt_from_long_normal (#98), a three-branch "
        "rule keyed to R_16in/R_m that REFUSES above 50 - which is the high-resistivity case "
        "most worth logging.",
        "es_curve_identify (#96): 64-inch long normal; asquith#30 Table 5.1, uninvaded zone."),
    "lateral_18ft8in": (
        ROLE_RT,
        "the 18-ft 8-in lateral is asymmetric and reads close to true resistivity only in sands "
        "at least five times the tool's measure length (beg#34); departure_correction (#97) "
        "applies before this value is R_t.",
        "es_curve_identify (#96): 18-ft 8-in lateral."),
}


# --------------------------------------------------------------------------
# Parameters. Not curves: header facts, lab facts and picks the tool cannot see.
# --------------------------------------------------------------------------
PARAMETER_NOTE: dict[str, str] = {
    "lithology": LITHOLOGY_STATEMENT,
    "rho_matrix": "Table 1.2 phi_Density; supplied directly or via `lithology` "
                  "(matrix_constant_lookup #24).",
    "rho_fluid": "Table 1.2 phi_Density; supplied directly or via `lithology`.",
    "dt_matrix": "Table 1.2 phi_Sonic; supplied directly or via `lithology`.",
    "dt_fluid": "Table 1.2 phi_Sonic (Wyllie only); supplied directly or via `lithology`.",
    "a": "Table 1.2 F = a/phi^m; the tortuosity factor. Table 1.2 keys it to lithology "
         "(1.0 carbonates, 0.81 consolidated sandstones, 0.62 unconsolidated sands).",
    "m": "Table 1.2 F = a/phi^m; the cementation exponent, keyed to lithology.",
    "n": "Table 1.2 S_w = ((a x R_w)/(R_t x phi^m))^(1/n); the saturation exponent.",
    "rw": 'asquith#9: R_w is "obtained by analysis of water samples from a drill stem test, a '
          "water-producing well, or from a catalog of water resistivity values ... also "
          'determined from the spontaneous-potential log ... or ... by the apparent water '
          'resistivity (R_wa) method".',
    "rmf": 'asquith#9: "Resistivity values of the drilling mud (R_m), mud filtrate (R_mf), mud '
           "cake (R_mc), and the temperatures at which they are measured are recorded on a "
           'log\'s header." A header fact, not a curve.',
    "formation_temperature": 'asquith#9: resistivities "vary with temperature", so R_m, R_mf and '
                             "R_w must be corrected to T_f before use.",
    "bht": 'asquith#9, formation temperature is "determined by knowing: formation depth, bottom '
           'hole temperature (BHT), total depth of the well (TD), surface temperature".',
    "total_depth": "asquith#9, one of the four named inputs to formation temperature.",
    "surface_temperature": "asquith#9, one of the four named inputs to formation temperature.",
    "formation_depth": "asquith#9, one of the four named inputs to formation temperature.",
    "gr_clean": "asquith#15 Eq. 3.1, GR_min - the clean (non-shale) pick. A judgment read off "
                "the log, not a measurement.",
    "gr_shale": "asquith#15 Eq. 3.1, GR_max - the shale pick.",
    "r_sh": "asquith#50 Eq. 7.48 Simandoux, the V_shale/R_sh term; resistivity of the adjacent "
            "shale.",
    "sw_irr": "Table 1.2 K_e = (250 x (phi^3/S_wirr))^2; irreducible water saturation. No "
              "logging tool measures it.",
}

# A parameter in this map is also satisfied by `lithology`, per LITHOLOGY_STATEMENT.
VIA_LITHOLOGY: frozenset[str] = frozenset(
    {"rho_matrix", "rho_fluid", "dt_matrix", "dt_fluid", "a", "m"}
)


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------
PROD_POROSITY = "porosity"
PROD_PHI_N = "phi_n"
PROD_PHI_D = "phi_d"
PROD_F = "formation_factor"
PROD_RW = "rw"
PROD_SW = "sw"
PROD_SXO = "sxo"
PROD_VSHALE = "vshale"
PROD_BVW = "bvw"
PROD_PERMEABILITY = "permeability"
PROD_MHI = "moveable_hydrocarbon_index"
PROD_TF = "formation_temperature"

PRODUCT_LABEL: dict[str, str] = {
    PROD_POROSITY: "porosity (phi)",
    PROD_PHI_N: "neutron porosity (phi_N)",
    PROD_PHI_D: "density porosity (phi_D)",
    PROD_F: "formation factor (F)",
    PROD_RW: "formation water resistivity (R_w)",
    PROD_SW: "water saturation of the uninvaded zone (S_w)",
    PROD_SXO: "water saturation of the flushed zone (S_xo)",
    PROD_VSHALE: "shale volume (V_shale)",
    PROD_BVW: "bulk volume water (BVW)",
    PROD_PERMEABILITY: "estimated permeability (K_e)",
    PROD_MHI: "moveable hydrocarbon index (S_w/S_xo)",
    PROD_TF: "formation temperature (T_f)",
}

# A recorded porosity curve is itself a product - but conditionally. The matrix
# constant it was computed against is not in the curve, and Table 1.2 shows the
# answer depends on it.
MATRIX_REFERENCE_CONDITION_ND = (
    'asquith#20: neutron porosity is "normally recorded in limestone porosity units", so a '
    "recorded NPHI is porosity only on its own matrix reference; neutron_porosity_correct (#27) "
    "reads it directly where the log lithology matches the formation and otherwise needs a "
    "vendor chartbook."
)
MATRIX_REFERENCE_CONDITION_D = (
    "the matrix density used to compute the recorded DPHI is not carried in the curve; Table 1.2 "
    "phi_Density = (rho_matrix - rho_bulk)/(rho_matrix - rho_fluid) shows the answer depends on "
    "it. Confirm it from ~P or the log header, or recompute from RHOB."
)
MATRIX_REFERENCE_CONDITION_S = (
    "the matrix travel time used to compute the recorded SPHI is not carried in the curve; "
    "Table 1.2 phi_Sonic depends on delta_t_matrix. Confirm it from ~P, or recompute from DT."
)

# role -> (product, condition or None, basis)
PRODUCT_FROM_ROLE: dict[str, tuple[str, str | None, str]] = {
    ROLE_PHI_N_CURVE: (PROD_PHI_N, MATRIX_REFERENCE_CONDITION_ND,
                       "the recorded NPHI curve is phi_N (asquith#19)."),
    ROLE_PHI_D_CURVE: (PROD_PHI_D, MATRIX_REFERENCE_CONDITION_D,
                       "the recorded DPHI curve is phi_D (asquith#18)."),
}
# roles that additionally stand in for porosity itself, each conditionally
POROSITY_FROM_ROLE: dict[str, tuple[str, str]] = {
    ROLE_PHI_D_CURVE: (MATRIX_REFERENCE_CONDITION_D, ASQ_DENSITY),
    ROLE_PHI_S_CURVE: (MATRIX_REFERENCE_CONDITION_S, ASQ_SONIC),
    ROLE_PHI_N_CURVE: (MATRIX_REFERENCE_CONDITION_ND, ASQ_ND),
}


# --------------------------------------------------------------------------
# Return shapes
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Requirement:
    """One input an analysis needs, and every way it can be met."""

    name: str
    kind: str                       # curve | product | parameter
    alternatives: tuple[str, ...]   # roles, products or parameter names - any one suffices
    source: str
    via_lithology: bool = False

    def describe(self) -> str:
        if self.kind == KIND_CURVE:
            labels = " or ".join(ROLE_LABEL.get(a, a) for a in self.alternatives)
            return f"{self.name}: a curve reading {labels}"
        if self.kind == KIND_PRODUCT:
            return f"{self.name}: {PRODUCT_LABEL.get(self.name, self.name)}"
        extra = " (or supply `lithology`)" if self.via_lithology else ""
        return f"{self.name}: parameter{extra}"


@dataclass(frozen=True)
class Unmet:
    """One unsatisfied requirement, with what would satisfy it. The product."""

    requirement: Requirement
    why: str
    candidates_present_but_unusable: tuple[str, ...] = ()
    producers_blocked: tuple[str, ...] = ()
    root_causes: tuple[str, ...] = ()

    def __repr__(self) -> str:  # keeps test failures readable
        return f"Unmet({self.requirement.name!r}: {self.why})"


@dataclass(frozen=True)
class AnalysisVerdict:
    analysis: str
    title: str            # the caption Table 1.2 gives the row
    equation: str         # the row, quoted
    status: str
    produces: str
    requires: tuple[Requirement, ...]
    satisfied_by: dict[str, str]
    missing: tuple[Unmet, ...]
    conditions: tuple[str, ...]   # file-specific, clearable; these set `conditional`
    caveats: tuple[str, ...]      # method caveats; reported, never change status
    warnings: tuple[str, ...]
    degraded: bool
    source: str

    @property
    def possible(self) -> bool:
        """True for `possible` and `conditional` - i.e. the inputs exist."""
        return self.status in (STATUS_POSSIBLE, STATUS_CONDITIONAL)

    def __repr__(self) -> str:
        deg = " degraded" if self.degraded else ""
        return f"AnalysisVerdict({self.analysis} -> {self.status}{deg})"


@dataclass(frozen=True)
class FeasibilityReport:
    verdicts: tuple[AnalysisVerdict, ...]
    possible: tuple[str, ...]
    conditional: tuple[str, ...]
    blocked: tuple[str, ...]
    roles: dict[str, tuple[str, ...]]
    role_basis: dict[str, str]
    unusable_curves: dict[str, str]
    unidentified: tuple[str, ...]
    known_no_role: dict[str, str]
    parameters_supplied: tuple[str, ...]
    parameters_missing: tuple[str, ...]
    coverage: Quantity
    source: str = TABLE_1_2
    flags: tuple[str, ...] = ()
    assumptions: dict[str, Any] = field(default_factory=dict)

    def verdict(self, analysis: str) -> AnalysisVerdict:
        for v in self.verdicts:
            if v.analysis == analysis:
                return v
        raise KeyError(f"{analysis!r} was not requested; asked for {self.requested()!r}")

    def requested(self) -> tuple[str, ...]:
        return tuple(v.analysis for v in self.verdicts)

    def why(self, analysis: str) -> str:
        """The missing list, rendered for an operator. This is the deliverable."""
        v = self.verdict(analysis)
        head = f"{v.analysis} ({v.title}) - {v.status}"
        if v.status != STATUS_BLOCKED:
            lines = [head, f"    equation: {v.equation}"]
            lines += [f"    condition: {c}" for c in v.conditions]
            lines += [f"    caveat: {c}" for c in v.caveats]
            lines += [f"    warning: {w}" for w in v.warnings]
            return "\n".join(lines)
        lines = [head, f"    equation: {v.equation}", "    missing:"]
        for unmet in v.missing:
            lines.append(f"      - {unmet.requirement.describe()}")
            lines.append(f"        {unmet.why}")
            if unmet.candidates_present_but_unusable:
                lines.append(
                    "        present but unusable: "
                    + ", ".join(unmet.candidates_present_but_unusable)
                )
            if unmet.producers_blocked:
                lines.append("        produced by (all blocked): "
                             + ", ".join(unmet.producers_blocked))
            if unmet.root_causes:
                lines.append("        supply any of: " + ", ".join(unmet.root_causes))
        return "\n".join(lines)


# --------------------------------------------------------------------------
# The rule table. One row per published analysis; each row's requirements are
# read off the right-hand side of its equation, quoted in `equation`.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class AnalysisRule:
    analysis: str
    title: str
    equation: str
    produces: str
    requires: tuple[Requirement, ...]
    source: str
    # Method caveats: true of the equation itself, whatever this file holds. They are
    # reported, but they never change `status` - status is about the inventory. A caveat
    # the caller cannot clear by finding a curve is not a gate.
    caveats: tuple[str, ...] = ()
    note: str = ""


def _curve_req(name: str, roles: tuple[str, ...], source: str) -> Requirement:
    return Requirement(name=name, kind=KIND_CURVE, alternatives=roles, source=source)


def _param_req(name: str, source: str) -> Requirement:
    return Requirement(
        name=name, kind=KIND_PARAMETER, alternatives=(name,), source=source,
        via_lithology=name in VIA_LITHOLOGY,
    )


def _product_req(name: str, source: str) -> Requirement:
    return Requirement(name=name, kind=KIND_PRODUCT, alternatives=(name,), source=source)


RULES: tuple[AnalysisRule, ...] = (
    # ---- Table 1.2, "Porosity, phi" -------------------------------------
    AnalysisRule(
        analysis="sonic_porosity_wyllie",
        title="Sonic log porosity (Wyllie time-average equation)",
        equation="phi_Sonic = (delta_t_log - delta_t_matrix)/(delta_t_fluid - delta_t_matrix)",
        produces=PROD_POROSITY,
        requires=(
            _curve_req("delta_t_log", (ROLE_DT,), ASQ_SONIC),
            _param_req("dt_matrix", TABLE_1_2),
            _param_req("dt_fluid", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    AnalysisRule(
        analysis="sonic_porosity_rhg",
        title="Sonic log porosity (Raymer-Hunt-Gardner equation)",
        equation="phi_Sonic = 5/8 x ((delta_t_log - delta_t_matrix)/delta_t_log)",
        produces=PROD_POROSITY,
        requires=(
            _curve_req("delta_t_log", (ROLE_DT,), ASQ_SONIC),
            _param_req("dt_matrix", TABLE_1_2),
        ),
        source=TABLE_1_2,
        note="Table 1.2 prints Wyllie and RHG side by side with no preference; the choice is "
             "the caller's (spec open question 6).",
    ),
    AnalysisRule(
        analysis="density_porosity",
        title="Density log porosity",
        equation="phi_Density = (rho_matrix - rho_bulk(log))/(rho_matrix - rho_fluid)",
        produces=PROD_POROSITY,
        requires=(
            _curve_req("rho_bulk", (ROLE_RHO_B,), ASQ_DENSITY),
            _param_req("rho_matrix", TABLE_1_2),
            _param_req("rho_fluid", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    AnalysisRule(
        analysis="neutron_density_gas_porosity",
        title="Porosity in a gas zone from neutron and density",
        equation="phi_NDgas = sqrt((phi_N^2 + phi_D^2)/2)",
        produces=PROD_POROSITY,
        requires=(
            _product_req(PROD_PHI_N, ASQ_NEUTRON),
            _product_req(PROD_PHI_D, ASQ_DENSITY),
        ),
        source=TABLE_1_2,
    ),
    # ---- Table 1.2, "Formation factor, F" -------------------------------
    AnalysisRule(
        analysis="formation_factor",
        title="Formation factor (general form; 1.0/phi^2.0 carbonates, 0.81/phi^2.0 "
              "consolidated sandstones, 0.62/phi^2.15 unconsolidated sands)",
        equation="F = a/phi^m",
        produces=PROD_F,
        requires=(
            _product_req(PROD_POROSITY, TABLE_1_2),
            _param_req("a", TABLE_1_2),
            _param_req("m", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    # ---- Table 1.2, "Formation-water resistivity" -----------------------
    AnalysisRule(
        analysis="rw_from_sp",
        title="First-order approximation of R_w from the SP",
        equation="R_w = 10^((K x log(R_mf) + SP)/K)   [SSP = -K x log(R_mf/R_w)]",
        produces=PROD_RW,
        requires=(
            _curve_req("SP", (ROLE_SP,), ASQ_SP),
            _param_req("rmf", TABLE_1_2),
            _product_req(PROD_TF, TABLE_1_2),
        ),
        source=TABLE_1_2,
        caveats=(
            'Table 1.2 captions this row "First-order approximation of R_w from the SP". The '
            "published procedure (rw_from_sp #33, asquith#14) returns R_we and additionally "
            "needs a bed-thickness correction (bed thickness, short-normal R_i, R_m at "
            "formation temperature) before R_w. It is invalid in oil-based mud and air-filled "
            "holes, and is suppressed by thin beds, shaliness and hydrocarbons.",
        ),
    ),
    # ---- Table 1.2, "Water saturation" ----------------------------------
    AnalysisRule(
        analysis="archie_sw",
        title="Water saturation in the uninvaded zone (Archie)",
        equation="S_w = ((a x R_w)/(R_t x phi^m))^(1/n)",
        produces=PROD_SW,
        requires=(
            _curve_req("R_t", (ROLE_RT,), ASQ_CURVES),
            _product_req(PROD_POROSITY, TABLE_1_2),
            _product_req(PROD_RW, TABLE_1_2),
            _param_req("a", TABLE_1_2),
            _param_req("m", TABLE_1_2),
            _param_req("n", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    AnalysisRule(
        analysis="flushed_zone_sw",
        title="Water saturation in the flushed zone",
        equation="S_xo = ((a x R_mf)/(R_xo x phi^m))^(1/n)",
        produces=PROD_SXO,
        requires=(
            _curve_req("R_xo", (ROLE_RXO,), ASQ_RATIO),
            _product_req(PROD_POROSITY, TABLE_1_2),
            _param_req("rmf", TABLE_1_2),
            _param_req("a", TABLE_1_2),
            _param_req("m", TABLE_1_2),
            _param_req("n", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    AnalysisRule(
        analysis="ratio_method_sw",
        title="Water saturation, ratio method",
        equation="S_w = ((R_xo/R_t)/(R_mf/R_w))^0.625",
        produces=PROD_SW,
        requires=(
            _curve_req("R_xo", (ROLE_RXO,), ASQ_RATIO),
            _curve_req("R_t", (ROLE_RT,), ASQ_CURVES),
            _param_req("rmf", TABLE_1_2),
            _product_req(PROD_RW, TABLE_1_2),
        ),
        source=TABLE_1_2,
        note=POROSITY_FREE_STATEMENT,
        caveats=(
            "asquith#43 Eq. 7.5: the ratio method substitutes S_xo = S_w^(1/5), which holds in "
            '"formations with moderate invasion and average residual hydrocarbon saturation"; '
            "the cementation exponent n is assumed 2.0.",
        ),
    ),
    AnalysisRule(
        analysis="moveable_hydrocarbon_index",
        title="Moveable hydrocarbon index by the ratio method (asquith#43 Eq. 7.4)",
        equation="S_w/S_xo = ((R_xo/R_t)/(R_mf/R_w))^(1/2)",
        produces=PROD_MHI,
        requires=(
            _curve_req("R_xo", (ROLE_RXO,), ASQ_RATIO),
            _curve_req("R_t", (ROLE_RT,), ASQ_CURVES),
            _param_req("rmf", ASQ_RATIO),
            _product_req(PROD_RW, ASQ_RATIO),
        ),
        source=ASQ_RATIO,
        note=POROSITY_FREE_STATEMENT,
        caveats=(
            "asquith#43: the cementation exponent n is assumed 2.0. A ratio >= 1.0 means "
            "hydrocarbons were not moved during invasion; moveable hydrocarbons are indicated "
            "below 0.7 for sandstones and 0.6 for carbonates (Schlumberger, 1972).",
        ),
    ),
    # ---- Table 1.2, "Bulk volume water" ---------------------------------
    AnalysisRule(
        analysis="bulk_volume_water",
        title="Bulk volume water",
        equation="BVW = phi x S_w",
        produces=PROD_BVW,
        requires=(
            _product_req(PROD_POROSITY, TABLE_1_2),
            _product_req(PROD_SW, TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    # ---- Table 1.2, "Permeability (estimated)" --------------------------
    AnalysisRule(
        analysis="permeability_oil",
        title="Permeability in millidarcys, oil reservoir",
        equation="K_e = (250 x (phi^3/S_wirr))^2",
        produces=PROD_PERMEABILITY,
        requires=(
            _product_req(PROD_POROSITY, TABLE_1_2),
            _param_req("sw_irr", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    AnalysisRule(
        analysis="permeability_gas",
        title="Permeability in millidarcys, gas reservoir",
        equation="K_e = (79 x (phi^3/S_wirr))^2",
        produces=PROD_PERMEABILITY,
        requires=(
            _product_req(PROD_POROSITY, TABLE_1_2),
            _param_req("sw_irr", TABLE_1_2),
        ),
        source=TABLE_1_2,
    ),
    # ---- rows Table 1.2 does not carry, each with its own anchor --------
    AnalysisRule(
        analysis="vshale_gr",
        title="Shale volume from the gamma ray index (asquith#15 Eq. 3.1)",
        equation="I_GR = (GR_log - GR_min)/(GR_max - GR_min);  V_shale = I_GR (linear)",
        produces=PROD_VSHALE,
        requires=(
            _curve_req("GR_log", (ROLE_GR,), ASQ_VSH),
            _param_req("gr_clean", ASQ_VSH),
            _param_req("gr_shale", ASQ_VSH),
        ),
        source=ASQ_VSH,
        caveats=(
            'asquith#15: "For a first-order estimation of shale volume, the linear response, '
            'where V_shale = I_GR, should be used." The nonlinear (Larionov, Steiber, Clavier) '
            "variants are area- or age-specific and "
            '"all nonlinear relationships are more optimistic".',
        ),
    ),
    AnalysisRule(
        analysis="shaly_sand_sw_simandoux",
        title="Shaly-sand water saturation, Simandoux 1963 (asquith#50 Eq. 7.48)",
        equation="S_w = (0.4 x R_w/phi^2) x [sqrt((V_shale/R_sh)^2 + 5 x phi^2/(R_t x R_w)) "
                 "- V_shale/R_sh]",
        produces=PROD_SW,
        requires=(
            _curve_req("R_t", (ROLE_RT,), ASQ_CURVES),
            _product_req(PROD_POROSITY, ASQ_SHALY),
            _product_req(PROD_VSHALE, ASQ_SHALY),
            _product_req(PROD_RW, ASQ_SHALY),
            _param_req("r_sh", ASQ_SHALY),
        ),
        source=ASQ_SHALY,
        caveats=(
            'asquith#50: the porosity entering a shaly-sand equation is the shale-corrected '
            'porosity ("After the shale-corrected porosity has been determined, the water '
            'saturation can be calculated"), and the source states the methodology for their '
            'use "is beyond the scope of this book".',
        ),
    ),
    AnalysisRule(
        analysis="formation_temperature",
        title="Formation temperature from a linear geothermal gradient",
        equation="y = mx + c, m = (BHT - surface temp)/TD;  T_f = m x formation depth + c",
        produces=PROD_TF,
        requires=(
            _param_req("bht", TABLE_1_2),
            _param_req("total_depth", TABLE_1_2),
            _param_req("surface_temperature", TABLE_1_2),
            _param_req("formation_depth", TABLE_1_2),
        ),
        source=TABLE_1_2,
        caveats=(
            'asquith#9 assumes "a linear geothermal gradient".',
        ),
    ),
)

RULE_BY_ID: dict[str, AnalysisRule] = {r.analysis: r for r in RULES}
KNOWN_ANALYSES: tuple[str, ...] = tuple(r.analysis for r in RULES)
KNOWN_PARAMETERS: frozenset[str] = frozenset(PARAMETER_NOTE)


# --------------------------------------------------------------------------
# Record access: mapping or object, matching curve_inventory's own accessor
# --------------------------------------------------------------------------
_MISSING = object()


def _field(record: Any, name: str, default: Any = _MISSING) -> Any:
    if isinstance(record, Mapping):
        value = record.get(name, _MISSING)
    else:
        value = getattr(record, name, _MISSING)
    if value is _MISSING:
        if default is _MISSING:
            raise TypeError(
                f"curve record is missing required field {name!r}: {record!r}. "
                "analysis_feasibility takes a CurveInventory (#3), its CurveRecords, or "
                "mappings carrying mnemonic/null_fraction/all_null."
            )
        return default
    return value


def _records(inventory: Any) -> list[Any]:
    curves = getattr(inventory, "curves", None)
    if curves is not None:
        return list(curves)
    if isinstance(inventory, Mapping):
        raise TypeError(
            "analysis_feasibility takes a CurveInventory or an iterable of curve records, "
            "not a single mapping; wrap it in a list if it is one curve"
        )
    if not isinstance(inventory, Iterable):
        raise TypeError(
            "inventory must be a CurveInventory or an iterable of curve records, got "
            f"{type(inventory).__name__}"
        )
    return list(inventory)


def _null_fraction(record: Any) -> float | None:
    """The fraction as a plain float. `curve_inventory` reports it as a Quantity."""
    raw = _field(record, "null_fraction", None)
    if raw is None:
        return None
    value = getattr(raw, "value", raw)
    if value is None:
        return None
    return float(value)


def _canonical_key(raw: str) -> str:
    key = str(raw).strip().upper()
    return key.split(":", 1)[0].strip()


# --------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class _Filled:
    """One role filled by one curve, with how and how well."""

    mnemonic: str
    role: str
    basis: str
    resolution: str          # normalized | canonical-exact | es_curve_identify
    null_fraction: float | None
    degraded: bool
    condition: str | None


def _resolve_roles(
    records: list[Any],
    normalized: Mapping[str, Any] | None,
    es_identification: Any,
    degraded_null_fraction: float,
    max_null_fraction: float | None,
) -> tuple[dict[str, list[_Filled]], dict[str, str], list[str], dict[str, str],
             list[str], list[str]]:
    """-> (role->filled, unusable, unidentified, known-but-roleless, index mnemonics, flags)."""
    filled: dict[str, list[_Filled]] = {}
    unusable: dict[str, str] = {}
    unidentified: list[str] = []
    known_no_role: dict[str, str] = {}
    index_mnemonics: list[str] = []
    flags: list[str] = []
    used_fallback = False

    es_roles = _es_role_map(es_identification, records)

    for record in records:
        mnem = str(_field(record, "mnemonic"))
        if bool(_field(record, "is_index", False)):
            index_mnemonics.append(mnem)
            continue

        claims: tuple[tuple[str, str, str | None], ...] = ()
        resolution: str | None = None

        # 1. mnemonic_normalize (#9) output - preferred, it owns the dictionary
        if normalized is not None and mnem in normalized:
            canonical = _field(normalized[mnem], "canonical", None)
            if canonical is not None:
                claims = ROLE_BY_CANONICAL.get(_canonical_key(canonical), ())
                if claims:
                    resolution = "normalized"
        # 2. the raw mnemonic is already canonical
        if not claims:
            claims = ROLE_BY_CANONICAL.get(_canonical_key(mnem), ())
            if claims:
                resolution = "canonical-exact"
                used_fallback = True
        # 3. es_curve_identify (#96), for ES spellings nothing here resolves
        if not claims and mnem in es_roles:
            es_role, es_condition, es_basis = es_roles[mnem]
            claims = ((es_role, es_basis, es_condition),)
            resolution = "es_curve_identify"
        elif claims and mnem in es_roles:
            # The canonical layer already named the roles, but #96 knows this curve is a
            # vintage ES device, and that carries a condition (an ES long normal is not
            # R_t until rt_from_long_normal #98 has run, and #98 refuses above
            # R_16in/R_m = 50). Dropping the condition just because the mnemonic happened
            # to be spelled canonically would silently un-gate the vintage case this tool
            # exists for.
            es_role, es_condition, es_basis = es_roles[mnem]
            if es_condition is not None:
                claims = tuple(
                    (r, f"{b} {es_basis}", es_condition) if r == es_role else (r, b, c)
                    for r, b, c in claims
                )

        if not claims:
            note = NO_ANALYSIS_ROLE.get(_canonical_key(mnem))
            if note is not None:
                known_no_role[mnem] = note
            else:
                unidentified.append(mnem)
            continue

        frac = _null_fraction(record)
        all_null = bool(_field(record, "all_null", False)) or (
            frac is not None and frac >= ALL_NULL_FRACTION
        )
        if all_null:
            unusable[mnem] = (
                "all-null: the curve is declared in ~C and every sample is null, so it is "
                "present to a file lister and absent to an analysis"
            )
            continue
        if max_null_fraction is not None and frac is not None and frac > max_null_fraction:
            unusable[mnem] = (
                f"null-fraction-above-caller-limit: {frac:.4g} > max_null_fraction="
                f"{max_null_fraction:g}"
            )
            continue

        degraded = frac is not None and frac >= degraded_null_fraction
        for role, basis, condition in claims:
            filled.setdefault(role, []).append(
                _Filled(mnemonic=mnem, role=role, basis=basis, resolution=resolution or "",
                        null_fraction=frac, degraded=degraded, condition=condition)
            )

    if used_fallback:
        flags.append(
            "role-resolution-fallback: at least one curve was resolved by exact canonical-name "
            "match rather than from mnemonic_normalize (#9) output. Pass `normalized=` so the "
            "resolution carries #9's own provenance; no fuzzy matching was attempted."
        )
    return filled, unusable, unidentified, known_no_role, index_mnemonics, flags


def _es_role_map(es_identification: Any, records: list[Any]) -> dict[str, tuple[str, str | None, str]]:
    """ES mnemonic -> (role, condition, basis). Empty for None or a Refusal."""
    if es_identification is None or isinstance(es_identification, Refusal):
        return {}
    curves = getattr(es_identification, "curves", None)
    if curves is None:
        raise TypeError(
            "es_identification must be an es_curve_identify (#96) result or its Refusal, got "
            f"{type(es_identification).__name__}"
        )
    inventory_mnemonics = {str(_field(r, "mnemonic")) for r in records}
    out: dict[str, tuple[str, str | None, str]] = {}
    for curve in curves:
        mnem = str(_field(curve, "mnemonic"))
        if mnem not in inventory_mnemonics:
            raise ValueError(
                f"es_identification classifies {mnem!r}, which is not in `inventory`; the two "
                "arguments describe different files"
            )
        es_role = _field(curve, "es_role", None)
        if es_role in ROLE_BY_ES_ROLE:
            out[mnem] = ROLE_BY_ES_ROLE[es_role]
    return out


# --------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------
def analysis_feasibility(
    inventory: Any,
    *,
    analyses: Sequence[str] | None = None,
    normalized: Mapping[str, Any] | None = None,
    parameters: Mapping[str, Any] | None = None,
    es_identification: Any = None,
    degraded_null_fraction: float = DEFAULT_DEGRADED_NULL_FRACTION,
    max_null_fraction: float | None = None,
) -> FeasibilityReport | Refusal:
    """Which published analyses this curve inventory supports, and what blocks the rest.

    `inventory` is `curve_inventory` (#3) output or any iterable of its records.
    `normalized` is `mnemonic_normalize` (#9) output keyed by raw mnemonic.
    `es_identification` is `es_curve_identify` (#96) output, or its `Refusal` - a
    refusal there means "not an ES suite", which is the ordinary modern case and
    is not a refusal here.

    Refuses on: an empty inventory; an inventory in which nothing resolves to a
    measurement role; a requested analysis the corpus does not describe. A
    *blocked* analysis is not a refusal - it is this tool working.
    """
    # ---- programmer-error guards ----------------------------------------
    if not 0.0 <= degraded_null_fraction <= 1.0:
        raise ValueError(
            f"degraded_null_fraction must be a fraction in [0, 1], got {degraded_null_fraction!r}"
        )
    if max_null_fraction is not None and not 0.0 <= max_null_fraction <= 1.0:
        raise ValueError(
            f"max_null_fraction must be a fraction in [0, 1], got {max_null_fraction!r}"
        )
    if parameters is not None and not isinstance(parameters, Mapping):
        raise TypeError("parameters must be a mapping of parameter name to value")
    if analyses is not None and len(analyses) == 0:
        raise ValueError("analyses=() asks for nothing; pass None for the whole table")

    records = _records(inventory)

    # ---- R1: nothing to gate --------------------------------------------
    if not records:
        return Refusal(
            reason="the curve inventory is empty; there are no curves to gate an analysis on",
            needed=("a curve_inventory (#3) result with at least one curve",),
            source=TABLE_1_2,
        )

    # ---- R3: an analysis the corpus does not describe --------------------
    requested = tuple(analyses) if analyses is not None else KNOWN_ANALYSES
    unknown = tuple(a for a in requested if a not in RULE_BY_ID)
    if unknown:
        return Refusal(
            reason=(
                f"no published rule for {', '.join(repr(u) for u in unknown)}. This tool gates "
                "the analyses Asquith and Krygowski Table 1.2 states, plus four rows carrying "
                "their own anchors; the corpus does not describe the requested one, so its "
                "required inputs cannot be asserted"
            ),
            needed=(
                "one of: " + ", ".join(KNOWN_ANALYSES),
                "or a corpus source stating what the requested analysis requires",
            ),
            source=TABLE_1_2,
        )

    filled, unusable, unidentified, known_no_role, index_mnemonics, flags = _resolve_roles(
        records, normalized, es_identification, degraded_null_fraction, max_null_fraction
    )

    # ---- R2: nothing resolves -------------------------------------------
    if not filled and not unusable:
        if unidentified or known_no_role:
            unidentified = unidentified + sorted(known_no_role)
            return Refusal(
                reason=(
                    "no curve in the inventory resolves to a measurement role: "
                    + ", ".join(sorted(unidentified))
                    + ". Every requirement in Table 1.2 is keyed to a measurement, so with "
                    "nothing identified the gate would have to guess what the file holds, and "
                    "a guessed role is a guessed analysis"
                ),
                needed=(
                    "mnemonic_normalize (#9) output for these mnemonics",
                    "or registration of the unknown ones via mnemonic_unknown_register (#10)",
                ),
                source=TABLE_1_2,
            )
        return Refusal(
            reason=(
                "the inventory holds only the depth index ("
                + ", ".join(index_mnemonics)
                + "); there are no measurement curves to gate an analysis on"
            ),
            needed=("an inventory with at least one non-index curve",),
            source=TABLE_1_2,
        )

    supplied = {
        k for k, v in (parameters or {}).items() if v is not None and k in KNOWN_PARAMETERS
    }
    stray = sorted(set(parameters or {}) - KNOWN_PARAMETERS)
    if stray:
        flags.append(
            "unknown parameter names ignored: " + ", ".join(stray)
            + ". Known names: " + ", ".join(sorted(KNOWN_PARAMETERS))
        )

    verdicts = _evaluate(requested, filled, supplied, unusable, degraded_null_fraction)

    # ---- report-level flags ---------------------------------------------
    flags.extend(_report_flags(filled, unusable, verdicts, es_identification))

    possible = tuple(v.analysis for v in verdicts if v.status == STATUS_POSSIBLE)
    conditional = tuple(v.analysis for v in verdicts if v.status == STATUS_CONDITIONAL)
    blocked = tuple(v.analysis for v in verdicts if v.status == STATUS_BLOCKED)

    coverage = Quantity(
        value=len(possible) / len(requested),
        unit="v/v",
        method="count of requested analyses with status 'possible' / count requested; "
               "'conditional' is excluded because it carries a file-specific condition the "
               "caller must still clear. Method caveats do not affect this count",
        source=TABLE_1_2,
        inputs={
            "n_requested": len(requested),
            "n_possible": len(possible),
            "n_conditional": len(conditional),
            "n_blocked": len(blocked),
        },
    )

    return FeasibilityReport(
        verdicts=verdicts,
        possible=possible,
        conditional=conditional,
        blocked=blocked,
        roles={role: tuple(f.mnemonic for f in fs) for role, fs in sorted(filled.items())},
        role_basis={
            f"{f.mnemonic} -> {f.role}":
                f"{ROLE_LABEL[f.role]} - {f.basis} [{f.resolution}]"
                + ("  CONDITIONAL: " + f.condition if f.condition else "")
            for fs in filled.values() for f in fs
        },
        unusable_curves=dict(unusable),
        unidentified=tuple(unidentified),
        known_no_role=dict(known_no_role),
        parameters_supplied=tuple(sorted(supplied)),
        parameters_missing=tuple(sorted(KNOWN_PARAMETERS - supplied)),
        coverage=coverage,
        flags=tuple(flags),
        assumptions={
            "degraded_null_fraction": degraded_null_fraction,
            "degraded_null_fraction_basis": (
                "HOUSE RULE. The corpus supplies no null-fraction threshold and the catalog's "
                "'Thresholds the corpus does not supply' table does not cover one. Only "
                "all-null is a hard block, because 'no data at all' needs no threshold."
            ),
            "max_null_fraction": max_null_fraction,
            "index_curves_skipped": tuple(index_mnemonics),
            "feasibility_interval": (
                "whole logged interval: curve_inventory (#3) reports null fraction over the "
                "whole file, so this gate judges over the whole file. A curve complete over the "
                "operator's zone and null elsewhere reads as degraded; see spec open question 2."
            ),
            "not_evaluated_here": (
                "'possible' means the inputs exist, not that the answer will be good. Bad hole "
                "(hole_quality #25, DRHO > 0.20 g/cm3), tool standoff and thin beds are "
                "downstream gates."
            ),
        },
    )


# --------------------------------------------------------------------------
# Closure over the rule table
# --------------------------------------------------------------------------
def _evaluate(
    requested: tuple[str, ...],
    filled: dict[str, list[_Filled]],
    supplied: set[str],
    unusable: dict[str, str],
    degraded_null_fraction: float,
) -> tuple[AnalysisVerdict, ...]:
    # product -> (by, condition, degraded, degradation warning naming the fraction).
    # The fourth element exists because `degraded=True` without the number is not
    # actionable: on a file that is 90.6% null over its declared frame, the
    # fraction IS the finding. Spec pass 2 requires the analysis be "warned with
    # the fraction", and a verdict satisfied only through products (phi_N and
    # phi_D, say) reaches no curve requirement of its own to raise one.
    products: dict[str, tuple[str, str | None, bool, str | None]] = {}

    # Seed 1: a caller who already has R_w or T_f does not need the analysis that
    # computes it. `rw` and `formation_temperature` are the two names that are both
    # a parameter and a product, and requiring them as parameters would have broken
    # the published chain rw_from_sp -> R_w -> Archie.
    for name in supplied:
        if name in PRODUCT_LABEL:
            products[name] = ("a value supplied by the caller", None, False, None)

    # Seed 2: curves that are themselves a product.
    for role, fs in filled.items():
        best = min(fs, key=lambda f: (f.degraded, f.null_fraction or 0.0))
        warning = _degradation_warning(best)
        if role in PRODUCT_FROM_ROLE:
            product, condition, basis = PRODUCT_FROM_ROLE[role]
            products[product] = (
                f"the recorded {best.mnemonic} curve", condition, best.degraded, warning
            )
        if role in POROSITY_FROM_ROLE:
            condition, _anchor = POROSITY_FROM_ROLE[role]
            if PROD_POROSITY not in products or products[PROD_POROSITY][1] is not None:
                products[PROD_POROSITY] = (
                    f"the recorded {best.mnemonic} curve", condition, best.degraded, warning
                )

    # Fixed point: a product only ever becomes available, and the set is finite.
    resolved: dict[str, dict[str, Any]] = {}
    while True:
        changed = False
        for rule in RULES:
            if rule.analysis in resolved:
                continue
            state = _evaluate_one(rule, filled, supplied, products, resolved, unusable)
            if state["status"] == STATUS_BLOCKED:
                continue
            resolved[rule.analysis] = state
            if rule.produces not in products or (
                products[rule.produces][1] is not None and not state["conditions"]
            ):
                products[rule.produces] = (
                    rule.analysis,
                    state["conditions"][0] if state["conditions"] else None,
                    state["degraded"],
                    state["warnings"][0] if state["warnings"] else None,
                )
            changed = True
        if not changed:
            break

    # Everything still unresolved is blocked; explain it against the final sets.
    for rule in RULES:
        if rule.analysis not in resolved:
            resolved[rule.analysis] = _evaluate_one(
                rule, filled, supplied, products, resolved, unusable
            )

    out: list[AnalysisVerdict] = []
    for analysis in requested:
        rule = RULE_BY_ID[analysis]
        state = resolved[analysis]
        out.append(
            AnalysisVerdict(
                analysis=analysis,
                title=rule.title,
                equation=rule.equation,
                status=state["status"],
                produces=rule.produces,
                requires=rule.requires,
                satisfied_by=state["satisfied_by"],
                missing=tuple(state["missing"]),
                conditions=tuple(state["conditions"]),
                caveats=tuple(state["caveats"]),
                warnings=tuple(state["warnings"]),
                degraded=state["degraded"],
                source=rule.source,
            )
        )
    return tuple(out)


def _degradation_warning(f: _Filled) -> str | None:
    """The null fraction, spelled out. One place, so curve- and product-satisfied
    requirements cannot report degradation two different ways."""
    if not f.degraded or f.null_fraction is None:
        return None
    return f"{f.mnemonic} is {f.null_fraction:.1%} null over the logged interval"


def _evaluate_one(
    rule: AnalysisRule,
    filled: dict[str, list[_Filled]],
    supplied: set[str],
    products: dict[str, tuple[str, str | None, bool, str | None]],
    resolved: dict[str, dict[str, Any]],
    unusable: dict[str, str],
) -> dict[str, Any]:
    satisfied_by: dict[str, str] = {}
    missing: list[Unmet] = []
    conditions: list[str] = []
    warnings: list[str] = []
    degraded = False

    for req in rule.requires:
        if req.kind == KIND_CURVE:
            # Prefer an unconditional fill over a conditional one, then a complete
            # curve over a degraded one. An MSFL must win over an SFL for R_xo:
            # asquith#33 states the pad-type devices are "designed to measure the
            # resistivity in the flushed zone (R_xo)" outright, where the shallow
            # focused curve reaches R_xo only through an unsettled conflict.
            candidates = [f for role in req.alternatives for f in filled.get(role, ())]
            hit = min(
                candidates,
                key=lambda f: (f.condition is not None, f.degraded, f.null_fraction or 0.0),
            ) if candidates else None
            if hit is None:
                missing.append(_unmet_curve(req, unusable))
                continue
            satisfied_by[req.name] = f"curve {hit.mnemonic} ({ROLE_LABEL[hit.role]})"
            if hit.condition:
                conditions.append(hit.condition)
            if hit.degraded:
                degraded = True
                warning = _degradation_warning(hit)
                if warning:
                    warnings.append(warning)
        elif req.kind == KIND_PRODUCT:
            got = products.get(req.name)
            if got is None:
                missing.append(_unmet_product(req, filled, supplied, products, unusable))
                continue
            by, condition, prod_degraded, prod_warning = got
            satisfied_by[req.name] = f"{PRODUCT_LABEL.get(req.name, req.name)} from {by}"
            if condition:
                conditions.append(condition)
            if prod_degraded:
                degraded = True
                if prod_warning:
                    warnings.append(prod_warning)
        else:  # parameter
            if req.name in supplied:
                satisfied_by[req.name] = "parameter supplied by the caller"
            elif req.via_lithology and "lithology" in supplied:
                satisfied_by[req.name] = (
                    "from `lithology` - " + LITHOLOGY_STATEMENT
                )
            else:
                missing.append(_unmet_parameter(req))

    if missing:
        status = STATUS_BLOCKED
    elif conditions:
        status = STATUS_CONDITIONAL
    else:
        status = STATUS_POSSIBLE
    return {
        "status": status,
        "satisfied_by": satisfied_by,
        "missing": missing,
        "conditions": _dedupe(conditions),
        "caveats": _dedupe(rule.caveats),
        "warnings": _dedupe(warnings),
        "degraded": degraded,
    }


def _unmet_curve(req: Requirement, unusable: dict[str, str]) -> Unmet:
    wanted = tuple(
        name for name, claims in ROLE_BY_CANONICAL.items()
        if any(role in req.alternatives for role, _b, _c in claims)
    )
    present_unusable = tuple(
        f"{m} ({why.split(':', 1)[0]})"
        for m, why in unusable.items()
        if _canonical_key(m) in wanted
    )
    labels = " or ".join(ROLE_LABEL.get(a, a) for a in req.alternatives)
    if present_unusable:
        why = (
            f"no usable curve reads {labels}. A curve that would is in the file but cannot be "
            "used - see below; the fix is the tape, not the tool string"
        )
    else:
        why = f"no curve in this file reads {labels}"
    return Unmet(
        requirement=req,
        why=why,
        candidates_present_but_unusable=present_unusable,
        root_causes=tuple(sorted(wanted)),
    )


def _roles_supplying(product: str) -> tuple[str, ...]:
    """Roles that ARE the product: phi_N is the NPHI curve, phi_D is DPHI.

    `PRODUCT_FROM_ROLE` and `POROSITY_FROM_ROLE` are routes no `AnalysisRule`
    carries, so a product reachable only that way used to explain itself with an
    empty missing list - "phi_N is not available" and nothing to supply, which is
    the "Archie is blocked" uselessness this module exists to reject. asquith#19
    gives phi_N as the NPHI curve and asquith#18 gives phi_D as DPHI; those are
    the leaves the operator can act on.
    """
    roles = [r for r, (p, _c, _b) in PRODUCT_FROM_ROLE.items() if p == product]
    if product == PROD_POROSITY:
        roles.extend(POROSITY_FROM_ROLE)
    return tuple(dict.fromkeys(roles))


def _curves_for_roles(roles: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            name
            for name, claims in ROLE_BY_CANONICAL.items()
            if any(role in roles for role, _b, _c in claims)
        )
    )


def _unmet_product(
    req: Requirement,
    filled: dict[str, list[_Filled]],
    supplied: set[str],
    products: dict[str, tuple[str, str | None, bool, str | None]],
    unusable: dict[str, str],
) -> Unmet:
    producers = tuple(r.analysis for r in RULES if r.produces == req.name)
    roots: list[str] = []
    unusable_named: list[str] = []
    for rule in RULES:
        if rule.produces != req.name:
            continue
        for sub in rule.requires:
            if sub.kind == KIND_CURVE:
                sub_unmet = _unmet_curve(sub, unusable)
                roots.extend(sub_unmet.root_causes)
                unusable_named.extend(sub_unmet.candidates_present_but_unusable)
            elif sub.kind == KIND_PARAMETER:
                if sub.name not in supplied and not (
                    sub.via_lithology and "lithology" in supplied
                ):
                    roots.append(f"parameter {sub.name}")
            elif sub.kind == KIND_PRODUCT and sub.name not in products:
                roots.append(f"{PRODUCT_LABEL.get(sub.name, sub.name)}")
                roots.extend(_curves_for_roles(_roles_supplying(sub.name)))
    roots.extend(_curves_for_roles(_roles_supplying(req.name)))
    if req.name in KNOWN_PARAMETERS:
        # `rw` and `formation_temperature` can simply be handed over.
        roots.insert(0, f"parameter {req.name}")
    label = PRODUCT_LABEL.get(req.name, req.name)
    return Unmet(
        requirement=req,
        why=(
            f"{label} is not available: every published route to it is blocked. "
            + (POROSITY_FREE_STATEMENT if req.name == PROD_POROSITY else "")
        ).strip(),
        candidates_present_but_unusable=tuple(dict.fromkeys(unusable_named)),
        producers_blocked=producers,
        root_causes=tuple(dict.fromkeys(roots)),
    )


def _unmet_parameter(req: Requirement) -> Unmet:
    note = PARAMETER_NOTE.get(req.name, "")
    extra = " or supply `lithology`" if req.via_lithology else ""
    return Unmet(
        requirement=req,
        why=f"parameter `{req.name}` was not supplied{extra}. {note}".strip(),
        root_causes=(f"parameter {req.name}",) + (("parameter lithology",) if extra else ()),
    )


def _report_flags(
    filled: dict[str, list[_Filled]],
    unusable: dict[str, str],
    verdicts: tuple[AnalysisVerdict, ...],
    es_identification: Any,
) -> list[str]:
    flags: list[str] = []

    if isinstance(es_identification, Refusal):
        flags.append(
            "es_curve_identify (#96) declined to classify this file as a conventional electrical "
            f"survey: {es_identification.reason} That is the ordinary modern answer and changes "
            "no verdict here."
        )
    elif es_identification is not None:
        suite = _field(es_identification, "suite", "an electrical survey")
        flags.append(
            f"es_curve_identify (#96) classified this file as {suite}. The conventional ES "
            "carries no density, neutron or sonic device, so every Table 1.2 porosity row is "
            "blocked on curves that did not exist when the log was run."
        )

    if unusable:
        flags.append(
            "curves declared in ~C but unusable for feasibility: "
            + "; ".join(f"{m} - {why}" for m, why in sorted(unusable.items()))
        )

    porosity_blocked = any(
        v.analysis == "archie_sw" and v.status == STATUS_BLOCKED
        and any(u.requirement.name == PROD_POROSITY for u in v.missing)
        for v in verdicts
    )
    if porosity_blocked and filled.get(ROLE_SP) and filled.get(ROLE_RT):
        flags.append(
            "porosity is blocked but SP and a deep resistivity are both present. beg#38 "
            "documents a two-curve IES technique that derives lithology, porosity and S_w from "
            '"only two curves: the spontaneous potential (SP) and the deep induction (RILD)" '
            "(Eqs. C-2 to C-7). NO TOOL IN THE CATALOG IMPLEMENTS IT, so it is not offered as a "
            "feasible analysis here - see spec open question 3."
        )

    shallow_focused = {
        f.mnemonic for f in filled.get(ROLE_RXO, ()) if f.condition == SHALLOW_FOCUSED_RXO_CONDITION
    }
    pad_type = {
        f.mnemonic for f in filled.get(ROLE_RXO, ()) if f.condition is None
    }
    if shallow_focused and not pad_type:
        flags.append(
            "the only curve reaching R_xo is a shallow focused laterolog-type measurement ("
            + ", ".join(sorted(shallow_focused))
            + "), so every verdict that needs R_xo is CONDITIONAL rather than possible. "
            "asquith#32 puts this device in the invaded zone twice and asquith#33 reserves "
            "R_xo for the pad-type micro devices (MLL, PL, MSFL); only asquith#11's SFLU "
            "caption and asquith#43's ratio-equation gloss read it as R_xo. The corpus is "
            "split and this tool does not pick - spec open question 5."
        )
    elif shallow_focused and pad_type:
        flags.append(
            "R_xo is taken from the pad-type device(s) " + ", ".join(sorted(pad_type))
            + " in preference to the shallow focused curve(s) " + ", ".join(sorted(shallow_focused))
            + ", because asquith#33 states the pad-type logs are \"designed to measure the "
            "resistivity in the flushed zone (R_xo)\" outright."
        )
    return flags


def _dedupe(items: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))
