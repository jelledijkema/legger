import unittest
import os.path
from shutil import copyfile
from legger.utils.theoretical_profiles import create_theoretical_profiles, write_theoretical_profile_results_to_db


test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestTheoreticalProfiles(unittest.TestCase):
    def setUp(self):

        self.legger_db = os.path.join(
            test_dir,
            'test_spatialite_output_with_theoretical_profiles_31012018.sqlite'
        )

        legger_db_original = os.path.join(
            test_dir,
            'test_spatialite_output_join_with_tdi_results_31012018.sqlite' #'test_spatialite_with_3di_results.sqlite'
        )

        copyfile(legger_db_original, self.legger_db)

    def test_all_together(self):

        profiles = create_theoretical_profiles(self.legger_db)

        write_theoretical_profile_results_to_db(profiles, self.legger_db)

        pass



# bereken_Manning(0.04217, 3.703667, 0.30, 1.5)