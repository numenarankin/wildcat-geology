"""Group P, the classic Asquith techniques. Every expected value hand-computed.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

Where Asquith prints a worked table, the oracle is HIS number, not one this code
produced: `mn_plot` is checked against Table 4.16, which lists M and N for eleven
depths of the Fusselman. That is the strongest oracle available here, because it
was computed by the author from the equation and not by this module from itself.

The two refusing tools are tested for refusing. `multimineral_solve` cannot be
checked against a known mixture, because there is no mixture to solve: the
N-mineral response system is not in this corpus and the tool returns no numbers
at all. Asserting it refuses, and that the refusal names what source would
unblock it, is the whole of its contract.
"""
from __future__ import annotations

import json
import pathlib
import unittest

from tools import classic
from tools.classic import (
    BUCKLES_SPREAD_TOLERANCE,
    bulk_volume_water,
    mid_plot,
    mn_plot,
    movable_hydrocarbon_index,
    multimineral_solve,
    rwa_method,
    thomas_stieber,
)
from tools.result import Quantity, Refusal


def segment_keys() -> set[str] | None:
    """Every anchor the corpus index actually defines, or None if it is absent.

    Found by walking up from this file rather than from the working directory,
    so the check runs the same way under `unittest discover` from anywhere.
    """
    for parent in pathlib.Path(__file__).resolve().parents:
        path = parent / "geology-corpus" / "toc" / ".segments.jsonl"
        if path.exists():
            return {json.loads(line)["key"]
                    for line in path.read_text().splitlines() if line.strip()}
    return None


class Provenance(unittest.TestCase):
    """Every anchor this module cites has to be a segment that exists.

    An anchor that does not resolve is worse than a missing tool: it passes
    `provenance_audit` and reads as though somebody checked it.
    """

    def test_every_anchor_resolves(self):
        keys = segment_keys()
        if keys is None:  # pragma: no cover - corpus not checked out
            self.skipTest("geology-corpus/toc/.segments.jsonl not found")
        anchors = {name: value for name, value in vars(classic).items()
                   if name.isupper() and isinstance(value, str) and "#" in value}
        self.assertGreaterEqual(len(anchors), 9)
        for name, anchor in sorted(anchors.items()):
            self.assertIn(anchor, keys, f"{name} does not resolve: {anchor}")


class BulkVolumeWaterTests(unittest.TestCase):
    """Eq. 7.22 and the Buckles verdict of asquith#45."""

    def test_tolerance_is_the_sources_own_example_band(self):
        # asquith#51, Figure 7.3a: "all the points plot between 0.04 and 0.05
        # BVW", in a formation producing 96% oil. Relative spread of that band:
        # (0.05 - 0.04) / 0.045 = 0.222222...
        self.assertAlmostEqual(BUCKLES_SPREAD_TOLERANCE, 0.01 / 0.045, places=12)

    def test_constant_bvw_is_at_irreducible(self):
        # phi x Sw = 0.042, 0.045, 0.048. Mean 0.045, spread 0.006,
        # relative 0.006/0.045 = 0.13333, inside the 0.22222 tolerance.
        out = bulk_volume_water([
            {"depth_ft": 5000.0, "phi": 0.10, "sw": 0.42},
            {"depth_ft": 5010.0, "phi": 0.15, "sw": 0.30},
            {"depth_ft": 5020.0, "phi": 0.20, "sw": 0.24},
        ])
        self.assertEqual([round(q.value, 6) for q in out.bvw],
                         [0.042, 0.045, 0.048])
        self.assertAlmostEqual(out.mean.value, 0.045, places=12)
        self.assertAlmostEqual(out.spread.assumptions["relative_spread"],
                               0.006 / 0.045, places=12)
        self.assertIs(out.at_irreducible, True)
        self.assertIn("water free", out.verdict)

    def test_varying_bvw_is_not_at_irreducible(self):
        # 0.040, 0.120, 0.125. Mean 0.095, spread 0.085, relative 0.894737.
        out = bulk_volume_water([
            {"phi": 0.10, "sw": 0.40},
            {"phi": 0.20, "sw": 0.60},
            {"phi": 0.25, "sw": 0.50},
        ])
        self.assertAlmostEqual(out.mean.value, 0.095, places=12)
        self.assertAlmostEqual(out.spread.assumptions["relative_spread"],
                               0.085 / 0.095, places=12)
        self.assertIs(out.at_irreducible, False)
        self.assertIn("not at irreducible", out.verdict)

    def test_one_depth_gives_no_verdict(self):
        out = bulk_volume_water([{"phi": 0.10, "sw": 0.40}])
        self.assertIsNone(out.at_irreducible)
        self.assertIsInstance(out.spread, Refusal)

    def test_tolerance_is_declared_provisional(self):
        out = bulk_volume_water([{"phi": 0.1, "sw": 0.4}, {"phi": 0.2, "sw": 0.2}])
        self.assertTrue(any("PROVISIONAL" in f for f in out.flags))

    def test_table_7_1_band_mismatch_is_flagged(self):
        # Mean BVW 0.045 against the "coarse" band 0.02 to 0.025.
        out = bulk_volume_water([{"phi": 0.10, "sw": 0.42},
                                 {"phi": 0.20, "sw": 0.24}],
                                rock_class="coarse")
        self.assertTrue(any("Table 7.1" in f for f in out.flags))

    def test_missing_saturation_refuses(self):
        out = bulk_volume_water([{"phi": 0.10}])
        self.assertIsInstance(out, Refusal)


class MovableHydrocarbonTests(unittest.TestCase):
    """Eq. 7.4 by both routes, with Eqs. 10.6 and 10.7."""

    def test_saturation_route(self):
        # MHI = 0.35/0.70 = 0.5; MOS = 0.70 - 0.35 = 0.35; ROS = 1 - 0.70 = 0.30.
        out = movable_hydrocarbon_index(sw=0.35, sxo=0.70, lithology="sandstone")
        self.assertAlmostEqual(out.mhi.value, 0.5, places=12)
        self.assertAlmostEqual(out.mos.value, 0.35, places=12)
        self.assertAlmostEqual(out.ros.value, 0.30, places=12)
        # asquith#43: below 0.7 for a sandstone, moveable hydrocarbons indicated.
        self.assertIn("moveable hydrocarbons are indicated", out.verdict)

    def test_ratio_route_matches_the_equation(self):
        # (Rxo/Rt)/(Rmf/Rw) = (20/10)/(0.5/0.05) = 2/10 = 0.2.
        # Eq. 7.4:  MHI = 0.2^0.5   = 0.4472135955
        # Eq. 7.7:  Sw  = 0.2^0.625 = 0.3657139...
        # Eq. 7.5:  Sxo = Sw^(1/5)  = 0.2^0.125 = 0.8177654...
        out = movable_hydrocarbon_index(rxo=20.0, rt=10.0, rmf=0.5, rw=0.05)
        self.assertAlmostEqual(out.mhi.value, 0.2 ** 0.5, places=12)
        self.assertAlmostEqual(out.sw.value, 0.2 ** 0.625, places=12)
        self.assertAlmostEqual(out.sxo.value, 0.2 ** 0.125, places=12)
        # MOS = Sxo - Sw, ROS = 1 - Sxo, from those two.
        self.assertAlmostEqual(out.mos.value, 0.2 ** 0.125 - 0.2 ** 0.625, places=12)
        self.assertAlmostEqual(out.ros.value, 1.0 - 0.2 ** 0.125, places=12)

    def test_the_two_routes_reconcile(self):
        """Sw/Sxo from Eqs. 7.7 and 7.5 must be the Eq. 7.4 MHI exactly.

        R^0.625 / R^0.125 = R^0.5, so this is an identity the source's three
        equations satisfy. If it ever fails, one of the exponents has drifted.
        """
        out = movable_hydrocarbon_index(rxo=20.0, rt=10.0, rmf=0.5, rw=0.05)
        self.assertAlmostEqual(out.sw.value / out.sxo.value, out.mhi.value, places=12)

    def test_mhi_above_one_says_nothing_moved(self):
        out = movable_hydrocarbon_index(sw=0.80, sxo=0.60)
        self.assertIn("were not moved", out.verdict)

    def test_sxo_above_one_refuses_mos_and_ros(self):
        out = movable_hydrocarbon_index(sw=0.5, sxo=1.4)
        self.assertIsInstance(out.mos, Refusal)
        self.assertIsInstance(out.ros, Refusal)
        self.assertIn("of no value", out.mos.reason)

    def test_carbonate_uses_the_carbonate_cutoff(self):
        # MHI 0.65: below the 0.7 sandstone cutoff, above the 0.6 carbonate one.
        out = movable_hydrocarbon_index(sw=0.65, sxo=1.0, lithology="limestone")
        self.assertIn("supports neither verdict", out.verdict)
        sand = movable_hydrocarbon_index(sw=0.65, sxo=1.0, lithology="sandstone")
        self.assertIn("moveable hydrocarbons are indicated", sand.verdict)

    def test_no_route_refuses(self):
        self.assertIsInstance(movable_hydrocarbon_index(sw=0.4), Refusal)


class RwaTests(unittest.TestCase):
    """Eqs. 7.16 and 7.17 with the source's a = 1.0, m = 2.0, n = 2."""

    ZONES = [
        {"name": "A", "rt": 10.0, "phi": 0.20},    # Rwa = 10 x 0.04 = 0.40
        {"name": "B", "rt": 40.0, "phi": 0.20},    # Rwa = 40 x 0.04 = 1.60
        {"name": "C", "rt": 400.0, "phi": 0.05},   # Rwa = 400 x 0.0025 = 1.00
    ]

    def test_rwa_per_zone(self):
        out = rwa_method(self.ZONES)
        self.assertEqual([round(q.value, 10) for q in out.rwa], [0.40, 1.60, 1.00])

    def test_minimum_rwa_is_the_rw_estimate(self):
        out = rwa_method(self.ZONES)
        self.assertAlmostEqual(out.rw_estimate.value, 0.40, places=12)
        self.assertEqual(out.wet_zone, "A")

    def test_saturations_from_the_ratio(self):
        # Eq. 7.17: Sw = sqrt(Rwa_min / Rwa_zone).
        # A: sqrt(0.40/0.40) = 1.0
        # B: sqrt(0.40/1.60) = sqrt(0.25) = 0.5
        # C: sqrt(0.40/1.00) = 0.632455532...
        out = rwa_method(self.ZONES)
        self.assertAlmostEqual(out.sw[0].value, 1.0, places=12)
        self.assertAlmostEqual(out.sw[1].value, 0.5, places=12)
        self.assertAlmostEqual(out.sw[2].value, 0.4 ** 0.5, places=12)

    def test_low_porosity_zone_is_flagged(self):
        out = rwa_method(self.ZONES)
        self.assertTrue(any("low-porosity" in f for f in out.flags))
        self.assertTrue(any("lower than the actual Rw" in f for f in out.rwa[2].flags))

    def test_one_zone_gives_no_rw(self):
        out = rwa_method([{"rt": 10.0, "phi": 0.20}])
        self.assertIsInstance(out.rw_estimate, Refusal)
        self.assertEqual(out.sw, ())

    def test_same_rw_assumption_is_recorded(self):
        out = rwa_method(self.ZONES)
        self.assertIn("assumed to be the same", out.assumptions["same_Rw_assumed"])


class MNPlotTests(unittest.TestCase):
    """Eqs. 4.9 and 4.10, checked against Asquith's own Table 4.16.

    Table 4.16 lists M and N for the Fusselman example. Two rows are used here.
    They are the author's numbers, computed from the equations before this module
    existed, which makes them a genuinely independent oracle.
    """

    def test_table_4_16_row_at_11522(self):
        # DT 47, RHOB 2.75, NPHI 0.090. Table 4.16: M = 0.811, N = 0.520.
        # M = (189 - 47) / (2.75 - 1.0) x 0.01 = 142/1.75 x 0.01 = 0.8114285714
        # N = (1.0 - 0.090) / (2.75 - 1.0)      = 0.91/1.75      = 0.52
        out = mn_plot(dt=47.0, rho_b=2.75, nphi=0.090)
        self.assertAlmostEqual(out.m.value, 0.8114285714285714, places=12)
        self.assertAlmostEqual(out.n.value, 0.52, places=12)
        self.assertEqual(round(out.m.value, 3), 0.811)
        self.assertEqual(round(out.n.value, 3), 0.520)

    def test_table_4_16_row_at_11593(self):
        # DT 50, RHOB 2.70, NPHI 0.000. Table 4.16: M = 0.818, N = 0.588.
        # M = 139/1.70 x 0.01 = 0.8176470588
        # N = 1.0/1.70        = 0.5882352941
        out = mn_plot(dt=50.0, rho_b=2.70, nphi=0.0)
        self.assertAlmostEqual(out.m.value, 0.8176470588235294, places=12)
        self.assertAlmostEqual(out.n.value, 0.5882352941176471, places=12)
        self.assertEqual(round(out.m.value, 3), 0.818)
        self.assertEqual(round(out.n.value, 3), 0.588)

    def test_metric_scaling(self):
        # Same row, metric constant 0.003 instead of 0.01: 142/1.75 x 0.003.
        out = mn_plot(dt=47.0, rho_b=2.75, nphi=0.090, metric=True)
        self.assertAlmostEqual(out.m.value, 142.0 / 1.75 * 0.003, places=12)

    def test_lithology_is_always_refused(self):
        out = mn_plot(dt=47.0, rho_b=2.75, nphi=0.090)
        self.assertIsInstance(out.lithology, Refusal)
        self.assertIn("image", out.lithology.reason)
        self.assertTrue(any("mid_plot" in n for n in out.lithology.needed))

    def test_zero_denominator_raises(self):
        with self.assertRaises(ValueError):
            mn_plot(dt=47.0, rho_b=1.0, nphi=0.1)


class MidPlotTests(unittest.TestCase):
    """Eqs. 4.11 to 4.13, against the published matrix points."""

    def test_pure_limestone_lands_on_the_limestone_point(self):
        # At zero crossplot porosity Eqs. 4.11 and 4.12 return the log readings
        # themselves, so a bulk density of Table 4.2's limestone rho_ma and a
        # transit time of Table 4.1's limestone Wyllie Dt_ma must rank limestone
        # first at distance zero.
        out = mid_plot(rho_b=2.710, phi_nd=0.0, dt=47.6, phi_ns=0.0)
        self.assertAlmostEqual(out.rho_maa.value, 2.710, places=12)
        self.assertAlmostEqual(out.dt_maa.value, 47.6, places=12)
        self.assertEqual(out.candidates[0][0], "limestone")
        self.assertAlmostEqual(out.candidates[0][1], 0.0, places=12)

    def test_apparent_matrix_values(self):
        # rho_maa = (2.50 - 0.10 x 1.0) / (1 - 0.10) = 2.40/0.90 = 2.666666...
        # Dt_maa  = (70 - 0.10 x 189)  / (1 - 0.10) = 51.1/0.90 = 56.777777...
        out = mid_plot(rho_b=2.50, phi_nd=0.10, dt=70.0, phi_ns=0.10)
        self.assertAlmostEqual(out.rho_maa.value, 2.40 / 0.90, places=12)
        self.assertAlmostEqual(out.dt_maa.value, 51.1 / 0.90, places=12)
        # 2.667 g/cm3 and 56.8 usec/ft sit nearest Table 4.2's sandstone
        # (2.644 g/cm3) and Table 4.1's sandstone Wyllie point (55.5 usec/ft):
        # closer on BOTH axes than any other published matrix, so the ranking
        # does not depend on the house-rule distance.
        self.assertEqual(out.candidates[0][0], "sandstone")

    def test_u_maa(self):
        # U_maa = (Pe x rho_b - phi_ND x U_fl) / (1 - phi_ND)
        #       = (5.08 x 2.71 - 0) / 1 = 13.7668
        out = mid_plot(rho_b=2.71, phi_nd=0.0, pe=5.08)
        self.assertAlmostEqual(out.u_maa.value, 13.7668, places=12)

    def test_missing_sonic_refuses_only_that_leg(self):
        out = mid_plot(rho_b=2.71, phi_nd=0.0)
        self.assertIsInstance(out.rho_maa, Quantity)
        self.assertIsInstance(out.dt_maa, Refusal)
        self.assertIsInstance(out.u_maa, Refusal)
        self.assertEqual(out.candidates, ())

    def test_ranking_is_declared_provisional(self):
        out = mid_plot(rho_b=2.710, phi_nd=0.0, dt=47.6, phi_ns=0.0)
        self.assertTrue(any("PROVISIONAL" in f for f in out.flags))


class UnsourcedToolTests(unittest.TestCase):
    """The two group P techniques this corpus does not carry."""

    def test_multimineral_solve_always_refuses(self):
        out = multimineral_solve({"rhob": 2.5, "nphi": 0.2, "dt": 60.0},
                                 ["quartz", "calcite", "dolomite"])
        self.assertIsInstance(out, Refusal)
        self.assertIn("response", out.reason)
        self.assertTrue(out.needed)
        self.assertIn("mid_plot", out.reason)

    def test_multimineral_solve_returns_no_number(self):
        self.assertIsNone(multimineral_solve().value)

    def test_thomas_stieber_always_refuses(self):
        out = thomas_stieber(phi_total=0.25, vshale=0.30)
        self.assertIsInstance(out, Refusal)
        self.assertIn("images", out.reason)
        self.assertTrue(any("Thomas and Stieber" in n for n in out.needed))

    def test_thomas_stieber_carries_the_sourced_model_mapping(self):
        """The refusal is useful: it names which model each distribution admits.

        That mapping is the one thing `shaly_sand_sw` cannot supply for itself,
        and jmest#1 states it outright.
        """
        out = thomas_stieber()
        self.assertIn("laminated clay models", out.reason)
        self.assertIn("dispersed clay", out.reason)
        self.assertIn("correlation_selector", out.reason)


class DispatchTests(unittest.TestCase):
    """Auto-discovery is the only thing registering these."""

    NAMES = ("bulk_volume_water", "movable_hydrocarbon_index", "rwa_method",
             "mn_plot", "mid_plot", "multimineral_solve", "thomas_stieber")

    def test_every_tool_is_registered(self):
        import dispatch
        table = dispatch.registry()
        for name in self.NAMES:
            self.assertIn(name, table, f"{name} is not in the registry")
            self.assertEqual(table[name][0], "tools.classic")

    def test_callable_through_dispatch(self):
        import dispatch
        out = dispatch.call("mn_plot", {"dt": 47.0, "rho_b": 2.75, "nphi": 0.090})
        self.assertAlmostEqual(out["m"]["value"], 0.8114285714285714, places=12)
        # `dispatch.plain` flattens with `asdict`, which converts nested
        # dataclasses before `plain` can stamp a "kind" on them, so a nested
        # refusal is recognised by its `reason` and its null `value`.
        self.assertIn("image", out["lithology"]["reason"])
        self.assertIsNone(out["lithology"].get("value"))

    def test_sequence_argument_survives_the_boundary(self):
        import dispatch
        out = dispatch.call("bulk_volume_water", {"samples": [
            {"phi": 0.10, "sw": 0.42}, {"phi": 0.20, "sw": 0.24}]})
        self.assertIs(out["at_irreducible"], True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
