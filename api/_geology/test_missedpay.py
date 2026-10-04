"""Group Q, missed pay. Two tools refuse and one screens.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

The wording assertions on `low_resistivity_screen` are not style checks. The
whole risk of a tool like this is that a candidate list gets read, quoted or
rendered as a pay determination, so the verdict says what it is in words and the
tests hold it to that.
"""
from __future__ import annotations

import unittest

from test_classic import segment_keys
from tools import missedpay
from tools.classic import BUCKLES_SPREAD_TOLERANCE
from tools.missedpay import low_resistivity_screen, rock_typing, thin_bed_correction
from tools.result import Refusal


class Provenance(unittest.TestCase):
    """Even a refusal's anchor has to resolve, and both of these cite one."""

    def test_every_anchor_resolves(self):
        keys = segment_keys()
        if keys is None:  # pragma: no cover - corpus not checked out
            self.skipTest("geology-corpus/toc/.segments.jsonl not found")
        anchors = {name: value for name, value in vars(missedpay).items()
                   if name.isupper() and isinstance(value, str) and "#" in value}
        self.assertGreaterEqual(len(anchors), 2)
        for name, anchor in sorted(anchors.items()):
            self.assertIn(anchor, keys, f"{name} does not resolve: {anchor}")


class LowResistivityScreenTests(unittest.TestCase):
    """asquith#45: a zone at irreducible saturation produces water free."""

    #: BVW = 0.045, 0.044, 0.0462. Mean 0.0450666..., spread 0.0022,
    #: relative 0.0022/0.04506667 = 0.048817, well inside the 0.22222 tolerance.
    #: Every Sw is above 0.40, so a conventional cutoff would call all three wet.
    FINE_SAND = [
        {"depth_ft": 6100.0, "phi": 0.09, "sw": 0.50},
        {"depth_ft": 6110.0, "phi": 0.10, "sw": 0.44},
        {"depth_ft": 6120.0, "phi": 0.11, "sw": 0.42},
    ]

    def test_constant_bvw_with_wet_looking_sw_yields_candidates(self):
        out = low_resistivity_screen(self.FINE_SAND, sw_wet_cutoff=0.40)
        self.assertIs(out.at_irreducible, True)
        self.assertEqual(len(out.candidates), 3)
        self.assertEqual([q.inputs["depth_ft"] for q in out.candidates],
                         [6100.0, 6110.0, 6120.0])
        # Hand-computed BVW on the first candidate: 0.09 x 0.50 = 0.045.
        self.assertAlmostEqual(out.candidates[0].value, 0.045, places=12)
        # And the interval's relative spread, hand-computed.
        self.assertAlmostEqual(out.bvw.spread.assumptions["relative_spread"],
                               0.0022 / (0.1352 / 3.0), places=12)

    def test_the_result_is_candidates_and_says_it_is_not_a_conclusion(self):
        out = low_resistivity_screen(self.FINE_SAND, sw_wet_cutoff=0.40)
        verdict = out.verdict.lower()
        self.assertIn("candidate", verdict)
        self.assertIn("not a conclusion", verdict)
        self.assertIn("not a pay determination", verdict)
        self.assertEqual(out.assumptions["result_status"],
                         "CANDIDATES for review, not a pay determination")

    def test_the_empty_outcome_is_also_not_a_conclusion(self):
        """No candidates must not read as "screened clean"."""
        out = low_resistivity_screen(self.FINE_SAND, sw_wet_cutoff=0.90)
        self.assertEqual(out.candidates, ())
        self.assertIs(out.at_irreducible, True)
        self.assertIn("not a conclusion", out.verdict.lower())

    def test_varying_bvw_yields_no_candidates(self):
        # BVW 0.040, 0.120, 0.125: relative spread 0.085/0.095 = 0.8947, far
        # outside the tolerance, so the zone is not at irreducible saturation and
        # a wet-looking resistivity needs no second explanation.
        varying = [{"phi": 0.10, "sw": 0.40},
                   {"phi": 0.20, "sw": 0.60},
                   {"phi": 0.25, "sw": 0.50}]
        out = low_resistivity_screen(varying, sw_wet_cutoff=0.30)
        self.assertIs(out.at_irreducible, False)
        self.assertEqual(out.candidates, ())
        self.assertIn("not at irreducible water saturation", out.verdict)
        self.assertIn("not a conclusion", out.verdict.lower())

    def test_one_depth_cannot_be_screened(self):
        out = low_resistivity_screen([{"phi": 0.10, "sw": 0.50}])
        self.assertIsNone(out.at_irreducible)
        self.assertEqual(out.candidates, ())
        self.assertIn("not a conclusion", out.verdict.lower())

    def test_untested_mechanisms_are_named_on_every_result(self):
        out = low_resistivity_screen(self.FINE_SAND, sw_wet_cutoff=0.40)
        joined = " ".join(out.flags)
        self.assertIn("thin_bed_correction", joined)
        self.assertIn("conductive minerals", joined)

    def test_both_thresholds_are_declared_provisional(self):
        out = low_resistivity_screen(self.FINE_SAND, sw_wet_cutoff=0.40)
        provisional = [f for f in out.flags if "PROVISIONAL" in f]
        self.assertTrue(any("sw_wet_cutoff" in f for f in provisional))
        self.assertTrue(any("tolerance" in f for f in provisional))

    def test_vshale_is_reported_and_not_acted_on(self):
        rows = [dict(r, vshale=0.35) for r in self.FINE_SAND]
        out = low_resistivity_screen(rows, sw_wet_cutoff=0.40)
        self.assertAlmostEqual(out.assumptions["vshale_max"], 0.35, places=12)
        self.assertTrue(any("shaly_sand_sw" in f for f in out.flags))
        # It changed nothing: the candidates are the same three depths.
        self.assertEqual(len(out.candidates), 3)

    def test_default_tolerance_is_the_buckles_one(self):
        out = low_resistivity_screen(self.FINE_SAND)
        self.assertAlmostEqual(out.bvw.tolerance, BUCKLES_SPREAD_TOLERANCE, places=12)

    def test_bad_samples_refuse(self):
        self.assertIsInstance(low_resistivity_screen([]), Refusal)
        self.assertIsInstance(low_resistivity_screen([{"phi": 0.1}]), Refusal)


class UnsourcedToolTests(unittest.TestCase):
    """The two group Q techniques this corpus does not carry."""

    def test_thin_bed_correction_always_refuses(self):
        out = thin_bed_correction(rt=2.0, rsand=20.0, rshale=1.0, vshale=0.5)
        self.assertIsInstance(out, Refusal)
        self.assertIsNone(out.value)
        self.assertIn("sand and shale laminae", out.reason)
        self.assertTrue(any("Poupon" in n for n in out.needed))

    def test_thin_bed_refusal_distinguishes_the_two_corrections(self):
        """The nearest corpus material is a different correction, and it says so."""
        out = thin_bed_correction()
        self.assertIn("trieste#5", out.reason)
        self.assertIn("thickness of the bed it sits in", out.reason)

    def test_rock_typing_always_refuses(self):
        out = rock_typing([{"k_md": 10.0, "phi": 0.18}])
        self.assertIsInstance(out, Refusal)
        self.assertIsNone(out.value)
        self.assertIn("flow zone indicator", out.reason)
        self.assertTrue(any("Amaefule" in n for n in out.needed))

    def test_rock_typing_redirects_to_what_is_citable(self):
        out = rock_typing()
        self.assertIn("asquith#48", out.reason)
        self.assertIn("bulk_volume_water", out.reason)


class DispatchTests(unittest.TestCase):
    """Auto-discovery is the only thing registering these."""

    NAMES = ("thin_bed_correction", "low_resistivity_screen", "rock_typing")

    def test_every_tool_is_registered(self):
        import dispatch
        table = dispatch.registry()
        for name in self.NAMES:
            self.assertIn(name, table, f"{name} is not in the registry")
            self.assertEqual(table[name][0], "tools.missedpay")

    def test_callable_through_dispatch(self):
        import dispatch
        out = dispatch.call("low_resistivity_screen", {
            "samples": [{"depth_ft": 6100.0, "phi": 0.09, "sw": 0.50},
                        {"depth_ft": 6110.0, "phi": 0.10, "sw": 0.44}],
            "sw_wet_cutoff": 0.40,
        })
        self.assertEqual(len(out["candidates"]), 2)
        self.assertIn("not a conclusion", out["verdict"].lower())

    def test_refusal_crosses_the_boundary_as_a_refusal(self):
        import dispatch
        out = dispatch.call("rock_typing", {})
        self.assertEqual(out["kind"], "Refusal")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
