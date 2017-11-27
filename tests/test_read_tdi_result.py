import unittest
import os.path
from legger.utils.read_tdi_results import (
    read_tdi_results, write_tdi_results_to_db, read_tdi_culvert_results,
    write_tdi_culvert_results_to_db)
from legger.sql_models.legger_views import create_legger_views
from pyspatialite import dbapi2 as dbapi

test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


class TestReadTdiResults(unittest.TestCase):
    def setUp(self):
        testdir = os.path.join(
            os.path.dirname(__file__),
            'data',
            'tdimodel'
        )

        self.model_db = os.path.join(
            testdir,
            'hhw_1d2d.sqlite'
        )

        self.result_db = os.path.join(
            testdir,
            'subgrid_map.sqlite1'
        )

        self.result_nc = os.path.join(
            testdir,
            'subgrid_map.nc'
        )

        self.legger_db = os.path.join(
            os.path.dirname(__file__),
            'data',
            'test_spatialite.sqlite'
        )

    def test_read_and_join_tdi_results(self):
        result = read_tdi_results(
            self.model_db,
            self.result_db,
            self.result_nc,
            self.legger_db
        )

        # todo: check results

        write_tdi_results_to_db(result,
                                self.legger_db)

    def test_read_culvert_results(self):
        results = read_tdi_culvert_results(
            self.model_db,
            self.result_nc,
            self.legger_db
        )

        write_tdi_culvert_results_to_db(results,
                                        self.legger_db)

        self.assertEqual(len(results), 1373)
        # todo: check results


    def test_create_views(self):
        con_legger = dbapi.connect(self.legger_db)

        create_legger_views(con_legger)
