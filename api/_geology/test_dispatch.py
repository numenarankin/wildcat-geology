"""Argument repair, and the line it must not cross.

Run: python3 -m unittest discover -s api/_geology -p 'test_*.py'

A caller writing `las_header` for `header` has understood the tool and spelled
one word differently; rejecting that costs a whole model step. A caller whose
name matches TWO parameters has not been understood at all, and filling one of
them would return a plausible number computed from the wrong input — which is
worse than the error, because nothing downstream can tell.
"""
from __future__ import annotations

import unittest

from dispatch import _canon, _repair


def sample(tvd, kb=None, datum_resolved=None, reference="KB"):
    return (tvd, kb, datum_resolved, reference)


def ambiguous(rho_ma=None, rho_matrix=None):
    return (rho_ma, rho_matrix)


class Repair(unittest.TestCase):
    def test_renames_a_near_miss(self):
        # Units are noise, so `kb_ft` is `kb` spelled longer.
        kwargs, repairs = _repair(sample, {"tvd": 4109.0, "kb_ft": 1131.0})
        self.assertEqual(kwargs, {"tvd": 4109.0, "kb": 1131.0})
        self.assertEqual(repairs, {"kb_ft": "kb"})

    def test_will_not_map_a_number_into_a_string_parameter(self):
        """The near-miss that must NOT be repaired.

        `reference_elevation_ft` was the model's word for the KB elevation. An
        earlier canonicalisation stripped `_elevation` and landed it on
        `reference` — a real parameter of the same function taking "KB" or "GL".
        The elevation would have gone in as the reference NAME, the tool would
        have returned something, and nothing downstream could have told.
        """
        kwargs, repairs = _repair(sample, {"tvd": 4109.0, "reference_elevation_ft": 1131.0})
        self.assertEqual(repairs, {})
        self.assertIn("reference_elevation_ft", kwargs)

    def test_strips_the_las_prefix(self):
        # `datum_resolve` takes `header`; the model wrote `las_header`.
        def takes_header(header=None):
            return header

        kwargs, repairs = _repair(takes_header, {"las_header": {"EKB": 1131}})
        self.assertEqual(list(kwargs), ["header"])
        self.assertEqual(repairs, {"las_header": "header"})

    def test_leaves_a_correct_call_untouched(self):
        kwargs, repairs = _repair(sample, {"tvd": 4109.0, "kb": 1131.0})
        self.assertEqual(kwargs, {"tvd": 4109.0, "kb": 1131.0})
        self.assertEqual(repairs, {})

    def test_refuses_to_choose_between_two_candidates(self):
        # Both parameters canonicalise the same. Filling either would put the
        # value in a slot the caller did not mean, and the answer would look
        # exactly as trustworthy as a correct one.
        kwargs, repairs = _repair(ambiguous, {"matrix_density_gcc": 2.71})
        self.assertEqual(repairs, {})
        self.assertIn("matrix_density_gcc", kwargs)

    def test_never_overwrites_an_argument_the_caller_supplied(self):
        kwargs, repairs = _repair(sample, {"tvd": 4109.0, "kb": 1131.0, "kb_elevation_ft": 999.0})
        self.assertEqual(kwargs["kb"], 1131.0)
        self.assertEqual(repairs, {})

    def test_canonicalisation_collapses_units_and_prefixes(self):
        self.assertEqual(_canon("kb_ft"), _canon("kb"))
        self.assertEqual(_canon("las_header"), _canon("header"))
        # And does NOT collapse two different ideas into one.
        self.assertNotEqual(_canon("reference_elevation_ft"), _canon("reference"))
        self.assertEqual(_canon("bht_degf"), "bht")
        # Distinct ideas stay distinct.
        self.assertNotEqual(_canon("rho_b"), _canon("rho_ma"))


if __name__ == "__main__":
    unittest.main()
