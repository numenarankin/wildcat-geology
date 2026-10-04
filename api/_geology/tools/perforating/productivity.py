"""Tool #88 `productivity_ratio` - and the refusal that matters more than it.

The catalog specifies Locke (1981) / SPE-8804-PA, "An Advanced Method for
Predicting the Productivity Ratio of a Perforated Well", which maps gun geometry
(shot density, phasing, penetration) to PR. **That paper is not in the corpus.**
Searching the whole knowledge base for `Locke`, `8804`, "productivity ratio",
"flow efficiency" and nomographs finds exactly one real hit: the paper's own
bibliography entry, reference 9 of
`10-perforating/medcrave-elsharafi-perforation-skin-hsd-guns`. Every adjacent
thing is either a different quantity (PetroWiki's Sukarno-Winogroho
rate-dependent-skin IPR correction) or an image whose plot area was lost to
conversion (the SLB "Productivity ratio" y-axis, AAPG Figures 7-8).

So this module implements the substitute the catalog itself chose - the
steady-state radial-flow skin ratio derived from Ahmed Eq. 6-145 - under one
hard condition: **it must never be mistaken for Locke.** Hence the two design
choices that look redundant and are not:

1. A Locke-shaped call (gun geometry, no skin) returns a `Refusal` naming
   SPE 8804. Silently answering it with a skin ratio is the exact failure this
   build exists to prevent, because the answer would be a plausible number that
   contains no perforating physics at all.
2. Every `Quantity` this module returns carries the unavailability of Locke and
   the blindness to gun design as permanent flags, and its `method` string names
   the substitute rather than the specified method.

`skin` is an argument rather than an import of `perforation_skin` (#87) so the
two tools stay independently testable, and so a caller holding a total skin from
a build-up test can use this without pretending it came from a gun.
"""
from __future__ import annotations

import math
from typing import Any

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused; kept for the module contract)

# --- Provenance ------------------------------------------------------------
#
# Constants and citation strings live here rather than inline in the formula,
# per the build rules. There are no physical constants in this tool; what needs
# provenance is the equation and the fact of the missing one.

#: The equation actually implemented. Ahmed, *Reservoir Engineering Handbook*,
#: "Skin Factor" -> "Steady-State Radial Flow", printed p. 424:
#:     Q_o = 0.00708 kh (p_i - p_wf) / (mu_o B_o [ln(r_e/r_w) + s])   (6-145)
#: Setting s = 0 gives the ideal rate at the same drawdown; the ratio of the two
#: cancels k, h, mu_o, B_o and the drawdown, leaving
#:     PR = ln(r_e/r_w) / [ln(r_e/r_w) + s]
SOURCE = "00-reference/ahmed-reservoir-engineering-handbook#92 (Eq. 6-145, p. 424)"

METHOD = (
    "steady-state radial-flow skin ratio, PR = ln(re/rw)/[ln(re/rw)+s], "
    "derived from Ahmed Eq. 6-145 by taking the ratio to the same equation at s = 0"
)

#: Ahmed Eq. 6-152, p. 425, same segment: r_wa = r_w e^(-s). It gives the same
#: denominator by an independent route, since ln(r_e/r_wa) = ln(r_e/r_w) + s,
#: which is why it is computed and reported rather than left implicit.
APPARENT_RADIUS_SOURCE = "00-reference/ahmed-reservoir-engineering-handbook#92 (Eq. 6-152, p. 425)"

#: Ahmed Eq. 6-149, p. 425, same segment: the pseudosteady form carries -0.75 in
#: both ln terms. Reported alongside so a caller can see what the regime choice
#: is worth; never returned as the value (see spec Open question 2).
PSEUDOSTEADY_CONSTANT = 0.75
PSEUDOSTEADY_SOURCE = "00-reference/ahmed-reservoir-engineering-handbook#92 (Eq. 6-149, p. 425)"

#: The method the catalog specified and the corpus does not hold.
LOCKE_CITATION = (
    "Locke, S. (1981), 'An Advanced Method for Predicting the Productivity Ratio "
    "of a Perforated Well', JPT 33(12):2481-2488, SPE-8804-PA"
)

#: Where the corpus proves its own absence: a bibliography entry and nothing else.
LOCKE_ABSENCE_EVIDENCE = (
    "10-perforating/medcrave-elsharafi-perforation-skin-hsd-guns (reference 9) "
    "cites Locke but reproduces no equation, chart or coefficient from it"
)

#: Flags every result carries. These are not decoration: without them a caller
#: cannot tell that the number answers a different question from the one the
#: catalog names.
PERMANENT_FLAGS: tuple[str, ...] = (
    "locke-method-unavailable: catalog specifies Locke (1981) / SPE 8804, which is not in the corpus",
    "substitute-method: steady-state radial-flow skin ratio (Ahmed Eq. 6-145), not Locke's nomograph",
    "blind-to-gun-design: shot density, phasing and penetration do not enter this equation",
    "steady-state form; pseudosteady (Ahmed Eq. 6-149) would subtract 0.75 from both ln terms",
)

#: PROVISIONAL, and labelled as such in the flag text. Ahmed states no lower
#: bound on the denominator and no maximum physical PR, so this never changes
#: the returned value -- it only warns that the arithmetic is sensitive when the
#: skin has removed almost all of the radial resistance. See spec Open q. 3.
NEAR_SINGULAR_FRACTION = 0.10


def _finite(name: str, x: Any) -> float:
    """Bad arguments are programmer error, so they raise rather than refuse."""
    try:
        v = float(x)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"{name} must be a number, got {x!r}") from exc
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite, got {v!r}")
    return v


def _coerce_skin(skin: Any) -> tuple[float | None, Refusal | None, dict[str, Any], tuple[str, ...]]:
    """Accept a float, a `Quantity` from #87, or a `Refusal` to propagate.

    Returns (value, refusal, provenance, upstream_flags). Exactly one of value
    and refusal is not None.
    """
    if skin is None:
        return None, None, {}, ()

    if isinstance(skin, Refusal):
        return (
            None,
            Refusal(
                reason=(
                    "skin factor is unavailable upstream, so the productivity ratio is too: "
                    + skin.reason
                ),
                needed=skin.needed or ("a skin factor s",),
                source=skin.source or SOURCE,
            ),
            {},
            (),
        )

    if isinstance(skin, Quantity):
        unit = (skin.unit or "").strip().lower()
        if unit not in ("", "-", "dimensionless", "unitless", "none"):
            raise ValueError(
                f"skin must be dimensionless; got a Quantity in {skin.unit!r}"
            )
        provenance = {"skin_method": skin.method, "skin_source": skin.source}
        return _finite("skin", skin.value), None, provenance, tuple(skin.flags)

    return _finite("skin", skin), None, {}, ()


def _locke_refusal(reason: str) -> Refusal:
    return Refusal(
        reason=reason,
        needed=(
            LOCKE_CITATION,
            "or a skin factor s from perforation_skin (#87), which productivity_ratio "
            "converts to a steady-state productivity ratio by a different method",
        ),
        source=f"no source in corpus: {LOCKE_ABSENCE_EVIDENCE}",
    )


def locke_productivity_ratio(
    shot_density_spf: float | None = None,
    phasing_deg: float | None = None,
    penetration_in: float | None = None,
    **_ignored: Any,
) -> Refusal:
    """Locke's PR from gun geometry. **Always refuses** - SPE 8804 is not held.

    This entry point exists so that a caller reaching for Locke by name finds a
    refusal that names the missing paper, rather than finding nothing and
    reaching for `productivity_ratio` under the impression that it is the same
    method. It takes the Locke arguments precisely so the call compiles and the
    refusal is what comes back.
    """
    return _locke_refusal(
        "Locke's productivity-ratio method (shot density, phasing, penetration) is not "
        "implementable: SPE 8804 is not in the corpus. The only trace of it is a "
        "bibliography entry, which carries no equation, chart or coefficients. No "
        "adjacent equation in the corpus maps gun geometry to a productivity ratio, "
        "and substituting one would produce a plausible number containing no "
        "perforating physics."
    )


def productivity_ratio(
    re_ft: float,
    rw_ft: float,
    skin: Any = None,
    *,
    shot_density_spf: float | None = None,
    phasing_deg: float | None = None,
    penetration_in: float | None = None,
) -> Quantity | Refusal:
    """Fraction of zero-skin steady-state productivity delivered at a given skin.

    PR = ln(re/rw) / [ln(re/rw) + s], from Ahmed Eq. 6-145. PR = 1 at s = 0,
    below 1 when damaged (s > 0), above 1 when stimulated (s < 0).

    **This is not Locke's method.** It says nothing about the shot-density,
    phasing and penetration tradeoffs Locke's nomograph existed to quantify; all
    of that sits upstream, inside whatever produced `s`. A Locke-shaped call -
    gun geometry with no skin - refuses.

    Args:
        re_ft: external (drainage) radius, ft.
        rw_ft: wellbore radius, ft. Must use the same convention as the tool
            that produced the skin.
        skin: total skin factor, dimensionless. A float, a `Quantity`
            (e.g. from `perforation_skin`, #87), or a `Refusal` to propagate.
        shot_density_spf, phasing_deg, penetration_in: Locke-shaped inputs,
            accepted only so that a Locke-shaped call can be recognised and
            refused. **They do not enter the calculation.** Supplied alongside a
            skin, they are ignored and flagged.

    Returns:
        `Quantity` (dimensionless) or `Refusal`.

    Raises:
        ValueError: for impossible arguments (non-positive or non-finite radii,
            a skin `Quantity` carrying a non-dimensionless unit).
    """
    re_v = _finite("re_ft", re_ft)
    rw_v = _finite("rw_ft", rw_ft)
    if re_v <= 0.0:
        raise ValueError(f"re_ft must be positive, got {re_v}")
    if rw_v <= 0.0:
        raise ValueError(f"rw_ft must be positive, got {rw_v}")

    geometry = {
        "shot_density_spf": shot_density_spf,
        "phasing_deg": phasing_deg,
        "penetration_in": penetration_in,
    }
    geometry_given = {k: v for k, v in geometry.items() if v is not None}

    s_val, s_refusal, s_provenance, s_flags = _coerce_skin(skin)
    if s_refusal is not None:
        return s_refusal

    # R5 - the refusal this tool exists for. Checked before anything else that
    # could produce a number, because a number is the wrong answer here.
    if s_val is None and geometry_given:
        return _locke_refusal(
            "a productivity ratio was requested from perforation geometry ("
            + ", ".join(f"{k}={v}" for k, v in geometry_given.items())
            + "), which is Locke's method. SPE 8804 is not in the corpus, and no "
            "equation in the corpus maps shot density, phasing or penetration to a "
            "productivity ratio. productivity_ratio can answer only from a skin "
            "factor, by a different method (steady-state radial-flow skin ratio, "
            "Ahmed Eq. 6-145), which is blind to gun design and must not be "
            "reported as Locke."
        )

    # R1 - no skin, no Locke geometry: nothing to compute from.
    if s_val is None:
        return Refusal(
            reason=(
                "no skin factor supplied. Ahmed Eq. 6-145 has no other unknown: every "
                "other term (k, h, mu_o, B_o, drawdown) cancels in the ratio, so the "
                "skin is the whole calculation."
            ),
            needed=(
                "skin factor s, dimensionless - from perforation_skin (#87) or a "
                "pressure build-up test",
            ),
            source=SOURCE,
        )

    # R2 - the geometry Eq. 6-145 is derived on: flow inward from r_e to r_w.
    if re_v <= rw_v:
        return Refusal(
            reason=(
                f"drainage radius re_ft={re_v:g} is not greater than wellbore radius "
                f"rw_ft={rw_v:g}, so ln(re/rw) <= 0. Ahmed Eq. 6-145 integrates radial "
                "flow inward from re to rw; at re = rw the zero-skin rate is itself zero "
                "and the ratio is 0/0."
            ),
            needed=("re_ft > rw_ft",),
            source=SOURCE,
        )

    ln_ratio = math.log(re_v / rw_v)
    denominator = ln_ratio + s_val
    rwa_ft = rw_v * math.exp(-s_val)  # Ahmed Eq. 6-152

    # R3 - exactly singular. Returning +inf would let a downstream calculation
    # carry an undefined value silently.
    if denominator == 0.0:
        return Refusal(
            reason=(
                f"skin s={s_val:.10g} exactly cancels ln(re/rw)={ln_ratio:.10g}, so the "
                "denominator of Ahmed Eq. 6-145 is zero and the productivity ratio is "
                "undefined (Q_o unbounded at finite drawdown). Equivalently, by "
                f"Eq. 6-152 the apparent wellbore radius rwa = {rwa_ft:.6g} ft equals the "
                "drainage radius: there is no reservoir left between the sandface and "
                "the boundary. The result is not a large number, it is no number."
            ),
            needed=("a skin s > -ln(re/rw)",),
            source=SOURCE,
        )

    # R4 - negative denominator: apparent wellbore outside the drainage boundary.
    if denominator < 0.0:
        return Refusal(
            reason=(
                f"skin s={s_val:.10g} is below -ln(re/rw) = {-ln_ratio:.10g}, so the "
                f"denominator of Ahmed Eq. 6-145 is negative ({denominator:.10g}) and the "
                "productivity ratio would be negative - a well producing backwards at "
                f"positive drawdown. By Eq. 6-152 it means rwa = {rwa_ft:.6g} ft lies "
                f"outside re = {re_v:g} ft, a geometry the source does not admit. The "
                "skin, the radii, or both are wrong."
            ),
            needed=("a skin s > -ln(re/rw)", "or radii consistent with that skin"),
            source=SOURCE,
        )

    pr = ln_ratio / denominator
    pseudosteady_ln = ln_ratio - PSEUDOSTEADY_CONSTANT
    pseudosteady_den = pseudosteady_ln + s_val
    pseudosteady_pr = (
        pseudosteady_ln / pseudosteady_den if pseudosteady_den > 0.0 and pseudosteady_ln > 0.0 else None
    )

    flags: list[str] = list(PERMANENT_FLAGS)
    if s_val < 0.0:
        flags.append("stimulated: negative skin, PR > 1")
    if geometry_given:
        flags.append(
            "perforation geometry supplied but unused by this method ("
            + ", ".join(f"{k}={v}" for k, v in geometry_given.items())
            + "); it affects the result only through the skin"
        )
    if denominator < NEAR_SINGULAR_FRACTION * ln_ratio:
        flags.append(
            f"near-singular: skin removes more than {int((1 - NEAR_SINGULAR_FRACTION) * 100)}% "
            f"of the radial resistance (denominator {denominator:.4g} of ln(re/rw) "
            f"{ln_ratio:.4g}); PR is arithmetically sensitive here. PROVISIONAL - the "
            "source states no bound on the denominator"
        )
    for f in s_flags:
        flags.append(f"skin carries flags from upstream: {f}")

    assumptions: dict[str, Any] = {
        "flow_regime": (
            "steady-state radial flow to a circular drainage boundary of radius re "
            "with pressure held at re (Ahmed Eq. 6-145)"
        ),
        "drainage_geometry": "circular, radius re",
        "well_model": "single-phase Darcy flow, homogeneous k, fully-penetrating vertical well",
        "catalog_specified_method": f"{LOCKE_CITATION} - unavailable in corpus",
        "catalog_decision": (
            "tool-catalog.md: 'Locke absent; derive PR = ln(re/rw)/[ln(re/rw)+s] from "
            "perforation_skin instead'"
        ),
        "skin_meaning": (
            "Eq. 6-145's s is the TOTAL skin; passing only a perforation component "
            "answers a narrower question and the tool cannot tell which it was given"
        ),
        "pseudosteady_alternative": pseudosteady_pr,
        "pseudosteady_source": PSEUDOSTEADY_SOURCE,
    }

    inputs: dict[str, Any] = {
        "re_ft": re_v,
        "rw_ft": rw_v,
        "skin": s_val,
        "ln_re_over_rw": ln_ratio,
        "denominator": denominator,
        "rwa_ft": rwa_ft,
        "rwa_source": APPARENT_RADIUS_SOURCE,
    }
    inputs.update(s_provenance)

    return Quantity(
        value=pr,
        unit="dimensionless",
        method=METHOD,
        source=SOURCE,
        inputs=inputs,
        assumptions=assumptions,
        flags=tuple(flags),
    )
