"""Group N: rock and fluid properties.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

The oracles here are Ahmed's and Asquith's own printed answers wherever the
corpus works an example, because a number this code produced is no evidence about
whether this code is right:

  * Ahmed Example 5-1 prints k_ro = 0.512 and k_rw = 0.008 at S_w = 0.40.
  * Ahmed Example 5-5 prints k_ro = 0.557 and k_rw = 0.092 at S_w = 0.40.
  * Ahmed Example 4-5 prints FWL = 5033.5 ft from a WOC of 5023 ft.

The rest are transcriptions of the published equation written out longhand, which
is an independent statement of the same intent rather than a call back into the
implementation.

Two properties carry the whole module. `free_water_level` must refuse without an
entry pressure, because returning the WOC would move a contact by tens of feet
with no symptom, and `permeability_estimate` must refuse outside each
correlation's stated validity limits rather than extrapolate.
"""
from __future__ import annotations

import math
import unittest

import dispatch
from tools.result import Quantity, Range, Refusal
from tools.rockfluid import (
    RelativePermeabilityPair, capillary_pressure, fractional_flow, free_water_level,
    kv_kh_ratio, permeability_estimate, relative_permeability, saturation_height,
)


class PermeabilityEstimate(unittest.TestCase):
    def test_refuses_when_irreducible_saturation_is_not_declared(self):
        """Asquith #48: the formulas are 'only valid for estimating permeability
        in formations at irreducible water saturation'."""
        result = permeability_estimate(0.20, 0.25, hydrocarbon="medium_gravity_oil")
        self.assertIsInstance(result, Refusal)
        self.assertIn("irreducible", result.reason)

    def test_refuses_when_the_caller_declares_it_is_not_at_irreducible(self):
        result = permeability_estimate(0.20, 0.25, at_irreducible=False,
                                       hydrocarbon="medium_gravity_oil")
        self.assertIsInstance(result, Refusal)
        self.assertIn("FALSE", result.reason)

    def test_wyllie_rose_medium_gravity_oil_is_exact(self):
        """Eq. 7.30: K = (250 phi^3 / S_wirr)^2.

        250 * 0.20^3 = 250 * 0.008 = 2.0;  2.0 / 0.25 = 8.0;  8.0^2 = 64 md.
        """
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="medium_gravity_oil")
        self.assertIsInstance(result, Range)
        self.assertAlmostEqual(result.members["wyllie_rose"], 64.0, places=9)

    def test_wyllie_rose_dry_gas_uses_the_other_constant(self):
        """Eq. 7.31: (79 * 0.008 / 0.25)^2 = 2.528^2 = 6.390784 md."""
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="dry_gas")
        self.assertAlmostEqual(result.members["wyllie_rose"], 6.390784, places=9)

    def test_wyllie_rose_refuses_a_fluid_it_publishes_no_constant_for(self):
        """The validity limit that matters: two constants, nothing between."""
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="condensate")
        self.assertIn("wyllie_rose", result.assumptions["excluded"])
        self.assertTrue(any("condensate" in flag for flag in result.flags))

    def test_wyllie_rose_refuses_when_the_fluid_is_unstated(self):
        result = permeability_estimate(0.20, 0.25, at_irreducible=True)
        self.assertIn("wyllie_rose", result.assumptions["excluded"])
        self.assertIn("timur", result.members)

    def test_timur_matches_equation_7_32(self):
        """K = (93 phi^2.2 / S_wirr)^2, transcribed from Asquith #48."""
        expected = (93.0 * 0.20 ** 2.2 / 0.25) ** 2
        result = permeability_estimate(0.20, 0.25, at_irreducible=True)
        self.assertAlmostEqual(result.members["timur"], expected, places=9)

    def test_coates_dumanoir_matches_equations_7_33_to_7_35(self):
        c = 23.0 + 465.0 * 0.8 - 188.0 * 0.8 ** 2
        w = math.sqrt((3.75 - 0.20) + (math.log10(0.05 / 20.0) + 2.2) ** 2 / 2.0)
        expected = (c * 0.20 ** (2.0 * w) / (w ** 4 * (0.05 / 20.0))) ** 2
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       rho_h_g_cc=0.8, rw=0.05, r_irr=20.0)
        self.assertAlmostEqual(result.members["coates_dumanoir"], expected, places=6)

    def test_coates_dumanoir_refuses_without_its_own_inputs(self):
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="medium_gravity_oil")
        self.assertIn("coates_dumanoir", result.assumptions["excluded"])

    def test_the_legs_disagree_and_are_not_averaged(self):
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="medium_gravity_oil",
                                       rho_h_g_cc=0.8, rw=0.05, r_irr=20.0)
        self.assertEqual(len(result.members), 3)
        self.assertEqual(result.low, min(result.members.values()))
        self.assertEqual(result.high, max(result.members.values()))
        self.assertGreater(result.high / result.low, 1.5)

    def test_a_ruled_out_leg_is_named_and_the_rest_still_answer(self):
        """Asquith #48 publishes no heavy-oil constant, so Wyllie-Rose is ruled
        out by name while Timur, which has no fluid term, still answers."""
        result = permeability_estimate(0.20, 0.25, at_irreducible=True,
                                       hydrocarbon="heavy_oil")
        self.assertIsInstance(result, Range)
        self.assertEqual(list(result.members), ["timur"])
        self.assertIn("wyllie_rose", result.assumptions["excluded"])
        self.assertIn("coates_dumanoir", result.assumptions["excluded"])
        self.assertTrue(any("degenerate" in flag for flag in result.flags))


class KvKhRatio(unittest.TestCase):
    def test_refuses_to_guess_from_lithology(self):
        """The corpus defines F_k and publishes no table of typical values."""
        result = kv_kh_ratio(lithology="shaly_sandstone", bedding="laminated")
        self.assertIsInstance(result, Refusal)
        self.assertIn("no table of typical ratios", result.reason)
        self.assertIn("shaly_sandstone", result.reason)

    def test_refuses_with_nothing_at_all(self):
        self.assertIsInstance(kv_kh_ratio(), Refusal)

    def test_measured_plugs_give_equation_10_29(self):
        """Ahmed's own Chapter 9 example runs k_v = 40 md against k_h = 1000 md."""
        result = kv_kh_ratio(k_v_md=40.0, k_h_md=1000.0)
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.value, 0.04, places=12)

    def test_layered_beds_use_eq_4_50_over_eq_4_52(self):
        """Two 10 ft beds of 100 md with a 1 ft, 1 md streak between them.

        k_h = (100*10 + 1*1 + 100*10)/21 = 2001/21 = 95.2857142857...
        k_v = 21 / (10/100 + 1/1 + 10/100) = 21/1.2 = 17.5
        ratio = 17.5 * 21 / 2001 = 367.5/2001 = 0.18365817...
        """
        result = kv_kh_ratio(layer_k_md=[100.0, 1.0, 100.0],
                             layer_thickness_ft=[10.0, 1.0, 10.0])
        self.assertAlmostEqual(result.inputs["k_h_md"], 2001.0 / 21.0, places=10)
        self.assertAlmostEqual(result.inputs["k_v_md"], 17.5, places=12)
        self.assertAlmostEqual(result.value, 367.5 / 2001.0, places=12)

    def test_one_layer_is_refused_as_isotropic_by_construction(self):
        result = kv_kh_ratio(layer_k_md=[100.0], layer_thickness_ft=[10.0])
        self.assertIsInstance(result, Refusal)

    def test_will_not_take_both_routes(self):
        with self.assertRaises(ValueError):
            kv_kh_ratio(k_v_md=40.0, k_h_md=1000.0, layer_k_md=[1.0, 2.0],
                        layer_thickness_ft=[1.0, 1.0])

    def test_feeds_the_coning_tool_it_exists_for(self):
        from tools.coning import coning_critical_rate
        anisotropy = kv_kh_ratio(layer_k_md=[100.0, 1.0, 100.0],
                                 layer_thickness_ft=[10.0, 1.0, 10.0])
        result = coning_critical_rate(
            "oil_water", 50.0, 15.0, k_h_md=anisotropy.inputs["k_h_md"],
            k_v_md=anisotropy.inputs["k_v_md"], mu_o_cp=0.73, b_o_bbl_stb=1.1,
            r_e_ft=1000.0, r_w_ft=0.25, rho_o_lb_ft3=47.5, rho_w_lb_ft3=63.76)
        self.assertIsInstance(result, Range)
        self.assertIn("chaperon", result.members)


class RelativePermeability(unittest.TestCase):
    def test_analytical_reproduces_ahmed_example_5_5(self):
        """S_wc 0.25, S_orw 0.35, (k_ro)_Swc 0.85, (k_rw)_Sorw 0.4, n_o 0.9,
        n_w 1.5. Ahmed's table at S_w = 0.40 prints 0.557 and 0.092."""
        pair = relative_permeability(0.40, 0.25, 0.35, k_ro_swc=0.85, k_rw_sor=0.4,
                                     n_o=0.9, n_w=1.5)
        self.assertIsInstance(pair, RelativePermeabilityPair)
        self.assertAlmostEqual(pair.k_ro.value, 0.557, places=3)
        self.assertAlmostEqual(pair.k_rw.value, 0.092, places=3)

    def test_analytical_hits_the_endpoints_ahmed_prints(self):
        """His table also prints k_ro = 0.850 at S_w = 0.25 and k_rw = 0.400 at
        S_w = 0.65, which is 1 - S_orw."""
        at_swc = relative_permeability(0.25, 0.25, 0.35, k_ro_swc=0.85, k_rw_sor=0.4,
                                       n_o=0.9, n_w=1.5)
        self.assertAlmostEqual(at_swc.k_ro.value, 0.850, places=9)
        self.assertAlmostEqual(at_swc.k_rw.value, 0.000, places=9)
        at_sor = relative_permeability(0.65, 0.25, 0.35, k_ro_swc=0.85, k_rw_sor=0.4,
                                       n_o=0.9, n_w=1.5)
        self.assertAlmostEqual(at_sor.k_ro.value, 0.000, places=9)
        self.assertAlmostEqual(at_sor.k_rw.value, 0.400, places=9)

    def test_analytical_refuses_without_endpoints(self):
        result = relative_permeability(0.40, 0.25, 0.35)
        self.assertIsInstance(result, Refusal)
        self.assertIn("k_ro_swc", result.needed)
        self.assertIn("k_rw_sor", result.needed)

    def test_wyllie_gardner_reproduces_ahmed_example_5_1(self):
        """Unconsolidated well-sorted sand, S_wc 0.25. Ahmed's table prints
        k_ro = 0.512 and k_rw = 0.0080 at S_w = 0.40, and k_rw = 0.2160 at 0.70."""
        pair = relative_permeability(0.40, 0.25, 0.30, model="wyllie_gardner",
                                     formation="unconsolidated_well_sorted")
        self.assertAlmostEqual(pair.k_ro.value, 0.512, places=9)
        self.assertAlmostEqual(pair.k_rw.value, 0.008, places=9)
        self.assertAlmostEqual(pair.k_ro_swc.value, 1.0, places=9)
        self.assertAlmostEqual(pair.k_rw_sor.value, 0.216, places=9)

    def test_wyllie_gardner_needs_no_measured_endpoints(self):
        """The route that actually unblocks a stripper well with no core."""
        pair = relative_permeability(0.40, 0.25, 0.30, model="wyllie_gardner",
                                     formation="cemented_sandstone")
        self.assertIsInstance(pair, RelativePermeabilityPair)
        self.assertEqual(set(pair.mobility_ratio_input), {"k_rw_sor", "k_ro_swc"})

    def test_wyllie_gardner_refuses_an_untabulated_formation(self):
        result = relative_permeability(0.40, 0.25, 0.30, model="wyllie_gardner",
                                       formation="dolomite")
        self.assertIsInstance(result, Refusal)

    def test_refuses_outside_the_mobile_window(self):
        self.assertIsInstance(
            relative_permeability(0.20, 0.25, 0.35, k_ro_swc=0.85, k_rw_sor=0.4),
            Refusal)
        self.assertIsInstance(
            relative_permeability(0.90, 0.25, 0.35, k_ro_swc=0.85, k_rw_sor=0.4),
            Refusal)

    def test_the_endpoints_close_the_coning_break(self):
        """coning_breakthrough_time takes k_rw_sor and k_ro_swc and nothing in the
        catalog produced them. This is that wiring, run end to end."""
        from tools.coning import coning_breakthrough_time
        pair = relative_permeability(0.40, 0.25, 0.30, model="wyllie_gardner",
                                     formation="unconsolidated_well_sorted")
        result = coning_breakthrough_time(
            500.0, 80.0, 20.0, rho_w_lb_ft3=63.0, rho_o_lb_ft3=47.0, k_h_md=93.0,
            k_v_md=9.3, mu_o_cp=0.73, b_o_bbl_stb=1.1, phi=0.14,
            k_rw_sor=pair.k_rw_sor.value, k_ro_swc=pair.k_ro_swc.value, mu_w_cp=0.6)
        self.assertNotIsInstance(result, Refusal)
        # M = (0.216/1.0) * (0.73/0.6) = 0.2628, which is Ahmed Eq. 9-24's grouping.
        self.assertAlmostEqual((0.216 / 1.0) * (0.73 / 0.6), 0.2628, places=4)


class FractionalFlow(unittest.TestCase):
    def test_hand_worked_water_cut(self):
        """f_w = 1/(1 + (k_ro/k_rw)(mu_w/mu_o))

        (0.512/0.008) = 64;  (0.5/2.0) = 0.25;  1/(1 + 16) = 0.0588235294...
        """
        result = fractional_flow(0.512, 0.008, 2.0, 0.5)
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.value, 1.0 / 17.0, places=12)

    def test_zero_at_irreducible_water(self):
        """Ahmed #182: at S_wc the water flow rate is zero, so the water cut is 0%."""
        self.assertAlmostEqual(fractional_flow(0.85, 0.0, 2.0, 0.5).value, 0.0)

    def test_one_at_residual_oil(self):
        """And at S_or the oil rate is zero, so the water cut reaches 100%."""
        self.assertAlmostEqual(fractional_flow(0.0, 0.4, 2.0, 0.5).value, 1.0)

    def test_a_more_viscous_oil_shifts_the_curve_up(self):
        light = fractional_flow(0.512, 0.008, 1.0, 0.5).value
        heavy = fractional_flow(0.512, 0.008, 20.0, 0.5).value
        self.assertGreater(heavy, light)

    def test_chains_from_the_relative_permeability_pair(self):
        pair = relative_permeability(0.40, 0.25, 0.30, model="wyllie_gardner",
                                     formation="unconsolidated_well_sorted")
        result = fractional_flow(pair.k_ro.value, pair.k_rw.value, 2.0, 0.5)
        self.assertAlmostEqual(result.value, 1.0 / 17.0, places=12)


class CapillaryPressure(unittest.TestCase):
    def test_refuses_without_both_tensions(self):
        result = capillary_pressure(1.05, sigma_lab_dynes_cm=72.0)
        self.assertIsInstance(result, Refusal)
        self.assertIn("sigma_res_dynes_cm", result.needed)

    def test_tension_correction_alone(self):
        """1.05 * 30/72 = 0.4375 psi."""
        result = capillary_pressure(1.05, sigma_lab_dynes_cm=72.0,
                                    sigma_res_dynes_cm=30.0)
        self.assertAlmostEqual(result.value, 0.4375, places=12)
        self.assertFalse(result.assumptions["rock_correction_applied"])

    def test_full_equation_4_37(self):
        """0.4375 * sqrt(phi_res k_core / (phi_core k_res))
           = 0.4375 * sqrt(0.19*80 / (0.16*120))"""
        expected = 0.4375 * math.sqrt(0.19 * 80.0 / (0.16 * 120.0))
        result = capillary_pressure(1.05, sigma_lab_dynes_cm=72.0,
                                    sigma_res_dynes_cm=30.0, phi_core=0.16,
                                    k_core_md=80.0, phi_res=0.19, k_res_md=120.0)
        self.assertAlmostEqual(result.value, expected, places=12)
        self.assertTrue(result.assumptions["rock_correction_applied"])

    def test_refuses_a_half_supplied_rock_correction(self):
        result = capillary_pressure(1.05, sigma_lab_dynes_cm=72.0,
                                    sigma_res_dynes_cm=30.0, phi_core=0.16)
        self.assertIsInstance(result, Refusal)
        self.assertIn("k_core_md", result.needed)


class SaturationHeight(unittest.TestCase):
    ANALYTICAL = dict(swc=0.25, sor=0.35, pc_swc_psi=20.0, n_p=0.71)

    def test_hand_worked_saturation_at_100_ft(self):
        """p_c = 100 * 20.6 / 144 = 14.305556 psi
           S_w = 1 - 0.35 - 0.40 * (14.305556/20)^(1/0.71)
        """
        pc = 100.0 * 20.6 / 144.0
        expected = 1.0 - 0.35 - 0.40 * (pc / 20.0) ** (1.0 / 0.71)
        result = saturation_height(100.0, 20.6, **self.ANALYTICAL)
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.inputs["pc_psi"], pc, places=12)
        self.assertAlmostEqual(result.value, expected, places=12)

    def test_saturation_falls_with_height(self):
        low = saturation_height(20.0, 20.6, **self.ANALYTICAL).value
        high = saturation_height(120.0, 20.6, **self.ANALYTICAL).value
        self.assertGreater(low, high)

    def test_pins_at_connate_above_the_transition_zone(self):
        result = saturation_height(300.0, 20.6, **self.ANALYTICAL)
        self.assertAlmostEqual(result.value, 0.25, places=12)
        self.assertTrue(any("pinned at S_wc" in flag for flag in result.flags))

    def test_flags_that_eq_5_24_does_not_reach_full_water_at_the_fwl(self):
        """At p_c = 0 the equation gives 1 - S_orw, not 1.0. That is a property of
        the source and is reported rather than clamped."""
        result = saturation_height(0.0, 20.6, **self.ANALYTICAL)
        self.assertAlmostEqual(result.value, 0.65, places=12)
        self.assertTrue(any("not S_w = 1" in flag for flag in result.flags))

    def test_refuses_below_the_free_water_level(self):
        self.assertIsInstance(saturation_height(-5.0, 20.6, **self.ANALYTICAL), Refusal)

    def test_refuses_the_analytical_route_without_its_anchors(self):
        result = saturation_height(100.0, 20.6, swc=0.25, sor=0.35)
        self.assertIsInstance(result, Refusal)
        self.assertIn("pc_swc_psi", result.needed)

    def test_leverett_route_reads_a_converted_lab_curve(self):
        """A lab curve at 72 dynes/cm converted to 30 scales every p_c by 30/72.

        At h = 50 ft and delta-rho 20.6 the reservoir p_c is 50*20.6/144 = 7.1528
        psi. The converted curve is (S_w, p_c*30/72): (0.20, 5.0), (0.40, 2.5),
        (1.00, 0.4166667). 7.1528 sits above the highest converted p_c, so the
        reading is held at the driest measured point, S_w = 0.20.
        """
        curve = [(0.20, 12.0), (0.40, 6.0), (1.00, 1.0)]
        result = saturation_height(50.0, 20.6, method="leverett_j", lab_curve=curve,
                                   sigma_lab_dynes_cm=72.0, sigma_res_dynes_cm=30.0)
        self.assertAlmostEqual(result.inputs["pc_psi"], 50.0 * 20.6 / 144.0, places=12)
        self.assertAlmostEqual(result.value, 0.20, places=12)

    def test_leverett_route_interpolates_inside_the_curve(self):
        """p_c at 20 ft is 20 * 20.6 / 144 = 2.8611111 psi.

        The converted curve, ascending in p_c, is
            (1.00, 0.4166667), (0.40, 2.5), (0.20, 5.0)
        so 2.8611111 falls between the second and third points and

            S_w = 0.40 + (0.20 - 0.40) * (2.8611111 - 2.5) / (5.0 - 2.5)
                = 0.40 - 0.2 * 0.14444444
                = 0.37111111
        """
        curve = [(0.20, 12.0), (0.40, 6.0), (1.00, 1.0)]
        result = saturation_height(20.0, 20.6, method="leverett_j", lab_curve=curve,
                                   sigma_lab_dynes_cm=72.0, sigma_res_dynes_cm=30.0)
        self.assertAlmostEqual(result.value, 0.37111111, places=7)
        self.assertEqual(result.flags, ())

    def test_leverett_route_refuses_without_a_curve(self):
        result = saturation_height(50.0, 20.6, method="leverett_j")
        self.assertIsInstance(result, Refusal)


class FreeWaterLevel(unittest.TestCase):
    def test_refuses_without_an_entry_pressure(self):
        """The refusal this pair exists for: the WOC is not the FWL."""
        result = free_water_level(5023.0, 20.6)
        self.assertIsInstance(result, Refusal)
        self.assertIn("entry_pressure_psi", " ".join(result.needed))
        self.assertIn("zero capillary pressure", result.reason)

    def test_reproduces_ahmed_example_4_5(self):
        """FWL = 5023 + (144)(1.5)/(64.1 - 43.5) = 5033.5 ft."""
        result = free_water_level(5023.0, 64.1 - 43.5, 1.5)
        self.assertIsInstance(result, Quantity)
        self.assertAlmostEqual(result.value, 5033.5, places=1)
        self.assertAlmostEqual(result.value, 5023.0 + 144.0 * 1.5 / 20.6, places=10)

    def test_the_fwl_is_below_the_woc(self):
        result = free_water_level(5023.0, 20.6, 1.5)
        self.assertGreater(result.value, 5023.0)
        self.assertAlmostEqual(result.inputs["offset_ft"], 144.0 * 1.5 / 20.6, places=10)

    def test_a_tighter_rock_moves_the_contact_further(self):
        loose = free_water_level(4000.0, 20.6, 0.75).inputs["offset_ft"]
        tight = free_water_level(4000.0, 10.0, 6.0).inputs["offset_ft"]
        self.assertGreater(tight, loose)
        self.assertGreater(tight, 80.0)

    def test_reproduces_ahmed_example_4_6(self):
        """Ahmed #50 Step 1: FWL = 4060 + (144)(0.75)/(65.2 - 55.2) = 4070.8 ft."""
        result = free_water_level(4060.0, 65.2 - 55.2, 0.75)
        self.assertAlmostEqual(result.value, 4070.8, places=1)

    def test_the_pair_composes(self):
        """FWL first, then the saturation at a standoff above it."""
        fwl = free_water_level(5023.0, 20.6, 1.5)
        height = fwl.value - 4990.0          # a perforation 33.5 ft above the FWL
        sw = saturation_height(height, 20.6, swc=0.25, sor=0.35, pc_swc_psi=20.0,
                               n_p=0.71)
        self.assertIsInstance(sw, Quantity)
        self.assertGreater(sw.value, 0.25)
        self.assertLess(sw.value, 0.65)


class Dispatch(unittest.TestCase):
    NAMES = ("permeability_estimate", "kv_kh_ratio", "relative_permeability",
             "fractional_flow", "capillary_pressure", "saturation_height",
             "free_water_level")

    def test_every_tool_is_discovered(self):
        table = dispatch.registry()
        for name in self.NAMES:
            with self.subTest(name):
                self.assertIn(name, table)
                self.assertEqual(table[name][0], "tools.rockfluid")

    def test_the_fwl_refusal_crosses_the_boundary_as_a_value(self):
        out = dispatch.call("free_water_level", {"woc_ft": 5023.0,
                                                 "delta_rho_lb_ft3": 20.6})
        self.assertEqual(out["kind"], "Refusal")
        self.assertIn("entry", out["reason"])

    def test_the_fwl_answer_crosses_the_boundary_intact(self):
        out = dispatch.call("free_water_level", {"woc_ft": 5023.0,
                                                 "delta_rho_lb_ft3": 20.6,
                                                 "entry_pressure_psi": 1.5})
        self.assertEqual(out["kind"], "Quantity")
        self.assertAlmostEqual(out["value"], 5033.5, places=1)

    def test_the_relative_permeability_pair_flattens(self):
        out = dispatch.call("relative_permeability",
                            {"sw": 0.40, "swc": 0.25, "sor": 0.30,
                             "model": "wyllie_gardner",
                             "formation": "unconsolidated_well_sorted"})
        self.assertEqual(out["kind"], "RelativePermeabilityPair")
        self.assertAlmostEqual(out["k_ro"]["value"], 0.512, places=9)
        self.assertAlmostEqual(out["k_rw_sor"]["value"], 0.216, places=9)
        self.assertTrue(out["k_rw_sor"]["source"])

    def test_the_permeability_spread_flattens(self):
        out = dispatch.call("permeability_estimate",
                            {"phi": 0.20, "sw_irr": 0.25, "at_irreducible": True,
                             "hydrocarbon": "medium_gravity_oil"})
        self.assertEqual(out["kind"], "Range")
        self.assertAlmostEqual(out["members"]["wyllie_rose"], 64.0, places=9)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
