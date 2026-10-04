"""Group R: production and well test.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

Every expected number below is hand-computed from the published equation and
written as a literal. Where Ahmed prints the answer himself the test asserts
against HIS number, not against this code's: Example 7-2 ((Q_o)max = 1067.1),
Example 7-3 (Q_o = 709 at p_wf = 1500), Example 7-4 (J = 0.5 from a test point
below the bubble point) and Example 6-25 (k = 12.8 md, s = 8.6).

The synthetic Horner line is built from p_ws = p* - m log10((t_p+dt)/dt) with
m and p* chosen by hand, so recovering m is recovering something typed in, and
kh, skin and radius of investigation are then hand-computed from Eqs. 6-178,
6-179 and Earlougher 8.7 against that m.
"""
from __future__ import annotations

import math
import unittest

import dispatch
from tools import welltest
from tools.result import Quantity, Refusal


def rate_at(result: Quantity, p_wf: float) -> float:
    """The IPR rate at a flowing pressure that is on the returned grid."""
    for point in result.inputs["curve"]:
        if abs(point.inputs["p_wf_psig"] - p_wf) < 1e-9:
            return point.value
    raise AssertionError(f"no curve point at p_wf = {p_wf}")


class VogelIPR(unittest.TestCase):
    def test_saturated_reproduces_ahmed_example_7_2(self):
        """p_r = p_b = 2500 psig, 350 STB/day at p_wf = 2000 psig.

        By hand from Eq. 7-9: 1 - 0.2(0.8) - 0.8(0.8)^2 = 1 - 0.16 - 0.512 =
        0.328, so (Q_o)max = 350/0.328 = 1067.07 STB/day. Ahmed prints 1067.1.
        """
        out = welltest.vogel_ipr(p_r_psig=2500.0, p_b_psig=2500.0,
                                 test_q_stb_d=350.0, test_p_wf_psig=2000.0)
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, 1067.07, places=2)
        self.assertEqual(out.inputs["regime"], "saturated")

    def test_saturated_curve_returns_the_reference_point(self):
        # The curve must pass through the stabilized test point it was built
        # from: 350 STB/day at 2000 psig, which is grid step 2 of 10.
        out = welltest.vogel_ipr(2500.0, 2500.0, 350.0, 2000.0)
        self.assertAlmostEqual(rate_at(out, 2000.0), 350.0, places=6)
        # And at p_wf = 1250, x = 0.5: 1 - 0.1 - 0.2 = 0.7, so
        # Q = 0.7 x 1067.0731707 = 746.95 STB/day.
        self.assertAlmostEqual(rate_at(out, 1250.0), 746.95, places=2)
        # AOF is Eq. 7-9 at p_wf = 0, which is (Q_o)max itself.
        self.assertAlmostEqual(rate_at(out, 0.0), out.value, places=6)

    def test_undersaturated_case_1_reproduces_ahmed_example_7_3(self):
        """p_r = 3000, p_b = 2130, 250 STB/day at p_wf = 2500 psig.

        Eq. 7-1: J = 250/(3000-2500) = 0.5 STB/day/psi.
        Eq. 7-10: Q_ob = 0.5(3000-2130) = 435 STB/day.
        Eq. 7-11 at p_wf = 1500, x = 1500/2130 = 0.70422535:
          1 - 0.14084507 - 0.8(0.49593336) = 0.46240824
          Q = 435 + (0.5 x 2130/1.8)(0.46240824) = 435 + 273.5915 = 708.59
        Ahmed's table prints 709. AOF = 435 + 591.6667 = 1026.67 (he prints 1027).
        """
        out = welltest.vogel_ipr(3000.0, 2130.0, 250.0, 2500.0)
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.inputs["j_stb_d_psi"], 0.5, places=9)
        self.assertAlmostEqual(out.inputs["q_ob_stb_d"], 435.0, places=6)
        self.assertAlmostEqual(out.value, 1026.67, places=2)
        self.assertAlmostEqual(rate_at(out, 1500.0), 708.59, places=2)
        # Above the bubble point the IPR is the straight line Q = J(p_r - p_wf).
        self.assertAlmostEqual(rate_at(out, 2700.0), 150.0, places=6)

    def test_undersaturated_case_2_reproduces_ahmed_example_7_4(self):
        """The same well retested at p_wf = 1700 psig, below p_b, 630.7 STB/day.

        Eq. 7-12 denominator, x = 1700/2130 = 0.79812207:
          (3000-2130) + (2130/1.8)[1 - 0.15962441 - 0.8(0.63699884)]
          = 870 + 1183.3333(0.33077652) = 870 + 391.4189 = 1261.4189
        J = 630.7/1261.4189 = 0.49999 STB/day/psi. Ahmed prints 0.5, and the
        recomputed IPR is his Example 7-3 table again.
        """
        out = welltest.vogel_ipr(3000.0, 2130.0, 630.7, 1700.0)
        self.assertAlmostEqual(out.inputs["j_stb_d_psi"], 0.5, places=4)
        self.assertIn("case-2", out.assumptions["case"])
        self.assertAlmostEqual(out.value, 1026.67, places=1)

    def test_refuses_without_a_bubble_point(self):
        out = welltest.vogel_ipr(3000.0, 0.0, 250.0, 2500.0)
        self.assertIsInstance(out, Refusal)
        self.assertIn("drawdown_estimate", " ".join(out.needed))

    def test_refuses_a_test_point_with_no_drawdown(self):
        out = welltest.vogel_ipr(2500.0, 2500.0, 350.0, 2500.0)
        self.assertIsInstance(out, Refusal)


class NodalAnalysis(unittest.TestCase):
    # Inflow p = 3000 - q, tubing p = 1000 + q/2, both straight by hand.
    # 3000 - q = 1000 + q/2  ->  2000 = 1.5 q  ->  q = 1333.333, p = 1666.667.
    INFLOW = [[0.0, 3000.0], [1000.0, 2000.0], [2000.0, 1000.0]]
    TUBING = [[0.0, 1000.0], [2000.0, 2000.0]]

    def test_finds_the_hand_placed_intersection(self):
        out = welltest.nodal_analysis(self.INFLOW, self.TUBING)
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, 4000.0 / 3.0, places=6)
        self.assertAlmostEqual(out.inputs["p_node"], 5000.0 / 3.0, places=6)
        self.assertEqual(out.inputs["n_intersections"], 1)

    def test_refuses_when_the_curves_do_not_cross(self):
        # Tubing everywhere above inflow: PetroWiki's System A.
        out = welltest.nodal_analysis(self.INFLOW, [[0.0, 3500.0], [2000.0, 4000.0]])
        self.assertIsInstance(out, Refusal)
        self.assertIn("not expected to produce", out.reason)

    def test_takes_a_vogel_ipr_result_as_its_inflow(self):
        """Ahmed Example 7-3 against a flat 1500 psig tubing curve.

        The IPR at 1500 psig is the hand-computed 708.59 STB/day, so that is
        where a constant 1500 psig outflow curve must cross it.
        """
        ipr = welltest.vogel_ipr(3000.0, 2130.0, 250.0, 2500.0)
        out = welltest.nodal_analysis(ipr, [[0.0, 1500.0], [2000.0, 1500.0]])
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, 708.59, places=2)
        self.assertAlmostEqual(out.inputs["p_node"], 1500.0, places=6)
        self.assertEqual(out.unit, "STB/day")

    def test_returns_the_stable_high_rate_intersection_of_two(self):
        # A hooked outflow curve crossing at q = 500 and again at q = 1500.
        # Inflow p = 2000 - q/2 (2000, 1750, 1500, 1250 at q = 0, 500, 1000, 1500).
        inflow = [[0.0, 2000.0], [500.0, 1750.0], [1000.0, 1500.0], [1500.0, 1250.0]]
        tubing = [[0.0, 1900.0], [500.0, 1750.0], [1000.0, 1400.0], [1500.0, 1250.0]]
        out = welltest.nodal_analysis(inflow, tubing)
        self.assertAlmostEqual(out.value, 1500.0, places=6)
        self.assertEqual(out.inputs["n_intersections"], 2)
        self.assertTrue(any("not a stable solution" in f for f in out.flags))

    def test_refuses_a_curve_that_is_not_a_curve(self):
        self.assertIsInstance(welltest.nodal_analysis([[100.0, 200.0]], self.TUBING),
                              Refusal)


class BuildupKhSkin(unittest.TestCase):
    """A Horner line typed in by hand: m = 50 psi/cycle, p* = 3000 psi, t_p = 100 hr.

    p_ws = 3000 - 50 log10((100+dt)/dt):
      dt =   1 hr, ratio 101,  log10 = 2.004321374 -> 2899.783931
      dt =  10 hr, ratio  11,  log10 = 1.041392685 -> 2947.930366
      dt = 100 hr, ratio   2,  log10 = 0.301029996 -> 2984.948500
    p_wf at shut-in is 2500 psi, so p_1hr = 3000 - 50 log10(101) = 2899.783931.

    With q = 500 STB/day, B_o = 1.2, mu = 1.0 cp, h = 50 ft:
      Eq. 6-178: kh = 162.6(500)(1.2)(1.0)/50 = 1951.2 md.ft, k = 39.024 md
      Eq. 6-179 with phi = 0.10, c_t = 1e-5, r_w = 0.5 ft:
        log10(39.024/(0.10 x 1.0 x 1e-5 x 0.25)) = log10(1.56096e8) = 8.193395
        s = 1.1513[(2899.783931-2500)/50 - 8.193395 + 3.23]
          = 1.1513[7.995679 - 8.193395 + 3.23] = 1.1513(3.032284) = 3.4911
      Earlougher 8.7 at t = 100 hr:
        r = 0.029 sqrt(39.024 x 100/(0.10 x 1.0 x 1e-5))
          = 0.029 sqrt(3.9024e9) = 0.029(62469.18) = 1811.6 ft
    """
    POINTS = [[0.0, 2500.0], [1.0, 2899.783931], [10.0, 2947.930366],
              [100.0, 2984.948500]]
    KWARGS = dict(t_p_hr=100.0, q_stb_d=500.0, b_o_rb_stb=1.2, mu_cp=1.0, h_ft=50.0,
                  phi=0.10, ct_psi=1e-5, rw_ft=0.5, delta_t_min_hr=1.0)

    def test_kh_skin_and_radius_off_the_hand_built_line(self):
        out = welltest.buildup_kh_skin(self.POINTS, **self.KWARGS)
        self.assertIsInstance(out, dict)
        self.assertAlmostEqual(out["kh_md_ft"].value, 1951.2, places=3)
        self.assertAlmostEqual(out["k_md"].value, 39.024, places=4)
        self.assertAlmostEqual(out["skin"].value, 3.4911, places=3)
        self.assertAlmostEqual(out["radius_of_investigation_ft"].value, 1811.6, places=1)
        # The slope it worked from is the slope that was typed in.
        self.assertAlmostEqual(out["kh_md_ft"].inputs["slope_m_psi_per_cycle"], 50.0,
                               places=5)

    def test_reproduces_ahmed_example_6_25(self):
        """m = 40 psi/cycle, t_p = 310 hr, p_1hr = 3266, p_wf = 2761.

        Ahmed's answers: k = 162.6(4900)(1.55)(0.20)/((40)(482)) = 12.8 md, and
        s = 1.1513[(3266-2761)/40 - log10(12.81/(0.09 x 0.20 x 22.6e-6 x 0.354^2))
        + 3.23] = 8.6. The line is constructed at that m and that p_1hr.
        """
        m, t_p, p_1hr = 40.0, 310.0, 3266.0
        p_star = p_1hr + m * math.log10(t_p + 1.0)
        points = [[0.0, 2761.0]] + [
            [dt, p_star - m * math.log10((t_p + dt) / dt)] for dt in (1.0, 10.0, 37.54)]
        out = welltest.buildup_kh_skin(
            points, t_p_hr=t_p, q_stb_d=4900.0, b_o_rb_stb=1.55, mu_cp=0.20, h_ft=482.0,
            phi=0.09, ct_psi=22.6e-6, rw_ft=0.354, delta_t_min_hr=1.0)
        self.assertAlmostEqual(out["k_md"].value, 12.8, places=1)
        self.assertAlmostEqual(out["skin"].value, 8.6, places=1)

    def test_skin_refuses_without_the_flowing_pressure(self):
        # Same line with the dt = 0 row dropped: kh survives, skin cannot.
        out = welltest.buildup_kh_skin(self.POINTS[1:], **self.KWARGS)
        self.assertAlmostEqual(out["kh_md_ft"].value, 1951.2, places=3)
        self.assertIsInstance(out["skin"], Refusal)
        self.assertIn("p_wf", out["skin"].reason)

    def test_passes_through_the_horner_fit_refusal(self):
        # No window and no storage screen: pressure.formation_pressure_estimate
        # refuses, and this tool must not compute a kh from an unfitted line.
        kwargs = dict(self.KWARGS)
        del kwargs["delta_t_min_hr"]
        self.assertIsInstance(welltest.buildup_kh_skin(self.POINTS, **kwargs), Refusal)


class WorXplot(unittest.TestCase):
    """Two points by hand: WOR 1.0 at 100,000 STB and 10.0 at 200,000 STB.

    log10(WOR) = 0 and 1, so the semilog line is
    log10(WOR) = -1 + 1e-5 N_p. At the limiting WOR of 100, log10 = 2 and
    N_p = (2 + 1)/1e-5 = 300,000 STB, leaving 100,000 STB.
    Area under WOR against N_p (Ahmed step 6) = (1+10)/2 x 100,000 = 550,000 bbl.
    """
    POINTS = [[100_000.0, 1.0], [200_000.0, 10.0]]

    def test_forecast_and_remaining_oil(self):
        out = welltest.wor_xplot(self.POINTS, wor_limit=100.0)
        self.assertAlmostEqual(out["np_at_limit_stb"].value, 300_000.0, places=3)
        self.assertAlmostEqual(out["remaining_oil_stb"].value, 100_000.0, places=3)
        self.assertAlmostEqual(out["cumulative_water_bbl"].value, 550_000.0, places=6)

    def test_refuses_to_extrapolate_a_falling_wor(self):
        out = welltest.wor_xplot([[100_000.0, 10.0], [200_000.0, 1.0]], wor_limit=100.0)
        self.assertIsInstance(out, Refusal)

    def test_refuses_a_zero_wor(self):
        self.assertIsInstance(welltest.wor_xplot([[1.0, 0.0], [2.0, 1.0]]), Refusal)

    def test_water_history_alone_when_no_limit_is_given(self):
        out = welltest.wor_xplot(self.POINTS)
        self.assertEqual(set(out), {"cumulative_water_bbl"})


class MaterialBalance(unittest.TestCase):
    """Two surveys placed exactly on F = N E_o with N = 10,000,000 STB.

    B_oi = 1.3 rb/STB, R_si = 600 scf/STB.
      p = 2000: B_o = 1.25, R_s = R_p = 500, B_g = 0.0015
        E_o = (1.25-1.30) + (600-500)(0.0015) = -0.05 + 0.15 = 0.10 rb/STB
        F   = 800,000(1.25 + 0) = 1,000,000 rb = 1e7 x 0.10
      p = 1500: B_o = 1.20, R_s = R_p = 400, B_g = 0.002
        E_o = (1.20-1.30) + (600-400)(0.002) = -0.10 + 0.40 = 0.30 rb/STB
        F   = 2,500,000(1.20) = 3,000,000 rb = 1e7 x 0.30
    """
    HISTORY = [
        {"p_psia": 2000.0, "np_stb": 800_000.0, "bo_rb_stb": 1.25, "rs_scf_stb": 500.0,
         "rp_scf_stb": 500.0, "bg_rb_scf": 0.0015},
        {"p_psia": 1500.0, "np_stb": 2_500_000.0, "bo_rb_stb": 1.20, "rs_scf_stb": 400.0,
         "rp_scf_stb": 400.0, "bg_rb_scf": 0.002},
    ]

    def test_refuses_without_a_pressure_history(self):
        out = welltest.material_balance()
        self.assertIsInstance(out, Refusal)
        self.assertIn("pressure history", out.reason)
        self.assertIsInstance(welltest.material_balance(history=[]), Refusal)

    def test_original_oil_in_place_from_the_straight_line(self):
        out = welltest.material_balance(self.HISTORY, b_oi_rb_stb=1.3, r_si_scf_stb=600.0)
        self.assertIsInstance(out, Quantity)
        self.assertAlmostEqual(out.value, 10_000_000.0, places=3)
        self.assertAlmostEqual(out.inputs["e_o_rb_stb"][0], 0.10, places=9)
        self.assertAlmostEqual(out.inputs["f_rb"][1], 3_000_000.0, places=6)

    def test_least_squares_through_the_origin_not_a_ratio_of_sums(self):
        """A third survey off the line, exercising the (R_p - R_s) and W_p terms.

        p = 1750: B_o = 1.22, R_s = 440, R_p = 540, B_g = 0.00175, W_p = 208,000
          E_o = (1.22-1.30) + (600-440)(0.00175) = -0.08 + 0.28 = 0.20 rb/STB
          F   = 1,600,000(1.22 + 100 x 0.00175) + 208,000(1.0)
              = 1,600,000(1.395) + 208,000 = 2,440,000 rb

        N = sum(E F)/sum(E^2) = (0.1(1e6) + 0.2(2.44e6) + 0.3(3e6))/(0.01+0.04+0.09)
          = 1,488,000/0.14 = 10,628,571.43 STB.
        A ratio of sums, sum(F)/sum(E) = 6.44e6/0.6, would give 10,733,333 and
        is a different estimator; this asserts the one Ahmed's zero intercept
        implies.
        """
        scatter = [self.HISTORY[0],
                   {"p_psia": 1750.0, "np_stb": 1_600_000.0, "bo_rb_stb": 1.22,
                    "rs_scf_stb": 440.0, "rp_scf_stb": 540.0, "bg_rb_scf": 0.00175,
                    "wp_bbl": 208_000.0, "bw_rb_bbl": 1.0},
                   self.HISTORY[1]]
        out = welltest.material_balance(scatter, b_oi_rb_stb=1.3, r_si_scf_stb=600.0)
        self.assertAlmostEqual(out.inputs["e_o_rb_stb"][1], 0.20, places=9)
        self.assertAlmostEqual(out.inputs["f_rb"][1], 2_440_000.0, places=6)
        self.assertAlmostEqual(out.value, 10_628_571.4286, places=3)
        # Worst residual 314,286 rb against a largest withdrawal of 3,000,000:
        # over Ahmed's "there is some reason for it" reporting threshold.
        self.assertAlmostEqual(out.inputs["max_residual_rb"], 314_285.7143, places=3)
        self.assertTrue(any("deviates from this straight line" in f for f in out.flags))

    def test_refuses_a_drive_it_does_not_model(self):
        out = welltest.material_balance(self.HISTORY, 1.3, 600.0, drive="water")
        self.assertIsInstance(out, Refusal)

    def test_refuses_without_the_initial_pvt(self):
        self.assertIsInstance(welltest.material_balance(self.HISTORY), Refusal)


class AlwaysRefuse(unittest.TestCase):
    """The two the corpus does not carry. A number here would be invented."""

    def test_chan_diagnostic_refuses_and_names_its_source(self):
        out = welltest.chan_diagnostic([[1.0, 0.5], [2.0, 0.9]])
        self.assertIsInstance(out, Refusal)
        self.assertIn("SPE 30775", " ".join(out.needed))

    def test_artificial_lift_screen_refuses_and_names_its_source(self):
        out = welltest.artificial_lift_screen(q_liquid_bbl_d=30.0, depth_ft=4000.0)
        self.assertIsInstance(out, Refusal)
        self.assertIn("Clegg", " ".join(out.needed))


class Provenance(unittest.TestCase):
    def test_every_anchor_is_a_real_corpus_segment(self):
        import json
        import pathlib
        import tools.kb as kb

        # kb resolves the corpus from GEOLOGY_CORPUS_ROOT; in this repo it is
        # vendored at the repo root instead, so both are tried.
        here = pathlib.Path(__file__).resolve()
        candidates = [pathlib.Path(kb.SEGMENT_META),
                      here.parents[2] / "geology-corpus/toc/.segments.jsonl"]
        index = next((p for p in candidates if p.exists()), None)
        if index is None:
            self.skipTest("corpus segment index not present")
        keys = {json.loads(line)["key"]
                for line in index.read_text().splitlines() if line.strip()}
        for name in ("VOGEL", "VOGEL_CASE2", "NODAL", "BUILDUP", "RADIUS", "WOR", "MBE",
                     "LIFT_OPTIONS", "PLUNGER", "CHAN_LINK_ONLY"):
            with self.subTest(anchor=name):
                self.assertIn(getattr(welltest, name), keys)


class Discovery(unittest.TestCase):
    """Auto-discovery is the only thing registering these, so it gets asserted."""

    NAMES = ("vogel_ipr", "nodal_analysis", "buildup_kh_skin", "chan_diagnostic",
             "wor_xplot", "material_balance", "artificial_lift_screen")

    def test_all_seven_are_in_the_registry_from_this_module(self):
        table = dispatch.registry()
        for name in self.NAMES:
            with self.subTest(tool=name):
                self.assertIn(name, table)
                self.assertEqual(table[name][0], "tools.welltest")

    def test_no_private_helper_leaked_into_the_registry(self):
        table = dispatch.registry()
        self.assertNotIn("rate_at", table)
        for helper in ("_vogel", "_as_curve", "_interp", "_grid"):
            self.assertNotIn(helper, table)

    def test_callable_through_dispatch(self):
        out = dispatch.call("vogel_ipr", {"p_r_psig": 2500.0, "p_b_psig": 2500.0,
                                          "test_q_stb_d": 350.0, "test_p_wf_psig": 2000.0})
        self.assertEqual(out["kind"], "Quantity")
        self.assertAlmostEqual(out["value"], 1067.07, places=2)

        nodal = dispatch.call("nodal_analysis", {
            "inflow": [[0.0, 3000.0], [2000.0, 1000.0]],
            "tubing": [[0.0, 1000.0], [2000.0, 2000.0]]})
        self.assertEqual(nodal["kind"], "Quantity")
        self.assertAlmostEqual(nodal["value"], 4000.0 / 3.0, places=6)

        refused = dispatch.call("material_balance", {})
        self.assertEqual(refused["kind"], "Refusal")


if __name__ == "__main__":
    unittest.main()
