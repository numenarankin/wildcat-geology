"""#108 `squeeze_recommend` — select the squeeze technique for a DIAGNOSED problem.

Spec: `specs/108-squeeze_recommend.md`.
Source: `13-cement-integrity/petrowiki-remedial-cementing#0` (five-step go/no-go list,
six techniques and their selection criteria); plugback branch at `#1`.

This tool selects *how* to squeeze. It is structurally incapable of deciding *whether*
to squeeze, and that is the point of it rather than a docstring promise:

1. `SqueezeRecommendation` has no `should_squeeze` field. There is nowhere for a caller
   to read the decision off, whatever it passes in.
2. The source's five-step go/no-go list is *consumed*, never derived. All five are
   required inputs with no defaults; the tool cannot compute any of them and does not
   try.
3. `bond_index`, `cbl_amplitude_mv`, `attenuation_db_ft`, `vdl_class` and
   `isolation_length_ft` are accepted as real arguments **solely so they can be
   refused**. `squeeze_recommend(bond_index=0.35)` returns the scope refusal with the
   source's warning quoted, rather than a TypeError a caller reads as "wrong keyword,
   try again". No log value reaches any branch.

The source's own warning is why: "Most squeeze applications are unnecessary because they
result from poor primary-cement-job evaluations or job diagnostics." Nothing in this
corpus states a bond index, amplitude, footage or VDL class at which a squeeze is
indicated, so the leap from a CBL reading to "squeeze it" is unsupported and this tool
declines to make it.

This page carries no equations — checked: `13-cement-integrity/` has `.equations.md`
sidecars for five documents and none is this one, and the four that hold math hold only
bond-index and attenuation formulae. So every branch below is a quoted sentence, and the
only number on the page is "approximately 2 bbl/min".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

# --------------------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------------------

REMEDIAL = "13-cement-integrity/petrowiki-remedial-cementing#0"
REMEDIAL_PLUG = "13-cement-integrity/petrowiki-remedial-cementing#1"
SLB_CEMENTING = "13-cement-integrity/slb-defining-well-cementing-fundamentals#1"

# --------------------------------------------------------------------------------------
# The scope boundary, quoted. Tests assert these two strings literally.
# --------------------------------------------------------------------------------------

#: `#0`, *Squeeze cementing*, verbatim. The catalog prints the full sentence; the
#: (older) `tool-verification.md:124` row truncates it at "evaluations." The source has
#: the longer form and the catalog is right.
UNNECESSARY_SQUEEZE_WARNING = (
    "Most squeeze applications are unnecessary because they result from poor "
    "primary-cement-job evaluations or job diagnostics."
)

SCOPE_REFUSAL_REASON = (
    "squeeze_recommend selects HOW to squeeze a problem that has already been "
    "diagnosed; it does not decide WHETHER to squeeze. Log evidence alone cannot "
    "establish the source's five-step go/no-go list, and no threshold anywhere in this "
    "corpus turns a bond log into a squeeze indication. "
    + UNNECESSARY_SQUEEZE_WARNING
)

#: Argument names that carry log evidence. Present only to be refused; never read by a
#: selection branch.
LOG_EVIDENCE_ARGS = (
    "bond_index",
    "cbl_amplitude_mv",
    "attenuation_db_ft",
    "vdl_class",
    "isolation_length_ft",
    "log_evidence",
)

LOG_EVIDENCE_IGNORED_FLAG = (
    "log evidence was supplied and is NOT used in technique selection: {names}. "
    "Technique selection is driven entirely by the diagnosis, void type, fracture "
    "pressure, injectivity and available tools."
)

# --------------------------------------------------------------------------------------
# The five-step go/no-go list — `#0`, *Squeeze cementing*, verbatim
# --------------------------------------------------------------------------------------

GO_NO_GO_PREAMBLE = (
    "Before using a squeeze application, a series of decisions must be made to determine"
)


@dataclass(frozen=True)
class GoNoGoStepDef:
    number: int
    text: str            # verbatim from the source
    argument: str        # the required argument that answers it
    kind: str            # "bool" | "statement" | "enumeration"
    source: str = REMEDIAL


GO_NO_GO_STEPS: tuple[GoNoGoStepDef, ...] = (
    GoNoGoStepDef(1, "If a problem exists", "problem_exists", "bool"),
    GoNoGoStepDef(2, "The magnitude of the problem", "magnitude", "statement"),
    GoNoGoStepDef(3, "If squeeze cementing will correct it", "squeeze_will_correct", "bool"),
    GoNoGoStepDef(4, "The risk factors present", "risk_factors", "enumeration"),
    GoNoGoStepDef(5, "If economics will support it", "economics_support", "bool"),
)


@dataclass(frozen=True)
class SqueezeGoNoGo:
    """The caller's answers to the source's five-step list. All five are required.

    The tool never fills one in. Step 2 is a magnitude, not a yes/no, and step 4 is an
    enumeration whose *empty* value is a real answer ("assessed, none present") — which
    is why `None` and `()` mean different things here.
    """

    problem_exists: bool | None = None
    magnitude: str | None = None
    squeeze_will_correct: bool | None = None
    risk_factors: Sequence[str] | None = None
    economics_support: bool | None = None


@dataclass(frozen=True)
class GoNoGoAnswer:
    number: int
    text: str
    answer: Any
    source: str = REMEDIAL


# --------------------------------------------------------------------------------------
# The six techniques — `#0`, *Squeeze techniques*: "The following techniques are the six
# commonly recognized squeeze applications."
# --------------------------------------------------------------------------------------

TECHNIQUES_PREAMBLE = (
    "The following techniques are the six commonly recognized squeeze applications."
)


@dataclass(frozen=True)
class TechniqueDef:
    key: str
    name: str
    axis: str            # "pumping" | "pressure" | "placement"
    choice: str
    definition: str      # verbatim
    criterion: str       # verbatim selection criterion
    source: str = REMEDIAL


TECHNIQUES: tuple[TechniqueDef, ...] = (
    TechniqueDef(
        key="running_squeeze",
        name="Running squeeze",
        axis="pumping",
        choice="running",
        definition=(
            "A running squeeze is any squeeze operation in which continuous pumping is "
            "used to force the cement into the squeeze interval."
        ),
        criterion=(
            "Running squeezes may be applied whenever the wellbore can be circulated at "
            "a reasonable pump rate (approximately 2 bbl/min)."
        ),
    ),
    TechniqueDef(
        key="hesitation_squeeze",
        name="Hesitation squeeze",
        axis="pumping",
        choice="hesitation",
        definition=(
            "During a hesitation squeeze, the pumping sequence is started and stopped "
            "repeatedly, while the pressure is closely monitored on the surface."
        ),
        criterion=(
            "This technique is often used when a squeeze pressure cannot be obtained "
            "using a running technique because of"
        ),
    ),
    TechniqueDef(
        key="high_pressure_squeeze",
        name="High-pressure squeeze",
        axis="pressure",
        choice="high_pressure",
        definition=(
            "A high-pressure squeeze is an application performed above formation "
            "fracturing pressures when fracturing is necessary to displace the cement "
            "and seal off formations or establish injection points between channels and "
            "perforations."
        ),
        criterion=(
            "performed above formation fracturing pressures when fracturing is necessary"
        ),
    ),
    TechniqueDef(
        key="low_pressure_squeeze",
        name="Low-pressure squeeze",
        axis="pressure",
        choice="low_pressure",
        definition=(
            "A low-pressure squeeze, the most common technique, is any squeeze "
            "application conducted below the fracturing pressure."
        ),
        criterion=(
            "This method can be applied whenever clean wellbore fluids can be injected "
            "into a formation, such as permeable sand, lost-circulation interval, "
            "fractured limestone, vugs, or voids."
        ),
    ),
    TechniqueDef(
        key="packer_retainer_squeeze",
        name="Packer/retainer squeeze",
        axis="placement",
        choice="packer_retainer",
        definition=(
            "Squeeze tools are often used to isolate the squeeze interval and place the "
            "cement as close to the squeeze target as possible before applying pressure."
        ),
        criterion=(
            "Retainers or bridge plugs are used to create a false bottom and are set "
            "just below the squeeze target inside the casing or tubing. ... A packer can "
            "be run into the wellbore and set above the squeeze interval, between two "
            "intervals, or below an interval."
        ),
    ),
    TechniqueDef(
        key="bradenhead_squeeze",
        name="Bradenhead squeeze",
        axis="placement",
        choice="bradenhead",
        definition=(
            "Whether during drilling or completion, a Bradenhead is performed by "
            "circulating cement slurry down to the squeeze interval, then pulling the "
            "workstring above the top of the cement column. The backside of the wellbore "
            "is closed in, and pressure is applied through the workstring to force "
            "cement into the squeeze interval."
        ),
        criterion=(
            "A Bradenhead squeeze is performed when squeeze tools are unavailable or "
            "cannot be run in the hole, or when the operator feels he can successfully "
            "control the problem without pulling the drillstring, tubulars, etc. out of "
            "the wellbore."
        ),
    ),
)

TECHNIQUE_BY_KEY = {t.key: t for t in TECHNIQUES}
TECHNIQUE_ORDER = tuple(t.key for t in TECHNIQUES)

# The three named causes a running squeeze fails, `#0`, *Hesitation squeeze*, verbatim.
HESITATION_CAUSES: tuple[tuple[str, str], ...] = (
    ("void_size", "The size of the void"),
    ("filtrate_control", "Lack of filtrate control"),
    (
        "critical_wellbore_pressure",
        "When the squeeze must be performed below a critical wellbore pressure",
    ),
)

# Source-stated preconditions carried onto the recommendation.
PREREQUISITES = {
    "hesitation": (
        "The slurry volume should be clear of all downhole tools before the hesitation "
        "cycles begin."
    ),
    "packer_retainer": (
        "Retainers or bridge plugs are used to create a false bottom and are set just "
        "below the squeeze target inside the casing or tubing."
    ),
    "bradenhead": (
        "A Bradenhead is performed by circulating cement slurry down to the squeeze "
        "interval, then pulling the workstring above the top of the cement column. The "
        "backside of the wellbore is closed in, and pressure is applied through the "
        "workstring."
    ),
    "block": (
        "'Block' squeezing ... requires isolation of the zone with a packer and "
        "retainer, using high pressure to force cement slurry (fracture) into the zone."
    ),
    "openhole_low_pressure_zone": (
        "To protect a low-pressure zone in an openhole before squeezing"
    ),
}

# Advisory notes that never change a branch.
NOTES = {
    "running_turns_high": (
        "When applied correctly, most running squeezes are low-pressure applications; "
        "however, they often turn into high-pressure applications because of: Unknown "
        "formation characteristics / The quality of slurry used / Lack of job control"
    ),
    "walking_squeeze": (
        "As running-squeeze pressure builds, the pump rate should be reduced, creating a "
        "walking squeeze."
    ),
    "bullheading": (
        "High pressure is usually required to force all wellbore fluids into the "
        "formations ahead of the cement slurry. This technique is often referred to as "
        "'bullheading.'"
    ),
    "bradenhead_hesitation": (
        "A hesitation squeeze is sometimes used to more effectively pack off the cement "
        "into all voids."
    ),
    "coiled_tubing": (
        "Most coiled-tubing (CT) squeeze applications are performed using this technique."
    ),
    "no_slurry_invasion": (
        "Cement slurry will not invade a formation unless it is fractured away, creating "
        "a large crack to accommodate the entire slurry. Otherwise, dehydration occurs "
        "and only the filtrate enters the zone."
    ),
    "hesitation_economy": (
        "For many otherwise large and expensive conventional squeeze applications, a "
        "hesitation squeeze can be a safer, less expensive, and effective technique."
    ),
}

# --------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------

#: SOURCED. `#0`: "Running squeezes may be applied whenever the wellbore can be
#: circulated at a reasonable pump rate (approximately 2 bbl/min)." The only number on
#: the page.
RUNNING_SQUEEZE_MIN_CIRCULATION_BBLPM = 2.0

#: OWNED, flag-only. The source wrote "approximately"; a rate inside this band of the
#: gate gets a flag telling the caller to confirm with a field circulation test. It
#: NEVER moves the branch — the `>= 2.0` comparison decides regardless.
RUNNING_GATE_NEAR_BAND_BBLPM = 0.2

# --------------------------------------------------------------------------------------
# Void types — `#0`: "The slurry is designed specifically to fill the type of void in the
# wellbore, whether it is a small crack or micro-annuli, casing split or large vug,
# formation rock or another kind of cavity." Plus the low-pressure applicability list.
#
# Size is stated by the source for TWO voids only: "small" for crack/micro-annuli and
# "large" for vug. Everything else is None and is never guessed — hesitation cause 1
# ("The size of the void") cannot fire from an unstated size.
# --------------------------------------------------------------------------------------

SLURRY_DESIGN_CONSTRAINT = (
    "The slurry is designed specifically to fill the type of void in the wellbore ... "
    "Thus, the slurry design and rate of dehydration or fluid loss designed into the "
    "slurry is critical, and a poor design may not provide a complete fill and seal of "
    "the voids."
)


@dataclass(frozen=True)
class VoidTypeDef:
    key: str
    quoted_as: str            # the phrase exactly as the source prints it
    size: str | None          # "small" | "large" | None = source does not state
    size_quote: str | None
    low_pressure_named: bool  # named in the low-pressure applicability list
    source: str = REMEDIAL


_SIZE_QUOTE = (
    "whether it is a small crack or micro-annuli, casing split or large vug, formation "
    "rock or another kind of cavity"
)

VOID_TYPES: dict[str, VoidTypeDef] = {
    v.key: v
    for v in (
        VoidTypeDef("micro_annulus", "micro-annuli", "small", _SIZE_QUOTE, False),
        VoidTypeDef("small_crack", "small crack", "small", _SIZE_QUOTE, False),
        VoidTypeDef("casing_split", "casing split", None, None, False),
        VoidTypeDef("large_vug", "large vug", "large", _SIZE_QUOTE, True),
        VoidTypeDef("formation_rock", "formation rock", None, None, False),
        VoidTypeDef("other_cavity", "another kind of cavity", None, None, False),
        VoidTypeDef("permeable_sand", "permeable sand", None, None, True),
        VoidTypeDef("lost_circulation_interval", "lost-circulation interval", None, None, True),
        VoidTypeDef("fractured_limestone", "fractured limestone", None, None, True),
        VoidTypeDef("vugs", "vugs", None, None, True),
        VoidTypeDef("voids", "voids", None, None, True),
    )
}

# --------------------------------------------------------------------------------------
# Diagnoses the source's squeeze section covers.
#
# THE TOOL DOES NOT DIAGNOSE. This table says which diagnoses the source's technique list
# covers, not how to arrive at one.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DiagnosisDef:
    key: str
    quoted_as: str
    source: str = REMEDIAL
    also_a_plug_indication: bool = False
    plug_note: str | None = None
    technique_hint: str | None = None   # a technique the source names for this problem
    hint_quote: str | None = None


DIAGNOSES: dict[str, DiagnosisDef] = {
    d.key: d
    for d in (
        DiagnosisDef(
            "lost_circulation",
            "the problem occurs during drilling (lost circulation)",
            technique_hint="bradenhead_squeeze",
            hint_quote=(
                "This technique is often applied when the problem occurs during drilling "
                "(lost circulation) or soon after a primary cement job (weak casing shoe)."
            ),
            # NOT routed to plugback. `#0`'s plug section also names lost-circulation
            # control, and the low-pressure list names a "lost-circulation interval", so
            # the source puts this problem on BOTH sides. Routing it away would drop the
            # Bradenhead indication the source prints for it.
            also_a_plug_indication=True,
            plug_note=(
                "The source also describes a plug remedy for this problem: 'When mud "
                "circulation is lost during drilling, lost returns can sometimes be "
                "restored by spotting a cement plug across the thief (lost-circulation) "
                "zone and then drilling back through the plug.' Compare with "
                "plugback_vs_squeeze (#114)."
            ),
        ),
        DiagnosisDef(
            "weak_casing_shoe",
            "soon after a primary cement job (weak casing shoe)",
            technique_hint="bradenhead_squeeze",
            hint_quote=(
                "This technique is often applied when the problem occurs during drilling "
                "(lost circulation) or soon after a primary cement job (weak casing shoe)."
            ),
        ),
        DiagnosisDef(
            "channel",
            "establish injection points between channels and perforations",
            technique_hint="high_pressure_squeeze",
            hint_quote=(
                "A high-pressure squeeze is an application performed above formation "
                "fracturing pressures when fracturing is necessary to displace the cement "
                "and seal off formations or establish injection points between channels "
                "and perforations."
            ),
        ),
        DiagnosisDef(
            "permeable_zone_above_below_production",
            "squeezing off permeable sections above and below a production zone",
            technique_hint="high_pressure_squeeze",
            hint_quote=(
                "'Block' squeezing is the process of squeezing off permeable sections "
                "above and below a production zone, which requires isolation of the zone "
                "with a packer and retainer, using high pressure to force cement slurry "
                "(fracture) into the zone."
            ),
        ),
        DiagnosisDef("micro_annulus", "micro-annuli"),
        DiagnosisDef("casing_split", "casing split"),
        DiagnosisDef(
            "casing_leak",
            "repairing casing leaks caused by a corroded or split casing",
            source=SLB_CEMENTING,
        ),
        DiagnosisDef(
            "corroded_casing",
            "repairing casing leaks caused by a corroded or split casing",
            source=SLB_CEMENTING,
        ),
        DiagnosisDef(
            "poor_bonding",
            "logging operations indicate that the cement job is defective, either in the "
            "form of poor cement bonding or communication between zones",
            source=SLB_CEMENTING,
        ),
        DiagnosisDef(
            "interzonal_communication",
            "logging operations indicate that the cement job is defective, either in the "
            "form of poor cement bonding or communication between zones",
            source=SLB_CEMENTING,
        ),
        DiagnosisDef("defective_primary_cement", "correct a problem in the wellbore"),
    )
}

# --------------------------------------------------------------------------------------
# Diagnoses the source routes to PLUG CEMENTING, not to a squeeze.
#
# A plug is a different remedy. `plugback_vs_squeeze` (#114) owns that decision; this
# tool routes and declines rather than dressing a plug up as a squeeze.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PlugbackDef:
    key: str
    quoted_as: str
    source: str


PLUGBACK_INDICATIONS: dict[str, PlugbackDef] = {
    p.key: p
    for p in (
        PlugbackDef("shut_off_water", "To shut off water", REMEDIAL_PLUG),
        PlugbackDef(
            "recomplete_shallower", "To recomplete a zone at a shallower depth", REMEDIAL_PLUG
        ),
        PlugbackDef(
            "abandon_depleted_zone",
            "abandoning a depleted or unprofitable producing zone may be beneficial",
            REMEDIAL_PLUG,
        ),
        PlugbackDef(
            "abandonment",
            "To seal off selected intervals of a dry hole or a depleted well, operators "
            "can place a cement plug at the required depth",
            REMEDIAL,
        ),
        PlugbackDef(
            "sidetrack",
            "it is often necessary to place a cement plug at the required depth to change "
            "the wellbore direction or to help support a mechanical whipstock",
            REMEDIAL,
        ),
        PlugbackDef(
            "well_control",
            "Plugs, typically made of cement, are sometimes placed in a wellbore when the "
            "well has reached a critical state in which no margins remain between pore "
            "and frac pressures and no other options exist.",
            REMEDIAL,
        ),
        PlugbackDef(
            "formation_testing",
            "Plugs are occasionally placed in the open hole below a zone to be tested",
            REMEDIAL_PLUG,
        ),
        PlugbackDef(
            "wellbore_stability",
            "placing a plugging material across an unstable formation can be beneficial",
            REMEDIAL_PLUG,
        ),
    )
}

# --------------------------------------------------------------------------------------
# Tools and objectives
# --------------------------------------------------------------------------------------

#: `#0`, *Packer/retainer squeeze* and *Bradenhead squeeze*.
SQUEEZE_TOOLS = ("packer", "retainer", "bridge_plug", "coiled_tubing", "workstring")

#: Tools that isolate the interval and so put the job on the packer/retainer branch.
ISOLATION_TOOLS = ("packer", "retainer", "bridge_plug")

#: OWNED vocabulary. "block" and "establish_injection_points" are the source's two named
#: reasons fracturing is necessary; "seal_voids" is this project's residual name.
OBJECTIVES = ("seal_voids", "block", "establish_injection_points")


# --------------------------------------------------------------------------------------
# Return types
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Injectivity:
    """Clean-wellbore-fluid injection actually observed, not estimated.

    `#0`, low-pressure squeeze: "This method can be applied whenever clean wellbore
    fluids can be injected into a formation". Both fields are required; a rate of zero
    is a real, meaningful answer (nothing injects) and is not the same as unstated.
    """

    rate_bblpm: float | None = None
    pressure_psi: float | None = None
    fluid: str | None = None


@dataclass(frozen=True)
class SelectionCriterion:
    axis: str
    choice: str
    technique: str
    quote: str           # verbatim from the source
    anchor: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class SqueezeRecommendation:
    """How to squeeze. Deliberately has no `should_squeeze` field: see module docstring."""

    techniques: tuple[str, ...]
    pumping_mode: str
    pressure_branch: str
    placement: str
    pressure_limit: Quantity
    pressure_bound: str                       # "ceiling" | "floor"
    criteria: tuple[SelectionCriterion, ...]
    go_no_go: tuple[GoNoGoAnswer, ...]
    slurry_design_note: str
    prerequisites: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    source: str = REMEDIAL


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------


def _as_go_no_go(go_no_go, kwargs: dict[str, Any]) -> SqueezeGoNoGo:
    """Accept a record, a mapping, or the five individual keywords — not both."""
    individual = {k: v for k, v in kwargs.items() if v is not None}
    if go_no_go is not None and individual:
        raise ValueError(
            "supply the five go/no-go answers either as `go_no_go` or as the individual "
            f"keywords, not both (got both: {sorted(individual)})"
        )
    if go_no_go is None:
        return SqueezeGoNoGo(**kwargs)
    if isinstance(go_no_go, SqueezeGoNoGo):
        return go_no_go
    if isinstance(go_no_go, Mapping):
        unknown = set(go_no_go) - {s.argument for s in GO_NO_GO_STEPS}
        if unknown:
            raise ValueError(f"unknown go/no-go keys: {sorted(unknown)}")
        return SqueezeGoNoGo(**dict(go_no_go))
    raise ValueError("go_no_go must be a SqueezeGoNoGo, a mapping, or omitted")


def _as_injectivity(injectivity) -> Injectivity | None:
    if injectivity is None:
        return None
    if isinstance(injectivity, Injectivity):
        return injectivity
    if isinstance(injectivity, Mapping):
        unknown = set(injectivity) - {"rate_bblpm", "pressure_psi", "fluid"}
        if unknown:
            raise ValueError(f"unknown injectivity keys: {sorted(unknown)}")
        return Injectivity(**dict(injectivity))
    raise ValueError("injectivity must be an Injectivity, a mapping, or omitted")


def _step(number: int) -> GoNoGoStepDef:
    return GO_NO_GO_STEPS[number - 1]


def _stated(value: Any, kind: str) -> bool:
    """Is the caller's answer *stated*? `()` is a stated enumeration; None never is."""
    if value is None:
        return False
    if kind == "statement":
        return bool(str(value).strip())
    return True


# --------------------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------------------


def squeeze_recommend(
    *,
    # --- the diagnosed problem (the tool does not diagnose) -----------------------------
    diagnosis: str | None = None,
    # --- the five-step go/no-go list, consumed and never derived ------------------------
    go_no_go: SqueezeGoNoGo | Mapping[str, Any] | None = None,
    problem_exists: bool | None = None,
    magnitude: str | None = None,
    squeeze_will_correct: bool | None = None,
    risk_factors: Sequence[str] | None = None,
    economics_support: bool | None = None,
    # --- well state, none of it inferrable from a log ------------------------------------
    void_type: str | None = None,
    frac_pressure_psi: float | None = None,
    injectivity: Injectivity | Mapping[str, Any] | None = None,
    available_tools: Sequence[str] | None = None,
    circulation_rate_bblpm: float | None = None,
    filtrate_control: bool | None = None,
    # --- optional well state --------------------------------------------------------------
    critical_wellbore_pressure_psi: float | None = None,
    objective: str = "seal_voids",
    fracturing_required: bool | None = None,
    squeeze_pressure_obtainable_running: bool | None = None,
    tools_can_be_run_in_hole: bool | None = None,
    pull_workstring_acceptable: bool | None = None,
    openhole_low_pressure_zone_present: bool | None = None,
    target_depth_ft: float | None = None,
    # --- log evidence: accepted ONLY so it can be refused ----------------------------------
    bond_index: float | None = None,
    cbl_amplitude_mv: float | None = None,
    attenuation_db_ft: float | None = None,
    vdl_class: str | None = None,
    isolation_length_ft: float | None = None,
    log_evidence: Mapping[str, Any] | None = None,
) -> SqueezeRecommendation | Refusal:
    """Select the squeeze technique for a diagnosed cement problem.

    Returns a `SqueezeRecommendation` naming one branch per axis (running/hesitation,
    low/high-pressure, packer-retainer/Bradenhead) plus the operative pressure bound, or
    a `Refusal`.

    It does **not** decide whether to squeeze. See the module docstring for how that is
    enforced structurally rather than by convention.
    """
    supplied_log_evidence = {
        name: value
        for name, value in (
            ("bond_index", bond_index),
            ("cbl_amplitude_mv", cbl_amplitude_mv),
            ("attenuation_db_ft", attenuation_db_ft),
            ("vdl_class", vdl_class),
            ("isolation_length_ft", isolation_length_ft),
            ("log_evidence", log_evidence),
        )
        if value is not None
    }

    gng = _as_go_no_go(
        go_no_go,
        {
            "problem_exists": problem_exists,
            "magnitude": magnitude,
            "squeeze_will_correct": squeeze_will_correct,
            "risk_factors": risk_factors,
            "economics_support": economics_support,
        },
    )

    unstated_steps = tuple(
        s for s in GO_NO_GO_STEPS if not _stated(getattr(gng, s.argument), s.kind)
    )

    # ---- Guard 1: the scope boundary. Runs before everything else. --------------------
    # A caller holding only a bond log and asking whether to squeeze lands here. This is
    # the refusal the tool exists for.
    if supplied_log_evidence and (diagnosis is None or unstated_steps):
        needed = []
        if diagnosis is None:
            needed.append(
                "diagnosis — the diagnosed problem, established off-tool "
                f"(one of: {', '.join(sorted(DIAGNOSES))})"
            )
        for s in unstated_steps:
            needed.append(f"go/no-go step {s.number} ({s.argument}): \"{s.text}\"")
        needed.append(
            "these are decisions about the well and the economics, not readings; "
            "cbl_bond_index (#103) and isolation_length_check (#104) evaluate a bond "
            "log, and no source in this corpus states a bond-log threshold at which a "
            "squeeze is indicated"
        )
        return Refusal(
            reason=SCOPE_REFUSAL_REASON,
            needed=tuple(needed),
            source=REMEDIAL,
        )

    # ---- Guard 2: the tool does not diagnose ------------------------------------------
    if diagnosis is None:
        return Refusal(
            reason=(
                "no diagnosed problem was supplied. squeeze_recommend selects a technique "
                "for a problem that has already been diagnosed; it does not diagnose. "
                + UNNECESSARY_SQUEEZE_WARNING
            ),
            needed=(
                "diagnosis — one of: " + ", ".join(sorted(DIAGNOSES)),
                "or, if the remedy is a plug rather than a squeeze, one of: "
                + ", ".join(sorted(PLUGBACK_INDICATIONS)),
            ),
            source=REMEDIAL,
        )

    # ---- Guard 3: does the source route this to a plug instead? ------------------------
    if diagnosis in PLUGBACK_INDICATIONS and diagnosis not in DIAGNOSES:
        p = PLUGBACK_INDICATIONS[diagnosis]
        return Refusal(
            reason=(
                f"the source routes '{diagnosis}' to plug cementing, not to a squeeze: "
                f"\"{p.quoted_as}\" ({p.source}). A plug and a squeeze are different "
                "remedies and this tool will not return a squeeze technique for a "
                "plugback. No technique selected."
            ),
            needed=(
                "route to plugback_vs_squeeze (#114), which owns the plug-versus-squeeze "
                "decision",
                "note the source treats the two as combinable, not exclusive: plug "
                "'integrity ... is frequently enhanced mechanically by placing them above "
                "bridge plugs or through and above squeeze retainers' "
                f"({REMEDIAL_PLUG})",
            ),
            source=p.source,
        )

    # ---- Guard 4: a problem the technique list does not cover -------------------------
    if diagnosis not in DIAGNOSES:
        return Refusal(
            reason=(
                f"'{diagnosis}' is not a problem the source's six squeeze techniques are "
                "stated to address, and nothing in this corpus extends the list. No "
                "technique selected."
            ),
            needed=(
                "a diagnosis the source covers: " + ", ".join(sorted(DIAGNOSES)),
                "or a source stating a squeeze technique for this problem",
            ),
            source=REMEDIAL,
        )
    diag = DIAGNOSES[diagnosis]

    # ---- Guard 5: the five-step go/no-go list must be established ---------------------
    if unstated_steps:
        return Refusal(
            reason=(
                "the source's go/no-go list for a squeeze is not established. "
                f"\"{GO_NO_GO_PREAMBLE}\" "
                + "; ".join(f"{s.number}. {s.text}" for s in GO_NO_GO_STEPS)
                + ". Unstated: "
                + ", ".join(f"step {s.number} (\"{s.text}\")" for s in unstated_steps)
                + ". squeeze_recommend consumes these decisions; it cannot make them."
            ),
            needed=tuple(
                f"{s.argument} — go/no-go step {s.number}: \"{s.text}\""
                for s in unstated_steps
            ),
            source=REMEDIAL,
        )

    # ---- Guard 6: a step answered "no" ------------------------------------------------
    for number, value in (
        (1, gng.problem_exists),
        (3, gng.squeeze_will_correct),
        (5, gng.economics_support),
    ):
        if value is False:
            s = _step(number)
            tail = (
                " " + UNNECESSARY_SQUEEZE_WARNING if number in (1, 3) else ""
            )
            return Refusal(
                reason=(
                    f"go/no-go step {number} — \"{s.text}\" — was answered no, so the "
                    "source's precondition for a squeeze is not met. No technique "
                    "selected." + tail
                ),
                needed=(
                    f"{s.argument} = True, established off-tool, before a technique can "
                    "be selected",
                ),
                source=REMEDIAL,
            )

    go_no_go_trail = tuple(
        GoNoGoAnswer(s.number, s.text, getattr(gng, s.argument)) for s in GO_NO_GO_STEPS
    )

    # ---- Guard 7: required well state -------------------------------------------------
    if void_type is None:
        return Refusal(
            reason=(
                "void type was not stated. " + SLURRY_DESIGN_CONSTRAINT + " It also sets "
                "one of the three named causes a running squeeze fails (\"The size of "
                "the void\")."
            ),
            needed=("void_type — one of: " + ", ".join(sorted(VOID_TYPES)),),
            source=REMEDIAL,
        )
    if void_type not in VOID_TYPES:
        return Refusal(
            reason=(
                f"'{void_type}' is not a void type this source names. The source's void "
                f"vocabulary is: \"{_SIZE_QUOTE}\", plus the low-pressure list "
                "\"permeable sand, lost-circulation interval, fractured limestone, vugs, "
                "or voids\"."
            ),
            needed=("void_type — one of: " + ", ".join(sorted(VOID_TYPES)),),
            source=REMEDIAL,
        )
    void = VOID_TYPES[void_type]

    if frac_pressure_psi is None:
        return Refusal(
            reason=(
                "formation fracture pressure was not stated, and the two pressure "
                "branches are defined by it: a low-pressure squeeze is \"any squeeze "
                "application conducted below the fracturing pressure\" and a "
                "high-pressure squeeze is \"performed above formation fracturing "
                "pressures when fracturing is necessary\". Without it there is no "
                "boundary to select against. It cannot be inferred from a log. Getting "
                "this branch wrong has a stated cost: \""
                + NOTES["no_slurry_invasion"] + "\""
            ),
            needed=("frac_pressure_psi — formation fracture pressure at the squeeze target",),
            source=REMEDIAL,
        )
    if frac_pressure_psi <= 0:
        raise ValueError("frac_pressure_psi must be positive")

    inj = _as_injectivity(injectivity)
    if inj is None or inj.rate_bblpm is None or inj.pressure_psi is None:
        return Refusal(
            reason=(
                "injectivity was not stated. The low-pressure branch turns on it: \""
                + TECHNIQUE_BY_KEY["low_pressure_squeeze"].criterion
                + "\" A rate of zero is a valid, meaningful answer (nothing injects) and "
                "is not the same as leaving it unstated."
            ),
            needed=(
                "injectivity.rate_bblpm — clean-wellbore-fluid injection rate observed",
                "injectivity.pressure_psi — the pressure at which it was observed",
            ),
            source=REMEDIAL,
        )
    if inj.rate_bblpm < 0 or inj.pressure_psi < 0:
        raise ValueError("injectivity rate and pressure must be non-negative")

    if available_tools is None:
        return Refusal(
            reason=(
                "available squeeze tools were not stated, so the placement branch cannot "
                "be selected: \""
                + TECHNIQUE_BY_KEY["bradenhead_squeeze"].criterion
                + "\" An empty tuple is a valid statement (no tools available) and "
                "resolves to a Bradenhead; None is not."
            ),
            needed=(
                "available_tools — a (possibly empty) sequence drawn from: "
                + ", ".join(SQUEEZE_TOOLS),
            ),
            source=REMEDIAL,
        )
    tools = tuple(available_tools)
    unknown_tools = [t for t in tools if t not in SQUEEZE_TOOLS]
    if unknown_tools:
        raise ValueError(
            f"unknown squeeze tools {unknown_tools}; expected any of {list(SQUEEZE_TOOLS)}"
        )

    if circulation_rate_bblpm is None:
        return Refusal(
            reason=(
                "the wellbore circulation rate was not stated, and it is the source's "
                "gate for a running squeeze: \""
                + TECHNIQUE_BY_KEY["running_squeeze"].criterion
                + "\""
            ),
            needed=(
                "circulation_rate_bblpm — the rate at which the wellbore can actually be "
                "circulated",
            ),
            source=REMEDIAL,
        )
    if circulation_rate_bblpm < 0:
        raise ValueError("circulation_rate_bblpm must be non-negative")

    if filtrate_control is None:
        return Refusal(
            reason=(
                "filtrate control was not stated. \"Lack of filtrate control\" is one of "
                "the three named causes a squeeze pressure cannot be obtained using a "
                "running technique, so the running-versus-hesitation branch cannot be "
                "selected without it."
            ),
            needed=(
                "filtrate_control — True if the slurry's fluid-loss control is "
                "established, False if it is not",
            ),
            source=REMEDIAL,
        )

    if objective not in OBJECTIVES:
        raise ValueError(f"objective must be one of {list(OBJECTIVES)}; got {objective!r}")
    if critical_wellbore_pressure_psi is not None and critical_wellbore_pressure_psi <= 0:
        raise ValueError("critical_wellbore_pressure_psi must be positive")

    flags: list[str] = []
    notes: list[str] = []
    prerequisites: list[str] = []
    criteria: list[SelectionCriterion] = []

    if supplied_log_evidence:
        flags.append(
            LOG_EVIDENCE_IGNORED_FLAG.format(names=", ".join(sorted(supplied_log_evidence)))
        )

    # ---- Axis 1: pressure. Defined relative to formation fracture pressure. -----------
    frac_reasons: list[str] = []
    if inj.rate_bblpm == 0:
        frac_reasons.append(
            "clean wellbore fluids cannot be injected (injectivity rate = 0), so the "
            "low-pressure criterion is not met"
        )
    if inj.pressure_psi >= frac_pressure_psi and inj.rate_bblpm > 0:
        frac_reasons.append(
            f"injection was observed at {inj.pressure_psi:g} psi, at or above the "
            f"fracture pressure of {frac_pressure_psi:g} psi — the formation is already "
            "being fractured"
        )
    if objective == "block":
        frac_reasons.append(
            "objective is a block squeeze: \"'Block' squeezing ... requires isolation of "
            "the zone with a packer and retainer, using high pressure to force cement "
            "slurry (fracture) into the zone.\""
        )
    if objective == "establish_injection_points":
        frac_reasons.append(
            "objective is to \"establish injection points between channels and "
            "perforations\", one of the source's two named reasons fracturing is "
            "necessary"
        )
    if fracturing_required is True:
        frac_reasons.append("caller states fracturing is required")

    if frac_reasons:
        pressure_branch = "high_pressure"
        pressure_bound = "floor"
        tech = TECHNIQUE_BY_KEY["high_pressure_squeeze"]
        notes.append(NOTES["bullheading"])
    else:
        pressure_branch = "low_pressure"
        pressure_bound = "ceiling"
        tech = TECHNIQUE_BY_KEY["low_pressure_squeeze"]
        frac_reasons.append(
            f"clean wellbore fluids inject at {inj.rate_bblpm:g} bbl/min at "
            f"{inj.pressure_psi:g} psi, below the fracture pressure of "
            f"{frac_pressure_psi:g} psi"
        )
        if void.low_pressure_named:
            frac_reasons.append(
                f"\"{void.quoted_as}\" is named in the source's low-pressure "
                "applicability list"
            )
    notes.append(NOTES["no_slurry_invasion"])
    criteria.append(
        SelectionCriterion(
            axis="pressure",
            choice=pressure_branch,
            technique=tech.key,
            quote=tech.definition,
            anchor=REMEDIAL,
            evidence=tuple(frac_reasons),
        )
    )

    # The impossible case: the job must fracture, and must stay below a pressure that
    # precludes fracturing. The source offers no technique that does both.
    if (
        pressure_branch == "high_pressure"
        and critical_wellbore_pressure_psi is not None
        and critical_wellbore_pressure_psi < frac_pressure_psi
    ):
        return Refusal(
            reason=(
                "the case requires a high-pressure squeeze — \""
                + TECHNIQUE_BY_KEY["high_pressure_squeeze"].criterion
                + f"\" — while a critical wellbore pressure of "
                f"{critical_wellbore_pressure_psi:g} psi sits below the fracture pressure "
                f"of {frac_pressure_psi:g} psi, which forbids fracturing. No technique in "
                "the source's list both fractures the formation and stays below a "
                "pressure that precludes fracturing. No technique selected. "
                "(High-pressure was selected because: "
                + "; ".join(frac_reasons)
                + ".)"
            ),
            needed=(
                "a critical wellbore pressure above the fracture pressure, or a revised "
                "fracture pressure",
                "or re-establish go/no-go step 3 (\"If squeeze cementing will correct "
                "it\") for this well",
            ),
            source=REMEDIAL,
        )

    # ---- Axis 2: pumping. Running unless a named cause fires. -------------------------
    hesitation_evidence: list[str] = []
    if void.size == "large":
        hesitation_evidence.append(
            f"\"{dict(HESITATION_CAUSES)['void_size']}\" — the source calls "
            f"\"{void.quoted_as}\" large: \"{void.size_quote}\""
        )
    if filtrate_control is False:
        hesitation_evidence.append(f"\"{dict(HESITATION_CAUSES)['filtrate_control']}\"")
    if critical_wellbore_pressure_psi is not None:
        hesitation_evidence.append(
            f"\"{dict(HESITATION_CAUSES)['critical_wellbore_pressure']}\" — "
            f"{critical_wellbore_pressure_psi:g} psi"
        )
    if squeeze_pressure_obtainable_running is False:
        hesitation_evidence.append(
            "caller states a squeeze pressure cannot be obtained using a running technique"
        )
    if circulation_rate_bblpm < RUNNING_SQUEEZE_MIN_CIRCULATION_BBLPM:
        hesitation_evidence.append(
            f"the wellbore circulates at {circulation_rate_bblpm:g} bbl/min, below the "
            f"source's running-squeeze gate: \""
            + TECHNIQUE_BY_KEY["running_squeeze"].criterion
            + "\""
        )

    if hesitation_evidence:
        pumping_mode = "hesitation"
        tech = TECHNIQUE_BY_KEY["hesitation_squeeze"]
        prerequisites.append(PREREQUISITES["hesitation"])
        notes.append(NOTES["hesitation_economy"])
        pumping_quote = tech.criterion + " " + "; ".join(t for _, t in HESITATION_CAUSES)
        pumping_evidence = tuple(hesitation_evidence)
    else:
        pumping_mode = "running"
        tech = TECHNIQUE_BY_KEY["running_squeeze"]
        pumping_quote = tech.criterion
        pumping_evidence = (
            f"the wellbore circulates at {circulation_rate_bblpm:g} bbl/min, at or above "
            f"the source's approximate {RUNNING_SQUEEZE_MIN_CIRCULATION_BBLPM:g} bbl/min "
            "gate",
            "none of the source's three named causes of running-squeeze failure is "
            "present",
        )
        notes.append(NOTES["walking_squeeze"])
        # The source says the branch is not self-enforcing.
        flags.append(NOTES["running_turns_high"])

    if (
        abs(circulation_rate_bblpm - RUNNING_SQUEEZE_MIN_CIRCULATION_BBLPM)
        <= RUNNING_GATE_NEAR_BAND_BBLPM
    ):
        flags.append(
            f"circulation rate {circulation_rate_bblpm:g} bbl/min sits within "
            f"{RUNNING_GATE_NEAR_BAND_BBLPM:g} bbl/min of the source's approximate gate "
            "(\"approximately 2 bbl/min\"); confirm with a field circulation test. This "
            "band is this project's and is advisory only — it does not move the branch."
        )

    criteria.append(
        SelectionCriterion(
            axis="pumping",
            choice=pumping_mode,
            technique=tech.key,
            quote=pumping_quote,
            anchor=REMEDIAL,
            evidence=pumping_evidence,
        )
    )

    # ---- Axis 3: placement. -----------------------------------------------------------
    isolation_available = tuple(t for t in tools if t in ISOLATION_TOOLS)

    if objective == "block" and not ({"packer", "retainer"} <= set(tools)):
        return Refusal(
            reason=(
                "a block squeeze was requested, and the source states the tools it "
                "requires: \"'Block' squeezing is the process of squeezing off permeable "
                "sections above and below a production zone, which requires isolation of "
                "the zone with a packer and retainer, using high pressure to force cement "
                "slurry (fracture) into the zone.\" Available tools: "
                + (", ".join(tools) if tools else "none")
                + ". No technique selected."
            ),
            needed=(
                "both a packer and a retainer in available_tools",
                "or a different objective",
            ),
            source=REMEDIAL,
        )

    bradenhead_evidence: list[str] = []
    if not isolation_available:
        bradenhead_evidence.append(
            "no packer, retainer or bridge plug is available — \"squeeze tools are "
            "unavailable\""
        )
    if tools_can_be_run_in_hole is False:
        bradenhead_evidence.append("squeeze tools \"cannot be run in the hole\"")
    if pull_workstring_acceptable is False:
        bradenhead_evidence.append(
            "the operator elects to control the problem \"without pulling the "
            "drillstring, tubulars, etc. out of the wellbore\""
        )
    if tools == ("coiled_tubing",):
        bradenhead_evidence.append(NOTES["coiled_tubing"])

    if bradenhead_evidence:
        placement = "bradenhead"
        tech = TECHNIQUE_BY_KEY["bradenhead_squeeze"]
        prerequisites.append(PREREQUISITES["bradenhead"])
        if pumping_mode != "hesitation":
            notes.append(NOTES["bradenhead_hesitation"])
        placement_quote = tech.criterion
        placement_evidence = tuple(bradenhead_evidence)
    else:
        placement = "packer_retainer"
        tech = TECHNIQUE_BY_KEY["packer_retainer_squeeze"]
        prerequisites.append(PREREQUISITES["packer_retainer"])
        placement_quote = tech.definition
        placement_evidence = (
            "isolation tools available: " + ", ".join(isolation_available),
            "The following can be more accurately determined and controlled using "
            "squeeze tools: Cement volumes / Squeeze pressures / Squeeze targets",
        )
    if "coiled_tubing" in tools and placement == "bradenhead":
        notes.append(NOTES["coiled_tubing"])

    criteria.append(
        SelectionCriterion(
            axis="placement",
            choice=placement,
            technique=tech.key,
            quote=placement_quote,
            anchor=REMEDIAL,
            evidence=placement_evidence,
        )
    )

    if objective == "block":
        prerequisites.append(PREREQUISITES["block"])
    if openhole_low_pressure_zone_present is True:
        prerequisites.append(
            "the source names a plug as a precursor here, not an alternative: \""
            + PREREQUISITES["openhole_low_pressure_zone"]
            + f"\" ({REMEDIAL_PLUG}). See plugback_vs_squeeze (#114)."
        )

    # ---- The one number, and it is sourced --------------------------------------------
    # Low-pressure: "conducted below the fracturing pressure" -> frac pressure is the
    # ceiling. High-pressure: "above formation fracturing pressures" -> it is the floor.
    # A stated critical wellbore pressure lowers the ceiling when it is lower, because
    # the source requires the squeeze be performed below that too.
    limit_psi = float(frac_pressure_psi)
    limit_method = (
        "low-pressure branch ceiling = formation fracture pressure"
        if pressure_branch == "low_pressure"
        else "high-pressure branch floor = formation fracture pressure"
    )
    if (
        critical_wellbore_pressure_psi is not None
        and critical_wellbore_pressure_psi < limit_psi
    ):
        limit_psi = float(critical_wellbore_pressure_psi)
        limit_method = (
            "low-pressure branch ceiling = min(formation fracture pressure, critical "
            "wellbore pressure); the squeeze \"must be performed below a critical "
            "wellbore pressure\""
        )

    pressure_limit = Quantity(
        limit_psi,
        "psi",
        limit_method,
        REMEDIAL,
        inputs={
            "frac_pressure_psi": frac_pressure_psi,
            "critical_wellbore_pressure_psi": critical_wellbore_pressure_psi,
        },
        assumptions={
            "bound": pressure_bound,
            "definition": (
                "low-pressure is \"any squeeze application conducted below the fracturing "
                "pressure\"; high-pressure is \"performed above formation fracturing "
                "pressures when fracturing is necessary\""
            ),
        },
        flags=(NOTES["no_slurry_invasion"],),
    )

    selected = {
        "running_squeeze" if pumping_mode == "running" else "hesitation_squeeze",
        "low_pressure_squeeze"
        if pressure_branch == "low_pressure"
        else "high_pressure_squeeze",
        "packer_retainer_squeeze"
        if placement == "packer_retainer"
        else "bradenhead_squeeze",
    }
    techniques = tuple(k for k in TECHNIQUE_ORDER if k in selected)

    # ---- Diagnosis-level notes --------------------------------------------------------
    if diag.technique_hint:
        hinted = TECHNIQUE_BY_KEY[diag.technique_hint]
        notes.append(
            f"the source names a technique for this problem directly: {hinted.name} — "
            f"\"{diag.hint_quote}\""
        )
        if diag.technique_hint not in selected:
            # Reported, not resolved: the well state is what the source's criteria are
            # written against, so it wins, but the caller is told the two disagree.
            flags.append(
                f"the source names {hinted.name} for '{diagnosis}', but the well state "
                f"supplied selects the other branch of the {hinted.axis} axis "
                f"({dict((c.axis, c.choice) for c in criteria)[hinted.axis]}). The well "
                "state was followed; the disagreement is reported, not resolved."
            )
    if diag.also_a_plug_indication and diag.plug_note:
        flags.append(diag.plug_note)

    return SqueezeRecommendation(
        techniques=techniques,
        pumping_mode=pumping_mode,
        pressure_branch=pressure_branch,
        placement=placement,
        pressure_limit=pressure_limit,
        pressure_bound=pressure_bound,
        criteria=tuple(criteria),
        go_no_go=go_no_go_trail,
        slurry_design_note=(
            f"void type \"{void.quoted_as}\". " + SLURRY_DESIGN_CONSTRAINT
        ),
        prerequisites=tuple(prerequisites),
        notes=tuple(dict.fromkeys(notes)),
        flags=tuple(dict.fromkeys(flags)),
        inputs={
            "diagnosis": diagnosis,
            "void_type": void_type,
            "frac_pressure_psi": frac_pressure_psi,
            "injectivity_rate_bblpm": inj.rate_bblpm,
            "injectivity_pressure_psi": inj.pressure_psi,
            "available_tools": tools,
            "circulation_rate_bblpm": circulation_rate_bblpm,
            "filtrate_control": filtrate_control,
            "critical_wellbore_pressure_psi": critical_wellbore_pressure_psi,
            "objective": objective,
            "target_depth_ft": target_depth_ft,
            "log_evidence_supplied_and_ignored": dict(supplied_log_evidence) or None,
        },
        source=REMEDIAL,
    )
