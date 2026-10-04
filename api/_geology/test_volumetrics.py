"""Group M: volumetrics and uncertainty.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

Every expected value here is worked from the published equation, by hand or as an
independent transcription of it, never from running the tool. Two of them are
Ahmed's own printed answers, which is the strongest oracle available: Example 4-1
prints 4,276,998 STB and Example 13-2 prints 18.2 MMMscf, and neither number came
out of this code.

The four properties that matter most are the ones a plausible-looking wrong
answer would pass: `volumetrics` must refuse without an area rather than assume
one, `recovery_factor` must never collapse its band to a point, the Monte Carlo
must be byte-identical on a repeated seed and different on a new one, and the
whole group must be reachable through `dispatch.registry()`, since auto-discovery
is the only thing that registers it.
"""
from __future__ import annotations

import unittest

import dispatch
from tools.result import Quantity, Range, Refusal
from tools.volumetrics import (
    BBL_PER_ACRE_FT, CF_PER_ACRE_FT, RECOVERY_RANGES, archie_sensitivity,
    hcpv_thickness, propagate_uncertainty, recovery_factor, volumetrics,
    volumetrics_probabilistic,
)

RW_SOURCE = "measured water analysis, Morrow sand"


class HcpvThickness(unittest.TestCase):
    def test_hand_worked_interval(self):
        """phi (1 - S_w) h summed by hand over three samples.

        0.14*4*0.65 = 0.364;  0.10*3*0.45 = 0.135;  0.18*5*0.70 = 0.630
        total 1.129 ft.
        """
        result = hcpv_thickness([0.14, 0.10, 0.18], [0.35, 0.55, 0.30], [4.0, 3.0, 5.0])
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.value, 1.129, places=10)
        self.assertEqual(result.unit, "ft")

    def test_reconciles_with_the_phi_h_weighted_average(self):
        """Ahmed Eq. 4-17 is the independent derivation of the same quantity.

        phi_h = 0.56 + 0.30 + 0.90 = 1.76
        sum(phi h S_w) = 0.196 + 0.165 + 0.270 = 0.631
        S_w_avg = 0.631/1.76 = 0.358522727...
        1.76 * (1 - 0.358522727) = 1.129, which is the integral above.
        """
        result = hcpv_thickness([0.14, 0.10, 0.18], [0.35, 0.55, 0.30], [4.0, 3.0, 5.0])
        self.assertAlmostEqual(result.inputs["phi_h_ft"], 1.76, places=10)
        self.assertAlmostEqual(result.inputs["sw_average"], 0.631 / 1.76, places=12)
        self.assertAlmostEqual(
            result.inputs["phi_h_ft"] * (1.0 - result.inputs["sw_average"]),
            result.value, places=12)

    def test_broadcasts_a_scalar_thickness(self):
        # 0.20 * 2 * 0.60 + 0.10 * 2 * 0.60 = 0.24 + 0.12 = 0.36
        result = hcpv_thickness([0.20, 0.10], [0.40, 0.40], 2.0)
        self.assertAlmostEqual(result.value, 0.36, places=12)

    def test_rejects_a_percentage_porosity(self):
        with self.assertRaises(ValueError):
            hcpv_thickness([14.0], [0.35], [4.0])


class Volumetrics(unittest.TestCase):
    def test_refuses_without_an_area(self):
        """The refusal this tool exists for."""
        result = volumetrics("oil", net_pay_ft=12.0, phi=0.14, sw=0.35, b_i=1.25)
        self.assertIsInstance(result, Refusal)
        self.assertIn("area", result.reason.lower())
        self.assertIn("area_acres", " ".join(result.needed))

    def test_hand_worked_stoiip(self):
        """N = 7758 A h phi (1 - S_w) / B_oi, worked by hand.

        7758 * 40      = 310,320
             * 12      = 3,723,840
             * 0.14    = 521,337.6
             * 0.65    = 338,869.44
             / 1.25    = 271,095.552 STB
        """
        result = volumetrics("oil", 40.0, net_pay_ft=12.0, phi=0.14, sw=0.35, b_i=1.25)
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.value, 271095.552, places=6)
        self.assertEqual(result.unit, "STB")

    def test_reproduces_ahmed_example_4_1(self):
        """Ahmed #42 Example 4-1 prints 4,276,998 STB for 640 acres of 10 ft."""
        result = volumetrics("oil", 640.0, net_pay_ft=10.0, phi=0.15, sw=0.25, b_i=1.306)
        self.assertAlmostEqual(result.value, 4276998.0, delta=1.0)

    def test_reproduces_ahmed_example_13_2(self):
        """Ahmed #171 Example 13-2 prints G = 18.2 MMMscf by Eq. 13-3."""
        result = volumetrics("gas", 1060.0, net_pay_ft=54.0, phi=0.13, sw=0.52,
                             b_i=0.00853)
        self.assertEqual(result.unit, "scf")
        self.assertAlmostEqual(result.value / 1e9, 18.2, delta=0.05)

    def test_oil_and_gas_do_not_share_a_coefficient(self):
        oil = volumetrics("oil", 40.0, net_pay_ft=10.0, phi=0.15, sw=0.30, b_i=1.0)
        gas = volumetrics("gas", 40.0, net_pay_ft=10.0, phi=0.15, sw=0.30, b_i=1.0)
        self.assertAlmostEqual(gas.value / oil.value, CF_PER_ACRE_FT / BBL_PER_ACRE_FT,
                               places=9)

    def test_accepts_an_integrated_hcpv_instead(self):
        """hcpv_thickness feeds this directly: 1.129 ft of hydrocarbon column."""
        hcpv = hcpv_thickness([0.14, 0.10, 0.18], [0.35, 0.55, 0.30], [4.0, 3.0, 5.0])
        result = volumetrics("oil", 40.0, hcpv_ft=hcpv.value, b_i=1.25)
        self.assertAlmostEqual(result.value, 7758.0 * 40.0 * 1.129 / 1.25, places=6)

    def test_will_not_take_both_forms(self):
        with self.assertRaises(ValueError):
            volumetrics("oil", 40.0, net_pay_ft=12.0, phi=0.14, sw=0.35, b_i=1.25,
                        hcpv_ft=1.1)

    def test_refuses_without_a_formation_volume_factor(self):
        result = volumetrics("oil", 40.0, net_pay_ft=12.0, phi=0.14, sw=0.35)
        self.assertIsInstance(result, Refusal)
        self.assertIn("b_i", result.needed)


class RecoveryFactor(unittest.TestCase):
    def test_returns_a_range_never_a_point(self):
        result = recovery_factor("water_drive")
        self.assertIsInstance(result, Range)
        self.assertNotIsInstance(result, Quantity)
        self.assertEqual((result.low, result.high), (0.35, 0.75))
        self.assertGreater(result.spread, 0.0)

    def test_every_published_mechanism_is_a_band(self):
        for name in RECOVERY_RANGES:
            with self.subTest(name):
                result = recovery_factor(name)
                self.assertIsInstance(result, Range)
                self.assertGreater(result.spread, 0.0)

    def test_scales_an_in_place_volume(self):
        """35% and 75% of 1,000,000 STB."""
        result = recovery_factor("water_drive", 1_000_000.0)
        self.assertAlmostEqual(result.low, 350_000.0, places=6)
        self.assertAlmostEqual(result.high, 750_000.0, places=6)
        self.assertEqual(result.unit, "STB")

    def test_depletion_drive_reads_as_solution_gas(self):
        """Ahmed #149 prints 5 to 30% for depletion drive, #177's solution-gas row."""
        result = recovery_factor("depletion drive")
        self.assertEqual((result.low, result.high), (0.05, 0.30))

    def test_gravity_drainage_records_its_missing_floor(self):
        result = recovery_factor("gravity_drainage")
        self.assertEqual(result.high, 0.80)
        self.assertTrue(any("no published lower bound" in flag for flag in result.flags))

    def test_refuses_an_unpublished_mechanism(self):
        result = recovery_factor("steam_flood")
        self.assertIsInstance(result, Refusal)


class Probabilistic(unittest.TestCase):
    ARGS = dict(area_acres=(30.0, 60.0), net_pay_ft=(8.0, 16.0), phi=(0.10, 0.18),
                sw=(0.25, 0.45), b_i=(1.15, 1.35), samples=2000)

    def test_the_same_seed_gives_the_identical_result(self):
        first = volumetrics_probabilistic("oil", 4242, **self.ARGS)
        second = volumetrics_probabilistic("oil", 4242, **self.ARGS)
        self.assertEqual(first.members, second.members)
        self.assertEqual((first.low, first.high), (second.low, second.high))

    def test_a_different_seed_gives_a_different_result(self):
        first = volumetrics_probabilistic("oil", 4242, **self.ARGS)
        other = volumetrics_probabilistic("oil", 99, **self.ARGS)
        self.assertNotEqual(first.members["P50"], other.members["P50"])

    def test_leaves_the_module_level_generator_alone(self):
        """`random.Random(seed)`, not `random.seed(seed)`.

        The distinction is invisible in this tool's own output and very visible
        in everything else's: a tool that reseeded the global generator would
        silently move the next answer of any other tool drawing from it. So the
        assertion is on the global stream, not on this result.
        """
        import random
        random.seed(31337)
        untouched = [random.random() for _ in range(3)]
        random.seed(31337)
        volumetrics_probabilistic("oil", 4242, **self.ARGS)
        self.assertEqual([random.random() for _ in range(3)], untouched)

    def test_reports_its_seed_and_sample_count(self):
        result = volumetrics_probabilistic("oil", 7, **self.ARGS)
        self.assertEqual(result.assumptions["seed"], 7)
        self.assertEqual(result.assumptions["samples"], 2000)

    def test_p90_is_the_low_case(self):
        result = volumetrics_probabilistic("oil", 7, **self.ARGS)
        self.assertLess(result.members["P90"], result.members["P50"])
        self.assertLess(result.members["P50"], result.members["P10"])
        self.assertEqual(result.low, result.members["P90"])
        self.assertEqual(result.high, result.members["P10"])

    def test_the_band_brackets_the_deterministic_mid_case(self):
        """Independent check: the deterministic answer at the interval midpoints
        must sit inside P90 to P10.

        7758 * 45 * 12 * 0.14 * (1 - 0.35) / 1.25
        """
        mid = 7758.0 * 45.0 * 12.0 * 0.14 * 0.65 / 1.25
        result = volumetrics_probabilistic("oil", 4242, **self.ARGS)
        self.assertLess(result.low, mid)
        self.assertGreater(result.high, mid)

    def test_refuses_without_an_area(self):
        args = dict(self.ARGS)
        args.pop("area_acres")
        self.assertIsInstance(volumetrics_probabilistic("oil", 1, **args), Refusal)

    def test_requires_an_integer_seed(self):
        with self.assertRaises(ValueError):
            volumetrics_probabilistic("oil", "4242", **self.ARGS)


class ArchieSensitivity(unittest.TestCase):
    """Rt = 10, phi = 0.20, Rw = 0.05, a = 1, m = 2.

    (a Rw)/(Rt phi^m) = 0.05 / (10 * 0.04) = 0.125, so S_w = 0.125^(1/n).
    """

    BASE = dict(a_candidates=[1.0], m_candidates=[2.0])

    def test_sweeps_n_and_reports_the_band(self):
        result = archie_sensitivity(10.0, 0.20, 0.05, RW_SOURCE,
                                    n_candidates=[1.8, 2.0, 2.2], **self.BASE)
        self.assertIsInstance(result, Range)
        self.assertAlmostEqual(result.low, 0.125 ** (1.0 / 1.8), places=10)
        self.assertAlmostEqual(result.high, 0.125 ** (1.0 / 2.2), places=10)
        self.assertAlmostEqual(result.members["a=1,m=2,n=2"], 0.125 ** 0.5, places=10)

    def test_refuses_a_single_combination(self):
        result = archie_sensitivity(10.0, 0.20, 0.05, RW_SOURCE,
                                    n_candidates=[2.0], **self.BASE)
        self.assertIsInstance(result, Refusal)
        self.assertIn("point estimate", result.reason)

    def test_defaults_no_axis(self):
        result = archie_sensitivity(10.0, 0.20, 0.05, RW_SOURCE,
                                    a_candidates=[1.0], m_candidates=[2.0])
        self.assertIsInstance(result, Refusal)
        self.assertIn("n_candidates", result.reason)

    def test_carries_the_rw_provenance_gate(self):
        """archie_sw refuses without Rw provenance, and the sweep inherits it
        rather than working around it."""
        result = archie_sensitivity(10.0, 0.20, 0.05, None, n_candidates=[1.8, 2.2],
                                    **self.BASE)
        self.assertIsInstance(result, Refusal)
        self.assertIn("provenance", result.reason)


class PropagateUncertainty(unittest.TestCase):
    """Three samples, 2 ft each, phi cutoff 0.10 and S_w cutoff 0.55.

    S_w = sqrt(Rw / (Rt phi^2)) at a = 1, m = n = 2.

      sample 1: Rt = 12, phi 0.10 or 0.12
        phi 0.10, Rw 0.04 -> 0.04/0.12   = 0.333333, S_w = 0.577350  wet
        phi 0.10, Rw 0.06 -> 0.06/0.12   = 0.500000, S_w = 0.707107  wet
        phi 0.12, Rw 0.04 -> 0.04/0.1728 = 0.231481, S_w = 0.481125  PAY
        phi 0.12, Rw 0.06 -> 0.06/0.1728 = 0.347222, S_w = 0.589256  wet
      sample 2: Rt = 30, phi 0.14 or 0.16, S_w between 0.228 and 0.319, PAY always
      sample 3: phi 0.08 or 0.09, below the 0.10 porosity cutoff, never pay

    So three corners give 2 ft of net pay and one gives 4 ft.
    """

    ARGS = dict(thickness_ft=2.0, phi_low=[0.10, 0.14, 0.08],
                phi_high=[0.12, 0.16, 0.09], rt=[12.0, 30.0, 5.0],
                rw=(0.04, 0.06), rw_source=RW_SOURCE,
                phi_cutoff=0.10, sw_cutoff=0.55)

    def test_returns_the_net_pay_interval(self):
        result = propagate_uncertainty(**self.ARGS)
        self.assertIsInstance(result, Range)
        self.assertAlmostEqual(result.low, 2.0, places=10)
        self.assertAlmostEqual(result.high, 4.0, places=10)
        self.assertEqual(result.unit, "ft")

    def test_enumerates_every_corner(self):
        result = propagate_uncertainty(**self.ARGS)
        self.assertEqual(len(result.members), 4)
        self.assertAlmostEqual(result.members["phi=high,rw=0.04,a=1,m=2,n=2"], 4.0)
        self.assertAlmostEqual(result.members["phi=low,rw=0.06,a=1,m=2,n=2"], 2.0)

    def test_a_pinned_call_costs_one_corner(self):
        args = dict(self.ARGS, rw=0.04, phi_high=[0.10, 0.14, 0.08])
        result = propagate_uncertainty(**args)
        self.assertEqual(len(result.members), 1)
        self.assertEqual(result.low, result.high)

    def test_the_porosity_cutoff_excludes_the_third_sample(self):
        result = propagate_uncertainty(**self.ARGS)
        self.assertAlmostEqual(result.inputs["gross_ft"], 6.0, places=10)
        self.assertLessEqual(result.high, 4.0)

    def test_carries_an_hcpv_interval_alongside(self):
        result = propagate_uncertainty(**self.ARGS)
        self.assertLess(result.assumptions["hcpv_ft_low"],
                        result.assumptions["hcpv_ft_high"])

    def test_refuses_without_rw_provenance(self):
        args = dict(self.ARGS, rw_source=None)
        self.assertIsInstance(propagate_uncertainty(**args), Refusal)

    def test_a_sample_reading_above_full_water_is_counted_as_not_pay(self):
        """A fourth sample at Rt = 0.1 and phi = 0.15 gives

            S_w = sqrt(0.04 / (0.1 * 0.0225)) = sqrt(17.78) = 4.22

        which archie_sw refuses rather than clipping. Above unity means wet, so
        the sample is excluded from net pay and the count is flagged. It is NOT
        allowed to sink the whole corner.
        """
        args = dict(self.ARGS, phi_low=[0.10, 0.14, 0.08, 0.15],
                    phi_high=[0.12, 0.16, 0.09, 0.15], rt=[12.0, 30.0, 5.0, 0.1])
        result = propagate_uncertainty(**args)
        self.assertIsInstance(result, Range)
        self.assertAlmostEqual(result.high, 4.0, places=10)   # unchanged by the wet bed
        self.assertAlmostEqual(result.inputs["gross_ft"], 8.0, places=10)
        self.assertTrue(any("above 1.0" in flag for flag in result.flags))


class Dispatch(unittest.TestCase):
    NAMES = ("hcpv_thickness", "volumetrics", "recovery_factor",
             "volumetrics_probabilistic", "archie_sensitivity", "propagate_uncertainty")

    def test_every_tool_is_discovered(self):
        table = dispatch.registry()
        for name in self.NAMES:
            with self.subTest(name):
                self.assertIn(name, table)
                self.assertEqual(table[name][0], "tools.volumetrics")

    def test_a_refusal_crosses_the_boundary_as_a_value(self):
        out = dispatch.call("volumetrics", {"fluid": "oil", "net_pay_ft": 12.0,
                                            "phi": 0.14, "sw": 0.35, "b_i": 1.25})
        self.assertEqual(out["kind"], "Refusal")
        self.assertIn("area", out["reason"].lower())

    def test_an_answer_crosses_the_boundary_intact(self):
        out = dispatch.call("volumetrics", {"fluid": "oil", "area_acres": 40.0,
                                            "net_pay_ft": 12.0, "phi": 0.14,
                                            "sw": 0.35, "b_i": 1.25})
        self.assertEqual(out["kind"], "Quantity")
        self.assertAlmostEqual(out["value"], 271095.552, places=6)
        self.assertTrue(out["source"])
        self.assertTrue(out["method"])

    def test_the_seeded_sampler_is_reproducible_through_dispatch(self):
        args = {"fluid": "oil", "seed": 11, "area_acres": [30.0, 60.0],
                "net_pay_ft": [8.0, 16.0], "phi": [0.10, 0.18], "sw": [0.25, 0.45],
                "b_i": [1.15, 1.35], "samples": 500}
        self.assertEqual(dispatch.call("volumetrics_probabilistic", args),
                         dispatch.call("volumetrics_probabilistic", args))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
