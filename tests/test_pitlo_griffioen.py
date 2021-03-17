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

    def test4(self):
        gradient = calc_pitlo_griffioen(
            flow=0.125,
            ditch_bottom_width=0.7,
            water_depth=0.8,
            slope=1.5,
            friction_manning=27.2,
            friction_begroeiing=80,
            begroeiingsdeel=0.1)
        self.assertAlmostEqual(gradient, 0.8768, 2)


