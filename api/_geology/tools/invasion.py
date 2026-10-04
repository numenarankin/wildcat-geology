"""Group D, #37 `invasion_profile` and #38 `microlog_permeability_flag`.

Two tools about what happens in the first few inches of rock around the borehole:
how far the mud filtrate got, and whether it got in at all. They share a module
because they share a subject and a source neighbourhood, not because they share a
letter.

Specs: `specs/37-invasion_profile.md`, `specs/38-microlog_permeability_flag.md`.

--- the decisions worth explaining ------------------------------------------

**#37 exists to say "no".** `asquith#9` licenses "the deep reading is R_t" in
exactly one place and under exactly one condition: *"The step profile ...
Shallow-reading resistivity logging tools read the resistivity of the invaded
zone (R_i), while deeper reading resistivity logging tools read true resistivity
of the uninvaded zone (R_t)."* Under a transition profile the same segment says
the deep reading "can be corrected to a more accurate value of true resistivity"
- it is an input to a correction, not the answer. And **step cannot be
distinguished from transition by resistivity ordering alone.** The chart that
does it is a vendor tornado/butterfly chart and is not in this corpus.

So the default posture is `rt_status = "not_usable"` with a `Refusal` in `rt`.
That is the point of the tool: `tool-verification.md:137` lists `archie_sw` (#35)
as missing invasion-corrected R_t with the consequence "uncorrected deep readings
are not R_t", and #35 used to take a caller-asserted `rt_invasion_corrected`
boolean. A boolean cannot be wrong in a way anyone notices. A `Refusal` can only
be ignored on purpose.

The gate is not a dead end. `asquith#43` items 1-4 give the one published
step-versus-transition discriminator - compare Archie's S_wa against the ratio
method's S_wr - so #35 can compute a provisional S_wa, call
`InvasionVerdict.reconcile_with_archie(swa)`, and feed a confirmed step profile
back through `with_declared_profile("step", ...)` to get a real `Quantity`.

**#37 needs Rmf and Rw because the ordering is meaningless without them.** The
same three readings mean opposite things in the two mud regimes. `asquith#9`: a
freshwater mud (Rmf > 3 Rw) wet zone shows "high (Rxo), intermediate (Ri), and
low (Rt)"; a freshwater mud hydrocarbon zone shows all three high. A saltwater
mud (Rw = Rmf) wet zone shows all three low; a saltwater mud hydrocarbon zone
shows "low (Rxo), intermediate (Ri) and high (Rt)". A **flat** triple is
therefore a wet zone in salt mud and a hydrocarbon zone in fresh mud. Classifying
on ordering alone would be wrong half the time and would never know it.

**The annulus is an artefact of the number, not of the fluid call.** `asquith#9`
says the annulus profile "can only occur in zones that bear hydrocarbons" - so it
is the strongest hydrocarbon indication in the segment, not a false one. What is
false is the deep reading: it is inflated by the annular ring of displaced
formation water. `asquith#43` case 3 confirms it from the saturation side. The
verdict therefore reports `fluid_indication` and `rt` separately, and conflating
them is the defect this separation prevents.

**#38 refuses in saltwater and gypsum muds because a negative result would be
meaningless.** `asquith#33`: "Where the pad is in contact with the formation,
positive separation cannot occur." Not "is less reliable" - cannot occur. So "no
separation" in those muds carries no information about permeability and the tool
must not report one.

**#38 never emits an R_xo.** Same segment: the microlog "generally does not
provide a good estimate of flushed-zone resistivity (R_xo)". `MicrologFlag.rxo`
is therefore a permanently-populated `Refusal` rather than an absent field, so a
consumer reaching for it gets the reason and cannot feed it to #37's shallow
input by accident.

**#38's R_m has two different meanings and they are different arguments.** The
header R_m sits in the `Rmc > Rm > Rmf` ordering test, which is
temperature-invariant (Arps scales all three by one monotone factor). Hilchie's
tight-rock rule is "approximately ten times the resistivity of the drilling mud
(R_m) **at formation temperature**", which is not. In the repass fixture those
are 1.68 and 1.15 ohm-m - a 1.5x difference in the cutoff, enough to flip the
verdict. The tool takes `rm_at_formation_temp_ohmm` separately and withholds the
tight verdict rather than substituting the header value.
"""
from __future__ import annotations

import math

from dataclasses import dataclass, field
from typing import Any

from .result import Quantity, Refusal

# --- corpus anchors -----------------------------------------------------------

ASQUITH_INVASION = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9"
ASQUITH_RATIO = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#43"
ASQUITH_MICROLOG = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#33"
ASQUITH_PROFILE_REVIEW = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#10"
ASQUITH_DUAL_INDUCTION = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#32"

# --- what a "wet" profile does and does not establish --------------------------
#
# asquith#10 closes BOTH water-bearing profile descriptions - freshwater and
# saltwater - with one sentence: "Both the above examples assume that the water
# saturation of the uninvaded zone is much greater than 60%." 60% is not 100%.
# The same paragraph does say "true resistivity (R_t) is equal to wet resistivity
# (R_o) because the formation is completely saturated with formation water", and
# the two cannot both be taken at face value; the 60% sentence is the later
# qualifier and governs both examples, so it wins.
#
# This matters outside this tool. formation_factor_field (#99) refuses a wet
# resistivity profile as evidence for R_o on exactly this ground, so #37 must not
# hand a consumer an unqualified "wet" that #99 would then have to argue with.
# Two tools reading the same evidence have to say the same thing about it.
WET_PROFILE_SW_CAVEAT = (
    "fluid_indication='wet' means the published wet resistivity profile, not S_w = 1. "
    f"{ASQUITH_PROFILE_REVIEW} closes both water-bearing profile descriptions with 'Both the "
    "above examples assume that the water saturation of the uninvaded zone is much greater "
    "than 60%', which permits a substantial hydrocarbon saturation. This verdict is not "
    "evidence that R_t = R_o - formation_factor_field (#99) refuses it as such - and nothing "
    "downstream may take it as a wet-zone certification"
)

# --- which shallow curve may be called R_xo ------------------------------------
#
# The corpus does not settle this and the build has already recorded the split
# twice. mnemonic_normalize (#9) gives RFOC a `measures` string that deliberately
# leaves the zone undetermined - "Consumers must treat the zone as undetermined
# rather than assume R_xo" - and analysis_feasibility (#101) lets SFL / LL8 / RFOC
# fill R_i unconditionally but R_xo only CONDITIONALLY, attaching the conflict.
#
# asquith#9's profile description labels the shallow reading R_xo, and that is
# enough for the ORDERING rule, which only needs three depths of investigation.
# It is not enough for asquith#43 Eq. 7.4, whose R_xo is the flushed zone.
# asquith#32 puts the dual induction's shallow focused curve in the INVADED zone
# twice, and asquith#33 reserves R_xo for the pad-type micro devices. So the MHI
# and S_wr carry the conflict unless the caller names a pad-type device.
PAD_RXO_DEVICES: tuple[str, ...] = ("msfl", "mll", "pl", "rxo", "proximity",
                                    "microlaterolog", "microspherically focused")
SHALLOW_FOCUSED_DEVICES: tuple[str, ...] = ("sfl", "sflu", "ll8", "laterolog-8",
                                            "laterolog8", "rfoc", "spherically focused")
MICROLOG_DEVICES: tuple[str, ...] = ("ml", "microlog", "minv", "mnor", "micronormal",
                                     "microinverse")

SHALLOW_FOCUSED_RXO_CAVEAT = (
    "the shallow curve was not declared to be a pad-type micro device, so its zone is "
    f"undetermined and this R_xo may be reading the invaded zone. {ASQUITH_DUAL_INDUCTION} puts "
    "the dual induction's shallow focused curve in the invaded zone twice ('similar in depth of "
    "investigation to the short normal'; 'R_i = resistivity tool measuring in the invaded zone, "
    f"usually laterolog-8 or spherically focused log') and {ASQUITH_MICROLOG} reserves R_xo for "
    "the pad-type micro devices (MLL, PL, MSFL); only asquith#11's SFLU caption and asquith#43's "
    "R_xo gloss read it as the flushed zone. mnemonic_normalize (#9) leaves RFOC's zone "
    "deliberately undetermined and analysis_feasibility (#101) marks this R_xo route "
    "conditional; this tool agrees. Declare shallow_device='MSFL' (or MLL / PL / RXO) to clear "
    "it, or accept an S_w/S_xo and S_wr biased by a shallow reading that is not the flushed zone"
)

# --- #37 thresholds -----------------------------------------------------------
#
# SOURCED. asquith#9 prints the freshwater definition inline: "A freshwater mud
# (i.e., R_mf > 3 R_w) results in a *wet* log profile ...". The saltwater case is
# written only as "R_w = R_mf" / "approximately equal", with no tolerance - see
# SALT_RATIO_TOLERANCE below.
FRESHWATER_RMF_OVER_RW = 3.0

# SOURCED, asquith#43 p. 116, verbatim: "If the ratio Sw/Sxo is equal to or
# greater than 1.0, then hydrocarbons were not moved during invasion. This is
# true regardless of whether or not a formation contains hydrocarbons. Whenever
# the ratio Sw/Sxo is less than 0.7 for sandstones or less than 0.6 for
# carbonates, moveable hydrocarbons are indicated (Schlumberger, 1972)."
#
# Note what this is NOT: a partition. [0.7, 1.0) for sandstone and [0.6, 1.0) for
# carbonate are unnamed by the source, and the tool reports "not_stated" there.
MHI_NONE_MOVED = 1.0
MHI_MOVEABLE_CUTOFF: dict[str, float] = {"sandstone": 0.7, "carbonate": 0.6}

# The exponents of Eqs. 7.4 and 7.7. 7.4 is the square root because n = 2; 7.7 is
# 5/8, printed both as a fraction (Eq. 7.6) and as 0.625 (Eq. 7.7).
MHI_EXPONENT = 0.5
SWR_EXPONENT = 0.625
# asquith#43 writes "The cementation exponent (n) is assumed to be 2.0" under
# Eq. 7.4. n is the *saturation* exponent; asquith#33 labels the same symbol
# correctly ("The saturation exponent (n) is assumed to be 2"). A labelling slip
# in the source, recorded and not acted on - the arithmetic is identical.
MHI_N = 2.0
MHI_N_NOTE = ("n = 2.0, the saturation exponent; asquith#43 labels it "
              "'cementation exponent' under Eq. 7.4, which is a slip - asquith#33 "
              "labels the same symbol correctly. Arithmetic unaffected.")

# PROVISIONAL. The source says only "R_w = R_mf" and "approximately equal".
SALT_RATIO_TOLERANCE = 1.25
# PROVISIONAL. asquith#9 says the readings "separate" and never says by how much.
SEPARATION_RATIO_TOLERANCE = 1.10
# PROVISIONAL. asquith#43 item 1 writes "If S_wa ~ S_wr" and gives no tolerance.
RECONCILE_TOLERANCE = 1.10
# SOURCED, asquith#43 Eq. 7.8 (Schlumberger, 1977): (Sw)_COR = Swa * (Swa/Swr)^0.25
SW_COR_EXPONENT = 0.25

THRESHOLD_STATUS_37: dict[str, str] = {
    "freshwater_mud": f"SOURCED ({ASQUITH_INVASION}: Rmf > {FRESHWATER_RMF_OVER_RW} Rw)",
    "mhi_bands": f"SOURCED ({ASQUITH_RATIO}: >= 1.0 none moved; < 0.7 sandstone / "
                 "< 0.6 carbonate moveable; the interval between is unnamed)",
    "saltwater_mud": f"PROVISIONAL (Rmf/Rw within +/-{(SALT_RATIO_TOLERANCE - 1) * 100:.0f}%; "
                     f"{ASQUITH_INVASION} says only 'Rw = Rmf')",
    "separation": f"PROVISIONAL (ratio dead-band; {ASQUITH_INVASION} says 'separate' "
                  "with no magnitude)",
    "reconcile": f"PROVISIONAL ({ASQUITH_RATIO} item 1 writes 'S_wa ~ S_wr' with no tolerance)",
}

TOOL_FAMILIES: tuple[str, ...] = ("induction", "laterolog")
PROFILES: tuple[str, ...] = ("step", "transition", "annulus")
LITHOLOGY_CLASSES: tuple[str, ...] = tuple(sorted(MHI_MOVEABLE_CUTOFF))

# --- #38 thresholds -----------------------------------------------------------
#
# SOURCED, asquith#33 p. 90: "Hilchie (1978) states that resistivities of
# approximately ten times the resistivity of the drilling mud (R_m) at formation
# temperature indicate an impermeable zone." The "approximately" is the source's
# own hedge and is flagged wherever this decides a verdict; no softer multiplier
# is invented.
TIGHT_RM_MULTIPLE = 10.0

# CALLER. asquith#33 says the micronormal "reads higher resistivity than the
# microinverse" with no magnitude, and calls the false shale case "minor,
# positive separation" without quantifying "minor".
SEPARATION_TOLERANCE_OHMM = 0.0
# CALLER. "mudcake is indicated where the caliper shows a borehole size smaller
# than the diameter of the drill bit". Mudcake is fractions of an inch thick, so
# a washout-sized cutoff here would miss every real mudcake.
MUDCAKE_TOLERANCE_IN = 0.0
# PROVISIONAL, borrowed from the catalog's own washout gate (tool-catalog.md:100),
# which is the house rule already settled for exactly this measurement.
ENLARGEMENT_TOLERANCE_IN = 1.0

THRESHOLD_STATUS_38: dict[str, str] = {
    "positive_separation": f"SOURCED ({ASQUITH_MICROLOG}: micronormal > microinverse)",
    "precondition": f"SOURCED ({ASQUITH_MICROLOG}: 'Positive separation can only occur "
                    "when Rmc > Rm > Rmf')",
    "mudcake_caliper": f"SOURCED, qualitative ({ASQUITH_MICROLOG}: caliper below bit size)",
    "tight": f"SOURCED ({ASQUITH_MICROLOG}, Hilchie 1978: ~{TIGHT_RM_MULTIPLE:.0f} x Rm at "
             "formation temperature)",
    "mud_refusal": f"SOURCED ({ASQUITH_MICROLOG}: saltwater and gypsum-based muds)",
    "separation_deadband": f"CALLER (default {SEPARATION_TOLERANCE_OHMM} ohm-m; the source "
                           "gives no magnitude)",
    "mudcake_deadband": f"CALLER (default {MUDCAKE_TOLERANCE_IN} in; the source says only "
                        "'smaller than the diameter of the drill bit')",
    "enlargement_deadband": f"PROVISIONAL (default {ENLARGEMENT_TOLERANCE_IN} in, the "
                            "catalog's washout gate, tool-catalog.md:100; the source says "
                            "only 'enlarged')",
}

# Mud-type classification for #38's refusals. Token lists, not a parser: header
# ~P MUD is free text ("CHEM-GEL", "GYP", "SALT SATURATED"). Deliberately
# conservative - KCl and polymer muds are not on the saltwater list, because
# asquith#33 defines the saltwater case by fluid resistivities (Rmf ~ Rw), which
# is tested separately and exactly whenever Rw is supplied.
SALTWATER_MUD_TOKENS: tuple[str, ...] = (
    "salt water", "saltwater", "salt-water", "salt sat", "saturated salt",
    "brine", "sea water", "seawater", "nacl", "salt mud", "salt ",
)
GYPSUM_MUD_TOKENS: tuple[str, ...] = ("gyp", "gypsum", "plaster", "anhydrite mud")
# Not from asquith#33 - the segment does not discuss oil-based mud at all. A pad
# resistivity device in a non-conductive continuous phase is outside everything
# it describes, so this refuses by judgement rather than by quotation, and says so.
OIL_MUD_TOKENS: tuple[str, ...] = (
    "oil base", "oil-base", "oil based", "obm", "invert", "diesel", "synthetic",
)


# --- small helpers ------------------------------------------------------------

def _finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _positive(value: Any) -> bool:
    return _finite(value) and float(value) > 0.0


def _ratio_tolerance(name: str, value: float) -> float:
    v = float(value)
    if not (v > 1.0):
        raise ValueError(
            f"{name} must be greater than 1.0 (it is a ratio dead-band, applied as "
            f"[1/{name}, {name}]), got {value!r}")
    return v


def _classify_shallow_device(device: Any) -> str:
    """-> "pad" | "focused" | "microlog" | "undeclared".

    A free-text device name, not an enum: callers hold mnemonics ("RFOC"), tool
    names ("MSFL") and header strings ("DUAL INDUCTION FOCUSED LOG"). Anything
    unrecognised is treated as undeclared, which is the conservative branch - it
    keeps the R_xo conflict attached rather than clearing it on a guess.
    """
    if device is None or not str(device).strip():
        return "undeclared"
    text = f" {str(device).strip().lower()} "
    for token in MICROLOG_DEVICES:
        if f" {token} " in text or f" {token}" == text.rstrip():
            return "microlog"
    for token in PAD_RXO_DEVICES:
        if token in text:
            return "pad"
    for token in SHALLOW_FOCUSED_DEVICES:
        if token in text:
            return "focused"
    return "undeclared"


def _choice(value: Any, allowed: tuple[str, ...], argument: str) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower()
    if key not in allowed:
        raise ValueError(
            f"{argument}={value!r} is not one of {allowed}; this tool does not guess.")
    return key


# =============================================================================
# #37  invasion_profile
# =============================================================================

@dataclass(frozen=True)
class RatioReconcile:
    """The `asquith#43` items 1-4 comparison of Archie S_wa against ratio S_wr.

    The one published discriminator between a step and a transition profile.
    `sw_corrected` is Eq. 7.8 and exists only in case 3.
    """

    profile: str            # "step" | "transition" | "annulus"
    verdict: str            # the source's own sentence for the case
    ratio: Quantity         # S_wa / S_wr
    swa: Quantity
    swr: Quantity
    sw_corrected: Quantity | None
    note: str
    source: str = ASQUITH_RATIO


@dataclass(frozen=True)
class InvasionVerdict:
    """What #37 returns. The contract `archie_sw` (#35) consumes.

    `rt` is the field that matters: a `Quantity` may be used as R_t in Archie, a
    `Refusal` may not, and #35 is specified to propagate the refusal rather than
    downgrade it to a flag on a returned saturation.

    `fluid_indication` and `rt` are separate on purpose. An annulus profile is a
    hydrocarbon indication (asquith#9: it "can only occur in zones that bear
    hydrocarbons") whose deep reading is an artefact. Both facts have to survive.
    """

    rt: Quantity | Refusal
    rt_status: str            # "usable" | "corrected" | "not_usable"
    profile: str
    mud_regime: str           # "freshwater" | "saltwater" | "intermediate"
    fluid_indication: str     # "wet" | "hydrocarbon" | "indeterminate"
    ordering: str             # "descending" | "flat" | "ascending" | "non_monotonic"
    annulus_effect: bool
    separations: dict[str, Quantity]
    mhi: Quantity | Refusal
    mhi_verdict: str
    swr: Quantity | Refusal
    source: str = ASQUITH_INVASION
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()
    call: dict[str, Any] = field(default_factory=dict)

    @property
    def rt_usable(self) -> bool:
        return self.rt_status != "not_usable"

    def rt_for_archie(self) -> Quantity | Refusal:
        """The #35 entry point, named so the call site reads as what it is."""
        return self.rt

    def with_declared_profile(self, profile: str, profile_source: str) -> Any:
        """Re-run with an externally established profile.

        The route back from `reconcile_with_archie`: #35 computes a provisional
        S_wa off the uncorrected deep reading, reconciles, and if the answer is a
        step profile it comes back here for a real R_t. A declared profile that
        contradicts the readings does **not** win - see the conflict flag in
        `invasion_profile`.
        """
        kwargs = dict(self.call)
        kwargs["profile_declared"] = profile
        kwargs["profile_source"] = profile_source
        return invasion_profile(**kwargs)

    def reconcile_with_archie(self, swa: float,
                              tolerance: float = RECONCILE_TOLERANCE
                              ) -> RatioReconcile | Refusal:
        """asquith#43 p. 117, items 1-4. Compares Archie S_wa against ratio S_wr.

        1. S_wa ~ S_wr  -> step-contact profile, "all values determined
           (S_w, R_t, R_xo and d_i) are correct".
        2. S_wa > S_wr  -> R_xo/R_t too low; a transition-type profile might be
           indicated and S_wa "is considered a good value".
        3. S_wa < S_wr  -> R_xo/R_t too high; an annulus-type profile might be
           indicated. Eq. 7.8 gives the corrected saturation.
        4. S_wa < S_wr  -> may instead be a carbonate with moldic porosity and
           low permeability. Carried as a note, because the source offers it as
           an alternative reading of the same observation, not a different test.
        """
        tol = _ratio_tolerance("tolerance", tolerance)
        if isinstance(self.swr, Refusal):
            return Refusal(
                reason=("the ratio-method S_wr could not be computed, so there is nothing "
                        "to reconcile Archie's S_wa against: " + self.swr.reason),
                needed=tuple(self.swr.needed) or ("a ratio-method S_wr",),
                source=ASQUITH_RATIO)
        if not _positive(swa):
            raise ValueError(f"swa must be a positive saturation, got {swa!r}")
        swa_q = Quantity(
            value=float(swa), unit="v/v",
            method="Archie water saturation, supplied by the caller (#35)",
            source=ASQUITH_RATIO, inputs={"S_wa": float(swa)})
        ratio_value = float(swa) / self.swr.value
        ratio = Quantity(
            value=ratio_value, unit="ratio", method="S_wa / S_wr (asquith#43 items 1-4)",
            source=ASQUITH_RATIO,
            inputs={"S_wa": float(swa), "S_wr": self.swr.value},
            assumptions={"tolerance": tol,
                         "tolerance_status": THRESHOLD_STATUS_37["reconcile"]})

        if 1.0 / tol <= ratio_value <= tol:
            return RatioReconcile(
                profile="step", ratio=ratio, swa=swa_q, swr=self.swr, sw_corrected=None,
                verdict=("S_wa ~ S_wr: the assumption of a step-contact invasion profile is "
                         "indicated to be correct, and all values determined (S_w, R_t, R_xo "
                         "and d_i) are correct"),
                note=("asquith#43 item 1. Feed this back through "
                      "with_declared_profile('step', <source>) to clear the deep reading as "
                      f"R_t. The '~' tolerance is ours: {THRESHOLD_STATUS_37['reconcile']}"))
        if ratio_value > tol:
            return RatioReconcile(
                profile="transition", ratio=ratio, swa=swa_q, swr=self.swr, sw_corrected=None,
                verdict=("S_wa > S_wr: R_xo/R_t is too low - R_xo too low because invasion is "
                         "very shallow, or R_t too high because invasion is very deep. A "
                         "transition-type invasion profile might be indicated and S_wa is "
                         "considered a good value for the zone's actual water saturation"),
                note=("asquith#43 item 2. The deep reading is still not R_t; the source's "
                      "advice is to trust S_wa, not to promote the deep resistivity."))
        sw_cor = float(swa) * (ratio_value ** SW_COR_EXPONENT)
        return RatioReconcile(
            profile="annulus", ratio=ratio, swa=swa_q, swr=self.swr,
            sw_corrected=Quantity(
                value=sw_cor, unit="v/v",
                method="corrected water saturation, Schlumberger 1977 (asquith#43 Eq. 7.8)",
                source=ASQUITH_RATIO,
                inputs={"S_wa": float(swa), "S_wr": self.swr.value},
                assumptions={"exponent": SW_COR_EXPONENT}),
            verdict=("S_wa < S_wr: R_xo/R_t is too high - R_xo too high from adjacent "
                     "high-resistivity beds, or R_t estimated from the deep resistivity "
                     "measurement is too low. An annulus-type invasion profile might be "
                     "indicated and/or S_xo < S_w^(1/5)"),
            note=("asquith#43 items 3 and 4. Eq. 7.8 applied. Item 4 offers an alternative "
                  "reading of the same observation: the reservoir might be a carbonate with "
                  "moldic (oomoldic, fossil-moldic) porosity and low permeability."))


def _ratio_quantity(numerator: float, denominator: float, label: str, source: str,
                    inputs: dict[str, Any],
                    assumptions: dict[str, Any] | None = None) -> Quantity:
    return Quantity(
        value=numerator / denominator, unit="ratio", method=label, source=source,
        inputs=inputs, assumptions=assumptions or {})


def _classify_mud_regime(rmf: float, rw: float, salt_tol: float) -> tuple[str, str]:
    """-> (regime, why). asquith#9 defines one end and gestures at the other."""
    ratio = rmf / rw
    if ratio > FRESHWATER_RMF_OVER_RW:
        return ("freshwater",
                f"Rmf/Rw = {ratio:.3g} > {FRESHWATER_RMF_OVER_RW}; asquith#9 defines a "
                "freshwater mud as Rmf > 3 Rw")
    if 1.0 / salt_tol <= ratio <= salt_tol:
        return ("saltwater",
                f"Rmf/Rw = {ratio:.3g} is within the +/-{(salt_tol - 1) * 100:.0f}% band "
                "around 1; asquith#9 writes the saltwater case as 'Rw = Rmf'")
    return ("intermediate",
            f"Rmf/Rw = {ratio:.3g} falls between the saltwater band and the freshwater cut "
            f"of {FRESHWATER_RMF_OVER_RW}; asquith#9 describes no profile here")


def _classify_ordering(deep_over_medium: float, medium_over_shallow: float | None,
                       tol: float) -> str:
    """Shallow -> deep ordering.

    'ascending' means resistivity rises with depth of investigation, which is the
    saltwater-mud hydrocarbon signature and the direction the annulus exaggerates.
    """
    def sign(r: float) -> int:
        if r > tol:
            return 1
        if r < 1.0 / tol:
            return -1
        return 0

    dm = sign(deep_over_medium)
    if medium_over_shallow is None:
        return {1: "ascending", -1: "descending", 0: "flat"}[dm]
    ms = sign(medium_over_shallow)
    if dm == 0 and ms == 0:
        return "flat"
    if dm >= 0 and ms >= 0:
        return "ascending"
    if dm <= 0 and ms <= 0:
        return "descending"
    return "non_monotonic"


#: asquith#9, "Water-bearing Zones" and "Hydrocarbon-bearing Zones", as a table.
#: A flat triple is wet in salt mud and hydrocarbon-bearing in fresh mud, which
#: is the entire reason Rmf and Rw are required inputs.
_FLUID_TABLE: dict[tuple[str, str], str] = {
    ("freshwater", "descending"): "wet",
    ("freshwater", "flat"): "hydrocarbon",
    ("freshwater", "ascending"): "hydrocarbon",
    ("saltwater", "flat"): "wet",
    ("saltwater", "ascending"): "hydrocarbon",
}

_FLUID_BASIS: dict[tuple[str, str], str] = {
    ("freshwater", "descending"): ("asquith#9: a freshwater mud wet profile has the shallow, "
                                   "medium and deep measurements separate and record high "
                                   "(Rxo), intermediate (Ri) and low (Rt) resistivities"),
    ("freshwater", "flat"): ("asquith#9: a hydrocarbon zone invaded with freshwater mud has "
                             "the shallow, medium and deep measurements all record high "
                             "resistivities"),
    ("freshwater", "ascending"): ("asquith#9: a hydrocarbon zone invaded with freshwater mud "
                                  "reads all high, and 'in some instances, the deep "
                                  "resistivity is higher than the medium resistivity'"),
    ("saltwater", "flat"): ("asquith#9: a saltwater mud wet profile has the shallow, medium "
                            "and deep measurements all read low resistivity"),
    ("saltwater", "ascending"): ("asquith#9: a hydrocarbon zone invaded with saltwater mud has "
                                 "the measurements separate and record low (Rxo), intermediate "
                                 "(Ri) and high (Rt) resistivities"),
}


def invasion_profile(
    r_deep_ohmm: float,
    r_medium_ohmm: float,
    *,
    rmf_ohmm: float,
    rw_ohmm: float,
    rmf_source: str,
    rw_source: str,
    r_shallow_ohmm: float | None = None,
    shallow_device: str | None = None,
    lithology_class: str | None = None,
    tool_family: str | None = None,
    rt_corrected_ohmm: float | None = None,
    rt_corrected_source: str | None = None,
    profile_declared: str | None = None,
    profile_source: str | None = None,
    separation_ratio_tolerance: float = SEPARATION_RATIO_TOLERANCE,
    salt_ratio_tolerance: float = SALT_RATIO_TOLERANCE,
    allow_uncorrected_rt: bool = False,
    depth_ft: float | None = None,
) -> InvasionVerdict | Refusal:
    """Characterize invasion from a shallow / medium / deep resistivity triple.

    asquith#9 (p. 7) for the three profiles and the two mud regimes; asquith#43
    (pp. 116-117) for the moveable-hydrocarbon index and its thresholds.

    Answers two questions and keeps them apart: what fluid the profile indicates,
    and whether the deep reading may be used as R_t. The second is the contract
    `archie_sw` (#35) consumes - see `InvasionVerdict.rt`.

    Rmf and Rw are required and must be at formation temperature. Without them
    the ordering has no meaning: the same flat triple is a wet zone in saltwater
    mud and a hydrocarbon zone in freshwater mud.
    """
    sep_tol = _ratio_tolerance("separation_ratio_tolerance", separation_ratio_tolerance)
    salt_tol = _ratio_tolerance("salt_ratio_tolerance", salt_ratio_tolerance)
    litho = _choice(lithology_class, LITHOLOGY_CLASSES, "lithology_class")
    family = _choice(tool_family, TOOL_FAMILIES, "tool_family")
    declared = _choice(profile_declared, PROFILES, "profile_declared")

    call: dict[str, Any] = {
        "r_deep_ohmm": r_deep_ohmm, "r_medium_ohmm": r_medium_ohmm,
        "rmf_ohmm": rmf_ohmm, "rw_ohmm": rw_ohmm,
        "rmf_source": rmf_source, "rw_source": rw_source,
        "r_shallow_ohmm": r_shallow_ohmm, "shallow_device": shallow_device,
        "lithology_class": lithology_class,
        "tool_family": tool_family,
        "rt_corrected_ohmm": rt_corrected_ohmm,
        "rt_corrected_source": rt_corrected_source,
        "profile_declared": profile_declared, "profile_source": profile_source,
        "separation_ratio_tolerance": separation_ratio_tolerance,
        "salt_ratio_tolerance": salt_ratio_tolerance,
        "allow_uncorrected_rt": allow_uncorrected_rt, "depth_ft": depth_ft,
    }

    # --- gates that stop a verdict existing at all ---------------------------
    for name, value in (("rmf_ohmm", rmf_ohmm), ("rw_ohmm", rw_ohmm)):
        if not _positive(value):
            return Refusal(
                reason=(f"{name} is {value!r}; the invasion profile's meaning is defined by "
                        "the contrast between mud filtrate and formation water, and asquith#9 "
                        "gives opposite readings of the same resistivity ordering in the two "
                        "mud regimes"),
                needed=("Rmf and Rw at formation temperature - the log header for Rmf, and "
                        "rw_from_sp (#33), rw_pickett (#34) or a water analysis for Rw",),
                source=ASQUITH_INVASION)
    missing_prov = [n for n, s in (("rmf_source", rmf_source), ("rw_source", rw_source))
                    if not str(s or "").strip()]
    if missing_prov:
        return Refusal(
            reason=(f"{' and '.join(missing_prov)} not stated; an Rw or Rmf with no provenance "
                    "cannot support an R_t verdict that archie_sw (#35) will act on"),
            needed=tuple(missing_prov),
            source=ASQUITH_INVASION)
    for name, value in (("r_deep_ohmm", r_deep_ohmm), ("r_medium_ohmm", r_medium_ohmm)):
        if not _positive(value):
            return Refusal(
                reason=(f"{name} is {value!r} (null, non-finite or non-positive); the annulus "
                        "test is a deep-versus-medium comparison and there is nothing to "
                        "compare"),
                needed=("a deep and a medium resistivity reading at this depth",
                        "null_scrub (#12) over both curves first"),
                source=ASQUITH_INVASION)
    if rt_corrected_ohmm is not None:
        if not _positive(rt_corrected_ohmm):
            return Refusal(
                reason=f"rt_corrected_ohmm is {rt_corrected_ohmm!r}, not a usable resistivity",
                needed=("a positive invasion-corrected R_t, or omit it",),
                source=ASQUITH_INVASION)
        if not str(rt_corrected_source or "").strip():
            return Refusal(
                reason=("an invasion-corrected R_t was supplied with no stated source; the "
                        "correction chart is not in this corpus, so its provenance is the "
                        "only evidence the correction happened"),
                needed=("rt_corrected_source - which chart or service applied the correction",),
                source=ASQUITH_INVASION)
    if declared is not None and not str(profile_source or "").strip():
        return Refusal(
            reason=(f"profile_declared={declared!r} was supplied with no stated source; "
                    "asquith#9 licenses 'the deep reading is R_t' only under a step profile, "
                    "so an undocumented profile assertion is exactly the boolean this tool "
                    "exists to replace"),
            needed=("profile_source - e.g. the reconcile_with_archie verdict, or a chart",),
            source=ASQUITH_INVASION)

    shallow_ok = _positive(r_shallow_ohmm)
    flags: list[str] = []

    # --- geometry ------------------------------------------------------------
    dm = float(r_deep_ohmm) / float(r_medium_ohmm)
    ms = (float(r_medium_ohmm) / float(r_shallow_ohmm)) if shallow_ok else None
    ordering = _classify_ordering(dm, ms, sep_tol)
    annulus_effect = dm > sep_tol

    separations: dict[str, Quantity] = {
        "deep_over_medium": _ratio_quantity(
            float(r_deep_ohmm), float(r_medium_ohmm),
            "R_deep / R_medium (asquith#9 annulus detector)", ASQUITH_INVASION,
            {"R_deep": float(r_deep_ohmm), "R_medium": float(r_medium_ohmm)},
            {"dead_band": sep_tol, "dead_band_status": THRESHOLD_STATUS_37["separation"]}),
        "rmf_over_rw": _ratio_quantity(
            float(rmf_ohmm), float(rw_ohmm),
            "Rmf / Rw at formation temperature (asquith#9 mud regime)", ASQUITH_INVASION,
            {"Rmf": float(rmf_ohmm), "Rw": float(rw_ohmm)},
            {"freshwater_cut": FRESHWATER_RMF_OVER_RW,
             "status": THRESHOLD_STATUS_37["freshwater_mud"],
             "Rmf_source": rmf_source, "Rw_source": rw_source}),
    }
    if ms is not None:
        separations["medium_over_shallow"] = _ratio_quantity(
            float(r_medium_ohmm), float(r_shallow_ohmm),
            "R_medium / R_shallow", ASQUITH_INVASION,
            {"R_medium": float(r_medium_ohmm), "R_shallow": float(r_shallow_ohmm)},
            {"dead_band": sep_tol, "dead_band_status": THRESHOLD_STATUS_37["separation"]})
    else:
        flags.append(
            "no shallow resistivity supplied; the ordering was called from the deep/medium "
            "pair alone, and the wet-versus-hydrocarbon patterns of asquith#9 are stated over "
            "all three measurements")

    regime, regime_why = _classify_mud_regime(float(rmf_ohmm), float(rw_ohmm), salt_tol)
    fluid = _FLUID_TABLE.get((regime, ordering), "indeterminate")
    fluid_basis = _FLUID_BASIS.get(
        (regime, ordering),
        f"asquith#9 describes no {ordering} profile for a {regime} mud")

    # --- profile -------------------------------------------------------------
    if annulus_effect:
        profile = "annulus"
    elif declared is not None:
        profile = declared
    elif ordering in ("ascending", "descending"):
        profile = "invaded_step_or_transition"
    else:
        profile = "indeterminate"

    if declared == "step" and annulus_effect:
        flags.append(
            "profile_declared='step' contradicts the readings: R_deep exceeds R_medium, which "
            "asquith#9 gives as the annulus detector. The observation stands and the "
            "declaration is not applied - a caller assertion does not overwrite a measurement")
    if annulus_effect:
        if family != "induction":
            seen = family or "not declared"
            flags.append(
                f"an annulus ordering (R_deep > R_medium) was seen but tool_family is {seen}; "
                "asquith#9 says the annulus profile 'is detected only by an induction log run "
                "soon after a well is drilled', so this ordering on another device is not "
                "explained by the source")
        if regime == "saltwater":
            flags.append(
                "an annulus ordering in a saltwater mud: the annulus forms from the "
                "resistivity contrast between displaced formation water and mud filtrate, and "
                "with Rmf ~ Rw there is none. asquith#9 does not describe this case")
    if regime == "intermediate":
        flags.append(
            f"{regime_why}; the wet-versus-hydrocarbon patterns of asquith#9 are published for "
            "the two named regimes only, so the fluid indication is withheld rather than "
            "extrapolated across the gap")
    if ordering == "non_monotonic":
        flags.append(
            "the three readings are not monotonic with depth of investigation; asquith#9's "
            "profiles are all monotonic, so no published pattern matches")
    if fluid == "wet":
        flags.append(WET_PROFILE_SW_CAVEAT)

    # --- the R_t gate, which is the point of the tool -------------------------
    rt: Quantity | Refusal
    if rt_corrected_ohmm is not None:
        rt_status = "corrected"
        rt = Quantity(
            value=float(rt_corrected_ohmm), unit="ohm-m",
            method="invasion-corrected true resistivity, supplied by the caller",
            source=ASQUITH_INVASION,
            inputs={"R_t_corrected": float(rt_corrected_ohmm),
                    "R_deep_uncorrected": float(r_deep_ohmm)},
            assumptions={"correction_source": rt_corrected_source,
                         "basis": "asquith#9: under a transition profile the deep reading "
                                  "'can be corrected to a more accurate value of true "
                                  "resistivity (R_t)'; the chart that does it is not in this "
                                  "corpus, so the correction is the caller's"},
            flags=("R_t was corrected outside this tool; its accuracy is the correction "
                   "source's, not this layer's",)
            + (("the readings show an annulus effect (R_deep > R_medium); confirm the "
                "correction accounted for it",) if annulus_effect else ()))
    elif annulus_effect:
        rt_status = "not_usable"
        rt = Refusal(
            reason=("the deep reading is not R_t: R_deep exceeds R_medium, which asquith#9 "
                    "gives as the annulus detector. The annulus is a ring of formation water "
                    "displaced ahead of the mud filtrate, so the deep curve is reading that "
                    "ring, not the uninvaded zone. asquith#43 case 3 records the same failure "
                    "from the saturation side: 'R_t estimated from the deep resistivity "
                    "measurement is too low ... an annulus-type invasion profile might be "
                    "indicated'. Note this profile is still a hydrocarbon indication - "
                    "asquith#9: it 'can only occur in zones that bear hydrocarbons' - the "
                    "artefact is in the number, not in the fluid call"),
            needed=("an invasion-corrected R_t (rt_corrected_ohmm with its source)",
                    "or the asquith#43 Eq. 7.8 correction via reconcile_with_archie(S_wa), "
                    "which returns (S_w)_COR directly"),
            source=ASQUITH_INVASION)
    elif profile == "step":
        rt_status = "usable"
        rt = Quantity(
            value=float(r_deep_ohmm), unit="ohm-m",
            method="deep reading taken as R_t under a declared step profile (asquith#9)",
            source=ASQUITH_INVASION,
            inputs={"R_deep": float(r_deep_ohmm), "R_medium": float(r_medium_ohmm)},
            assumptions={"profile": "step", "profile_source": profile_source,
                         "basis": "asquith#9: 'The step profile ... deeper reading resistivity "
                                  "logging tools read true resistivity of the uninvaded zone "
                                  "(R_t)'"},
            flags=("the step profile was declared by the caller, not measured; asquith#9 says "
                   "a transition profile 'is probably a more realistic model for true borehole "
                   "conditions than is the step profile'",))
    elif profile == "transition":
        rt_status = "not_usable"
        rt = Refusal(
            reason=("a transition profile was declared, and asquith#9 says of it that the deep "
                    "reading 'can be corrected to a more accurate value of true resistivity "
                    "(R_t)' - it is an input to a correction, not R_t. The chart that performs "
                    "that correction is not in this corpus"),
            needed=("an invasion-corrected R_t (rt_corrected_ohmm with its source)",
                    "or a tornado/butterfly invasion-correction chart added to the corpus"),
            source=ASQUITH_INVASION)
    else:
        rt_status = "not_usable"
        rt = Refusal(
            reason=("the deep reading has not been established as R_t. asquith#9 licenses "
                    "'deep reading = R_t' only under a step profile, and a step profile cannot "
                    "be distinguished from a transition profile by resistivity ordering alone "
                    "- the segment says three measurements let the deep reading 'be "
                    "corrected', not that they identify which profile applies"),
            needed=("a tornado/butterfly invasion-correction chart (absent from this corpus)",
                    "or an invasion-corrected R_t with its source",
                    "or the asquith#43 route: compute a provisional S_wa, call "
                    "reconcile_with_archie(S_wa), and if it returns profile='step' come back "
                    "through with_declared_profile('step', <its source>)"),
            source=ASQUITH_INVASION)

    # --- moveable hydrocarbon index, asquith#43 Eqs. 7.4 and 7.7 --------------
    mhi: Quantity | Refusal
    swr: Quantity | Refusal
    mhi_verdict = "unavailable"
    rt_for_ratio: float | None = None
    rt_basis = ""
    if isinstance(rt, Quantity):
        rt_for_ratio = rt.value
        rt_basis = rt.method
    elif allow_uncorrected_rt:
        rt_for_ratio = float(r_deep_ohmm)
        rt_basis = "uncorrected deep reading, by explicit caller opt-in"
        flags.append(
            "allow_uncorrected_rt: the MHI and S_wr were computed from the raw deep reading. "
            "asquith#43 defines R_t in Eqs. 7.4/7.7 as 'deep induction or deep laterolog "
            "corrected for invasion'. The source does note that for the Rxo/Rt quick-look "
            "curve 'the measurements are normally used without any environmental corrections "
            "being applied', which is the practice this opt-in reflects - it is not a licence "
            "for the MHI")

    device_class = _classify_shallow_device(shallow_device)
    if not shallow_ok:
        why = Refusal(
            reason=("no shallow resistivity: asquith#43 Eqs. 7.4 and 7.7 need R_xo from a "
                    "shallow measurement such as laterolog-8, a microspherically focused log "
                    "or a microlaterolog"),
            needed=("r_shallow_ohmm from LL8, MSFL or MLL - not from a microlog, which "
                    "asquith#33 says 'generally does not provide a good estimate of "
                    "flushed-zone resistivity'",),
            source=ASQUITH_RATIO)
        mhi = why
        swr = why
    elif device_class == "microlog":
        why = Refusal(
            reason=(f"shallow_device={shallow_device!r} is a microlog curve. asquith#33: "
                    "'Because the microlog is so greatly affected by borehole conditions, it "
                    "generally does not provide a good estimate of flushed-zone resistivity "
                    "(R_xo).' asquith#43 Eqs. 7.4 and 7.7 are defined on R_xo, and "
                    "microlog_permeability_flag (#38) refuses to emit one for the same reason, "
                    "so this tool will not accept one through the back door"),
            needed=("r_shallow_ohmm from a focused device - MSFL, MLL, PL or RXO for a flushed-"
                    "zone reading, which asquith#33 calls 'more accurate predictors of "
                    "flushed-zone resistivity'",),
            source=ASQUITH_MICROLOG)
        mhi = why
        swr = why
    elif rt_for_ratio is None:
        why = Refusal(
            reason=("R_t has not been established, and asquith#43 defines R_t in Eqs. 7.4 and "
                    "7.7 as the deep measurement 'corrected for invasion'. Computing the "
                    "moveable-hydrocarbon index off an uncorrected deep reading would launder "
                    "the same error this tool exists to catch"),
            needed=("an invasion-corrected R_t",
                    "or allow_uncorrected_rt=True, accepting the flag that comes with it"),
            source=ASQUITH_RATIO)
        mhi = why
        swr = why
    else:
        ratio = (float(r_shallow_ohmm) / rt_for_ratio) / (float(rmf_ohmm) / float(rw_ohmm))
        ratio_inputs = {"R_xo": float(r_shallow_ohmm), "R_t": rt_for_ratio,
                        "Rmf": float(rmf_ohmm), "Rw": float(rw_ohmm),
                        "(Rxo/Rt)/(Rmf/Rw)": ratio}
        # asquith#9's ordering rule only needs three depths of investigation, so
        # the profile call above stands whatever the shallow device is. Eq. 7.4's
        # R_xo is the flushed zone specifically, and the corpus does not agree
        # that a shallow focused curve reads it - see SHALLOW_FOCUSED_RXO_CAVEAT.
        rxo_flags: tuple[str, ...] = (
            () if device_class == "pad" else (SHALLOW_FOCUSED_RXO_CAVEAT,))
        if rxo_flags:
            flags.append(
                "the moveable-hydrocarbon index and S_wr were computed from a shallow curve "
                "whose zone is undetermined; see the R_xo caveat on those quantities")
        swr = Quantity(
            value=ratio ** SWR_EXPONENT, unit="v/v",
            method="ratio-method water saturation S_wr (asquith#43 Eq. 7.7)",
            source=ASQUITH_RATIO, inputs=dict(ratio_inputs),
            assumptions={"exponent": SWR_EXPONENT, "R_t_basis": rt_basis,
                         "S_xo": "assumed S_w^(1/5) (Eq. 7.5)",
                         "shallow_device": shallow_device,
                         "shallow_device_class": device_class},
            flags=("compare against Archie's S_wa via reconcile_with_archie(S_wa); asquith#43 "
                   "items 1-4 are the only published step-versus-transition discriminator",)
            + rxo_flags)
        mhi_value = ratio ** MHI_EXPONENT
        cutoff: float | None
        if litho is None:
            cutoff = None
            mhi_verdict = "unavailable"
            mhi_flags: tuple[str, ...] = (
                "lithology_class not supplied, so no verdict was drawn; asquith#43 publishes "
                "different cutoffs for sandstones (0.7) and carbonates (0.6)",)
        else:
            cutoff = MHI_MOVEABLE_CUTOFF[litho]
            if mhi_value >= MHI_NONE_MOVED:
                mhi_verdict = "none_moved"
                mhi_flags = ("asquith#43: 'If the ratio Sw/Sxo is equal to or greater than "
                             "1.0, then hydrocarbons were not moved during invasion. This is "
                             "true regardless of whether or not a formation contains "
                             "hydrocarbons.'",)
            elif mhi_value < cutoff:
                mhi_verdict = "moveable_hydrocarbons"
                mhi_flags = ("asquith#43: 'Whenever the ratio Sw/Sxo is less than 0.7 for "
                             "sandstones or less than 0.6 for carbonates, moveable "
                             "hydrocarbons are indicated (Schlumberger, 1972).' Cutoff used: "
                             f"{cutoff} for {litho}",)
            else:
                mhi_verdict = "not_stated"
                mhi_flags = (f"S_w/S_xo = {mhi_value:.4g} falls in [{cutoff}, "
                             f"{MHI_NONE_MOVED}), which asquith#43 does not name. The source "
                             "states a 'moveable hydrocarbons' band and a 'none moved' band "
                             "and leaves the interval between them unlabelled; no verdict is "
                             "interpolated",)
        mhi = Quantity(
            value=mhi_value, unit="ratio",
            method="moveable hydrocarbon index S_w/S_xo (asquith#43 Eq. 7.4)",
            source=ASQUITH_RATIO, inputs=dict(ratio_inputs),
            assumptions={"exponent": MHI_EXPONENT, "n": MHI_N, "n_note": MHI_N_NOTE,
                         "lithology_class": litho, "cutoff": cutoff,
                         "bands": THRESHOLD_STATUS_37["mhi_bands"],
                         "R_t_basis": rt_basis,
                         "shallow_device": shallow_device,
                         "shallow_device_class": device_class},
            flags=mhi_flags + rxo_flags)

    assumptions: dict[str, Any] = {
        "mud_regime_basis": regime_why,
        "fluid_indication_basis": fluid_basis,
        "separation_dead_band": sep_tol,
        "separation_dead_band_status": THRESHOLD_STATUS_37["separation"],
        "saltwater_band": salt_tol,
        "saltwater_band_status": THRESHOLD_STATUS_37["saltwater_mud"],
        "Rmf_source": rmf_source,
        "Rw_source": rw_source,
        "tool_family": family,
        "shallow_device": shallow_device,
        "shallow_device_class": device_class,
        "profile_declared": declared,
        "profile_source": profile_source if declared else None,
    }
    if depth_ft is not None:
        assumptions["depth_ft"] = depth_ft

    return InvasionVerdict(
        rt=rt, rt_status=rt_status, profile=profile, mud_regime=regime,
        fluid_indication=fluid, ordering=ordering, annulus_effect=annulus_effect,
        separations=separations, mhi=mhi, mhi_verdict=mhi_verdict, swr=swr,
        assumptions=assumptions, flags=tuple(flags), call=call)


# =============================================================================
# #38  microlog_permeability_flag
# =============================================================================

def _rxo_refusal() -> Refusal:
    """`MicrologFlag.rxo` is always this.

    asquith#33 warns the microlog is a poor R_xo estimator, so the field exists
    to hand back the reason rather than a number a downstream tool would use.
    """
    return Refusal(
        reason=("asquith#33: 'Because the microlog is so greatly affected by borehole "
                "conditions, it generally does not provide a good estimate of flushed-zone "
                "resistivity (R_xo).' This tool returns a permeability flag and no "
                "resistivity, and nothing downstream may take the micronormal for R_xo"),
        needed=("R_xo from a focused pad device - the microlaterolog (MLL), proximity log (PL) "
                "or microspherically focused log (MSFL), which asquith#33 calls 'more accurate "
                "predictors of flushed-zone resistivity'",),
        source=ASQUITH_MICROLOG)


@dataclass(frozen=True)
class MicrologFlag:
    """What #38 returns: a permeability flag and the evidence behind it.

    Sign convention, pinned: **positive separation = micronormal above
    microinverse = the permeable direction** (asquith#33, "positive separation").
    Nothing downstream should re-derive it.
    """

    verdict: str            # permeable | shale_or_impermeable | impermeable_tight
                            # | false_separation
    separation: Quantity
    separation_sign: str    # "positive" | "negative" | "none"
    mudcake_indicated: bool | None
    diffcal: Quantity
    hole_condition: str     # "mudcake" | "at_gauge" | "enlarged"
    tight_check: Quantity | Refusal
    precondition: str
    rxo: Refusal = field(default_factory=_rxo_refusal)
    source: str = ASQUITH_MICROLOG
    assumptions: dict[str, Any] = field(default_factory=dict)
    flags: tuple[str, ...] = ()


def _classify_mud(mud_type: str) -> tuple[str, str] | None:
    """-> (class, matched token) for the classes that force a refusal, else None."""
    text = f" {str(mud_type).strip().lower()} "
    for token in GYPSUM_MUD_TOKENS:
        if token in text:
            return ("gypsum", token)
    for token in SALTWATER_MUD_TOKENS:
        if token in text:
            return ("saltwater", token)
    for token in OIL_MUD_TOKENS:
        if token in text:
            return ("oil_based", token)
    return None


def microlog_permeability_flag(
    micronormal_ohmm: float,
    microinverse_ohmm: float,
    *,
    rmc_ohmm: float,
    rm_ohmm: float,
    rmf_ohmm: float,
    caliper_in: float,
    bit_size_in: float,
    mud_type: str,
    rw_ohmm: float | None = None,
    rm_at_formation_temp_ohmm: float | None = None,
    header_temps_match: bool = True,
    separation_tolerance_ohmm: float = SEPARATION_TOLERANCE_OHMM,
    mudcake_tolerance_in: float = MUDCAKE_TOLERANCE_IN,
    enlargement_tolerance_in: float = ENLARGEMENT_TOLERANCE_IN,
    depth_ft: float | None = None,
) -> MicrologFlag | Refusal:
    """Permeable or not, from a microlog pair.  asquith#33, p. 90.

    The chain the source establishes: micronormal above microinverse -> the
    microinverse is seeing mudcake -> mudcake means filtrate invaded -> the
    formation is permeable. Every link is quoted in
    `specs/38-microlog_permeability_flag.md`.

    Three inputs beyond the curves are required and each is what makes the tool
    refuse correctly. Rmc/Rm/Rmf, because "positive separation can only occur
    when Rmc > Rm > Rmf". The microcaliper against bit size, because "in enlarged
    boreholes, a shale zone can exhibit minor, positive separation". The mud
    type, because in saltwater and gypsum-based muds "positive separation cannot
    occur" regardless of permeability, which makes a negative result meaningless
    rather than informative.
    """
    if bit_size_in is not None and _finite(bit_size_in) and float(bit_size_in) <= 0:
        raise ValueError(
            f"bit_size_in must be a positive length, got {bit_size_in!r}; a non-positive hole "
            "diameter is a wiring fault at the call site, not a condition of the data")
    for name, value in (("separation_tolerance_ohmm", separation_tolerance_ohmm),
                        ("mudcake_tolerance_in", mudcake_tolerance_in),
                        ("enlargement_tolerance_in", enlargement_tolerance_in)):
        if not _finite(value) or float(value) < 0:
            raise ValueError(f"{name} must be a non-negative dead-band, got {value!r}")

    # --- gate 1: the mud. First, because in these muds nothing else means anything.
    if not str(mud_type or "").strip():
        return Refusal(
            reason=("mud type not stated; asquith#33 refuses the microlog outright in "
                    "saltwater and gypsum-based muds, and that check cannot be made"),
            needed=("mud_type from the log header (~P MUD)",),
            source=ASQUITH_MICROLOG)
    hit = _classify_mud(mud_type)
    if hit is not None:
        mud_class, token = hit
        if mud_class in ("saltwater", "gypsum"):
            label = "saltwater" if mud_class == "saltwater" else "gypsum-based"
            return Refusal(
                reason=(f"mud_type {mud_type!r} reads as a {label} mud (matched {token!r}). "
                        "asquith#33: 'The microlog does not work well in saltwater muds (where "
                        "Rmf ~ Rw) or gypsum-based muds because the mudcake may not be strong "
                        "enough to keep the pad away from the formation. Where the pad is in "
                        "contact with the formation, positive separation cannot occur.' A "
                        "negative result here carries no information about permeability, so "
                        "no flag is returned"),
                needed=("a microlog run in a freshwater mud",
                        "or a different permeability indicator for this interval"),
                source=ASQUITH_MICROLOG)
        return Refusal(
            reason=(f"mud_type {mud_type!r} reads as an oil-based or invert mud (matched "
                    f"{token!r}). asquith#33 discusses the microlog in freshwater, saltwater "
                    "and gypsum-based muds and does not address oil-based mud at all; a pad "
                    "resistivity device in a non-conductive continuous phase is outside "
                    "everything the segment describes. Refused by judgement, not by quotation "
                    "- see specs/38, open question 4"),
            needed=("a source covering pad microresistivity devices in oil-based mud",
                    "or a different permeability indicator for this interval"),
            source=ASQUITH_MICROLOG)

    # The source defines the saltwater case by fluid resistivities, so test that
    # exactly whenever Rw is available, regardless of what the header calls the mud.
    if rw_ohmm is not None and _positive(rw_ohmm) and _positive(rmf_ohmm):
        rmf_rw = float(rmf_ohmm) / float(rw_ohmm)
        if 1.0 / SALT_RATIO_TOLERANCE <= rmf_rw <= SALT_RATIO_TOLERANCE:
            return Refusal(
                reason=(f"Rmf/Rw = {rmf_rw:.3g}, i.e. Rmf ~ Rw, which is how asquith#33 itself "
                        "defines the saltwater case: 'does not work well in saltwater muds "
                        "(where Rmf ~ Rw)'. The pad may contact the formation and positive "
                        "separation cannot occur regardless of permeability, whatever the "
                        f"header calls the mud ({mud_type!r})"),
                needed=("a microlog run where Rmf is well above Rw",
                        "or a different permeability indicator for this interval"),
                source=ASQUITH_MICROLOG)

    # --- gate 2: the header ordering ----------------------------------------
    missing = [n for n, v in (("rmc_ohmm", rmc_ohmm), ("rm_ohmm", rm_ohmm),
                              ("rmf_ohmm", rmf_ohmm)) if not _positive(v)]
    if missing:
        return Refusal(
            reason=(f"{', '.join(missing)} missing or non-positive. asquith#33: 'Positive "
                    "separation can only occur when Rmc > Rm > Rmf. If there is any doubt, "
                    "check the log heading for resistivity values of the mudcake, drilling "
                    "mud, and mud filtrate.' Without them a separation cannot be read as "
                    "permeability"),
            needed=tuple(f"{n} from the log header" for n in missing),
            source=ASQUITH_MICROLOG)
    rmc, rm, rmf = float(rmc_ohmm), float(rm_ohmm), float(rmf_ohmm)
    precondition = f"Rmc {rmc:g} > Rm {rm:g} > Rmf {rmf:g}"
    if not (rmc > rm > rmf):
        broken = "Rmc > Rm" if not rmc > rm else "Rm > Rmf"
        return Refusal(
            reason=(f"the log heading gives Rmc={rmc:g}, Rm={rm:g}, Rmf={rmf:g}, so {broken} "
                    "does not hold. asquith#33: 'Positive separation can only occur when "
                    "Rmc > Rm > Rmf.' Whatever the two curves are doing here, it is not the "
                    "mudcake mechanism that makes positive separation a permeability "
                    "indication, so no permeability verdict is available"),
            needed=("header resistivities satisfying Rmc > Rm > Rmf",
                    "or a different permeability indicator for this interval"),
            source=ASQUITH_MICROLOG)

    # --- gate 3: the microcaliper against the bit size ------------------------
    #
    # A header with no BS is a condition of the data, not a wiring fault: plenty
    # of vintage LAS files simply do not print item D. #25 `hole_quality` already
    # settled the house answer for the identical caliper-minus-bit-size
    # comparison - it refuses the washout and undergauge gates rather than
    # assuming a hole - and specs/38 refusal condition 6 lists a missing
    # `bit_size_in` alongside a missing `caliper_in`. So a missing bit size
    # refuses here; only a finite non-positive one raises, per condition 9.
    if bit_size_in is None or not _finite(bit_size_in):
        return Refusal(
            reason=("no bit size, so the microcaliper has nothing to be compared against. "
                    "asquith#33: 'mudcake is indicated where the caliper shows a borehole size "
                    "smaller than the diameter of the drill bit used to drill the hole', and "
                    "'in enlarged boreholes, a shale zone can exhibit minor, positive "
                    "separation'. Both tests are differences against the bit size and neither "
                    "can be run against an assumed hole"),
            needed=("bit_size_in from the log header (~P BS, RRC log-header item D)",),
            source=ASQUITH_MICROLOG)
    if not _finite(caliper_in):
        return Refusal(
            reason=("no microcaliper reading at this depth. asquith#33: 'in enlarged "
                    "boreholes, a shale zone can exhibit minor, positive separation. To detect "
                    "zones of erroneous positive separation, a microcaliper log is run in "
                    "track 1'. Without the caliper a positive separation cannot be told from "
                    "an erroneous one, and a decrease in hole size cannot corroborate mudcake"),
            needed=("caliper_in - the microcaliper curve at this depth",
                    "bit_size_in from the log header"),
            source=ASQUITH_MICROLOG)

    # --- gate 4: the curves themselves --------------------------------------
    bad = [n for n, v in (("micronormal_ohmm", micronormal_ohmm),
                          ("microinverse_ohmm", microinverse_ohmm)) if not _positive(v)]
    if bad:
        return Refusal(
            reason=(f"{', '.join(bad)} is null, non-finite or non-positive; there is no "
                    "separation to read"),
            needed=("both microlog curves at this depth",
                    "null_scrub (#12) over MNOR and MINV first"),
            source=ASQUITH_MICROLOG)

    mnor, minv = float(micronormal_ohmm), float(microinverse_ohmm)
    sep_value = mnor - minv
    sep_tol = float(separation_tolerance_ohmm)
    if sep_value > sep_tol:
        sign = "positive"
    elif sep_value < -sep_tol:
        sign = "negative"
    else:
        sign = "none"

    diffcal_value = float(caliper_in) - float(bit_size_in)
    if diffcal_value < -float(mudcake_tolerance_in):
        hole = "mudcake"
        mudcake_indicated: bool | None = True
    elif diffcal_value >= float(enlargement_tolerance_in):
        hole = "enlarged"
        mudcake_indicated = False
    else:
        hole = "at_gauge"
        mudcake_indicated = None

    flags: list[str] = []

    # Hilchie's tight-rock check. Deliberately NOT falling back on the header Rm.
    tight_check: Quantity | Refusal
    tight = False
    if _positive(rm_at_formation_temp_ohmm):
        rm_tf = float(rm_at_formation_temp_ohmm)
        cutoff_ohmm = TIGHT_RM_MULTIPLE * rm_tf
        tight = min(mnor, minv) >= cutoff_ohmm
        tight_check = Quantity(
            value=min(mnor, minv) / rm_tf, unit="ratio",
            method=("min(micronormal, microinverse) / Rm at formation temperature "
                    "(asquith#33, Hilchie 1978)"),
            source=ASQUITH_MICROLOG,
            inputs={"micronormal": mnor, "microinverse": minv, "Rm_at_Tf": rm_tf},
            assumptions={"multiple": TIGHT_RM_MULTIPLE, "cutoff_ohmm": cutoff_ohmm,
                         "status": THRESHOLD_STATUS_38["tight"]},
            flags=("asquith#33 writes 'approximately ten times'; the tool applies >= 10x and "
                   "does not invent a softer multiplier",))
    else:
        tight_check = Refusal(
            reason=("no Rm at formation temperature, so Hilchie's impermeable-zone rule cannot "
                    "be applied. asquith#33: 'resistivities of approximately ten times the "
                    "resistivity of the drilling mud (Rm) at formation temperature indicate an "
                    "impermeable zone'. The header Rm was deliberately NOT substituted - it is "
                    "measured at surface temperature and would move the cutoff by the whole "
                    "Arps correction"),
            needed=("rm_at_formation_temp_ohmm - the header Rm run through "
                    "resistivity_at_temperature (Arps, asquith#9 Eq. 1.10) at this depth's "
                    "formation temperature",),
            source=ASQUITH_MICROLOG)
        if sign != "positive":
            flags.append(
                "the impermeable/tight verdict was unavailable (no Rm at formation "
                "temperature), so 'shale_or_impermeable' here does not distinguish shale from "
                "tight rock")

    # --- the verdict, in the order the source presents the cases -------------
    if sign == "positive" and hole == "enlarged":
        verdict = "false_separation"
        flags.append(
            f"positive separation of {sep_value:.4g} ohm-m in a hole {diffcal_value:.3g} in "
            "over gauge. asquith#33: 'in enlarged boreholes, a shale zone can exhibit minor, "
            "positive separation. To detect zones of erroneous positive separation, a "
            "microcaliper log is run in track 1'. The separation is not read as permeability")
    elif sign == "positive":
        verdict = "permeable"
        if hole == "mudcake":
            flags.append(
                f"corroborated: the caliper reads {abs(diffcal_value):.3g} in under gauge. "
                "asquith#33: 'A decrease in borehole diameter can indicate mudcake and support "
                "the interpretation of permeability'")
        else:
            flags.append(
                "uncorroborated: the caliper is at gauge, so the mudcake that positive "
                "separation implies is not confirmed by a decrease in hole size")
        if tight:
            flags.append(
                "both curves also exceed 10x Rm at formation temperature, which asquith#33 "
                "gives as an impermeable-zone indication. The source does not describe a "
                "positive separation in a nonporous zone; the separation verdict is kept and "
                "the contradiction is reported rather than resolved")
    elif tight:
        verdict = "impermeable_tight"
        flags.append(
            f"{'no' if sign == 'none' else 'negative'} separation and both curves at or above "
            f"{TIGHT_RM_MULTIPLE:.0f}x Rm at formation temperature. asquith#33: 'Nonporous and "
            "impermeable zones have high resistivity values on both the micronormal and "
            "microinverse curves ... resistivities of approximately ten times the resistivity "
            "of the drilling mud (Rm) at formation temperature indicate an impermeable zone'")
    else:
        verdict = "shale_or_impermeable"
        flags.append(
            "asquith#33: 'Shale zones are indicated by no separation or negative separation "
            "(i.e., micronormal < microinverse).' The source names shale but does not claim "
            "the converse, so the verdict is not narrowed to shale")

    if sep_tol == 0.0 and sign != "none":
        scale = max(mnor, minv)
        if scale > 0 and abs(sep_value) / scale < 0.05:
            flags.append(
                f"the separation is {abs(sep_value) / scale * 100:.1f}% of the larger curve "
                "value, called on a bare '>' with separation_tolerance_ohmm at its default "
                f"0.0. {THRESHOLD_STATUS_38['separation_deadband']}")
    if hole == "mudcake" and float(mudcake_tolerance_in) == 0.0:
        flags.append(
            f"mudcake called from a caliper {abs(diffcal_value):.3g} in under gauge with no "
            f"dead-band. {THRESHOLD_STATUS_38['mudcake_deadband']}")
    if sign == "positive" and hole == "at_gauge" and diffcal_value > 0:
        # The PROVISIONAL gate decided this one: asquith#33 says only "enlarged",
        # with no size, and an over-gauge hole with positive separation is
        # exactly the erroneous-shale-separation case it warns about. Under the
        # house 1.0 in gate this is 'permeable'; on the source's bare word it
        # would be 'false_separation'. specs/38 requires any CALLER/PROVISIONAL
        # dead-band that actually decided an outcome to say so.
        flags.append(
            f"the hole is {diffcal_value:.3g} in OVER gauge, but under the "
            f"{enlargement_tolerance_in} in enlargement gate, so the separation was read as "
            "permeability rather than as the erroneous positive separation of a washed-out "
            f"shale. {THRESHOLD_STATUS_38['enlargement_deadband']}; this dead-band decided "
            "the verdict")
    if hole == "enlarged":
        flags.append(
            f"'enlarged' used the {enlargement_tolerance_in} in gate. "
            f"{THRESHOLD_STATUS_38['enlargement_deadband']}; diffcal is reported so a caller "
            "who reads asquith#33's bare word 'enlarged' as any over-gauge reading can "
            "re-decide")
    if not header_temps_match:
        flags.append(
            "header_temps_match=False: the Rmc > Rm > Rmf test assumes the three were measured "
            "at one temperature. Arps scales all three by a single monotone factor, so the "
            "ordering survives a common correction, but three different measurement "
            "temperatures are not covered by the source")

    separation = Quantity(
        value=sep_value, unit="ohm-m",
        method="microlog separation, micronormal - microinverse (asquith#33)",
        source=ASQUITH_MICROLOG,
        inputs={"micronormal_R2": mnor, "microinverse_R1x1": minv},
        assumptions={"sign_convention": ("positive = micronormal above microinverse = the "
                                         "permeable direction"),
                     "dead_band_ohmm": sep_tol,
                     "dead_band_status": THRESHOLD_STATUS_38["separation_deadband"]})
    diffcal = Quantity(
        value=diffcal_value, unit="in",
        method="microcaliper - bit size (asquith#33)", source=ASQUITH_MICROLOG,
        inputs={"caliper_in": float(caliper_in), "bit_size_in": float(bit_size_in)},
        assumptions={"sign_convention": "negative = under gauge = mudcake",
                     "mudcake_dead_band_in": float(mudcake_tolerance_in),
                     "enlargement_dead_band_in": float(enlargement_tolerance_in),
                     "mudcake_status": THRESHOLD_STATUS_38["mudcake_deadband"],
                     "enlargement_status": THRESHOLD_STATUS_38["enlargement_deadband"]})

    assumptions: dict[str, Any] = {
        "mud_type": mud_type,
        "precondition": precondition,
        "precondition_status": THRESHOLD_STATUS_38["precondition"],
        "separation_status": THRESHOLD_STATUS_38["positive_separation"],
        "mudcake_caliper_status": THRESHOLD_STATUS_38["mudcake_caliper"],
        "header_temps_match": header_temps_match,
        "rxo": "withheld by design - see MicrologFlag.rxo",
    }
    if depth_ft is not None:
        assumptions["depth_ft"] = depth_ft

    return MicrologFlag(
        verdict=verdict, separation=separation, separation_sign=sign,
        mudcake_indicated=mudcake_indicated, diffcal=diffcal, hole_condition=hole,
        tight_check=tight_check, precondition=precondition,
        assumptions=assumptions, flags=tuple(flags))


__all__ = [
    "InvasionVerdict", "RatioReconcile", "invasion_profile",
    "MicrologFlag", "microlog_permeability_flag",
    "ASQUITH_INVASION", "ASQUITH_RATIO", "ASQUITH_MICROLOG",
    "FRESHWATER_RMF_OVER_RW", "MHI_NONE_MOVED", "MHI_MOVEABLE_CUTOFF",
    "TIGHT_RM_MULTIPLE", "THRESHOLD_STATUS_37", "THRESHOLD_STATUS_38",
]
