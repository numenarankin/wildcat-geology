"""Group O against hand-computed oracles.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

Every expected number in this file was computed by hand from the intent, never
by running the tool. The fixture is built so that can be done: five wells on a
square with one at the centroid, so the centred normal equations have Sxy = 0
and the plane coefficients fall out in one line of arithmetic. Working it that
way is what caught the point the whole group turns on, that an outlier at the
centroid leaves the DIP exact and moves only the intercept, so a datum error
shows up as residual and never as a wrong dip.
"""
from __future__ import annotations

import json
import math
import pathlib
import time
import unittest

import dispatch
from tools import multiwell
from tools.result import Quantity, Range, Refusal

CORPUS = pathlib.Path(__file__).resolve().parents[2] / "geology-corpus" / "toc" / ".segments.jsonl"

# --------------------------------------------------------------------------- #
# The fixture, and the hand arithmetic behind it.
#
# True plane: SSTVD = -0.03 x - 0.04 y - 5000, x east ft, y north ft.
#   gradient magnitude   hypot(0.03, 0.04) = 0.05
#   true dip             atan(0.05)                       = 2.862405... deg
#   down-dip is +x +y    bearing atan2(0.03, 0.04) = atan(0.75) = 36.869898 deg
#   dip rate             0.05 * 5280                      = 264 ft/mile
#
# Corners at (0,0) (1000,0) (0,1000) (1000,1000) and a centre well at (500,500):
#   (0,0)        -5000
#   (1000,0)     -5030
#   (0,1000)     -5040
#   (1000,1000)  -5070
#   (500,500)    -5035
# The set spans 70 ft of relief, which matters for the "does not flag ordinary
# structural relief" test: 70 ft of real structure, zero residual.
# --------------------------------------------------------------------------- #

TRUE_DIP_DEG = math.degrees(math.atan(0.05))
TRUE_AZIMUTH_DEG = math.degrees(math.atan2(0.03, 0.04))
CORNERS = [("A", 0.0, 0.0, -5000.0), ("B", 1000.0, 0.0, -5030.0),
           ("C", 0.0, 1000.0, -5040.0), ("D", 1000.0, 1000.0, -5070.0)]
CENTRE = ("E", 500.0, 500.0, -5035.0)


def pick(well, x, y, z, **kw):
    row = {"well": well, "x_ft": x, "y_ft": y, "sstvd_ft": z,
           "depth_basis": "SSTVD", "datum_resolved": True, "depth_reference": "KB"}
    row.update(kw)
    return row


def planar(rows):
    return [pick(*r) for r in rows]


class StructureMap(unittest.TestCase):
    def test_four_wells_return_the_dip_and_azimuth_computed_by_hand(self):
        out = multiwell.structure_map(planar(CORNERS))
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, TRUE_DIP_DEG, places=9)
        self.assertAlmostEqual(out.value, 2.8624052, places=6)
        self.assertAlmostEqual(out.inputs["dip_azimuth_deg"], TRUE_AZIMUTH_DEG, places=9)
        self.assertAlmostEqual(out.inputs["dip_azimuth_deg"], 36.8698976, places=6)
        self.assertAlmostEqual(out.inputs["dip_ft_per_mile"], 264.0, places=6)
        # Four exact points on one plane: no residual anywhere.
        self.assertAlmostEqual(out.inputs["rmse_ft"], 0.0, places=9)

    def test_predicts_the_surface_at_an_undrilled_location(self):
        # Hand: -0.03(500) - 0.04(500) - 5000 = -15 - 20 - 5000 = -5035.
        out = multiwell.structure_map(planar(CORNERS), target_x_ft=500.0, target_y_ft=500.0)
        self.assertAlmostEqual(out.inputs["target"]["predicted_sstvd_ft"], -5035.0, places=6)

    def test_true_dip_is_at_least_the_apparent_dip_between_any_two_of_the_picks(self):
        # The invariant that ties this to structural_dip (#20): an apparent dip
        # is a component of the true one and can never exceed it.
        from tools import geometry
        picks = planar(CORNERS)
        for i in range(len(picks)):
            for j in range(i + 1, len(picks)):
                apparent = geometry.structural_dip([picks[i], picks[j]], same_flank=True)
                self.assertLessEqual(apparent.value, TRUE_DIP_DEG + 1e-9)

    def test_refuses_on_exactly_three_picks(self):
        out = multiwell.structure_map(planar(CORNERS[:3]))
        self.assertIsInstance(out, Refusal)
        self.assertIn("three", out.reason)
        self.assertIn("r-squared of 1", out.reason)

    def test_refuses_a_collinear_population(self):
        line = [("A", 0.0, 0.0, -5000.0), ("B", 1000.0, 0.0, -5030.0),
                ("C", 2000.0, 0.0, -5060.0), ("D", 3000.0, 0.0, -5090.0)]
        out = multiwell.structure_map(planar(line))
        self.assertIsInstance(out, Refusal)
        self.assertIn("collinear", out.reason)

    def test_refuses_picks_hung_on_different_references(self):
        rows = planar(CORNERS)
        rows[2]["depth_reference"] = "GL"
        out = multiwell.structure_map(rows)
        self.assertIsInstance(out, Refusal)
        self.assertIn("datum_reconcile", out.needed[0])


class UnresolvedDatumIsExcludedAndCounted(unittest.TestCase):
    """The most important test in the file.

    A well whose datum will not resolve must leave the fit and stay visible in
    the count. Quietly defaulting it to zero, or quietly dropping it, both give a
    surface the operator cannot audit; one of them gives a confidently wrong one.
    """

    def setUp(self):
        # A sixth well, far out at (2000, 2000), whose depth would drag the plane
        # a long way if it were used: -4000 ft SS against a true -5140 there.
        self.rogue = {"well": "X", "x_ft": 2000.0, "y_ft": 2000.0,
                      "sstvd_ft": -4000.0, "depth_basis": "SSTVD",
                      "datum_resolved": False, "depth_reference": "KB"}
        self.rows = planar(CORNERS + [CENTRE]) + [self.rogue]

    def test_the_surface_is_fitted_without_it(self):
        out = multiwell.structure_map(self.rows)
        self.assertIsInstance(out, Quantity)
        # Unchanged from the five clean wells: the true plane, exactly.
        self.assertAlmostEqual(out.value, TRUE_DIP_DEG, places=9)
        self.assertAlmostEqual(out.inputs["dip_azimuth_deg"], TRUE_AZIMUTH_DEG, places=9)
        self.assertAlmostEqual(out.inputs["rmse_ft"], 0.0, places=9)
        self.assertAlmostEqual(out.inputs["plane"]["c_ft_ss"], -5000.0, places=6)
        self.assertNotIn("X", out.inputs["wells_used"])

    def test_it_is_counted_and_named_with_a_reason(self):
        out = multiwell.structure_map(self.rows)
        self.assertEqual(out.inputs["wells_supplied"], 6)
        self.assertEqual(out.inputs["placed_in_subsea"], 5)
        self.assertEqual(out.inputs["excluded_no_datum"], 1)
        self.assertEqual(out.inputs["excluded"][0]["well"], "X")
        self.assertIn("datum_resolved", out.inputs["excluded"][0]["reason"])
        self.assertIn("excluded_unresolved_datum", out.flags)

    def test_a_well_subsea_convert_refuses_is_excluded_the_same_way(self):
        # Raw TVD with no datum evidence at all: subsea_convert (#18) refuses and
        # the refusal travels into the exclusion reason rather than being caught.
        rows = planar(CORNERS + [CENTRE]) + [
            {"well": "X", "x_ft": 2000.0, "y_ft": 2000.0, "tvd_ft": 5140.0}
        ]
        out = multiwell.structure_map(rows)
        self.assertEqual(out.inputs["excluded_no_datum"], 1)
        self.assertIn("subsea_convert refused", out.inputs["excluded"][0]["reason"])
        self.assertAlmostEqual(out.value, TRUE_DIP_DEG, places=9)

    def test_a_raw_tvd_with_a_resolved_datum_is_placed_through_subsea_convert(self):
        # KB 1140 ft, TVD 6140 ft -> SSTVD = 1140 - 6140 = -5000 ft, which is the
        # corner-A value. Same fit as the all-subsea set.
        rows = planar(CORNERS[1:] + [CENTRE]) + [
            {"well": "A", "x_ft": 0.0, "y_ft": 0.0, "tvd_ft": 6140.0,
             "datum": {"reference": "KB", "elevation_ft": 1140.0}}
        ]
        out = multiwell.structure_map(rows)
        self.assertIsInstance(out, Quantity)
        self.assertEqual(out.inputs["excluded_no_datum"], 0)
        self.assertAlmostEqual(out.inputs["residuals_ft"]["A"], 0.0, places=6)
        self.assertAlmostEqual(out.value, TRUE_DIP_DEG, places=9)


class OffsetConsistency(unittest.TestCase):
    """Residuals against a hand-solved fit.

    Centre well pushed 100 ft deep, a datum-sized error. Centred sums over the
    five wells: Sxx = Syy = 1e6, Sxy = 0, Sxz = -30000, Syz = -40000, so
    a = -0.03 and b = -0.04 exactly, unchanged. mean z = -5055, so
    c = -5055 + 15 + 20 = -5020, i.e. the whole surface drops 20 ft.
    Residuals: +20 at each corner and -80 at the centre. Sum zero.
    ssres = 4(400) + 6400 = 8000, rmse = sqrt(1600) = 40 ft exactly.
    """

    BAD_CENTRE = ("E", 500.0, 500.0, -5135.0)

    def test_flags_the_datum_sized_outlier_and_nothing_else(self):
        out = multiwell.offset_consistency(planar(CORNERS + [self.BAD_CENTRE]),
                                           tolerance_ft=50.0)
        self.assertIsInstance(out, Range)
        for well in ("A", "B", "C", "D"):
            self.assertAlmostEqual(out.members[well], 20.0, places=6)
        self.assertAlmostEqual(out.members["E"], -80.0, places=6)
        self.assertAlmostEqual(out.low, -80.0, places=6)
        self.assertAlmostEqual(out.high, 20.0, places=6)
        self.assertAlmostEqual(out.inputs["rmse_ft"], 40.0, places=6)
        self.assertEqual([r["well"] for r in out.inputs["inconsistent_wells"]], ["E"])
        self.assertEqual(out.inputs["consistent_wells"], ["A", "B", "C", "D"])
        self.assertIn("residual_exceeds_tolerance", out.flags)

    def test_the_outlier_does_not_corrupt_the_dip(self):
        # Because the bad well sits at the centroid it moves only the intercept.
        out = multiwell.offset_consistency(planar(CORNERS + [self.BAD_CENTRE]),
                                           tolerance_ft=50.0)
        self.assertAlmostEqual(out.inputs["dip_deg"], TRUE_DIP_DEG, places=9)
        self.assertAlmostEqual(out.inputs["dip_azimuth_deg"], TRUE_AZIMUTH_DEG, places=9)

    def test_does_not_flag_ordinary_structural_relief(self):
        # The same five wells with no error. 70 ft of relief across the map,
        # 264 ft/mile of dip, and every residual is zero: relief lives in the
        # surface, not in the residual.
        out = multiwell.offset_consistency(planar(CORNERS + [CENTRE]), tolerance_ft=50.0)
        self.assertEqual(out.inputs["inconsistent_wells"], [])
        self.assertNotIn("residual_exceeds_tolerance", out.flags)
        for residual in out.members.values():
            self.assertAlmostEqual(residual, 0.0, places=9)
        depths = [r[3] for r in CORNERS + [CENTRE]]
        self.assertAlmostEqual(max(depths) - min(depths), 70.0, places=9)
        self.assertAlmostEqual(out.inputs["dip_deg"], TRUE_DIP_DEG, places=9)

    def test_refuses_without_a_tolerance(self):
        out = multiwell.offset_consistency(planar(CORNERS + [CENTRE]))
        self.assertIsInstance(out, Refusal)
        self.assertIn("within the accuracy of the data", out.reason)

    def test_a_tighter_tolerance_flags_the_corners_too(self):
        # Same fit, 10 ft accuracy: every well is now outside it. The verdict is
        # the caller's number and nothing else moved.
        out = multiwell.offset_consistency(planar(CORNERS + [self.BAD_CENTRE]),
                                           tolerance_ft=10.0)
        self.assertEqual([r["well"] for r in out.inputs["inconsistent_wells"]],
                         ["E", "A", "B", "C", "D"])


class DepthShift(unittest.TestCase):
    """A shift put in by hand and taken back out."""

    STEP = 0.5
    TRUE_SHIFT = 7.5

    @staticmethod
    def curve(z):
        # Three incommensurate periods, so the shape does not repeat inside the
        # search band and the correlation maximum is unique.
        return (30.0 + 20.0 * math.sin(z / 17.0)
                + 35.0 * math.sin(z / 5.3 + 1.0)
                + 15.0 * math.sin(z / 2.7 + 2.0))

    def setUp(self):
        n = int(400.0 / self.STEP) + 1
        self.depths = [5000.0 + i * self.STEP for i in range(n)]
        self.reference = [self.curve(z) for z in self.depths]
        # The target reads every feature 7.5 ft shallow, so the sample its index
        # calls z actually came from z + 7.5. Adding +7.5 to its depths fixes it.
        self.target = [self.curve(z + self.TRUE_SHIFT) for z in self.depths]

    def test_recovers_the_shift_that_was_introduced(self):
        out = multiwell.depth_shift(self.depths, self.reference,
                                    self.depths, self.target,
                                    max_shift_ft=25.0, curve="GR")
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, self.TRUE_SHIFT, places=6)
        self.assertGreater(out.inputs["coefficient"], 0.99)
        self.assertEqual(out.unit, "ft")

    def test_recovers_a_negative_shift(self):
        target = [self.curve(z - 4.0) for z in self.depths]
        out = multiwell.depth_shift(self.depths, self.reference, self.depths, target,
                                    max_shift_ft=25.0)
        self.assertAlmostEqual(out.value, -4.0, places=6)

    def test_an_aligned_pair_returns_zero(self):
        out = multiwell.depth_shift(self.depths, self.reference,
                                    self.depths, list(self.reference),
                                    max_shift_ft=25.0)
        self.assertAlmostEqual(out.value, 0.0, places=6)
        self.assertAlmostEqual(out.inputs["coefficient"], 1.0, places=9)

    def test_states_its_decimation(self):
        out = multiwell.depth_shift(self.depths, self.reference, self.depths,
                                    self.target, max_shift_ft=25.0)
        self.assertIn("decimation", out.assumptions)
        self.assertIn("block-AVERAGED", out.assumptions["decimation"])
        # 400 ft at 0.5 ft is inside the sweep budget, so nothing is decimated
        # and the coarse lattice IS the sample interval. Decimation is a cost
        # response, not a fixed node count.
        self.assertEqual(out.assumptions["coarse_lag_step_ft"], self.STEP)
        self.assertEqual(out.assumptions["fine_lag_step_ft"], self.STEP)

    def test_a_long_log_is_decimated_and_still_exact(self):
        # 10,000 ft at 0.5 ft, 20,000 samples, the case the 30 s budget is about.
        # The shortest bed in this curve has a 17 ft period, so a coarse lag step
        # near it picks a neighbouring correlation maximum: point-sampling this
        # onto a 512-node grid returned -21.0 ft for a +12.5 ft shift. Block
        # averaging onto a budgeted lattice is what fixed it, and this is the
        # regression test.
        depths = [3000.0 + i * self.STEP for i in range(20000)]
        reference = [self.curve(z) for z in depths]
        target = [self.curve(z + 12.5) for z in depths]
        started = time.time()
        out = multiwell.depth_shift(depths, reference, depths, target, max_shift_ft=50.0)
        elapsed = time.time() - started
        self.assertAlmostEqual(out.value, 12.5, places=6)
        self.assertGreater(out.assumptions["coarse_lag_step_ft"], self.STEP)
        self.assertEqual(out.assumptions["fine_lag_step_ft"], self.STEP)
        self.assertLess(elapsed, 10.0, "cross-correlation must fit the turn budget")

    def test_flags_a_shift_pinned_at_the_search_limit(self):
        out = multiwell.depth_shift(self.depths, self.reference, self.depths,
                                    self.target, max_shift_ft=2.0)
        self.assertIn("shift_at_search_limit", out.flags)

    def test_refuses_when_the_two_logs_do_not_overlap(self):
        far = [z + 5000.0 for z in self.depths]
        out = multiwell.depth_shift(self.depths, self.reference, far, self.target,
                                    max_shift_ft=25.0)
        self.assertIsInstance(out, Refusal)
        self.assertIn("no common rock", out.reason)


class AutoCorrelate(unittest.TestCase):
    STEP = 0.5
    TRUE_SHIFT = 7.5

    def setUp(self):
        n = int(400.0 / self.STEP) + 1
        self.depths = [5000.0 + i * self.STEP for i in range(n)]
        self.reference = [DepthShift.curve(z) for z in self.depths]
        self.target = [DepthShift.curve(z + self.TRUE_SHIFT) for z in self.depths]

    def test_proposes_the_offset_pick_at_the_hand_computed_depth(self):
        # The reference pick is at 5200 ft. The offset reads everything 7.5 ft
        # shallow, so the same horizon is at 5200 - 7.5 = 5192.5 ft there.
        out = multiwell.auto_correlate(self.depths, self.reference, 5200.0,
                                       self.depths, self.target,
                                       window_ft=100.0, max_shift_ft=25.0, curve="GR")
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, 5192.5, places=6)
        self.assertAlmostEqual(out.inputs["shift_ft"], 7.5, places=6)
        self.assertGreater(out.inputs["coefficient"], 0.99)

    def test_returns_the_matched_interval_not_a_bare_depth(self):
        out = multiwell.auto_correlate(self.depths, self.reference, 5200.0,
                                       self.depths, self.target,
                                       window_ft=100.0, max_shift_ft=25.0)
        self.assertEqual(out.inputs["reference_window_ft"], [5150.0, 5250.0])
        self.assertEqual(out.inputs["matched_interval_ft"], [5142.5, 5242.5])

    def test_reaches_no_verdict_without_a_caller_threshold(self):
        out = multiwell.auto_correlate(self.depths, self.reference, 5200.0,
                                       self.depths, self.target,
                                       window_ft=100.0, max_shift_ft=25.0)
        self.assertIn("no_coefficient_threshold_in_corpus", out.flags)
        self.assertIn("correlation_is_interpretive", out.flags)

    def test_refuses_a_match_below_the_callers_threshold(self):
        noise = [(-1.0) ** i * 50.0 for i in range(len(self.depths))]
        out = multiwell.auto_correlate(self.depths, self.reference, 5200.0,
                                       self.depths, noise,
                                       window_ft=100.0, max_shift_ft=25.0,
                                       min_coefficient=0.8)
        self.assertIsInstance(out, Refusal)
        self.assertIn("below", out.reason)


class Isopach(unittest.TestCase):
    ROWS = [{"well": "A", "top_ft": 5000.0, "base_ft": 5080.0, "depth_basis": "TVD"},
            {"well": "B", "top_ft": 5100.0, "base_ft": 5150.0, "depth_basis": "TVD"},
            {"well": "C", "top_ft": 5200.0, "base_ft": 5290.0, "depth_basis": "TVD"}]

    def test_vertical_thickness_per_well_and_the_band(self):
        # By hand: 80, 50, 90 ft.
        out = multiwell.isopach(self.ROWS, formation="Caddo")
        self.assertIsInstance(out, Range)
        self.assertEqual(out.members, {"A": 80.0, "B": 50.0, "C": 90.0})
        self.assertEqual((out.low, out.high), (50.0, 90.0))
        self.assertEqual(out.unit, "ft TVT")
        self.assertIn("isochore", out.assumptions["map_kind"])

    def test_eq_14_10_converts_vertical_to_stratigraphic_thickness(self):
        # TST = TVT cos(60 deg) = TVT / 2 -> 40, 25, 45 ft.
        out = multiwell.isopach(self.ROWS, upper_dip_deg=60.0)
        self.assertAlmostEqual(out.members["A"], 40.0, places=9)
        self.assertAlmostEqual(out.members["B"], 25.0, places=9)
        self.assertAlmostEqual(out.members["C"], 45.0, places=9)
        self.assertEqual(out.unit, "ft TST")
        self.assertIn("14-10", out.assumptions["equation"])

    def test_eq_14_11_reduces_to_eq_14_10_when_both_dips_are_equal(self):
        # sin 60 tan 60 + cos 60 = 1.5 + 0.5 = 2, so the factor is 1/2 again.
        # Two published equations for one quantity must agree where they overlap.
        two = multiwell.isopach(self.ROWS, upper_dip_deg=60.0, lower_dip_deg=60.0)
        one = multiwell.isopach(self.ROWS, upper_dip_deg=60.0)
        self.assertAlmostEqual(two.assumptions["correction_factor"], 0.5, places=12)
        for well in ("A", "B", "C"):
            self.assertAlmostEqual(two.members[well], one.members[well], places=9)
        self.assertIn("14-11", two.assumptions["equation"])

    def test_needs_no_datum(self):
        # None of these picks carries one, and the tool says why.
        out = multiwell.isopach(self.ROWS)
        self.assertIn("thickness_needs_no_datum", out.flags)

    def test_refuses_an_inverted_interval(self):
        rows = [dict(self.ROWS[0]), {"well": "B", "top_ft": 5150.0,
                                     "base_ft": 5100.0, "depth_basis": "TVD"}]
        out = multiwell.isopach(rows)
        self.assertIsInstance(out, Refusal)
        self.assertIn("correlation error", out.reason)

    def test_refuses_a_mixed_depth_basis(self):
        rows = [dict(r) for r in self.ROWS]
        rows[1]["depth_basis"] = "MD"
        out = multiwell.isopach(rows)
        self.assertIsInstance(out, Refusal)
        self.assertIn("mix depth bases", out.reason)

    def test_flags_measured_depth_as_not_vertical(self):
        rows = [dict(r, depth_basis="MD") for r in self.ROWS]
        out = multiwell.isopach(rows)
        self.assertIn("measured_thickness_not_vertical", out.flags)


class CurveNormalize(unittest.TestCase):
    def test_refuses_and_names_the_source_it_would_need(self):
        out = multiwell.curve_normalize(wells=["A", "B"], curve="GR")
        self.assertIsInstance(out, Refusal)
        self.assertIn("No attempt was made to normalize the gamma-ray logs", out.reason)
        self.assertEqual(out.source, multiwell.BEG_DEPTH_SHIFT)
        self.assertTrue(any("normalization transform" in n for n in out.needed))


class Provenance(unittest.TestCase):
    ANCHORS = (multiwell.TEARPOCK_GRIDDING, multiwell.TEARPOCK_CORRELATION,
               multiwell.TEARPOCK_CORRELATION_CHECK, multiwell.TEARPOCK_ISOCHORE_ISOPACH,
               multiwell.TEARPOCK_TST, multiwell.TEARPOCK_TST_TWO_DIPS,
               multiwell.WERMUND_TREND_SURFACE, multiwell.TEARPOCK_DATUM,
               multiwell.BEG_DEPTH_SHIFT)

    @unittest.skipUnless(CORPUS.exists(), "corpus index not present in this checkout")
    def test_every_anchor_resolves_to_a_corpus_segment(self):
        keys = {json.loads(line)["key"] for line in CORPUS.read_text().splitlines() if line.strip()}
        for anchor in self.ANCHORS:
            self.assertIn(anchor, keys, f"{anchor} is not a segment in the corpus index")

    def test_no_returned_value_is_an_orphan(self):
        results = [
            multiwell.structure_map(planar(CORNERS)),
            multiwell.offset_consistency(planar(CORNERS + [CENTRE]), tolerance_ft=50.0),
            multiwell.isopach(Isopach.ROWS),
        ]
        for out in results:
            self.assertIn(out.source, self.ANCHORS)
            self.assertTrue(out.method)


class Registry(unittest.TestCase):
    NAMES = ("curve_normalize", "depth_shift", "auto_correlate",
             "isopach", "structure_map", "offset_consistency")

    def test_all_six_are_discovered_in_the_module_that_defines_them(self):
        table = dispatch.registry()
        for name in self.NAMES:
            self.assertIn(name, table, f"{name} did not auto-discover")
            self.assertEqual(table[name][0], "tools.multiwell")

    def test_helpers_stayed_private(self):
        table = dispatch.registry()
        for leaked in ("pick", "planar", "score", "grid", "blocks", "clean"):
            self.assertNotIn(leaked, table)

    def test_this_module_does_not_re_home_another_modules_tool(self):
        """A cross-module import binding a FUNCTION would steal that tool.

        `registry()` gives a name to the first module alphabetically that exposes
        it, and `multiwell` sorts before `geometry`. So `from .geometry import
        subsea_convert` would move an existing, working tool onto this file with
        nothing raised and no symptom but a wrong module name in the catalog.
        Import the module, or alias private.
        """
        table = dispatch.registry()
        owned = {n for n, (module, _) in table.items() if module == "tools.multiwell"}
        self.assertEqual(owned, set(self.NAMES),
                         "tools.multiwell owns a name it does not define")
        for borrowed in ("subsea_convert", "datum_resolve", "structural_dip"):
            self.assertEqual(table[borrowed][0], "tools.geometry",
                             f"{borrowed} was re-homed away from tools.geometry")

    def test_callable_through_dispatch_with_json_arguments(self):
        out = dispatch.call("structure_map", {
            "picks": [{"well": w, "x_ft": x, "y_ft": y, "sstvd_ft": z,
                       "depth_basis": "SSTVD", "datum_resolved": True,
                       "depth_reference": "KB"} for w, x, y, z in CORNERS]
        })
        self.assertEqual(out["kind"], "Quantity")
        self.assertAlmostEqual(out["value"], TRUE_DIP_DEG, places=9)

    def test_a_refusal_crosses_the_boundary_as_a_value(self):
        out = dispatch.call("curve_normalize", {"curve": "GR"})
        self.assertEqual(out["kind"], "Refusal")
        self.assertIn("beg-boonsville#36", out["reason"])


if __name__ == "__main__":
    unittest.main()
