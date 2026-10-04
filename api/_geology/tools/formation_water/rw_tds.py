"""Tool #92 `rw_from_tds` (group J, section 13 — formation water).

Merge note for the coordinator
------------------------------
Destination: `tools/petrophysics.py`.

`resistivity_at_temperature` below is a **drop-in replacement** for the function of
that name already in `tools/petrophysics.py` (lines 183-195), not a second copy.
The existing three-positional-argument call site keeps working and returns the same
number; what is added is the refusal set the original lacked (the Rwe trap, the
correlation pole) and honest handling of the Celsius constant, which the original
hard-coded at 21.0 with no note that a corpus source prints 21.5. `ASQUITH_TEMP`
is already defined in that module and is reused; the two new anchors below are new.

Why `rw_from_tds` always refuses
--------------------------------
The catalogued tool — concentration in, Rw out — has no arithmetic behind it in
this corpus. Every document that needs the step reads Schlumberger chart Gen-9
(= Western Atlas 1-5 = AAPG formation-water-density Figure 1 = Mosul Fig.2). The
assigned anchor `11-rw-and-crossplots/aapg-water-resistivity-determination#0`
gives three routes to Rw (SP, Archie, resistivity ratio) and not one of them takes
a salinity. Its Gen-9 use is a *temperature* correction of Rm/Rmf, and its Rwe->Rw
step is likewise a chart (Chart 5 / Schlumberger SP-2).

The nearest equation in the neighbourhood is a trap and is deliberately not used:
`aapg-formation-water-density#0` prints `rho_w = 1 + TDS * 0.695e-6 g/cm3`, which
is a *density*, not a resistivity. The ppm<->Rw relation is widely tabulated
outside this corpus, which is precisely why it is not reproduced from memory here:
an unsourced version would look right and pass every test in this suite.

What is genuinely printed, and is therefore implemented, is Arps — which moves a
resistivity between temperatures and says nothing about salinity. See
`specs/92-rw_from_tds.md`.
"""
from __future__ import annotations

from ..result import Quantity, Range, Refusal  # noqa: F401  (Range unused here)

# --------------------------------------------------------------------------
# Anchors
# --------------------------------------------------------------------------

# Assigned anchor. Read in full: SP / Archie / resistivity-ratio routes to Rw,
# Gen-9 and SP-2 invoked as charts, no concentration route and no Arps.
AAPG_RW_DETERMINATION = "11-rw-and-crossplots/aapg-water-resistivity-determination#0"

# The other source `tool-provenance.md` attributes to this tool. Its only closed
# form is a water-density formula; its NaCl step is Figure 1 (Schlumberger/Gen-9).
AAPG_WATER_DENSITY = "11-rw-and-crossplots/aapg-formation-water-density#0"

# Arps, Eq. 9 (degF) and Eq. 10 (degC), with a worked example.
MOSUL_ELECTRICAL = "11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties#1"

# Arps, Eq. 1.10, with the same worked example. Already defined in
# tools/petrophysics.py as ASQUITH_TEMP; repeated here so this fragment stands alone.
ASQUITH_TEMP = "01-curve-reading/asquith-krygowski-basic-well-log-analysis-2004#9"

# Upstream tool the caller must run before any resistivity transform.
NACL_EQUIVALENT_SOURCE = "11-rw-and-crossplots/mosul-well-log-analysis-lec2-electrical-properties"


# --------------------------------------------------------------------------
# Constant tables
# --------------------------------------------------------------------------

# Arps additive constant, R2 = R1 (T1 + X) / (T2 + X). Unit-bound: using the
# Fahrenheit constant on Celsius temperatures is a large error that looks
# entirely plausible, so the unit system is an argument and never inferred.
#
# The Fahrenheit value is unanimous across both citing sources. The Celsius
# value is NOT: Asquith prints 21.0, the Mosul lecture prints 21.5. That is a
# real corpus disagreement, unreconciled in tool-catalog.md, worth ~0.7% on a
# 20->80 degC conversion. Neither Celsius form carries a worked example; both
# Fahrenheit citations do. They are exposed separately and never averaged.
ARPS_CONSTANT = {
    "degF": {
        "value": 6.77,
        "source": ASQUITH_TEMP,
        "note": "6.77 degF; identical in Mosul #1 Eq. 9 and Asquith #9 Eq. 1.10",
    },
    # Celsius: selected by `celsius_constant`, default "asquith".
    "degC_asquith": {
        "value": 21.0,
        "source": ASQUITH_TEMP,
        "note": "Asquith Eq. 1.10 metric form",
    },
    "degC_mosul": {
        "value": 21.5,
        "source": MOSUL_ELECTRICAL,
        "note": "Mosul Eq. 10",
    },
}

# Equivalent resistivities. These are SP-derived quantities linearly related to
# chemical activity; converting one to a true resistivity is a chart step
# (anchor #0, "Chart 5" = Schlumberger SP-2 / Western Atlas 2-3), not a
# temperature correction. Arps cannot do it, so they are refused by name.
EQUIVALENT_RESISTIVITY_KINDS = ("Rwe", "Rmfe")

TRUE_RESISTIVITY_KINDS = ("Rw", "Rmf", "Rm", "Rmc", "Rt", "Rxo", "Ro")

# Bases that mean "this number has not been through nacl_equivalent (#91)".
RAW_TDS_BASES = ("raw_tds", "tds", "multi_ion_tds", "total_dissolved_solids", "raw")

# Not a validity window — the corpus states none for Arps. This is only the span
# of temperatures its published examples cover (Asquith 70/166 degF, Mosul
# 70/166/140/250 degF), used to flag extrapolation rather than to refuse it.
ARPS_EXAMPLE_SPAN = {"degF": (70.0, 250.0), "degC": (21.0, 121.0)}

# The chart that would unblock rw_from_tds, under all the names the corpus uses.
GEN9_ALIASES = (
    "Schlumberger Gen-9",
    "Western Atlas 1-5",
    "AAPG formation-water-density Figure 1",
    "Mosul lecture Fig.2",
)


# --------------------------------------------------------------------------
# #92 rw_from_tds — a refusal in every branch, by design
# --------------------------------------------------------------------------

def rw_from_tds(nacl_equivalent_ppm: float,
                temperature_degf: float,
                *,
                concentration_basis: str = "nacl_equivalent",
                concentration_units: str = "ppm") -> Refusal:
    """Rw from equivalent-NaCl concentration. **Always refuses** — see module docstring.

    The concentration -> Rw relation is chart-only in this corpus (Gen-9). There is
    no input for which this returns a number. The branches exist so the caller is
    told *which* thing is wrong, most specific first: a raw multi-ion TDS is a
    different and worse error than simply hitting the missing chart, and it is worth
    saying so even though the answer is a refusal either way.

    Args:
        nacl_equivalent_ppm: equivalent-NaCl concentration in ppm (mg/kg). NOT raw
            TDS from a multi-ion analysis — run `nacl_equivalent` (#91) first;
            sulfate-heavy water is badly wrong without its per-ion multipliers.
            Taken as a plain number so this tool does not depend on #91's module.
        temperature_degf: temperature the Rw is wanted at, degrees Fahrenheit.
        concentration_basis: "nacl_equivalent" (the only acceptable basis) or one
            of RAW_TDS_BASES, which triggers the #91 refusal.
        concentration_units: "ppm". "mg/l" triggers its own refusal.
    """
    if temperature_degf is None:
        raise ValueError("temperature_degf is required")

    basis = str(concentration_basis).strip().lower()
    units = str(concentration_units).strip().lower().replace(" ", "")

    # 1. Declared raw / multi-ion TDS: the upstream tool was skipped.
    if basis in RAW_TDS_BASES:
        return Refusal(
            reason=(
                "concentration_basis is declared as raw multi-ion TDS. Raw TDS is the "
                "wrong input to any resistivity transform: each ion contributes to "
                "conductivity differently, and sulfate-heavy water is substantially "
                "wrong without per-ion multipliers. Run nacl_equivalent (#91) first and "
                "pass its equivalent-NaCl ppm. (Separately, the concentration-to-Rw step "
                "itself is chart-only here - see the refusal you would get anyway.)"
            ),
            needed=(
                "equivalent-NaCl concentration in ppm from nacl_equivalent (#91)",
                "the per-ion multiplier table, digitized from the Mosul Fig-3 curves",
            ),
            source=NACL_EQUIVALENT_SOURCE,
        )

    if basis != "nacl_equivalent":
        raise ValueError(
            f"unrecognised concentration_basis {concentration_basis!r}; expected "
            f"'nacl_equivalent' or one of {RAW_TDS_BASES}"
        )

    # 2. mg/L declared: needs the water density, and Gen-9's own basis is unstated.
    if units in ("mg/l", "mgl", "mg/liter", "mg/litre", "ppmv"):
        return Refusal(
            reason=(
                "concentration declared in mg/L. Converting mg/L to ppm (mg/kg) requires "
                "the water density, and no source in this corpus states which basis the "
                "Gen-9 chart axis uses - at 200,000 ppm the two differ by over 10%. "
                "Pass ppm, or settle the chart's basis first."
            ),
            needed=(
                "concentration in ppm (mg/kg)",
                "the concentration basis of Schlumberger Gen-9's salinity axis",
            ),
            source=AAPG_WATER_DENSITY,
        )

    if units != "ppm":
        raise ValueError(
            f"unrecognised concentration_units {concentration_units!r}; expected 'ppm'"
        )

    # 3. The documented trap: an Rwe (a resistivity, typically 0.03-0.5 ohm-m)
    #    handed to an argument that wants a concentration. A type guard, not a
    #    source-derived threshold - the corpus states no concentration range.
    if nacl_equivalent_ppm is None or nacl_equivalent_ppm <= 0 or nacl_equivalent_ppm < 1.0:
        return Refusal(
            reason=(
                f"{nacl_equivalent_ppm!r} is not a concentration. Values below 1 ppm are "
                "the signature of a resistivity passed into the ppm argument - most often "
                "an Rwe. Rwe is an equivalent *resistivity* in ohm-m, not a concentration; "
                "a tool that accepted it here would return a confidently wrong Rw. "
                "Pass equivalent-NaCl ppm from nacl_equivalent (#91). (Type guard, not a "
                "source-stated limit: no document in this corpus gives a valid "
                "concentration range for the chart.)"
            ),
            needed=("equivalent-NaCl concentration in ppm (mg/kg), a positive number >= 1",),
            source=AAPG_RW_DETERMINATION,
        )

    # 4. The real refusal: the relation is a chart.
    return Refusal(
        reason=(
            "no closed form for Rw from concentration and temperature exists in this "
            "corpus - the relation is chart-only. The assigned source gives three routes "
            "to Rw (SP, Archie Rw = phi^2 Rt, and the resistivity ratio Rw = (Rt/Rxo) Rmf) "
            "and none of them takes a salinity; where it needs a resistivity at another "
            "temperature it reads chart Gen-9, and where it needs Rwe -> Rw it reads chart "
            "SP-2. AAPG formation-water-density does the same via its Figure 1, and its "
            "only equation (rho_w = 1 + TDS*0.695e-6) is a water *density*, not an Rw. "
            f"Would be unblocked by any of: {'; '.join(GEN9_ALIASES)} digitized as a "
            "lookup table with its stated axis ranges; a cited closed-form approximation "
            "with its validity range and concentration basis; or a laboratory Rw at a "
            "known temperature, which routes you to resistivity_at_temperature instead. "
            "This is NOT to be closed by writing the textbook approximation from memory."
        ),
        needed=(
            "Schlumberger chart Gen-9 digitized (Rw vs NaCl ppm vs temperature), with axis ranges",
            "or a cited published closed form with its validity range and ppm-vs-mg/L basis",
            "or a measured Rw at a stated temperature (then use resistivity_at_temperature)",
        ),
        source=AAPG_RW_DETERMINATION,
    )


# --------------------------------------------------------------------------
# The deterministic core that IS printed: Arps temperature conversion
# --------------------------------------------------------------------------

def resistivity_at_temperature(r_known: float,
                               t_known: float,
                               t_target: float,
                               units: str = "degF",
                               *,
                               quantity_kind: str = "Rw",
                               celsius_constant: str = "asquith"):
    """Arps temperature correction: R2 = R1 (T1 + X) / (T2 + X).

    Replaces the function of the same name in `tools/petrophysics.py`; the old
    three-positional-argument call returns an identical value.

    This converts a resistivity from one temperature to another. It does **not**
    convert a salinity into a resistivity - that is `rw_from_tds`, which refuses -
    and it does not convert an equivalent resistivity into a true one, which is why
    Rwe and Rmfe are refused rather than quietly rescaled.

    Sources (the assigned anchor for #92 does not contain Arps at all):
      Mosul #1 Eq. 9  : R2 = R1 [(T1 + 6.77)/(T2 + 6.77)] ; degF
      Mosul #1 Eq. 10 : R2 = R1 [(T1 + 21.5)/(T2 + 21.5)] ; degC
      Asquith #9 Eq. 1.10: R_TF = R_temp (Temp + 6.77)/(T_f + 6.77), 21.0 in metric

    Asquith introduces it as an approximation to a chart ("This chart is closely
    approximated by the Arp's formula"), which is the honest framing of its accuracy.
    """
    if units not in ("degF", "degC"):
        raise ValueError(f"units must be 'degF' or 'degC', got {units!r}")
    if r_known is None or r_known <= 0:
        raise ValueError(f"resistivity must be positive, got {r_known!r}")

    kind = str(quantity_kind)

    # The documented trap. Rwe -> Rw is chart SP-2 (Chart 5) in the anchor; Arps
    # is a temperature correction and cannot perform it. Returning a Quantity here
    # would hand the caller a wrong Rw that looks entirely reasonable.
    if kind in EQUIVALENT_RESISTIVITY_KINDS:
        return Refusal(
            reason=(
                f"{kind} is an equivalent resistivity, not a true one. Arps corrects a "
                "resistivity between temperatures; it cannot convert an equivalent "
                f"resistivity to a true one. In the assigned source that step is a chart "
                "(Chart 5 = Schlumberger SP-2 / Western Atlas 2-3): 'the true value of Rw "
                "is derived from its equivalent Rwe value, again using the appropriate "
                "charts.' Applying Arps here and labelling the result Rw produces a wrong "
                "Rw silently."
            ),
            needed=(
                "the Rwe -> Rw conversion (chart Schlumberger SP-2), or a true resistivity "
                "(Rw / Rmf / Rm / Rmc) to correct instead",
            ),
            source=AAPG_RW_DETERMINATION,
        )
    if kind not in TRUE_RESISTIVITY_KINDS:
        raise ValueError(
            f"unrecognised quantity_kind {quantity_kind!r}; expected one of "
            f"{TRUE_RESISTIVITY_KINDS + EQUIVALENT_RESISTIVITY_KINDS}"
        )

    if units == "degF":
        entry = ARPS_CONSTANT["degF"]
        other = None
    else:
        key = {"asquith": "degC_asquith", "mosul": "degC_mosul"}.get(str(celsius_constant).lower())
        if key is None:
            raise ValueError(
                f"celsius_constant must be 'asquith' or 'mosul', got {celsius_constant!r}"
            )
        entry = ARPS_CONSTANT[key]
        other = ARPS_CONSTANT["degC_mosul" if key == "degC_asquith" else "degC_asquith"]

    x = entry["value"]

    # The correlation's pole. Past it the formula returns a negative or infinite
    # resistivity, which is not a result the source supports at any confidence.
    if (t_known + x) <= 0 or (t_target + x) <= 0:
        return Refusal(
            reason=(
                f"temperature at or below the Arps pole: the correlation divides by "
                f"(T + {x}) in {units}, so T <= {-x} {units} yields a negative or infinite "
                f"resistivity. Got T1={t_known}, T2={t_target} {units}."
            ),
            needed=(f"both temperatures above {-x} {units}",),
            source=entry["source"],
        )

    r2 = r_known * (t_known + x) / (t_target + x)

    flags: list[str] = []
    lo, hi = ARPS_EXAMPLE_SPAN[units]
    if not (lo <= t_known <= hi) or not (lo <= t_target <= hi):
        flags.append(
            f"temperature outside {lo}-{hi} {units}, the span of the worked examples in "
            "the corpus; no source states a validity window for Arps, so this is "
            "extrapolation flagged rather than refused"
        )
    if units == "degC" and other is not None:
        flags.append(
            f"Celsius constant is disputed in the corpus: used {x} ({entry['note']}); "
            f"{other['value']} appears in {other['note']}. Worth ~0.7% on a 20->80 degC "
            "conversion. The Fahrenheit form is unanimous and is the supported path."
        )

    return Quantity(
        r2, "ohm-m",
        f"Arps temperature correction ({units}, X={x})",
        entry["source"],
        inputs={"R1": r_known, "T1": t_known, "T2": t_target, "quantity_kind": kind},
        assumptions={
            "constant": x,
            "units": units,
            "constant_source": entry["note"],
            "basis": "approximation to the fluid-resistivity temperature chart "
                     "(Asquith Fig. 1.11 / Schlumberger Gen-9)",
        },
        flags=tuple(flags),
    )
