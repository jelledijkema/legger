import unittest
import os.path
from shutil import copyfile
from legger.utils.profile_match_a import doe_profinprof, maaktabellen
from pyspatialite import dbapi2 as dbapi

test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestProfileMatch(unittest.TestCase):
    def setUp(self):

        self.legger_db = os.path.join(
            test_dir,
            'test_spatialite_with_matchprof.sqlite'
        )

        legger_db_original = os.path.join(
            test_dir,
            'test_spatialite_output_with_theoretical_profiles.sqlite'
        )

        copyfile(legger_db_original, self.legger_db)

    def test_all_together(self):

        con_legger = dbapi.connect(self.legger_db)
        maaktabellen(con_legger.cursor())
        con_legger.commit()
        doe_profinprof(con_legger.cursor(), con_legger.cursor())
        con_legger.commit()





