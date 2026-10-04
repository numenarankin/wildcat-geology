"""Required static underbalance for perforation cleanup — tool #89, group I.

Rescoped per `tool-catalog.md` line 630 from `underbalance_recommend` to
`underbalance_range`. The rescope is the finding, so it is worth stating why
rather than only what:

The cited source carries one figure, "Optimum Underbalance versus Permeability"
(Oilfield Review Winter 2003/04, p. 56), on which King (1985) and Behrmann (1995)
plot two *disagreeing* criteria. That figure is a raster image. The pdf-to-text
conversion recovered its axis labels and the two curve names and nothing else —
no ordinate of either curve is stated at any permeability, here or in prose. The
correlation the tool would need is Hsia & Behrmann, "Perforating Skin as a
Function of Rock Permeability and Underbalance", SPE 22810, which this document
cites by title in footnote 8 and does not reproduce.

So there is no permeability-to-pressure function in this corpus, and none is
written here. What the document *does* state numerically about the two curves is
a ratio, in prose, on p. 56: the Behrmann criteria "recommend underbalanced
pressures that are two to four times greater than those used in previous
methods". That is the entire quantitative content, and it only becomes psi if the
caller supplies a King (1985) ordinate — with provenance — from outside this
document. Every other path refuses.

Two source statements are load-bearing enough to be refusals rather than flags:

  "the required magnitude depends on the rock strength rather than its
   permeability" ... "For sandstone formations, rock strength and permeability
   are somewhat related, although no such relationship exists for carbonates."
  (p. 56)

  "Conventional underbalanced criteria do not apply for the dynamic underbalanced
   system and, in fact, sometimes overestimate the pressure differential required
   for optimal results." (p. 62)

`tool-verification.md` warns that this source's printed inequalities are
backwards. Accordingly **no inequality printed in the document is encoded as a
threshold anywhere below**. The only numeric bounds present are the chart's axis
extents, reconstructed from OCR and used solely to widen a refusal, and the 2-4x
multiplier, which is a stated factor and not an inequality.

`Range` in `tools/result.py` has no `flags` field, so the mandated
no-defensible-point-estimate flag is carried inside `method`, where a caller that
prints only the number still cannot lose it. See spec open question 1.
"""
from __future__ import annotations

from ..result import Quantity, Range, Refusal  # noqa: F401  (Quantity unused: nothing here is a point value)

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

ANCHOR = "10-perforating/slb-new-dynamics-of-underbalanced-perforating"

SOURCE = (
    f"{ANCHOR} (Oilfield Review Winter 2003/04, p.56) — figure 'Optimum "
    "Underbalance versus Permeability', curves King (1985) [SPE 14321] and "
    "Behrmann (1995) [SPE 30081]. The figure is an image; the k-based "
    "correlation itself is Hsia & Behrmann SPE 22810, cited by title only "
    "(footnote 8) and not held in this corpus."
)

# What a caller must obtain to get an actual number out of this area. Kept as one
# table so every refusal names the same unblocking set.
UNBLOCKING_SOURCES: tuple[str, ...] = (
    "a digitized 'Optimum Underbalance versus Permeability' chart "
    f"({ANCHOR} p.56) with the King and Behrmann ordinates as numbers",
    "SPE 22810 — Hsia & Behrmann, 'Perforating Skin as a Function of Rock "
    "Permeability and Underbalance' (the correlation itself)",
    "SPE 14321 — King, Anderson & Bingham 1985 (the King curve)",
    "SPE 30081 — Behrmann 1995, 'Underbalanced Criteria for Minimum "
    "Perforation Damage' (the Behrmann curve)",
)

# --------------------------------------------------------------------------
# Constant tables — every value below is quoted, none is fitted
# --------------------------------------------------------------------------

# "This technique recommends underbalanced pressures that are two to four times
#  greater than those used in previous methods (above)." — p. 56, where "(above)"
# is the Optimum-Underbalance-versus-Permeability chart and the only previous
# method drawn on it is King (1985). This is the ONLY numeric relation between
# the two curves anywhere in the document.
BEHRMANN_OVER_KING_LOW = 2.0
BEHRMANN_OVER_KING_HIGH = 4.0
BEHRMANN_OVER_KING_QUOTE = (
    '"This technique recommends underbalanced pressures that are two to four '
    'times greater than those used in previous methods" — p.56'
)

# Plotted extents of the chart's abscissa, reconstructed from the OCR'd axis
# labels (log decades 1, 10, 100, 1000, 10,000 mD). NOT a published validity
# limit — used only to refuse outside the frame, never to bound an answer.
CHART_K_MIN_MD = 1.0
CHART_K_MAX_MD = 10_000.0

# Plotted extents of the ordinate, recorded for completeness. Nothing reads them:
# no curve value is recoverable, so there is no ordinate to bound.
CHART_UNDERBALANCE_MIN_PSI = 100.0
CHART_UNDERBALANCE_MAX_PSI = 10_000.0

# The only rock split the source makes. It does NOT distinguish oil from gas
# wells for either plotted curve, nor consolidated from unconsolidated rock.
CARBONATE_LITHOLOGIES = frozenset(
    {"carbonate", "limestone", "dolomite", "dolostone", "chalk", "carbonates"}
)
SANDSTONE_LITHOLOGIES = frozenset({"sandstone", "sand", "sands", "sandstones"})

# Perforating modes for which the two plotted (static) criteria do not apply.
DYNAMIC_MODES = frozenset({"dynamic", "pure", "dynamic_underbalance", "dub"})
STATIC_MODES = frozenset({"static", "static_underbalance", "conventional"})

_NO_POINT_ESTIMATE = (
    "NO DEFENSIBLE POINT ESTIMATE — the 'Optimum Underbalance versus "
    "Permeability' chart is an image, so neither the King (1985) nor the "
    "Behrmann (1995) curve can be read at a permeability, and no ordinate of "
    "either is stated in prose"
)


# --------------------------------------------------------------------------
# The rescoped tool
# --------------------------------------------------------------------------


def underbalance_range(
    k_md: float | None = None,
    *,
    lithology: str | None = None,
    king_1985_underbalance_psi: float | None = None,
    king_1985_source: str | None = None,
    perforating_mode: str = "static",
) -> Range | Refusal:
    """Band of static underbalance spanning the King/Behrmann disagreement.

    Returns a `Range` in psi only when the caller supplies a provenanced King
    (1985) ordinate; the band is then that ordinate scaled by the 2x-4x factor
    the source quotes for the Behrmann criteria. Every other input refuses.

    The band is the *disagreement between two published criteria*, not an
    uncertainty interval and not a confidence interval. Its midpoint means
    nothing, which is why none is exposed.

    `k_md` never enters an arithmetic expression. It gates (R2, R3) and it
    labels (`members["k_md"]`). There is no permeability-to-pressure formula in
    this module because there is none in the source.
    """
    mode = (perforating_mode or "").strip().lower()

    # R1 — dynamic underbalance. Fires first: it invalidates the criteria
    # themselves, so no amount of good input downstream rescues the answer.
    if mode in DYNAMIC_MODES:
        return Refusal(
            reason=(
                "Both plotted curves are static-underbalance criteria. The "
                "source states that for dynamic underbalanced (PURE) "
                'perforating, "Conventional underbalanced criteria do not '
                "apply for the dynamic underbalanced system and, in fact, "
                "sometimes OVERESTIMATE the pressure differential required for "
                'optimal results" (p.62). Applying a static criterion here '
                "over-designs the job."
            ),
            needed=(
                "a dynamic-underbalance design method, none of which is in this "
                "corpus: SPE 71642 (Walton et al, laboratory experiments), "
                "SPE 63108 (Walton, optimum underbalance for damage removal), "
                "SPE 77364 (Behrmann et al, PURE field results)",
                "or the PURE/SPAN planning software the source designs with",
            ),
            source=SOURCE,
        )
    if mode and mode not in STATIC_MODES:
        raise ValueError(
            f"unknown perforating_mode {perforating_mode!r}; "
            f"expected one of {sorted(STATIC_MODES | DYNAMIC_MODES)}"
        )

    # R2 — no abscissa.
    if k_md is None:
        return Refusal(
            reason=(
                "Permeability is the abscissa of both the King (1985) and "
                "Behrmann (1995) curves and none was supplied, so there is "
                "nothing to read the chart at. " + _NO_POINT_ESTIMATE + "."
            ),
            needed=("permeability at the perforated interval, in mD",)
            + UNBLOCKING_SOURCES,
            source=SOURCE,
        )
    if not isinstance(k_md, (int, float)) or k_md != k_md or k_md <= 0.0:
        # Programmer error, not a source limitation.
        raise ValueError(f"k_md must be a positive finite permeability in mD, got {k_md!r}")

    # R3 — off the plotted frame. Before R5, so that an off-chart permeability
    # refuses on its own grounds even when a King ordinate is offered.
    if k_md < CHART_K_MIN_MD or k_md > CHART_K_MAX_MD:
        return Refusal(
            reason=(
                f"k = {k_md:g} mD lies outside the plotted abscissa of the only "
                f"chart in the source, which spans {CHART_K_MIN_MD:g} to "
                f"{CHART_K_MAX_MD:,.0f} mD — those extents are an OCR "
                "reconstruction of the figure's axis labels, not a published "
                "validity limit, and are used only to refuse more often. "
                "Neither curve is defined there, and "
                "extrapolating a curve that cannot be read inside its own frame "
                "is doubly unsupported. Note the source pairs 'about 4000 psi' "
                "with the East Painter Nugget reservoir at 0.01-100 mD (p.59), "
                "but that is a SPAN design output for a four-decade reservoir "
                "range, not a value off either curve."
            ),
            needed=UNBLOCKING_SOURCES,
            source=SOURCE,
        )

    # R4 — carbonate. The mechanism, not the data, is missing.
    lith = (lithology or "").strip().lower()
    if lith in CARBONATE_LITHOLOGIES:
        return Refusal(
            reason=(
                "The source states that underbalance requirement is set by rock "
                'strength, not permeability — "the required magnitude depends '
                'on the rock strength rather than its permeability" — and that '
                'while "For sandstone formations, rock strength and '
                'permeability are somewhat related", "no such relationship '
                'exists for carbonates" (p.56). A permeability-based criterion '
                f"in {lithology!r} has no mechanism behind it."
            ),
            needed=(
                "SPE 86542 — Subiaur, Graham & Walton, 'Underbalanced Criteria "
                "for Perforating Carbonates' (cited at footnote 13, not held)",
                "or a rock-strength / effective-stress measurement and a "
                "strength-based criterion",
            ),
            source=SOURCE,
        )

    # R5 — the honest default: the chart is an image.
    if king_1985_underbalance_psi is None:
        return Refusal(
            reason=(
                f"{_NO_POINT_ESTIMATE}. At k = {k_md:g} mD the source therefore "
                "gives no number for either criterion, and it supplies no "
                "closed form: the k-based correlation is SPE 22810, cited by "
                "title only (footnote 8). The only quantitative statement about "
                "the two curves is that the Behrmann (1995) criteria are two to "
                "four times the previous methods (p.56), which yields psi only "
                "if a King (1985) ordinate is supplied from outside this "
                "document."
            ),
            needed=UNBLOCKING_SOURCES,
            source=SOURCE,
        )

    # Impossible argument, not a source limitation.
    if (
        not isinstance(king_1985_underbalance_psi, (int, float))
        or king_1985_underbalance_psi != king_1985_underbalance_psi
        or king_1985_underbalance_psi <= 0.0
    ):
        raise ValueError(
            "king_1985_underbalance_psi must be a positive finite pressure in "
            f"psi, got {king_1985_underbalance_psi!r}"
        )

    # R6 — provenance, same rule as Archie without an Rw source.
    if not (king_1985_source or "").strip():
        return Refusal(
            reason=(
                "A King (1985) ordinate was supplied without provenance. This "
                "document cannot produce that number, so an unattributed value "
                "would launder a guess into a band that looks sourced."
            ),
            needed=(
                "king_1985_source: where the King (1985) underbalance came from",
            )
            + UNBLOCKING_SOURCES,
            source=SOURCE,
        )

    king = float(king_1985_underbalance_psi)
    low = BEHRMANN_OVER_KING_LOW * king
    high = BEHRMANN_OVER_KING_HIGH * king

    caveats = [
        _NO_POINT_ESTIMATE,
        "the band is the King (1985) / Behrmann (1995) disagreement, not an "
        "uncertainty interval — its midpoint has no meaning",
        f"Behrmann (1995) = {BEHRMANN_OVER_KING_LOW:g}x-{BEHRMANN_OVER_KING_HIGH:g}x "
        f"King (1985), quoted: {BEHRMANN_OVER_KING_QUOTE}",
        '"previous methods" is not explicitly equated to King (1985) in the '
        "text; the identification comes from the sentence's cross-reference to "
        "the chart, on which King (1985) is the only older criterion drawn",
        f"King (1985) ordinate supplied by caller from: {king_1985_source.strip()}",
    ]
    if lith in SANDSTONE_LITHOLOGIES or not lith:
        caveats.append(
            "permeability stands in for rock strength here and the source says "
            "that substitution holds in sandstone only (p.56)"
            + ("" if lith else "; lithology was not stated")
        )
    if mode in STATIC_MODES or not mode:
        caveats.append(
            "static-underbalance criteria; the source reports these sometimes "
            "overestimate what dynamic underbalanced perforating needs (p.62)"
        )

    return Range(
        low=low,
        high=high,
        unit="psi",
        method="; ".join(caveats),
        source=SOURCE,
        members={
            "k_md": float(k_md),
            "king_1985_psi": king,
            "behrmann_1995_low_psi": low,
            "behrmann_1995_high_psi": high,
            "behrmann_over_king_low": BEHRMANN_OVER_KING_LOW,
            "behrmann_over_king_high": BEHRMANN_OVER_KING_HIGH,
        },
    )


# --------------------------------------------------------------------------
# The catalog name, retained so it can refuse
# --------------------------------------------------------------------------


def underbalance_recommend(
    k_md: float | None = None,
    *,
    lithology: str | None = None,
    king_1985_underbalance_psi: float | None = None,
    king_1985_source: str | None = None,
    perforating_mode: str = "static",
) -> Refusal:
    """Always refuses. Kept as a name so callers get redirected, not served.

    A tool called "recommend" that returns a single underbalance implies someone
    can defend that number in front of an operator who is about to buy a
    perforating job on it. Nobody can, from this source: the two published
    criteria disagree by a factor of two to four and the chart carrying them is
    an image. Arguments are accepted and ignored so a caller's call site does
    not have to change to get the honest answer.
    """
    return Refusal(
        reason=(
            "No underbalance recommendation is defensible from this source. The "
            "two published criteria on the 'Optimum Underbalance versus "
            "Permeability' chart — King (1985) and Behrmann (1995) — disagree, "
            "the source quantifying the gap only as a factor of two to four "
            "(p.56), and the chart is an image so neither curve is readable at "
            "a permeability. Call underbalance_range() instead: it returns the "
            "band spanning that disagreement, or refuses and says what is "
            "missing."
        ),
        needed=("use underbalance_range() for the band",) + UNBLOCKING_SOURCES,
        source=SOURCE,
    )


def underbalance_from_chart_point(
    k_md: float | None = None,
    *,
    curve: str = "behrmann_1995",
) -> Refusal:
    """Read one named curve off the chart at `k_md`. Not implementable; refuses.

    This is the tool the catalog originally asked for. It exists as a refusing
    stub so the missing capability is visible on the tool surface instead of
    being an absence, and so a future digitization of the figure has an obvious
    place to land.
    """
    return Refusal(
        reason=(
            f"The {curve} curve cannot be read at any permeability. The "
            "'Optimum Underbalance versus Permeability' figure survived the "
            "corpus conversion as an image: only its axis labels "
            f"({CHART_K_MIN_MD:g}-{CHART_K_MAX_MD:,.0f} mD, "
            f"{CHART_UNDERBALANCE_MIN_PSI:g}-{CHART_UNDERBALANCE_MAX_PSI:,.0f} "
            "psi) and the two curve names were recovered. No ordinate of either "
            "curve appears in the prose, and the underlying correlation "
            "(SPE 22810) is cited by title only."
        ),
        needed=UNBLOCKING_SOURCES,
        source=SOURCE,
    )
