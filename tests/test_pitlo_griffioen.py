import unittest

from legger.utils.theoretical_profiles import calc_pitlo_griffioen


class TestProfileMatch(unittest.TestCase):

    def test1(self):

        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 27.2, 80, 0.9)
        self.assertAlmostEqual(gradient, 75, 0)

    def test2(self):
        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 27.2, 80, 0.5)
        self.assertAlmostEqual(gradient, 6.4, 1)

    def test3(self):
        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 27.2, 80, 0.1)
        self.assertAlmostEqual(gradient, 0.34, 2)



