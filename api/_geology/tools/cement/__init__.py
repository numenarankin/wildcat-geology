"""Cement and wellbore integrity. Tools #102-#108, catalog section 15.

A package because the seven tools collide by name - three define
`DRILLINGMANUAL`, two define `SOURCE` and `METHOD` - while quoting different
documents.

**`tool-verification.md` is stale on this whole section.** It records "the cement
path has no numbers" and lists `cbl_bond_index`, `isolation_length_check` and
`behind_pipe_isolation_check` as unsourced. That was true of the *markdown*: the
drilling manual's body literally reads "The bond index is given by [nothing]".
The equations were later recovered into the page-anchored `.equations.md`
sidecars and the catalog re-sourced the section. Every tool here followed the
catalog and says so in its own docstring. What remains true is narrower: no
*amplitude* number exists anywhere in the corpus, so `cbl_calibration`'s chart
table is empty by construction.

Two things hold the section together:

**One calibration, read by everyone.** `cbl_calibration` (#102) establishes the
two anchors - free pipe (BI = 0) and 100% bonded (BI = 1) - and `cbl_bond_index`
(#103) and `vdl_classify` (#106) both read it rather than each deriving its own.
The patent settles the line explicitly: BI = (dB(x) - dB_freePipe) /
(dB_100%bond - dB_freePipe), **linear in dB, not in amplitude**, and that
reconciles with the drilling manual's A_m/A_c because with attenuation
referenced to free pipe the free-pipe term is zero and the -20/d factors cancel.
Both give 0.596302 on the same inputs.

**One Pilkington rule.** `isolation_length_check` (#104) owns it - 5 ft of 80%
bond index for 5 in. OD casing, 15 ft for 9-5/8 in., "slightly higher" at 60%
(qualitative, so the 60% case refuses) - and `behind_pipe_isolation_check` (#107)
imports it rather than re-deriving. #107 holds no source number of its own. That
is deliberate: duplicating a table is how the last transcription error in this
project survived, two copies drifting while each looked corroborated by the
other.

The sign is the trap Part 5 of the build doc names. Attenuation is
(-20/d) log(measured / free-pipe) in the drilling manual and (+20/TR) in
OnePetro; the negative form is right, because cement attenuates and the result
must come out positive. It **cancels inside the bond-index ratio and does not
cancel in a reported attenuation**, so flipping the prefix leaves BI at 0.531320
while turning attenuation from +5.28 to -5.28. Tests assert the two separately;
an abs() would pass the corrupt form.

Three of the seven mostly decline, and that is the section rather than a gap in
it: `squeeze_recommend` cannot be asked *whether* to squeeze (its log-evidence
arguments exist only to be refused, quoting the source's own warning that "most
squeeze applications are unnecessary"), `vdl_classify` never returns a
channelling verdict because a single 3 ft amplitude curve cannot identify one,
and `cbl_calibration` refuses whenever the 100%-bonded anchor is missing, which
the patent admits is the common case.
"""
from .calibration import (
    cbl_calibration,
    cbl_characteristic_line,
    cbl_free_pipe_reference,
)
from .bond_index import (
    cbl_attenuation,
    cbl_bond_index,
    cbl_bond_index_from_attenuation,
)
from .isolation import (
    BiRun,
    gap_scan,
    isolation_length_check,
    pilkington_required_length_ft,
    sustained_bi_runs,
)
from .microannulus import microannulus_discriminate
from .vdl import vdl_class_name, vdl_classify
from .behind_pipe import behind_pipe_isolation_check
from .squeeze import squeeze_recommend
from .plugback import plugback_vs_squeeze

__all__ = [
    "cbl_calibration",
    "cbl_free_pipe_reference",
    "cbl_characteristic_line",
    "cbl_bond_index",
    "cbl_bond_index_from_attenuation",
    "cbl_attenuation",
    "isolation_length_check",
    "pilkington_required_length_ft",
    "sustained_bi_runs",
    "gap_scan",
    "BiRun",
    "microannulus_discriminate",
    "vdl_classify",
    "vdl_class_name",
    "behind_pipe_isolation_check",
    "squeeze_recommend",
    "plugback_vs_squeeze",
]
