"""Group D, tools #39 and #40 — net-pay summation and Passey ΔlogR TOC.

Two tools that look unrelated and are built around the same refusal. Both take a
number the log cannot supply — a cutoff set for #39, a baseline and a maturity
for #40 — and both are worthless, in the specific sense of being confidently
wrong, when that number is guessed. So neither has a default, and both decline
rather than compute when the caller cannot say where the number came from.

--- the decisions worth explaining -------------------------------------------

**#39 has no default cutoff set, and that is a resolved reconcile, not caution.**
The corpus publishes two sets. Boonsville `beg#40` uses Vsh 50 % / φ 4 % / Sw
60 %; `chapter4#2` uses 50 % / 10 % / 70 %. Both are internally correct for their
own field, which is the proof that these are parameters and not constants
(`tool-catalog.md:366-376`, *Reconcile — RESOLVED as "no default"*). The porosity
cutoffs differ by 2.5x. Applied to the wrong field either one is wrong, and both
look reasonable to anyone who cannot see which produced the footage — so the set
is a required argument, it must carry a source, and it travels on the result.
`PUBLISHED_CUTOFF_SETS` names both so a caller can cite one instead of typing
numbers; the Boonsville triple is the Bend Conglomerate answer and the only one
of the two whose porosity cutoff has a published rationale (0.05 md off a core
φ-k crossplot). Asking for it is still asking.

**#39 keeps net reservoir and net pay apart.** `beg#40` runs two summations, one
with Vsh + φ and one with Vsh + φ + Sw. Collapsing them loses the distinction an
operator maps with, so the record carries both, and net pay is a `Refusal` inside
the record when no Sw curve was supplied rather than quietly equalling net
reservoir.

**#39 sums footage by half-step bands, not by counting samples.** Real LAS has
irregular steps and gaps. Each sample owns midpoint-to-midpoint, clipped to the
window, which makes `net_reservoir + non_reservoir + unevaluated == gross` exact
under any sampling. That identity is asserted in code: two footages that disagree
would be the bug.

**#40's exponent is an exponent.** The source is an html2text conversion and
Equation 4 arrives as `10(2.297 - 0.1688LOM)` with the superscript markup gone.
Read as multiplication it makes TOC *rise* with maturity without limit, which
contradicts the article's own overmature-well result; read as exponentiation the
factor falls with maturity. The corpus index recovered from the same page and the
catalog both read it as a power. `specs/40-passey_toc.md` shows the arithmetic
both ways. `_MATURITY_A` / `_MATURITY_B` below are the pinned coefficients.

**#40 will not supply the scaling factor.** Passey's canonical 0.02 per µs/ft is
*not in this document* — the article defines the factor procedurally ("the ratio
of resistivity logarithmic cycles over the porosity log scale") and prints no
number. Supplying it here would be a fabricated constant with a real citation on
it, the exact failure Part 5 of the build doc catalogues. It is a required input.

**Both tools refuse an honestly-declared guess.** A provenance string of
"assumed", "default" or "tbd" is refused as firmly as a blank one. A caller who
knows they are guessing is the caller most likely to say so, and the point of the
gate is to stop the guess, not to reward candour with silence.
"""
from __future__ import annotations

import math

from dataclasses import dataclass
from typing import Any, Sequence

from .result import Quantity, Range, Refusal

# --- corpus anchors -----------------------------------------------------------

BOONSVILLE_CUTOFFS = "06-fort-worth-basin/beg-boonsville-secondary-gas-recovery#40"
CHAPTER4_CUTOFFS = "01-curve-reading/petrophysical-evaluation-chapter4#2"
OGJ_EAGLE_FORD = "08-evaluation/ogj-study-analyzes-eagle-ford-characteristics#1"

# --- the guessed-provenance gate ----------------------------------------------
#
# Shared by both tools. A provenance string containing any of these declares
# itself unsourced, and an unsourced cutoff or baseline is the failure mode both
# tools exist to prevent. Matched on word-ish boundaries so that a legitimate
# citation is not caught by a substring ("nan" inside "Bonanza", say).

GUESS_TOKENS: tuple[str, ...] = (
    "guess", "guessed", "guesses", "guessing",
    "assume", "assumed", "assumption", "assumptions",
    "default", "defaulted", "defaults",
    "unknown", "unspecified", "unstated",
    "placeholder", "placeholders", "made up", "made-up", "invented",
    "tbd", "n/a", "no idea", "typical value", "rule of thumb",
)

# Plurals are listed explicitly because matching is whole-word (see below) and
# "guesses" is as much a declared guess as "guess" is. `specs/40-passey_toc.md`
# says the gate refuses provenance *containing* these words; whole-word matching
# is the right mechanism -- it is what stops a real citation being caught by a
# substring -- but it does not inflect, so each form has to be named.
#
# Open question, deliberately NOT resolved here: the plural "unknowns" is left
# out. "unknown" declares a guess; "unknowns resolved by ECS" declares the
# opposite, and the spec does not distinguish them. Refusing it would reject
# honest provenance, so it stays permitted and is recorded here instead of being
# settled by whichever reading made a test pass.


_WORD_BREAKS = ",;:()[]{}.!?\"'\n\t"


def _provenance_problem(text: Any, what: str) -> str | None:
    """Return a refusal reason if `text` is not usable provenance, else None.

    Single-word tokens are matched whole so a real citation is not caught by a
    substring; multi-word tokens are matched as phrases.
    """
    if not isinstance(text, str) or not text.strip():
        return f"{what} arrived with no stated provenance"
    lowered = text.strip().lower()
    flattened = lowered
    for ch in _WORD_BREAKS:
        flattened = flattened.replace(ch, " ")
    words = set(flattened.split())
    padded = f" {flattened} "
    for token in GUESS_TOKENS:
        hit = token in words if " " not in token else f" {token} " in padded
        if hit:
            return (f"{what} declares its own provenance as {text.strip()!r}, "
                    f"which names it a guess")
    return None


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(float(value))


# =============================================================================
# #39  net_pay_cutoffs
# =============================================================================
#
# beg#40, p. C.29:
#   "Summations were then run for both net reservoir (using a shale volume cutoff
#    and a porosity cutoff) and net pay (using shale volume, porosity, and water
#    saturation cutoffs) for each layer."


@dataclass(frozen=True)
class CutoffSet:
    """A field's cutoffs, with the source that says they are that field's.

    Fractions, not percents: 50 % is 0.50. A percent-valued cutoff would pass
    every sample and report 100 % net-to-gross on shale, so it raises rather
    than refusing — that is a caller bug, not a gap in the source.

    `source` is deliberately not validated here. A caller may legitimately build
    a set and hand it around before it is used; the gate belongs at the point
    the number becomes footage, so `net_pay_cutoffs` returns the Refusal.
    """

    vsh_max: float
    phi_min: float
    sw_max: float | None = None
    source: str = ""
    label: str = ""
    porosity_basis: str = "unstated"   # "effective" | "total" | "unstated"
    rationale: str = ""

    def __post_init__(self) -> None:
        for name, value in (("vsh_max", self.vsh_max), ("phi_min", self.phi_min),
                            ("sw_max", self.sw_max)):
            if value is None:
                continue
            if not _finite(value):
                raise ValueError(f"{name} must be a finite fraction, got {value!r}")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(
                    f"{name}={value!r} is outside 0..1; cutoffs are fractions, "
                    "not percents (50% is 0.50)")
        if self.porosity_basis not in ("effective", "total", "unstated"):
            raise ValueError(
                f"porosity_basis must be 'effective', 'total' or 'unstated', "
                f"got {self.porosity_basis!r}")

    @property
    def defines_pay(self) -> bool:
        return self.sw_max is not None

    def as_dict(self) -> dict[str, Any]:
        return {
            "vsh_max": self.vsh_max,
            "phi_min": self.phi_min,
            "sw_max": self.sw_max,
            "source": self.source,
            "label": self.label,
            "porosity_basis": self.porosity_basis,
            "rationale": self.rationale,
        }


# The two published sets. Neither is a default and there is no third,
# reconciling set: `tool-catalog.md:366-376` resolves this as "no default",
# and averaging two field-specific parameters would be a fabricated constant
# with two real citations on it.

BOONSVILLE_BEND_CONGLOMERATE = CutoffSet(
    vsh_max=0.50,
    phi_min=0.04,
    sw_max=0.60,
    source=BOONSVILLE_CUTOFFS,
    label="Boonsville field, Bend Conglomerate, Fort Worth Basin (BEG/GRI)",
    porosity_basis="unstated",
    rationale=(
        "Shale cutoff 50% chosen to remove shaly sections whose density-derived "
        "porosity is too high under bad-hole conditions. Porosity cutoff 4% read "
        "off the core porosity-permeability crossplots (Figs. C2, C3, C20) as the "
        "porosity corresponding to a 0.05 md permeability cutoff, the lowest "
        "permeability at which the producible E and E2 sand facies occur. "
        "Water-saturation cutoff 60% used in the net pay summation. "
        "The source does not say whether the porosity cutoff is on total or "
        "effective porosity (it computes both; PHIE = PHIT*(1-VSH), Eq. C-13)."
    ),
)

SHARAF_1_ABU_GABRA = CutoffSet(
    vsh_max=0.50,
    phi_min=0.10,
    sw_max=0.70,
    source=CHAPTER4_CUTOFFS,
    label="Sharaf-1, Abu Gabra formation (petrophysical evaluation, ch. 4)",
    porosity_basis="effective",
    rationale=(
        "Sec. 4.3.7: 'Based on the log interpretation and DST, as well as the "
        "previous study results, the following Cutoffs can be adopted: "
        "Vsh = 50.0%, PHIE = 10.0%, Sw = 70.0%'. No further rationale is given. "
        "Tables 4.5 and 4.6 report the reservoir and pay summations separately."
    ),
)

PUBLISHED_CUTOFF_SETS: dict[str, CutoffSet] = {
    "boonsville_bend_conglomerate": BOONSVILLE_BEND_CONGLOMERATE,
    "sharaf_1_abu_gabra": SHARAF_1_ABU_GABRA,
}

# Deliberately absent: DEFAULT_CUTOFFS. Do not add one.

# Whether the cutoff value itself is in or out. Neither source says: beg#40 says
# "a value of 50 percent was chosen for the shale cutoff" and chapter4#2 says
# "Vsh = 50.0 %", and neither states which side of the number a sample sitting
# exactly on it falls. Implemented inclusive, and carried onto every Quantity so
# the choice is on the answer rather than only in the spec. Same choice, same
# wording, as `bypassed_pay_scan` (#110, tools/recompletion.py), which consumes
# the same two cutoff sets.
CUTOFF_BOUNDARY = (
    "inclusive: vsh <= vsh_max, phi >= phi_min, sw <= sw_max. Neither beg#40 nor "
    "chapter4#2 states whether a sample exactly at the cutoff is in or out; "
    "inclusive is this tool's choice, recorded rather than hidden"
)

PUBLISHED_SOURCES: frozenset[str] = frozenset(
    cs.source for cs in PUBLISHED_CUTOFF_SETS.values()
)


def published_cutoff_set(name: str) -> CutoffSet | Refusal:
    """Look up one of the two published sets by name.

    A lookup, not a default: the caller has to name a field, and the set that
    comes back names it too. An unknown name refuses rather than falling back.
    """
    key = str(name).strip().lower().replace("-", "_").replace(" ", "_")
    if key in PUBLISHED_CUTOFF_SETS:
        return PUBLISHED_CUTOFF_SETS[key]
    return Refusal(
        reason=(f"no published cutoff set named {name!r}; the corpus publishes "
                f"{sorted(PUBLISHED_CUTOFF_SETS)}, and they are field-specific "
                "parameters that must not be carried across fields"),
        needed=("a cutoff set from the operator, with the field and basis it "
                "was derived for",),
        source=BOONSVILLE_CUTOFFS,
    )


@dataclass(frozen=True)
class NetPaySummation:
    """One layer's summation. Every number on it is a Quantity or a Refusal.

    Not a Quantity itself: `beg#40` produces a *set* of footages per layer that
    only mean anything together, and the reconciliation
    `net_reservoir + non_reservoir + unevaluated == gross` is a property of the
    set, not of any one number.
    """

    zone: str
    interval: Range
    gross: Quantity
    net_reservoir: Quantity
    non_reservoir: Quantity
    unevaluated: Quantity
    net_to_gross_reservoir: Quantity
    net_pay: Quantity | Refusal
    net_to_gross_pay: Quantity | Refusal
    avg_phi_pay: Quantity | Refusal
    avg_sw_pay: Quantity | Refusal
    avg_vsh_pay: Quantity | Refusal
    phi_h_pay: Quantity | Refusal
    cutoffs: CutoffSet
    source: str
    method: str
    n_samples: int
    flags: tuple[str, ...] = ()

    @property
    def value(self) -> None:  # a record is not a single number
        return None


def _bands(depth: list[float], top: float, base: float) -> list[float]:
    """Thickness owned by each sample: midpoint to midpoint, clipped to window.

    End samples are extended by half their own step and then clipped, so for a
    regular array sampled exactly from `top` to `base` the bands sum to
    `base - top` and the two ends carry half a step each.
    """
    n = len(depth)
    bands: list[float] = []
    for i, d in enumerate(depth):
        prev_d = depth[i - 1] if i > 0 else None
        next_d = depth[i + 1] if i + 1 < n else None
        if prev_d is None:
            step_up = (next_d - d) if next_d is not None else 0.0
            upper = d - step_up / 2.0
        else:
            upper = (prev_d + d) / 2.0
        if next_d is None:
            step_dn = (d - prev_d) if prev_d is not None else 0.0
            lower = d + step_dn / 2.0
        else:
            lower = (d + next_d) / 2.0
        upper = max(upper, top)
        lower = min(lower, base)
        bands.append(max(0.0, lower - upper))
    return bands


class _LengthMismatch(Exception):
    """Internal: a curve is not aligned to depth. Surfaced as a Refusal."""

    def __init__(self, name: str, got: int, want: int) -> None:
        super().__init__(name)
        self.name, self.got, self.want = name, got, want


def _clean(seq: Sequence[Any] | None, n: int, name: str) -> list[float | None] | None:
    if seq is None:
        return None
    values = list(seq)
    if len(values) != n:
        raise _LengthMismatch(name, len(values), n)
    out: list[float | None] = []
    for v in values:
        out.append(float(v) if _finite(v) else None)
    return out


def net_pay_cutoffs(depth: Sequence[float], *, cutoffs: CutoffSet,
                    vsh: Sequence[Any], phi: Sequence[Any],
                    sw: Sequence[Any] | None = None,
                    top: float | None = None, base: float | None = None,
                    depth_unit: str = "ft",
                    zone: str = "") -> NetPaySummation | Refusal:
    """Net reservoir and net pay over an interval, under the caller's cutoffs.

    `beg#40`: net reservoir uses the shale-volume and porosity cutoffs; net pay
    adds the water-saturation cutoff. `cutoffs` is required and has no default —
    see the module docstring and `specs/39-net_pay_cutoffs.md`. The set travels
    onto the result so an operator can see whose cutoffs produced the footage.

    Curves are per-sample, aligned to `depth`; `None` or NaN marks missing.
    """
    if not isinstance(cutoffs, CutoffSet):
        raise ValueError("cutoffs must be a CutoffSet; there is no default set")

    problem = _provenance_problem(cutoffs.source, "the cutoff set")
    if problem is not None:
        return Refusal(
            reason=(f"{problem}. Cutoffs are field parameters, not constants: the "
                    "corpus publishes Vsh 50%/phi 4%/Sw 60% for the Bend "
                    "Conglomerate (beg#40) and 50%/10%/70% for Sharaf-1 "
                    "(chapter4#2), and applying either to the wrong field is a "
                    "wrong net pay that looks right"),
            needed=("a CutoffSet whose source names the field, study or operator "
                    "decision the cutoffs came from; "
                    "published_cutoff_set('boonsville_bend_conglomerate') is the "
                    "Bend Conglomerate answer",),
            source=BOONSVILLE_CUTOFFS,
        )

    if depth_unit not in ("ft", "m"):
        raise ValueError(f"depth_unit must be 'ft' or 'm', got {depth_unit!r}")

    raw_depth = list(depth)
    n = len(raw_depth)
    try:
        vsh_v = _clean(vsh, n, "vsh")
        phi_v = _clean(phi, n, "phi")
        sw_v = _clean(sw, n, "sw")
    except _LengthMismatch as mismatch:
        return Refusal(
            reason=(f"the {mismatch.name} curve has {mismatch.got} samples but "
                    f"depth has {mismatch.want}; a summation over misaligned "
                    "curves assigns readings to the wrong footage"),
            needed=("curves resampled onto one depth array "
                    "(depth_resample, #13)",),
            source=BOONSVILLE_CUTOFFS,
        )
    if vsh_v is None or phi_v is None:
        raise ValueError("vsh and phi are required curves")

    if n < 2:
        return Refusal(
            reason=f"a summation needs at least two samples; got {n}",
            needed=("a logged interval, not a single depth",),
            source=BOONSVILLE_CUTOFFS,
        )
    if any(not _finite(d) for d in raw_depth):
        return Refusal(
            reason="the depth array carries a null or non-finite depth",
            needed=("a scrubbed depth array (null_scrub, #12)",),
            source=BOONSVILLE_CUTOFFS,
        )

    ascending = raw_depth[-1] > raw_depth[0]
    order = list(range(n)) if ascending else list(range(n - 1, -1, -1))
    d_sorted = [float(raw_depth[i]) for i in order]
    if any(d_sorted[i + 1] <= d_sorted[i] for i in range(n - 1)):
        return Refusal(
            reason=("depth is not strictly monotonic; a summation over a spliced "
                    "or unsorted array double-counts footage"),
            needed=("a monotonic depth array (curve_splice_detect, #14; "
                    "depth_resample, #13)",),
            source=BOONSVILLE_CUTOFFS,
        )
    vsh_s = [vsh_v[i] for i in order]
    phi_s = [phi_v[i] for i in order]
    sw_s = [sw_v[i] for i in order] if sw_v is not None else None

    win_top = float(top) if top is not None else d_sorted[0]
    win_base = float(base) if base is not None else d_sorted[-1]
    if win_base <= win_top:
        raise ValueError(f"top {win_top} must be above base {win_base}")

    bands = _bands(d_sorted, win_top, win_base)

    want_pay = cutoffs.defines_pay and sw_s is not None
    pay_refusal: Refusal | None = None
    if cutoffs.defines_pay and sw_s is None:
        pay_refusal = Refusal(
            reason=("the cutoff set defines a water-saturation cutoff but no Sw "
                    "curve was supplied; beg#40 computes net pay from shale "
                    "volume, porosity AND water saturation"),
            needed=("an Sw curve (archie_sw, #35, or shaly_sand_sw, #36)",),
            source=BOONSVILLE_CUTOFFS,
        )
    elif not cutoffs.defines_pay:
        pay_refusal = Refusal(
            reason=("this cutoff set carries no water-saturation cutoff, so it "
                    "defines net reservoir only; beg#40 needs an Sw cutoff for "
                    "net pay"),
            needed=("sw_max on the CutoffSet, with its source",),
            source=BOONSVILLE_CUTOFFS,
        )

    gross = 0.0
    net_res = 0.0
    non_res = 0.0
    uneval = 0.0
    net_pay_ft = 0.0
    sum_phi_h = 0.0
    sum_sw_h = 0.0
    sum_vsh_h = 0.0
    n_in_window = 0

    for i, h in enumerate(bands):
        if h <= 0.0:
            continue
        n_in_window += 1
        gross += h
        v, p = vsh_s[i], phi_s[i]
        s = sw_s[i] if sw_s is not None else None

        # A present curve that already fails is decisive: the sample is non-net
        # whatever else is missing. Unevaluated is reserved for samples that
        # pass everything they can be checked against and are still incomplete.
        fails = (v is not None and v > cutoffs.vsh_max) or \
                (p is not None and p < cutoffs.phi_min)
        if fails:
            non_res += h
            continue
        if v is None or p is None:
            uneval += h
            continue

        net_res += h
        if not want_pay:
            continue
        if s is None:
            # reservoir is known, pay is not; the pay total is reported as
            # incomplete via the unevaluated-for-pay flag below.
            continue
        if s <= cutoffs.sw_max:  # type: ignore[operator]
            net_pay_ft += h
            sum_phi_h += p * h
            sum_sw_h += s * h
            sum_vsh_h += v * h

    if n_in_window < 2:
        return Refusal(
            reason=(f"only {n_in_window} sample(s) fall inside "
                    f"{win_top}-{win_base} {depth_unit}"),
            needed=("a window that overlaps the logged interval",),
            source=BOONSVILLE_CUTOFFS,
        )
    if gross <= 0.0:
        return Refusal(
            reason="the window sums to zero gross thickness",
            needed=("a window with non-zero height over sampled depths",),
            source=BOONSVILLE_CUTOFFS,
        )
    if uneval >= gross:
        return Refusal(
            reason=("every sample in the window is missing a curve; nothing "
                    "could be classified against the cutoffs"),
            needed=("Vsh and porosity curves over the interval",),
            source=BOONSVILLE_CUTOFFS,
        )

    # The reconciliation invariant. If this ever trips it is a defect in the
    # band arithmetic above, not a condition the source declines to cover.
    if abs((net_res + non_res + uneval) - gross) > 1e-6 * max(1.0, gross):
        raise AssertionError(
            f"footage does not reconcile: net_reservoir {net_res} + "
            f"non_reservoir {non_res} + unevaluated {uneval} != gross {gross}")

    flags: list[str] = []
    if cutoffs.porosity_basis == "unstated":
        flags.append(
            "the cutoff set does not say whether its porosity cutoff is on total "
            "or effective porosity; beg#40 computes both (PHIE = PHIT*(1-VSH), "
            "Eq. C-13) and names neither, and at Vsh 0.5 they differ by 2x")
    if cutoffs.source not in PUBLISHED_SOURCES:
        flags.append(
            f"cutoffs are the caller's own ({cutoffs.source!r}), not one of the "
            "two sets published in the corpus")
    if uneval > 0.0:
        flags.append(
            f"{uneval:.2f} {depth_unit} could not be classified (missing curve) "
            "and is counted in gross but in neither net figure")
    window_h = win_base - win_top
    step = (d_sorted[-1] - d_sorted[0]) / max(1, n - 1)
    if abs(gross - window_h) > step / 2.0:
        flags.append(
            f"logged footage {gross:.2f} {depth_unit} differs from the window "
            f"height {window_h:.2f} {depth_unit} by more than half a step; the "
            "interval has gaps or extends beyond the logged section")
    if want_pay:
        unpaid = sum(bands[i] for i in range(len(bands))
                     if bands[i] > 0 and sw_s is not None and sw_s[i] is None
                     and vsh_s[i] is not None and phi_s[i] is not None
                     and vsh_s[i] <= cutoffs.vsh_max and phi_s[i] >= cutoffs.phi_min)
        if unpaid > 0.0:
            flags.append(
                f"{unpaid:.2f} {depth_unit} of net reservoir has no Sw reading and "
                "is excluded from net pay; net pay is a lower bound there")

    method_res = ("net reservoir = footage passing the Vsh and porosity cutoffs "
                  "(beg#40, p. C.29)")
    method_pay = ("net pay = footage passing the Vsh, porosity and Sw cutoffs "
                  "(beg#40, p. C.29)")
    cut_dict = cutoffs.as_dict()
    common_inputs = {
        "top": win_top, "base": win_base, "depth_unit": depth_unit,
        "n_samples": n_in_window, "zone": zone,
    }

    def q(value: float, unit: str, method: str, extra: dict[str, Any] | None = None,
          src: str = BOONSVILLE_CUTOFFS, qflags: tuple[str, ...] = ()) -> Quantity:
        # The footages are beg#40's summation; the Net/Gross ratio and the
        # Av Phi / Av Sw / Av Vcl / PhiH columns are chapter4#2's Tables 4.5-4.6.
        # Each Quantity cites the source that publishes *that* number.
        ins = dict(common_inputs)
        if extra:
            ins.update(extra)
        return Quantity(value, unit, method, src,
                        inputs=ins,
                        assumptions={"cutoffs": cut_dict,
                                     "cutoff_boundary": CUTOFF_BOUNDARY},
                        flags=qflags)

    gross_q = q(gross, depth_unit,
                "gross = sum of per-sample midpoint bands clipped to the window")
    net_res_q = q(net_res, depth_unit, method_res)
    non_res_q = q(non_res, depth_unit, "footage failing the Vsh or porosity cutoff")
    uneval_q = q(uneval, depth_unit,
                 "footage with a missing curve that passed every cutoff it could "
                 "be checked against")
    ntg_res_q = q(net_res / gross, "v/v",
                  "net reservoir / gross (chapter4#2 Table 4.5 'Net/Gross', Res)",
                  extra={"net_reservoir": net_res, "gross": gross},
                  src=CHAPTER4_CUTOFFS)

    if pay_refusal is not None:
        net_pay_q: Quantity | Refusal = pay_refusal
        ntg_pay_q: Quantity | Refusal = pay_refusal
        avg_phi: Quantity | Refusal = pay_refusal
        avg_sw: Quantity | Refusal = pay_refusal
        avg_vsh: Quantity | Refusal = pay_refusal
        phi_h: Quantity | Refusal = pay_refusal
    else:
        net_pay_q = q(net_pay_ft, depth_unit, method_pay)
        ntg_pay_q = q(net_pay_ft / gross, "v/v",
                      "net pay / gross (chapter4#2 Table 4.6 'Net/Gross', Pay)",
                      extra={"net_pay": net_pay_ft, "gross": gross},
                      src=CHAPTER4_CUTOFFS)
        if net_pay_ft > 0.0:
            avg_phi = q(sum_phi_h / net_pay_ft, "v/v",
                        "thickness-weighted mean porosity over net pay "
                        "(chapter4#2 Table 4.6 'Av Phi')", src=CHAPTER4_CUTOFFS)
            avg_sw = q(sum_sw_h / net_pay_ft, "v/v",
                       "thickness-weighted mean Sw over net pay "
                       "(chapter4#2 Table 4.6 'Av Sw')", src=CHAPTER4_CUTOFFS)
            avg_vsh = q(sum_vsh_h / net_pay_ft, "v/v",
                        "thickness-weighted mean Vsh over net pay "
                        "(chapter4#2 Table 4.6 'Av Vcl')", src=CHAPTER4_CUTOFFS)
            phi_h = q(sum_phi_h, depth_unit,
                      "porosity-thickness over net pay "
                      "(chapter4#2 Table 4.6 'PhiH')", src=CHAPTER4_CUTOFFS)
        else:
            no_pay = Refusal(
                reason="no footage passed all three cutoffs, so there is no net "
                       "pay to average over",
                needed=("an interval with pay under these cutoffs",),
                source=BOONSVILLE_CUTOFFS,
            )
            avg_phi = avg_sw = avg_vsh = phi_h = no_pay

    return NetPaySummation(
        zone=zone,
        interval=Range(low=win_top, high=win_base, unit=depth_unit,
                       method="analysis window as given to net_pay_cutoffs",
                       source=BOONSVILLE_CUTOFFS,
                       members={"top": win_top, "base": win_base}),
        gross=gross_q,
        net_reservoir=net_res_q,
        non_reservoir=non_res_q,
        unevaluated=uneval_q,
        net_to_gross_reservoir=ntg_res_q,
        net_pay=net_pay_q,
        net_to_gross_pay=ntg_pay_q,
        avg_phi_pay=avg_phi,
        avg_sw_pay=avg_sw,
        avg_vsh_pay=avg_vsh,
        phi_h_pay=phi_h,
        cutoffs=cutoffs,
        source=BOONSVILLE_CUTOFFS,
        method="layer summation, net reservoir and net pay (beg#40, pp. C.29-C.31)",
        n_samples=n_in_window,
        flags=tuple(flags),
    )


# =============================================================================
# #40  passey_toc
# =============================================================================
#
# OGJ Eagle Ford study, segment #1:
#   Eq. 3  d logR = log10(R/Rbaseline) + ScalingFactor(dt - dt_baseline)
#   Eq. 4  TOC(wt.%) = (d logR) x 10^(2.297 - 0.1688*LOM) + dTOC
#
# The exponent is an exponent; see the module docstring and
# specs/40-passey_toc.md for why the html2text "10(...)" cannot be multiplication.

_MATURITY_A = 2.297    # Eq. 4 intercept, OGJ_EAGLE_FORD
_MATURITY_B = 0.1688   # Eq. 4 LOM coefficient, OGJ_EAGLE_FORD

# The maturities at which the study validated the method against core, and the
# one at which it did not. LOMs from the LOM diagram (Fig. 2): BD 11.3, CB 10.5
# (both mature, both correlated); LK 12.0 (overmature, underestimated).
LOM_VALIDATED = (10.5, 11.3)
LOM_OVERMATURE = 12.0

# Caveats the source attaches to every number this method produces. Carried in
# `assumptions` rather than `flags` because they are unconditional.
SOURCE_CAVEATS: tuple[str, ...] = (
    "empirical method; requires validation by a core-to-log calibration",
    "baseline selection is subjective and requires expertise",
    "heavy minerals such as pyrite affect resistivity logs; treat with caution",
    "low correlation with core measurements in intervals of low TOC",
    "may not be applicable at all maturity levels",
)


@dataclass(frozen=True)
class PickedValue:
    """A number an analyst picked, with how and from where.

    `basis` is *how* it was chosen, `source` is *where it came from*. Both are
    required by the tools that consume this; construction stays permissive so a
    caller can build one incrementally, and the refusal lands at the point of
    use where the operator will see it.
    """

    value: float
    unit: str
    basis: str = ""
    source: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"value": self.value, "unit": self.unit,
                "basis": self.basis, "source": self.source}


@dataclass(frozen=True)
class PasseyBaseline:
    """The organic-lean overlay pick: both baselines and the track scaling.

    One record because the source picks all three off the same interval on the
    same track — "the resistivity logarithmic scale was adjusted to get both
    curves overlain over a significant depth range of organic-lean interval...
    The baselines of resistivity and transit-time logs are chosen as the average
    values for the identified interval." Splitting them would let a caller pair
    a resistivity baseline from one well with a scaling from another.

    `scaling_factor` is per microsecond/foot and is NOT defaulted: the source
    defines it procedurally ("the ratio of resistivity logarithmic cycles over
    the porosity log scale") and prints no number.
    """

    r_baseline_ohmm: float
    dt_baseline_us_ft: float
    scaling_factor: float
    basis: str = ""
    source: str = ""
    interval_top: float | None = None
    interval_base: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "r_baseline_ohmm": self.r_baseline_ohmm,
            "dt_baseline_us_ft": self.dt_baseline_us_ft,
            "scaling_factor_per_us_ft": self.scaling_factor,
            "basis": self.basis,
            "source": self.source,
            "organic_lean_interval": (self.interval_top, self.interval_base),
        }


# Passey's minimum TOC in shale reservoirs, offered so a caller can cite it
# rather than type 0.8. A stand-in, not a default: it must be passed explicitly
# and using it raises a flag saying it is not a determination for the caller's
# basin. The source: "The regional background is not easy to determine, but
# Passey used 0.8 weight percentage as the minimum TOC in shale reservoirs."
PASSEY_BACKGROUND_TOC = PickedValue(
    value=0.8,
    unit="wt%",
    basis=("Passey's minimum TOC in shale reservoirs, used as a published "
           "stand-in for the regional background, which the source says is not "
           "easy to determine"),
    source=OGJ_EAGLE_FORD,
)


def _pick_problem(pick: Any, what: str) -> Refusal | None:
    """Refuse a pick that is missing, unprovenanced, or self-declared a guess."""
    if pick is None:
        return Refusal(
            reason=f"{what} was not supplied",
            needed=(f"{what}, with the basis it was picked on and its source",),
            source=OGJ_EAGLE_FORD,
        )
    for label, text in (("basis", getattr(pick, "basis", None)),
                        ("source", getattr(pick, "source", None))):
        problem = _provenance_problem(text, f"{what} ({label})")
        if problem is not None:
            return Refusal(
                reason=(f"{problem}; delta log R will not return a TOC from an "
                        "unprovenanced pick. The baseline and maturity choices "
                        "move the answer further than the equation does, and "
                        "the source calls baseline selection 'subjective' and "
                        "requiring 'some level of expertise'"),
                needed=(f"a {label} for {what} — how it was chosen and where "
                        "it came from",),
                source=OGJ_EAGLE_FORD,
            )
    return None


def passey_delta_log_r(resistivity_ohmm: Any, dt_us_ft: Any, *,
                       baseline: PasseyBaseline) -> Quantity | Refusal:
    """Eq. 3: d logR = log10(R/R_baseline) + ScalingFactor*(dt - dt_baseline).

    The overlay separation, in logarithmic resistivity cycles. Published in its
    own right, so it is exposed separately from the TOC that consumes it.
    """
    if not isinstance(baseline, PasseyBaseline):
        raise ValueError("baseline must be a PasseyBaseline")
    refusal = _pick_problem(baseline, "the organic-lean baseline")
    if refusal is not None:
        return refusal

    if not _finite(resistivity_ohmm):
        return Refusal(
            reason="no resistivity reading at this depth (null or non-finite)",
            needed=("a deep resistivity in ohm-m",),
            source=OGJ_EAGLE_FORD,
        )
    if not _finite(dt_us_ft):
        return Refusal(
            reason="no transit-time reading at this depth (null or non-finite)",
            needed=("a compressional transit time in us/ft; the source uses a "
                    "sonic log because density and neutron logs are adversely "
                    "affected by borehole conditions",),
            source=OGJ_EAGLE_FORD,
        )
    r = float(resistivity_ohmm)
    dt = float(dt_us_ft)
    if r <= 0.0:
        return Refusal(
            reason=f"resistivity {r} ohm-m is not positive; log10 is undefined "
                   "and a non-positive resistivity is bad data, not a formation",
            needed=("a positive deep resistivity",),
            source=OGJ_EAGLE_FORD,
        )
    if not _finite(baseline.r_baseline_ohmm) or baseline.r_baseline_ohmm <= 0.0:
        return Refusal(
            reason=f"baseline resistivity {baseline.r_baseline_ohmm!r} is not a "
                   "positive ohm-m value",
            needed=("R_baseline as the average resistivity over the "
                    "organic-lean interval",),
            source=OGJ_EAGLE_FORD,
        )
    if not _finite(baseline.dt_baseline_us_ft):
        return Refusal(
            reason=f"baseline transit time {baseline.dt_baseline_us_ft!r} is not "
                   "a finite us/ft value",
            needed=("dt_baseline as the average transit time over the "
                    "organic-lean interval",),
            source=OGJ_EAGLE_FORD,
        )
    if not _finite(baseline.scaling_factor):
        raise ValueError("scaling factor must be finite")
    if baseline.scaling_factor <= 0.0:
        return Refusal(
            reason=(f"scaling factor {baseline.scaling_factor} is not positive; "
                    "it is the ratio of resistivity logarithmic cycles over the "
                    "porosity log scale, and a non-positive value inverts the "
                    "overlay"),
            needed=("the scaling factor read off the plotted track; the source "
                    "publishes no numeric value, so it cannot be defaulted",),
            source=OGJ_EAGLE_FORD,
        )

    dlogr = math.log10(r / baseline.r_baseline_ohmm) \
        + baseline.scaling_factor * (dt - baseline.dt_baseline_us_ft)

    flags: list[str] = []
    if dlogr < 0.0:
        flags.append(
            "negative separation: the curves cross the other way from the "
            "organic-lean overlay, which Eq. 3 does not describe")
    return Quantity(
        dlogr, "log10 cycles",
        "delta log R overlay separation (OGJ Eq. 3, after Passey)",
        OGJ_EAGLE_FORD,
        inputs={"R_ohmm": r, "dt_us_ft": dt,
                "R_baseline_ohmm": baseline.r_baseline_ohmm,
                "dt_baseline_us_ft": baseline.dt_baseline_us_ft,
                "scaling_factor_per_us_ft": baseline.scaling_factor},
        assumptions={"baseline": baseline.as_dict(),
                     "porosity_log": "sonic (us/ft), as Eq. 3 is written",
                     "scaling_factor_units": "per us/ft, inferred from Eq. 3's "
                                             "dimensions; the source never "
                                             "states them"},
        flags=tuple(flags),
    )


def passey_toc(resistivity_ohmm: Any, dt_us_ft: Any, *,
               baseline: PasseyBaseline,
               lom: PickedValue,
               delta_toc: PickedValue,
               core_calibrated: bool,
               depth: float | None = None) -> Quantity | Refusal:
    """Eq. 4: TOC(wt%) = d logR * 10^(2.297 - 0.1688*LOM) + dTOC.

    Every picked input is required and must carry its own provenance. LOM in
    particular is a maturity estimate no log supplies — the study reads it off a
    LOM diagram against geochemical data — so a LOM that arrives without a
    source is wrong by construction and is refused.

    `core_calibrated` is a required declaration, not a flag with a default: the
    source's first stated limitation is that the method "requires validation by
    a core-to-log calibration", and a caller who has not done one should have to
    say so.
    """
    if not isinstance(lom, PickedValue):
        raise ValueError("lom must be a PickedValue carrying its own provenance")
    if not isinstance(delta_toc, PickedValue):
        raise ValueError("delta_toc must be a PickedValue carrying its own provenance")
    if not isinstance(core_calibrated, bool):
        raise ValueError("core_calibrated must be declared True or False")

    for pick, what in ((lom, "the LOM (level of maturity) estimate"),
                       (delta_toc, "the regional background TOC")):
        refusal = _pick_problem(pick, what)
        if refusal is not None:
            return refusal
    if not _finite(lom.value):
        return Refusal(
            reason=f"LOM {lom.value!r} is not a finite number",
            needed=("a LOM from a maturity diagram or geochemical analysis",),
            source=OGJ_EAGLE_FORD,
        )
    if not _finite(delta_toc.value):
        return Refusal(
            reason=f"regional background TOC {delta_toc.value!r} is not finite",
            needed=("a regional background TOC in wt%",),
            source=OGJ_EAGLE_FORD,
        )

    separation = passey_delta_log_r(resistivity_ohmm, dt_us_ft, baseline=baseline)
    if isinstance(separation, Refusal):
        return separation

    lom_v = float(lom.value)
    maturity_factor = 10.0 ** (_MATURITY_A - _MATURITY_B * lom_v)
    toc = separation.value * maturity_factor + float(delta_toc.value)

    flags: list[str] = list(separation.flags)
    if not core_calibrated:
        flags.append(
            "not core-calibrated: the source's first stated requirement is "
            "validation by a core-to-log calibration")
    if lom_v >= LOM_OVERMATURE:
        flags.append(
            f"LOM {lom_v} is at or above the overmature case the source reports "
            f"failing (LK well, LOM {LOM_OVERMATURE}: 'the delta log R technique "
            "underestimated the log-derived TOC of the overmature shale'); the "
            f"method was validated against core at LOM {LOM_VALIDATED[0]} and "
            f"{LOM_VALIDATED[1]}")
    if toc <= float(delta_toc.value):
        flags.append(
            "TOC is at or below the regional background, the low-TOC regime "
            "where the source says log-derived TOC correlates poorly with core")
    if delta_toc.source == OGJ_EAGLE_FORD and delta_toc.value == 0.8:
        flags.append(
            "regional background is Passey's 0.8 wt% minimum-in-shale stand-in, "
            "not a determination for this basin; the source says the regional "
            "background 'is not easy to determine'")

    return Quantity(
        toc, "wt%",
        "Passey delta log R TOC (OGJ Eq. 3 + Eq. 4)",
        OGJ_EAGLE_FORD,
        inputs={"R_ohmm": float(resistivity_ohmm), "dt_us_ft": float(dt_us_ft),
                "delta_log_r": separation.value,
                "LOM": lom_v,
                "maturity_factor_10^(2.297-0.1688*LOM)": maturity_factor,
                "delta_TOC_wtpct": float(delta_toc.value),
                "depth": depth},
        assumptions={
            "baseline": baseline.as_dict(),
            "lom": lom.as_dict(),
            "delta_toc": delta_toc.as_dict(),
            "core_calibrated": core_calibrated,
            "exponent_form": ("10 raised to (2.297 - 0.1688*LOM); the source is "
                              "an html2text conversion that lost the superscript "
                              "and prints '10(...)'. Read as multiplication, TOC "
                              "would rise without limit with maturity, which "
                              "contradicts the source's own overmature result"),
            "source_caveats": SOURCE_CAVEATS,
        },
        flags=tuple(flags),
    )
