import unittest

from legger.utils.theoretical_profiles import calc_pitlo_griffioen

# calc_pitlo_griffioen(flow, ditch_bottom_width, water_depth, slope, friction_manning, friction_begroeiing,
#                         begroeiingsdeel)
class TestProfileMatch(unittest.TestCase):

    def test1(self):

        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 34, 30, 0.25)
        self.assertAlmostEqual(gradient, 1.99, 2)

    def test2(self):
        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 34, 65, 0.9)
        self.assertAlmostEqual(gradient, 86, 0)

    def test3(self):
        gradient = calc_pitlo_griffioen(0.4508, 7.55, 0.76, 1.8, 34, 30, 0.5)
        self.assertAlmostEqual(gradient, 7.16, 2)

    def test4(self):
        gradient = calc_pitlo_griffioen(
            flow=0.125,
            ditch_bottom_width=0.7,
            water_depth=0.8,
            slope=1.5,
            friction_manning=34,
            friction_begroeiing=30,
            begroeiingsdeel=0.25)
        self.assertAlmostEqual(gradient, 6.04, 2)


