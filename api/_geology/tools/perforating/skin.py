"""Karakas-Tariq perforation skin. Elsharafi & Bodi, Eqs. (13)-(22).

Tool #87. Merge target: `tools/perforation.py` (which already holds #50
`perf_length_optimize`); the anchors and tables below are self-contained.

Three things about this source are worth knowing before reading the code, all of
them written up in full in `specs/87-perforation_skin.md`:

**The procedure is sound; the paper's worked example is not.** Its Tables 10-16
add feet to inches wherever `l_p` appears (`0.813 x (22.425 in + 0.292 ft) =
18.468`, which is what makes its `s_H = -4.147` instead of the dimensionally
consistent -1.794), compute `r_pD` with `2h = 12` when its own `h` is 0.167 ft,
print an `a` column that Eq. (20) does not reproduce, and print `S_v` twice with
a factor of 1000 between them. So the published perforation-skin numbers are
**not** this module's oracle. The one number in the paper that reproduces exactly
is the crushed-zone skin, Table 18 (`S_dp = 3.766428`), and that is why Eq. (9)
is implemented here too.

**Eq. (21) is printed as `b = b1 + r_pD + b2` and the paper computes it that way.**
Under that reading only `b1 + b2` is identifiable, so Table 2 publishing b1 and b2
separately per phasing would be pointless - the multiplication was lost in
typesetting, exactly as the two-branch brace in Eq. (15) was. This module uses
`b = b1 * r_pD + b2`, flags that choice on every result, and reports the
as-printed value alongside so the size of the choice is visible.

**Units are converted, not assumed.** Every length goes to feet before it meets a
formula. `perf_length_in` and `perf_radius_in` are inches because the source
tabulates perforations in inches; `wellbore_radius_ft` is feet because the source
tabulates it in feet. Mixing them is the source's own defect and it inflates every
`s_H` by about `ln 12`.
"""
from __future__ import annotations

import math

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

# Elsharafi MO, Bodi T. "Evaluation of the productivity of vertical oil wells by
# using different high shot density (HSD) guns." Int J Petrochem Sci Eng.
# 2017;2(2):52-64. Reproduces Karakas & Tariq (1988), SPE 18271.
KT_PROCEDURE = "10-perforating/medcrave-elsharafi-perforation-skin-hsd-guns#2"
KT_EXAMPLE = "10-perforating/medcrave-elsharafi-perforation-skin-hsd-guns#4"

IN_PER_FT = 12.0

# --------------------------------------------------------------------------
# Constant tables, quoted verbatim from the source. Keyed on phasing angle in
# degrees. 360 is an alias of 0 in every table ("0'(360 deg)").
# --------------------------------------------------------------------------

#: Table 1, "Depending of alpha-theta on Phasing" (`KT_PROCEDURE`, Eq. 15).
ALPHA_THETA = {
    0: 0.25,
    360: 0.25,
    180: 0.5,
    120: 0.648,
    90: 0.726,
    60: 0.813,
    45: 0.86,
}

#: Table 2, "Vertical Skin Correlation Coefficients" (`KT_PROCEDURE`, Eqs. 20-21).
#: (a1, a2, b1, b2)
VERTICAL_SKIN_COEFFICIENTS = {
    0: (-2.091, 0.0453, 5.1313, 1.8672),
    360: (-2.091, 0.0453, 5.1313, 1.8672),
    180: (-2.025, 0.0943, 3.0373, 1.8115),
    120: (-2.018, 0.0634, 1.6136, 1.777),
    90: (-1.905, 0.1038, 1.5674, 1.6935),
    60: (-1.898, 0.1023, 1.3654, 1.649),
    45: (-1.788, 0.2398, 1.1915, 1.6392),
}

#: Table 3, "Variables C1 and C2" (`KT_PROCEDURE`, Eq. 22). (c1, c2)
WELLBORE_SKIN_COEFFICIENTS = {
    0: (1.60e-01, 2.675),
    360: (1.60e-01, 2.675),
    180: (2.60e-02, 4.532),
    120: (6.60e-03, 5.42),
    90: (1.90e-03, 6.155),
    60: (3.00e-04, 7.509),
    45: (4.60e-05, 8.791),
}

#: The phasings Tables 1-3 supply, in the order the source prints them. There is
#: no interpolation between them: the tables are discrete and the source offers
#: no rule for an intermediate angle.
SUPPORTED_PHASINGS_DEG = (0, 360, 180, 120, 90, 60, 45)

#: The only envelope this document supplies is the one its worked example walks,
#: recomputed in consistent units (60 deg, 6 spf, l_p 22.4-30.8 in, r_p 0.14-0.15
#: in, r_w 0.187-0.292 ft, k_h/k_v = 5). It is NOT the correlation's fitted range
#: - Karakas & Tariq's own limits are in SPE 18271, which this corpus holds as a
#: bibliography line only. Used for a flag, never for a refusal.
SOURCE_DEMONSTRATED_HD = (0.145, 0.200)
SOURCE_DEMONSTRATED_RPD = (0.050, 0.055)

_NO_ENVELOPE_FLAG = (
    "no_published_validity_envelope: the source prints the Karakas-Tariq equations "
    "and Tables 1-3 but no fitted range for r_pD, h_D or perforation geometry. The "
    "only ranges in the document (0-30 in, 1/2/4 spf, 0/180 deg) belong to the "
    "Standing-Harris charts, a different method the paper explicitly rejects. "
    "SPE 18271 would supply the real limits."
)

_EQ21_FLAG = (
    "eq21_printed_as_sum_interpreted_as_product: the source prints Eq. (21) as "
    "b = b1 + r_pD + b2 and its Table 13 computes it that way, but that reading "
    "makes b1 and b2 separately unidentifiable while Table 2 publishes them "
    "separately per phasing. Read here as b = b1*r_pD + b2; see "
    "assumptions['s_v_if_eq21_read_as_printed'] for the alternative."
)


def _resolve_phasing(phasing_deg):
    """Normalise the phasing key, or None if the tables do not carry it."""
    if phasing_deg is None:
        return None
    key = int(round(float(phasing_deg)))
    return key if key in ALPHA_THETA else None


def perforation_skin(perf_length_in: float | None = None,
                     shot_density_spf: float | None = None,
                     phasing_deg: float | None = None,
                     perf_radius_in: float | None = None,
                     wellbore_radius_ft: float | None = None,
                     kh_over_kv: float | None = None):
    """Total perforation skin s_P = s_H + s_V + s_wb. Eqs. (13)-(22).

    perf_length_in    l_p, tunnel length beyond the wellbore wall (in)
    shot_density_spf  shots per foot; sets the perforation spacing h = 1/spf (ft)
    phasing_deg       one of 0/360, 180, 120, 90, 60, 45 - the table keys
    perf_radius_in    r_perf, the tunnel RADIUS (in). The source's prose calls it
                      "the perforation diameter" but the symbol is a radius and
                      its own Table 17 lists r_p = 0.15 in for a 0.30-in tunnel.
                      A caller holding a gun's diameter rating must halve it.
    wellbore_radius_ft r_w (ft)
    kh_over_kv        k_h/k_v. Required: the source's own example runs at 5 and a
                      silent isotropic default would move s_V without saying so.

    Returns the dimensionless total, with the three components in `inputs`.
    Not corrected for limited entry - the source's Eq. (11) applies (h/h_p) to
    s_P, and that multiplier is the caller's to apply.
    """
    missing = [name for name, val in (
        ("perf_length_in", perf_length_in),
        ("shot_density_spf", shot_density_spf),
        ("phasing_deg", phasing_deg),
        ("perf_radius_in", perf_radius_in),
        ("wellbore_radius_ft", wellbore_radius_ft),
        ("kh_over_kv", kh_over_kv),
    ) if val is None]
    if missing:
        return Refusal(
            reason="Karakas-Tariq needs the full perforation geometry; missing "
                   + ", ".join(missing),
            needed=tuple(missing),
            source=KT_PROCEDURE)

    # Impossible arguments are programmer error, not a limitation of the source.
    if perf_length_in < 0 or perf_radius_in < 0 or shot_density_spf < 0:
        raise ValueError("perforation length, radius and shot density cannot be negative")
    if wellbore_radius_ft <= 0:
        raise ValueError("wellbore radius must be positive")
    if kh_over_kv <= 0:
        raise ValueError("kh_over_kv must be positive")

    key = _resolve_phasing(phasing_deg)
    if key is None:
        return Refusal(
            reason=f"phasing {phasing_deg} deg is not in Tables 1-3; the constants are "
                   "tabulated only at 0 (360), 180, 120, 90, 60 and 45 degrees and the "
                   "source gives no rule for interpolating between them",
            needed=("phasing_deg in " + ", ".join(str(p) for p in SUPPORTED_PHASINGS_DEG),),
            source=KT_PROCEDURE)
    if perf_length_in == 0:
        return Refusal(
            reason="perforation length is zero: nothing penetrates past the wellbore wall, "
                   "so Eq. (15) has no effective wellbore radius and Eq. (16) no h_D",
            needed=("perf_length_in > 0",),
            source=KT_PROCEDURE)
    if shot_density_spf == 0:
        return Refusal(
            reason="shot density is zero: there are no perforations, so there is no "
                   "perforation skin to compute",
            needed=("shot_density_spf > 0",),
            source=KT_PROCEDURE)

    alpha_theta = ALPHA_THETA[key]
    a1, a2, b1, b2 = VERTICAL_SKIN_COEFFICIENTS[key]
    c1, c2 = WELLBORE_SKIN_COEFFICIENTS[key]

    l_p_ft = perf_length_in / IN_PER_FT
    r_perf_ft = perf_radius_in / IN_PER_FT
    r_w_ft = float(wellbore_radius_ft)
    h_ft = 1.0 / shot_density_spf          # Eq. (16) prose: h is the perforation spacing

    # --- plane-flow (horizontal) component, Eqs. (14)-(15) -------------------
    # Eq. (15) is two-branched; the html extraction collapsed the brace, the
    # print-variant OCR preserved it.
    # The l_p/4 of the theta = 0 branch is Table 1's alpha(0) = 0.25, so it is read
    # from the table rather than written as a 4.
    if key in (0, 360):
        r_w_prime_ft = alpha_theta * l_p_ft
    else:
        r_w_prime_ft = alpha_theta * (r_w_ft + l_p_ft)
    s_h = math.log(r_w_ft / r_w_prime_ft)

    # --- vertical converging component, Eqs. (16)-(21) ----------------------
    h_d = (h_ft / l_p_ft) * math.sqrt(kh_over_kv)
    r_pd = (r_perf_ft / (2.0 * h_ft)) * (1.0 + math.sqrt(1.0 / kh_over_kv))
    a = a1 * math.log10(r_pd) + a2
    b = b1 * r_pd + b2
    s_v = 10.0 ** a * h_d ** (b - 1.0) * r_pd ** b

    # The same s_V under Eq. (21) exactly as printed, carried for review.
    b_as_printed = b1 + r_pd + b2
    s_v_as_printed = 10.0 ** a * h_d ** (b_as_printed - 1.0) * r_pd ** b_as_printed

    # --- wellbore blockage component, Eqs. (18), (22) -----------------------
    r_wd = r_w_ft / (l_p_ft + r_w_ft)
    s_wb = c1 * math.exp(c2 * r_wd)

    s_p = s_h + s_v + s_wb

    flags = [_NO_ENVELOPE_FLAG, _EQ21_FLAG]
    if s_h > 0:
        flags.append(
            f"s_h_positive: r_w'(theta) = {r_w_prime_ft:.4f} ft is smaller than the "
            f"wellbore radius {r_w_ft:.4f} ft, so the perforations shrink the effective "
            "wellbore rather than enlarging it - short tunnels, or 0-degree phasing")
    if r_pd > 1.0:
        flags.append(
            f"r_pd_above_unity: r_pD = {r_pd:.4f}; log10(r_pD) changes sign above 1 and "
            "the source shows no case anywhere near it")
    if not SOURCE_DEMONSTRATED_HD[0] <= h_d <= SOURCE_DEMONSTRATED_HD[1]:
        flags.append(
            f"hd_outside_source_range: h_D = {h_d:.4f} outside {SOURCE_DEMONSTRATED_HD}, "
            "the band the source's own worked example walks. That is the demonstrated "
            "envelope, not the correlation's fitted range, which this corpus lacks")
    if not SOURCE_DEMONSTRATED_RPD[0] <= r_pd <= SOURCE_DEMONSTRATED_RPD[1]:
        flags.append(
            f"rpd_outside_source_range: r_pD = {r_pd:.4f} outside "
            f"{SOURCE_DEMONSTRATED_RPD}, the band the source's own worked example walks. "
            "Demonstrated envelope, not fitted range")

    return Quantity(
        s_p, "dimensionless",
        "Karakas-Tariq perforation skin, s_P = s_H + s_V + s_wb (Eqs. 13-22)",
        KT_PROCEDURE,
        inputs={
            "s_h": s_h,
            "s_v": s_v,
            "s_wb": s_wb,
            "alpha_theta": alpha_theta,
            "r_w_prime_ft": r_w_prime_ft,
            "h_ft": h_ft,
            "h_D": h_d,
            "r_pD": r_pd,
            "r_wD": r_wd,
            "a": a,
            "b": b,
            "perf_length_in": perf_length_in,
            "shot_density_spf": shot_density_spf,
            "phasing_deg": key,
            "perf_radius_in": perf_radius_in,
            "wellbore_radius_ft": wellbore_radius_ft,
            "kh_over_kv": kh_over_kv,
        },
        assumptions={
            "units": "lengths converted to feet before use; the source's own worked "
                     "example adds inches to feet and inflates every s_H by about ln 12",
            "h": "perforation spacing h = 1/shot density (ft), per the Eq. (16) prose - "
                 "not the formation thickness or the perforated interval, both of which "
                 "the source also calls h",
            "r_perf": "taken as the perforation RADIUS (source prose says 'diameter', but "
                      "the symbol and the source's Table 17 say radius)",
            "eq21": "b = b1*r_pD + b2; printed as b = b1 + r_pD + b2",
            "b_if_eq21_read_as_printed": b_as_printed,
            "s_v_if_eq21_read_as_printed": s_v_as_printed,
            "limited_entry": "s_P is NOT multiplied by h/h_p; the source's Eq. (11) leaves "
                             "that to the caller",
            "excludes": "crushed-zone skin (Eq. 9) and damage skin (Eq. 3) are separate "
                        "additive terms, not part of s_P",
            "worked_example": "the source's Tables 10-16 are not reproducible from its own "
                              "equations; see specs/87-perforation_skin.md",
        },
        flags=tuple(flags))


def crushed_zone_skin(k_md: float | None = None,
                      k_crushed_md: float | None = None,
                      k_damaged_md: float | None = None,
                      crushed_radius_in: float | None = None,
                      perf_radius_in: float | None = None,
                      perf_length_in: float | None = None,
                      perf_interval_ft: float | None = None,
                      shot_density_spf: float | None = None):
    """McLeod crushed-zone skin, Eq. (9). Companion to `perforation_skin`, not part of it.

    s_dp = (k/k_dp - k/k_a) * (12 h_p / (n L_p)) * ln(r_dp / r_p)

    The 12 converts the perforated interval from feet to inches so the middle
    group is dimensionless. `k_a` is the damaged-zone PERMEABILITY: the source's
    nomenclature line calls it a radius, but its Table 18 uses 33.8 mD and the
    arithmetic only closes that way.

    This is the one number in the paper's worked example that reproduces exactly
    (Table 18, gun 1: 3.766428), which is why it is here.
    """
    missing = [name for name, val in (
        ("k_md", k_md),
        ("k_crushed_md", k_crushed_md),
        ("k_damaged_md", k_damaged_md),
        ("crushed_radius_in", crushed_radius_in),
        ("perf_radius_in", perf_radius_in),
        ("perf_length_in", perf_length_in),
        ("perf_interval_ft", perf_interval_ft),
        ("shot_density_spf", shot_density_spf),
    ) if val is None]
    if missing:
        return Refusal(
            reason="McLeod Eq. (9) needs the crushed-zone geometry and permeabilities; "
                   "missing " + ", ".join(missing),
            needed=tuple(missing),
            source=KT_PROCEDURE)

    if min(k_md, k_crushed_md, k_damaged_md) <= 0:
        raise ValueError("permeabilities must be positive")
    if min(crushed_radius_in, perf_radius_in, perf_length_in,
           perf_interval_ft, shot_density_spf) <= 0:
        raise ValueError("radii, lengths, interval and shot density must be positive")
    if crushed_radius_in <= perf_radius_in:
        return Refusal(
            reason=f"crushed-zone radius {crushed_radius_in} in is not larger than the "
                   f"perforation radius {perf_radius_in} in, so ln(r_dp/r_p) is not "
                   "positive and there is no crushed annulus to model",
            needed=("crushed_radius_in > perf_radius_in",),
            source=KT_PROCEDURE)

    n_perfs = shot_density_spf * perf_interval_ft
    perm_group = k_md / k_crushed_md - k_md / k_damaged_md
    geom_group = (IN_PER_FT * perf_interval_ft) / (n_perfs * perf_length_in)
    s_dp = perm_group * geom_group * math.log(crushed_radius_in / perf_radius_in)

    flags = []
    if perm_group <= 0:
        flags.append(
            "crushed_zone_not_damaging: k/k_dp <= k/k_a, so the crushed zone is no less "
            "permeable than the damaged zone and Eq. (9) returns zero or a credit")
    return Quantity(
        s_dp, "dimensionless",
        "McLeod crushed-zone skin s_dp (Eq. 9)",
        KT_PROCEDURE,
        inputs={
            "n_perfs": n_perfs,
            "permeability_group": perm_group,
            "geometry_group": geom_group,
            "k_md": k_md,
            "k_crushed_md": k_crushed_md,
            "k_damaged_md": k_damaged_md,
            "crushed_radius_in": crushed_radius_in,
            "perf_radius_in": perf_radius_in,
            "perf_length_in": perf_length_in,
            "perf_interval_ft": perf_interval_ft,
            "shot_density_spf": shot_density_spf,
        },
        assumptions={
            "k_a": "damaged-zone permeability in mD (the source's nomenclature calls it a "
                   "radius; its Table 18 uses a permeability)",
            "n": "total perforations = shot density x perforated interval, as the source "
                 "computes it (6 spf x 6.56 ft = 39.36)",
            "limited_entry": "Eq. (11) does not apply h/h_p to s_dp",
            "oracle": "reproduces the source's Table 18 gun 1 exactly: 3.766428",
        },
        flags=tuple(flags))
