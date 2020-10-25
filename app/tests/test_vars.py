import math
from unittest import TestCase

import vars


class TestVars(TestCase):
    def test__calculate_speed_miner(self):
        self.assertEqual(
            2 * 3 / (1350 * 24 * 60 * 60),
            vars.calculate_speed_miner((0, 0, 0, 0, 0), (2, 3, 5, 7, 11)),
        )

    def test__calculate_speed_bruteforce(self):
        self.assertEqual(1, vars.calculate_speed_bruteforce((1, 1, 2, 3, 5), (2, 3, 5, 7, 11)))
        self.assertEqual(3 / 7, vars.calculate_speed_bruteforce((2, 3, 5, 7, 11), (1, 1, 2, 3, 5)))

    def test__standard_speed(self):
        self.assertEqual(1, vars.standard_speed((1, 1, 2, 3, 5), (2, 3, 5, 7, 11)))
        self.assertEqual(3 / 7, vars.standard_speed((2, 3, 5, 7, 11), (1, 1, 2, 3, 5)))
