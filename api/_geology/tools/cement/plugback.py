"""#114 `plugback_vs_squeeze` — cement plug or squeeze, decided from zone positions.

Spec: `specs/114-plugback_vs_squeeze.md`.
Source: `13-cement-integrity/petrowiki-remedial-cementing#1` (*Plug cementing — Zonal
isolation/conformance*, the plugback branch), with the squeeze branch at `#0` and one
corroborating sentence at `13-cement-integrity/slb-defining-well-cementing-fundamentals#1`.

Three decisions shape this module, and none of them is a docstring promise:

1. **The verdict is a set, because the source combines the two remedies.** There is no
   `remedy` field to read a forced either/or off; `verdicts` is a tuple and `combined`
   says whether both fired. The source describes plugs "enhanced mechanically by placing
   them ... through and above squeeze retainers", plugging fluids "combin[ed] ... with the
   remedial squeeze process", and a plug placed "before squeezing". A tool that returned
   one answer would have to drop those three sentences.

2. **The casing-condition arguments exist only to be refused.** `casing_condition`,
   `casing_grade`, `casing_leak_depth_ft`, `casing_corrosion_pct` and
   `casing_inspection_log` are accepted so that the natural call gets the reason instead
   of `TypeError: unexpected keyword argument`. No casing value is read by any branch —
   the refusal is the first guard in the function, so there is nowhere for one to go.
   The corpus search behind that is in the spec: it holds a casing-leak *diagnosis*
   ("squeeze cementing may be an effective technique for repairing casing leaks caused by
   a corroded or split casing", `slb...#1`, already owned by #108) and **no**
   casing-condition scale, grade, threshold, or sentence in which casing condition moves
   the plug-versus-squeeze decision.

3. **This tool never names a squeeze technique.** It decides *whether* the remedy is a
   plug or a squeeze; `squeeze_recommend` (#108) decides *how* to squeeze and is built so
   it cannot be asked whether. Every squeeze verdict here carries
   `next_tool="squeeze_recommend (#108)"`, and `Verdict` has no technique field. The
   routing tables are imported from `#108` rather than copied, so the two cannot drift:
   #108 refuses a plug indication and points here, #114 refuses a squeeze diagnosis and
   points there, and a diagnosis handed between them terminates.

This page carries no equations — `13-cement-integrity/` has `.equations.md` sidecars for
five of its seven documents and `petrowiki-remedial-cementing` is not one of them; the
only number on the page is "approximately 2 bbl/min", which belongs to #108. So every
branch below is a quoted sentence plus a `<=` on depths the caller supplied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Quantity unused: see plug_window)

# The routing tables are #108's, imported rather than re-typed. If this fragment is merged
# into `tools/cement/`, the import becomes `from .squeeze import ...`.
from .squeeze import (
    DIAGNOSES as SQUEEZE_DIAGNOSES,
    PLUGBACK_INDICATIONS,
    UNNECESSARY_SQUEEZE_WARNING,
)

# --------------------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------------------

REMEDIAL = "13-cement-integrity/petrowiki-remedial-cementing#0"
REMEDIAL_PLUG = "13-cement-integrity/petrowiki-remedial-cementing#1"
SLB_CEMENTING = "13-cement-integrity/slb-defining-well-cementing-fundamentals#1"

# --------------------------------------------------------------------------------------
# The quoted sentences. Every branch below cites one of these; tests assert them literally.
# --------------------------------------------------------------------------------------

#: `#1`, *Zonal isolation/conformance*. The plugback indication, and the catalog's anchor.
PLUG_PURPOSES = (
    "One of the more common reasons for plugging is to isolate a specific zone. The "
    "purpose may be: To shut off water / To recomplete a zone at a shallower depth / To "
    "protect a low-pressure zone in an openhole before squeezing"
)

RECOMPLETE_SHALLOWER = "To recomplete a zone at a shallower depth"

PERMANENT_PLUG = (
    "In a well with two or more producing intervals, abandoning a depleted or unprofitable "
    "producing zone may be beneficial. A permanent cement plug is used to isolate the "
    "zone, helping to prevent possible production losses into another interval or fluid "
    "migration from another interval."
)

#: `#0`, *Plug cementing*. The half of the discriminant that says where a plug seals.
PLUG_SEALS_THE_WELLBORE = (
    "In oil-gas-well construction, a plug must prevent fluid flow in a wellbore, either "
    "between formations or between a formation and the surface. As such, a competent plug "
    "must provide a hydraulic and mechanical seal."
)

#: `slb...#1`. The other half: where a squeeze seals, and what indicates one.
SQUEEZE_SEALS_THE_ANNULUS = (
    "When logging operations indicate that the cement job is defective, either in the form "
    "of poor cement bonding or communication between zones, a remedial cementing technique "
    "known as squeeze cementing may be performed to establish zonal isolation. A cementing "
    "crew perforates the casing at the defective interval and forces, or squeezes, cement "
    "slurry through the perforations and into the annulus to fill the voids."
)

#: `#0`, *High-pressure squeeze*. The source's own sentence for killing a zone that sits
#: above the interval you intend to keep producing.
BLOCK_SQUEEZE = (
    "'Block' squeezing is the process of squeezing off permeable sections above and below "
    "a production zone, which requires isolation of the zone with a packer and retainer, "
    "using high pressure to force cement slurry (fracture) into the zone."
)

#: `#1`. The three sentences that make the two remedies combinable rather than exclusive.
MECHANICAL_ENHANCEMENT = (
    "The integrity of such plugs is frequently enhanced mechanically by placing them above "
    "bridge plugs or through and above squeeze retainers."
)

COMBINED_METHOD = (
    "Other methods involve combining the spotting of plugging fluids with the remedial "
    "squeeze process of injecting a polymer plugging material into the formation matrix, "
    "followed by a small volume of cement slurry to shut off perforations."
)

PLUG_BEFORE_SQUEEZE = "To protect a low-pressure zone in an openhole before squeezing"

#: `slb...#1`. The corpus's only remedial sentence about casing condition — a *diagnosis*,
#: owned by #108. Quoted in the casing refusal so the caller is told what does exist.
CASING_LEAK_SENTENCE = (
    "In addition, squeeze cementing may be an effective technique for repairing casing "
    "leaks caused by a corroded or split casing."
)

# --------------------------------------------------------------------------------------
# Hand-off
# --------------------------------------------------------------------------------------

SQUEEZE_TOOL = "squeeze_recommend (#108)"

#: Diagnoses #108 owns. `lost_circulation` is in #108's `DIAGNOSES` *and* flagged
#: `also_a_plug_indication` there, so it is squeeze-owned with the plug remedy noted —
#: `squeeze.py:410-430`. Deriving the set rather than listing it is what keeps the two
#: tools from disagreeing when either table is edited.
SQUEEZE_OWNED = tuple(sorted(SQUEEZE_DIAGNOSES))

#: Diagnoses this tool owns: #108 guard 3 refuses each of these and routes here
#: (`squeeze.py:782-800`). Never routed back.
PLUG_OWNED = tuple(sorted(k for k in PLUGBACK_INDICATIONS if k not in SQUEEZE_DIAGNOSES))

#: `#0` prints a plug remedy for lost circulation as well as a Bradenhead squeeze, so
#: neither tool may silently drop the other half.
LOST_CIRCULATION_PLUG_REMEDY = (
    "When mud circulation is lost during drilling, lost returns can sometimes be restored "
    "by spotting a cement plug across the thief (lost-circulation) zone and then drilling "
    "back through the plug."
)

LOST_CIRCULATION_SQUEEZE_REMEDY = (
    "This technique is often applied when the problem occurs during drilling (lost "
    "circulation) or soon after a primary cement job (weak casing shoe)."
)

#: Plug purposes for which the source names no target zone above the plug — the geometry is
#: still required (this tool decides geometrically or not at all), but the caller is told
#: the source offers no squeeze alternative for them, so there is no real contest.
NO_SQUEEZE_ALTERNATIVE = {
    "abandonment": PLUGBACK_INDICATIONS["abandonment"].quoted_as,
    "well_control": PLUGBACK_INDICATIONS["well_control"].quoted_as,
    "sidetrack": PLUGBACK_INDICATIONS["sidetrack"].quoted_as,
    "formation_testing": PLUGBACK_INDICATIONS["formation_testing"].quoted_as,
    "wellbore_stability": PLUGBACK_INDICATIONS["wellbore_stability"].quoted_as,
}

# --------------------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------------------

#: Where the communication actually is. The plug seals the wellbore
#: (`PLUG_SEALS_THE_WELLBORE`); the squeeze seals the annulus and the voids behind pipe
#: (`SQUEEZE_SEALS_THE_ANNULUS`). That is the whole of the flow-path discriminant.
FLOW_PATHS = ("wellbore", "annulus", "behind_pipe", "perforations")
OUTSIDE_WELLBORE = ("annulus", "behind_pipe", "perforations")

#: `#1`: plugs are "enhanced mechanically by placing them above bridge plugs or through and
#: above squeeze retainers". A retainer is squeeze hardware; a bridge plug is not, and the
#: source calls the enhancement *mechanical*. So only the retainer adds a squeeze verdict.
MECHANICAL_SUPPORTS = ("bridge_plug", "squeeze_retainer")

#: Required geometry, in argument order. Measured depth, feet, increasing downward.
GEOMETRY_ARGS = (
    ("target_zone_top_ft", "top of the zone to be produced after the job"),
    ("target_zone_base_ft", "base of the zone to be produced after the job"),
    ("killed_zone_top_ft", "top of the zone being killed"),
    ("killed_zone_base_ft", "base of the zone being killed"),
    (
        "current_completion_depth_ft",
        "deepest point currently open to the wellbore (deepest perforation or PBTD)",
    ),
)

# --------------------------------------------------------------------------------------
# Return types
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    """One remedy the source indicates, with the sentence that indicates it.

    Deliberately has no `technique` field. Choosing among the six squeeze techniques is
    #108's job and this tool must not pre-empt it.
    """

    remedy: str                      # "plugback" | "squeeze"
    quote: str                       # verbatim from the source
    anchor: str
    evidence: tuple[str, ...] = ()
    next_tool: str | None = None


@dataclass(frozen=True)
class PlugbackSqueezeDecision:
    """Which remedy (or both). No single `remedy` field, by design: see module docstring."""

    verdicts: tuple[Verdict, ...]
    combined: bool
    plug_window: Range | None = None
    sequence: str | None = None
    notes: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    source: str = REMEDIAL_PLUG

    @property
    def remedies(self) -> tuple[str, ...]:
        return tuple(v.remedy for v in self.verdicts)


# --------------------------------------------------------------------------------------
# The tool
# --------------------------------------------------------------------------------------


def plugback_vs_squeeze(
    *,
    # --- the geometry. The decision is geometric; these are not optional. ---------------
    target_zone_top_ft: float | None = None,
    target_zone_base_ft: float | None = None,
    killed_zone_top_ft: float | None = None,
    killed_zone_base_ft: float | None = None,
    current_completion_depth_ft: float | None = None,
    # --- optional context ----------------------------------------------------------------
    diagnosis: str | None = None,
    flow_path: str | None = None,
    communication_depth_ft: float | None = None,
    mechanical_support: str | None = None,
    shut_off_perforations: bool | None = None,
    openhole_low_pressure_zone_present: bool | None = None,
    # --- casing condition: accepted ONLY so it can be refused ----------------------------
    casing_condition: str | None = None,
    casing_grade: str | None = None,
    casing_leak_depth_ft: float | None = None,
    casing_corrosion_pct: float | None = None,
    casing_inspection_log: Any = None,
) -> PlugbackSqueezeDecision | Refusal:
    """Decide whether the source indicates a cement plug, a squeeze, or both.

    Returns a `PlugbackSqueezeDecision` carrying one or two `Verdict`s — each with the
    sentence that indicates it — or a `Refusal`. Never a squeeze technique.
    """
    # ---- Programmer errors, not refusals ----------------------------------------------
    for name, value in (
        ("target_zone_top_ft", target_zone_top_ft),
        ("target_zone_base_ft", target_zone_base_ft),
        ("killed_zone_top_ft", killed_zone_top_ft),
        ("killed_zone_base_ft", killed_zone_base_ft),
        ("current_completion_depth_ft", current_completion_depth_ft),
        ("communication_depth_ft", communication_depth_ft),
        ("casing_leak_depth_ft", casing_leak_depth_ft),
    ):
        if value is not None and value < 0:
            raise ValueError(f"{name} must be non-negative; got {value!r}")
    if (
        target_zone_top_ft is not None
        and target_zone_base_ft is not None
        and target_zone_top_ft > target_zone_base_ft
    ):
        raise ValueError(
            "target_zone_top_ft must be at or above target_zone_base_ft "
            f"(depths increase downward); got {target_zone_top_ft} > {target_zone_base_ft}"
        )
    if (
        killed_zone_top_ft is not None
        and killed_zone_base_ft is not None
        and killed_zone_top_ft > killed_zone_base_ft
    ):
        raise ValueError(
            "killed_zone_top_ft must be at or above killed_zone_base_ft "
            f"(depths increase downward); got {killed_zone_top_ft} > {killed_zone_base_ft}"
        )
    if flow_path is not None and flow_path not in FLOW_PATHS:
        raise ValueError(f"flow_path must be one of {list(FLOW_PATHS)}; got {flow_path!r}")
    if mechanical_support is not None and mechanical_support not in MECHANICAL_SUPPORTS:
        raise ValueError(
            f"mechanical_support must be one of {list(MECHANICAL_SUPPORTS)}; "
            f"got {mechanical_support!r}"
        )

    # ---- Guard 1: the casing-condition scope boundary ----------------------------------
    # Runs first so a caller asking a casing question gets the reason rather than a
    # geometry complaint. Nothing below reads any of these values.
    supplied_casing = {
        name: value
        for name, value in (
            ("casing_condition", casing_condition),
            ("casing_grade", casing_grade),
            ("casing_leak_depth_ft", casing_leak_depth_ft),
            ("casing_corrosion_pct", casing_corrosion_pct),
            ("casing_inspection_log", casing_inspection_log),
        )
        if value is not None
    }
    if supplied_casing:
        return Refusal(
            reason=(
                "casing condition was supplied ("
                + ", ".join(sorted(supplied_casing))
                + ") and this tool will not let it influence the answer. The corpus "
                "contains a casing-leak *diagnosis*: \""
                + CASING_LEAK_SENTENCE
                + f"\" ({SLB_CEMENTING}) — which routes to {SQUEEZE_TOOL} as "
                "diagnosis='casing_leak' or 'corroded_casing'. It contains no "
                "casing-condition scale, no grade, no threshold, and not one sentence in "
                "which casing condition moves the plug-versus-squeeze decision. "
                "cbl_bond_index (#103) evaluates bond, not casing. Deciding on it would "
                "mean inventing the rule."
            ),
            needed=(
                "drop the casing argument and state the geometry: "
                + ", ".join(name for name, _ in GEOMETRY_ARGS),
                "or, if the problem IS a casing leak, call "
                f"{SQUEEZE_TOOL} with diagnosis='casing_leak' — a sourced route",
                "or a source stating a casing-condition threshold at which a plug displaces "
                "a squeeze; this corpus has none",
            ),
            source=SLB_CEMENTING,
        )

    # ---- Guard 2: diagnosis routing ----------------------------------------------------
    if diagnosis is not None:
        if diagnosis == "lost_circulation":
            return Refusal(
                reason=(
                    "the source prints both remedies for lost circulation and the choice "
                    "between them is not geometric, so this tool does not decide it. Plug: "
                    f"\"{LOST_CIRCULATION_PLUG_REMEDY}\" ({REMEDIAL}). Squeeze: "
                    f"\"{LOST_CIRCULATION_SQUEEZE_REMEDY}\" ({REMEDIAL}). "
                    f"{SQUEEZE_TOOL} owns this diagnosis and names the Bradenhead "
                    "technique for it; it carries the plug remedy as a note rather than "
                    "dropping it."
                ),
                needed=(
                    f"call {SQUEEZE_TOOL} with diagnosis='lost_circulation' for the "
                    "squeeze technique",
                    "or spot a plug across the thief zone per the sentence above — no "
                    "zone-position rule in this corpus decides between them",
                ),
                source=REMEDIAL,
            )
        if diagnosis in SQUEEZE_DIAGNOSES:
            d = SQUEEZE_DIAGNOSES[diagnosis]
            return Refusal(
                reason=(
                    f"the source treats '{diagnosis}' as a squeeze problem, not a plugback: "
                    f"\"{d.quoted_as}\" ({d.source}). This tool decides plug versus squeeze "
                    "from zone positions; the remedy here is already a squeeze, and "
                    f"{SQUEEZE_TOOL} selects the technique. No verdict issued. "
                    + UNNECESSARY_SQUEEZE_WARNING
                ),
                needed=(
                    f"call {SQUEEZE_TOOL} with diagnosis='{diagnosis}'",
                    "or, for a plugback question, one of: " + ", ".join(PLUG_OWNED),
                ),
                source=d.source,
            )
        if diagnosis not in PLUGBACK_INDICATIONS:
            return Refusal(
                reason=(
                    f"'{diagnosis}' is not a purpose either source names. The plug purposes "
                    f"are: \"{PLUG_PURPOSES}\", plus abandonment, sidetracking, "
                    "lost-circulation control, well control, formation testing and wellbore "
                    "stability. The squeeze problems are the ones "
                    f"{SQUEEZE_TOOL} lists. No verdict issued."
                ),
                needed=(
                    "diagnosis — a plug purpose: " + ", ".join(PLUG_OWNED),
                    f"or a squeeze problem, which routes to {SQUEEZE_TOOL}: "
                    + ", ".join(SQUEEZE_OWNED),
                    "or omit diagnosis entirely and decide on zone positions alone",
                ),
                source=REMEDIAL_PLUG,
            )

    # ---- Guard 3: the geometry is required ---------------------------------------------
    missing = [
        (name, meaning)
        for (name, meaning), value in zip(
            GEOMETRY_ARGS,
            (
                target_zone_top_ft,
                target_zone_base_ft,
                killed_zone_top_ft,
                killed_zone_base_ft,
                current_completion_depth_ft,
            ),
        )
        if value is None
    ]
    if missing:
        head = (
            f"the source states the plug indication as a relative position — "
            f"\"{RECOMPLETE_SHALLOWER}\" — so this decision is geometric and the depths "
            "are not optional. Missing: "
            + ", ".join(name for name, _ in missing)
            + "."
        )
        if diagnosis in NO_SQUEEZE_ALTERNATIVE:
            head += (
                f" (The source names a plug and no squeeze alternative for '{diagnosis}': "
                f"\"{NO_SQUEEZE_ALTERNATIVE[diagnosis]}\" — but this tool decides "
                "geometrically or not at all, and will not confirm a remedy for a wellbore "
                "it has not been told the shape of.)"
            )
        return Refusal(
            reason=head,
            needed=tuple(f"{name} — {meaning}, ft MD" for name, meaning in missing),
            source=REMEDIAL_PLUG,
        )

    target_top = float(target_zone_top_ft)
    target_base = float(target_zone_base_ft)
    killed_top = float(killed_zone_top_ft)
    killed_base = float(killed_zone_base_ft)
    completion = float(current_completion_depth_ft)

    # ---- Guard 4: the geometry must order sensibly -------------------------------------
    if (target_top, target_base) == (killed_top, killed_base):
        return Refusal(
            reason=(
                f"the target zone and the zone being killed are the same interval "
                f"({target_top:g}-{target_base:g} ft). A zone cannot be both produced and "
                "killed, and neither remedy addresses that. No verdict issued."
            ),
            needed=(
                "two distinct intervals — the zone to be produced and the zone to be shut "
                "off",
            ),
            source=REMEDIAL_PLUG,
        )
    if target_top < killed_base and killed_top < target_base:
        overlap = min(target_base, killed_base) - max(target_top, killed_top)
        return Refusal(
            reason=(
                f"the two zones overlap by {overlap:g} ft (target "
                f"{target_top:g}-{target_base:g} ft, zone being killed "
                f"{killed_top:g}-{killed_base:g} ft), so no depth separates them. A plug "
                "set anywhere between them would cement off part of the target — \""
                + PLUG_SEALS_THE_WELLBORE
                + "\" — and the source names no squeeze target inside the interval you "
                "intend to produce either. Selective isolation across interbedded pay is "
                "not covered by this corpus. No verdict issued."
            ),
            needed=(
                "non-overlapping target and killed intervals",
                "or a source describing selective isolation across interbedded zones; this "
                "corpus has none",
            ),
            source=REMEDIAL_PLUG,
        )
    if killed_top > completion:
        return Refusal(
            reason=(
                f"the zone being killed ({killed_top:g}-{killed_base:g} ft) lies below the "
                f"current completion depth ({completion:g} ft), so it is not open to this "
                "wellbore and nothing is flowing from it to shut off. The source's plug "
                f"case is a well \"with two or more producing intervals\" ({REMEDIAL_PLUG}). "
                "No verdict issued."
            ),
            needed=(
                "current_completion_depth_ft at or below the top of the zone being killed, "
                "if that zone is in fact open",
                "or the interval that is actually producing, as the zone being killed",
            ),
            source=REMEDIAL_PLUG,
        )

    # ---- The decision ------------------------------------------------------------------
    verdicts: list[Verdict] = []
    notes: list[str] = []
    flags: list[str] = []
    sequence: str | None = None
    plug_window: Range | None = None

    target_is_shallower = target_base <= killed_top
    killed_is_shallower = killed_base <= target_top

    if target_is_shallower:
        verdicts.append(
            Verdict(
                remedy="plugback",
                quote=RECOMPLETE_SHALLOWER,
                anchor=REMEDIAL_PLUG,
                evidence=(
                    f"the target zone ({target_top:g}-{target_base:g} ft) is shallower than "
                    f"the zone being killed ({killed_top:g}-{killed_base:g} ft), which is "
                    "the source's stated plug indication: \"" + PLUG_PURPOSES + "\"",
                    f"the zone being killed is open to this completion (its top at "
                    f"{killed_top:g} ft is at or above the completion depth of "
                    f"{completion:g} ft), so a plug above it isolates it: \""
                    + PERMANENT_PLUG
                    + "\"",
                    "a plug seals the wellbore, and the zone being killed is below it: \""
                    + PLUG_SEALS_THE_WELLBORE
                    + "\"",
                ),
            )
        )
        # The window, not a setting depth. The source states no plug length, no cement
        # volume and no minimum column, so the endpoints are the caller's own two depths.
        plug_window = Range(
            low=target_base,
            high=killed_top,
            unit="ft MD",
            method=(
                "geometric window only: a plug must sit below the base of the target zone "
                "and above the top of the zone being killed. The source states no plug "
                "length, setting depth or cement volume — \"place a cement plug at the "
                "required depth\" is as specific as it gets — so no point inside this "
                "window is recommended over another"
            ),
            source=REMEDIAL_PLUG,
            members={
                "target_zone_base_ft": target_base,
                "killed_zone_top_ft": killed_top,
                "window_length_ft": killed_top - target_base,
            },
        )
        if killed_top - target_base == 0:
            flags.append(
                "the target zone and the zone being killed abut exactly "
                f"({target_base:g} ft): the geometric window for the plug has zero length. "
                "The source states no minimum plug length, so this tool cannot say whether "
                "a competent plug fits — it reports the window and stops."
            )

    if killed_is_shallower:
        verdicts.append(
            Verdict(
                remedy="squeeze",
                quote=BLOCK_SQUEEZE,
                anchor=REMEDIAL,
                evidence=(
                    f"the zone being killed ({killed_top:g}-{killed_base:g} ft) lies ABOVE "
                    f"the target ({target_top:g}-{target_base:g} ft), so the source's plug "
                    f"indication — \"{RECOMPLETE_SHALLOWER}\" — does not apply",
                    "a plug set to isolate it would cut off the target below it, because a "
                    "plug seals the wellbore: \"" + PLUG_SEALS_THE_WELLBORE + "\"",
                    "the source's sentence for this geometry is a squeeze: \""
                    + BLOCK_SQUEEZE
                    + "\"",
                ),
                next_tool=SQUEEZE_TOOL,
            )
        )
        if target_top > completion:
            flags.append(
                f"the target zone ({target_top:g}-{target_base:g} ft) lies below the current "
                f"completion depth ({completion:g} ft), so it is not open to the wellbore "
                "yet. Perforating it is outside both sources; this tool decided only which "
                "remedy isolates the zone above it."
            )

    # Additional squeeze indications, which may be added to a plugback verdict. The two are
    # not exclusive and the source says so three times.
    squeeze_extra: list[str] = []

    if flow_path in OUTSIDE_WELLBORE:
        squeeze_extra.append(
            f"communication is stated to be in the {flow_path.replace('_', ' ')}"
            + (
                f" at {communication_depth_ft:g} ft"
                if communication_depth_ft is not None
                else ""
            )
            + ", which a plug does not reach: a plug \"must prevent fluid flow in a "
            "wellbore\", while a squeeze forces cement \"through the perforations and into "
            "the annulus to fill the voids\" (" + SLB_CEMENTING + ")"
        )
    elif flow_path is None:
        flags.append(
            "flow_path was not stated, so behind-pipe communication has not been ruled out. "
            "The decision above is on zone positions alone. A plug seals the wellbore only "
            "(\"" + PLUG_SEALS_THE_WELLBORE + "\"); annular communication would add a "
            f"squeeze verdict and is diagnosed by a bond log, not by depths."
        )

    if (
        flow_path == "wellbore"
        and communication_depth_ft is not None
        and target_is_shallower
        and communication_depth_ft < target_base
    ):
        squeeze_extra.append(
            f"the stated communication at {communication_depth_ft:g} ft is ABOVE the "
            f"plug window ({target_base:g}-{killed_top:g} ft), and a plug isolates what is "
            "below it, so plugging back does not address it: \""
            + SQUEEZE_SEALS_THE_ANNULUS
            + "\""
        )

    if mechanical_support == "squeeze_retainer":
        squeeze_extra.append(
            "a squeeze retainer is to be used, which the source describes as combined with "
            "the plug rather than as an alternative to it: \"" + MECHANICAL_ENHANCEMENT + "\""
        )
        if sequence is None:
            sequence = (
                "the retainer is set and squeezed first; the plug is then placed \"through "
                "and above\" it — the order is the source's preposition, not a stated "
                "procedure: \"" + MECHANICAL_ENHANCEMENT + "\""
            )
    elif mechanical_support == "bridge_plug":
        notes.append(
            "a bridge plug is a MECHANICAL enhancement of the plug, not a squeeze, so it "
            "adds no squeeze verdict: \"" + MECHANICAL_ENHANCEMENT + "\""
        )

    if shut_off_perforations is True:
        squeeze_extra.append(
            "perforations are to be shut off, which the source states as a combined "
            "plug-and-squeeze method: \"" + COMBINED_METHOD + "\""
        )
        if sequence is None:
            sequence = (
                "squeeze first, cement second — the source states this order: \""
                + COMBINED_METHOD
                + "\""
            )

    if openhole_low_pressure_zone_present is True:
        squeeze_extra.append(
            "a low-pressure zone is open in openhole, for which the source names a plug as "
            "a precursor to the squeeze, not an alternative: \"" + PLUG_BEFORE_SQUEEZE + "\""
        )
        # This order IS stated ("before squeezing"), so it outranks the retainer wording.
        sequence = (
            "plug first, squeeze second — the source states the order: \""
            + PLUG_BEFORE_SQUEEZE
            + "\" (" + REMEDIAL_PLUG + "). squeeze_recommend (#108) emits the matching "
            "prerequisite for this case."
        )
        if not target_is_shallower:
            notes.append(
                "the plug here protects the low-pressure zone during the squeeze; it is not "
                "the plugback of a producing interval."
            )

    if squeeze_extra:
        existing = next((v for v in verdicts if v.remedy == "squeeze"), None)
        if existing is None:
            verdicts.append(
                Verdict(
                    remedy="squeeze",
                    quote=SQUEEZE_SEALS_THE_ANNULUS,
                    anchor=SLB_CEMENTING,
                    evidence=tuple(squeeze_extra),
                    next_tool=SQUEEZE_TOOL,
                )
            )
        else:
            verdicts = [
                v
                if v.remedy != "squeeze"
                else Verdict(
                    remedy=v.remedy,
                    quote=v.quote,
                    anchor=v.anchor,
                    evidence=v.evidence + tuple(squeeze_extra),
                    next_tool=v.next_tool,
                )
                for v in verdicts
            ]

    # Order: plugback first, matching the source's own order of description.
    verdicts.sort(key=lambda v: 0 if v.remedy == "plugback" else 1)
    combined = len(verdicts) == 2

    if combined:
        notes.append(
            "both remedies are indicated, and the source treats them as combinable rather "
            "than exclusive: \"" + MECHANICAL_ENHANCEMENT + "\" and \"" + COMBINED_METHOD + "\""
        )
    if any(v.remedy == "squeeze" for v in verdicts):
        notes.append(
            f"this tool does not select a squeeze technique. {SQUEEZE_TOOL} does, and it "
            "requires the diagnosis, the five-step go/no-go list, void type, fracture "
            "pressure, injectivity, available tools and circulation rate — none of which "
            "this tool has or infers. " + UNNECESSARY_SQUEEZE_WARNING
        )
    if diagnosis in NO_SQUEEZE_ALTERNATIVE:
        notes.append(
            f"the source names a plug and no squeeze alternative for '{diagnosis}': \""
            + NO_SQUEEZE_ALTERNATIVE[diagnosis]
            + "\""
        )

    return PlugbackSqueezeDecision(
        verdicts=tuple(verdicts),
        combined=combined,
        plug_window=plug_window,
        sequence=sequence,
        notes=tuple(dict.fromkeys(notes)),
        flags=tuple(dict.fromkeys(flags)),
        inputs={
            "target_zone_top_ft": target_top,
            "target_zone_base_ft": target_base,
            "killed_zone_top_ft": killed_top,
            "killed_zone_base_ft": killed_base,
            "current_completion_depth_ft": completion,
            "diagnosis": diagnosis,
            "flow_path": flow_path,
            "communication_depth_ft": communication_depth_ft,
            "mechanical_support": mechanical_support,
            "shut_off_perforations": shut_off_perforations,
            "openhole_low_pressure_zone_present": openhole_low_pressure_zone_present,
        },
        source=REMEDIAL_PLUG,
    )
