# coding: utf-8
# todo:
#  X DuikerSifonHevel
#  X objectid vullen --> verwijderd
#  X verwijderen imp tabellen
#  X oplossing verzinnen voor geo_alchemy fix
#  - grondsoort? --> voorlopig niet
#  X geometry colom vastzetten (op 'geometry')
#  - logging van ogr2ogr terugsluizen naar logging
#  - melding of proces gelukt is en verwijzen naar logging indien mislukt

import datetime
import logging
import os
import os.path
import subprocess
import sys

from legger.sql_models.legger_database import LeggerDatabase

log = logging.getLogger(__name__)


def nonfloat(value, default_value=None):
    if value is None:
        return default_value
    try:
        return float(value)
    except ValueError:
        return default_value


def nonint(value, default_value=None):
    if value is None:
        return default_value
    try:
        return int(value)
    except ValueError:
        return default_value


def nonwkt(value, default_value=None):
    if value is None:
        return default_value
    try:
        return 'SRID=28992;' + value.wkt
    except ValueError:
        return default_value


class CreateLeggerSpatialite(object):
    """
        Select "dump" or "export" .gdb files that come from DAMO and HDB
        This should be similar to the export that is send to the N&S datachecker and modelbuilder for this model revision.

        The output of this step is a legger_{polder}_{datetime}.sqlite file with all the necessary tables and data.
        Step 1: make empty legger database
        Step 2: Read DAMO and HDB (geopandas)
        Step 3: make dataframes from data according to right format
        Step 4: write dataframes to legger database (sqlalchemy)
        """

    def __init__(self, filepath_DAMO, filepath_HDB, database_path):
        self.filepath_DAMO = filepath_DAMO
        self.filepath_HDB = filepath_HDB
        self.database_path = database_path

        self.profielpunten_tabel = None
        self.profielen_tabel = None
        self.kenmerken_tabel = None
        self.hydroobject_tabel = None
        self.waterdeel_tabel = None
        self.duikersifonhevel_tabel = None

        self.ogr_exe = os.path.abspath(os.path.join(sys.executable, os.pardir, os.pardir, 'bin', 'ogr2ogr.exe'))

        self.tables = ['DuikerSifonHevel', 'Waterdeel', 'HydroObject', 'PeilafwijkingGebied', 'PeilgebiedPraktijk',
                  'GW_PRO', 'GW_PRW', 'GW_PBP', 'IWS_GEO_BESCHR_PROFIELPUNTEN']

        self.db = LeggerDatabase(
            {
                'db_file': self.database_path,
                'db_path': self.database_path  # N&S inconsistent gebruik van  :-O
            },
            'spatialite'
        )

    def full_import_ogr2ogr(self):

        # Volgende activiteiten:
        # stap 1: aanmaken lege sqlite met de juiste tabellen en de juiste kolommen in tabellen lukt niet in mijn testomgeving.
        self.create_spatialite()

        # Stap 2: Laad data uit DAMO in spatialite
        self.dump_gdb_to_spatialite()

        # Stap 3: vul tabellen met queries
        self.vul_queries()

        # Stap 4: verwijder onnodige tabellen
        self.delete_imported_tables()

        # Stap 5: add default settings to tabellen
        self.add_default_settings()

    def create_spatialite(self, delete_existing=True):
        # Step 1: make empty legger database

        if os.path.exists(self.database_path):
            if delete_existing:
                os.remove(self.database_path)
            else:
                raise Exception('spatialite {0} already exist'.format(self.database_path))

        # Make new database
        self.db.create_db()

    def dump_gdb_to_spatialite(self):
        process_errors = []

        nr_tables = len(self.tables)
        for i, table in enumerate(self.tables):

            log.info("--- copy {0}/{1} table {2} ---".format(i+1, nr_tables, table))

            # "-overwrite"
            cmd = '"{ogr_exe}" -a_srs EPSG:28992 -f SQLite -dsco SPATIALITE=YES -append ' \
                  '-lco GEOMETRY_NAME=geometry -nln {dest_table}' \
                  ' "{spatialite_path}" "{gdb_path}" {source_table}'.format(
                ogr_exe=self.ogr_exe,
                gdb_path=self.filepath_DAMO,
                source_table=table,  # ' '.join(tables),
                dest_table="imp_{0}".format(table),
                spatialite_path=self.database_path
            )
            log.info(cmd)

            ret = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if ret != 0:
                msg = "ogr2ogr return code was '{ret}' unequal to 0 for table '{table}'".format(ret=ret, table=table)
                process_errors.append(msg)
                log.error(msg)

    def vul_queries(self):

        # vullen profielpunten
        session = self.db.get_session()
        session.execute("""
        INSERT INTO profielpunten  (pbp_id, prw_id, pbpident, osmomsch, iws_volgnr, iws_hoogte, afstand, pro_pro_id, geometry)
        SELECT pbp_id, prw_id, pbpident, osmomsch, iws_volgnr, iws_hoogte, iws_afstand, pro_pro_id, CastToXY(ipp.geometry)
        FROM imp_gw_pbp pbp, imp_iws_geo_beschr_profielpunten ipp, imp_gw_prw prw 
        WHERE pbp.pbp_id = ipp.pbp_pbp_id AND pbp.prw_prw_id = prw.prw_id
        """)

        # vullen profielen
        session.execute("""
        INSERT INTO profielen  (proident, bron_profiel, pro_id, hydro_id)
        SELECT proident, osmomsch, pro_id, ho.hydroobject_id
        FROM imp_gw_pro pro
        LEFT JOIN imp_hydroobject ho ON st_intersects(pro.geometry, ho.geometry)  
        where betrouwbaar = 1
        """)

        # vullen kenmerken
        session.execute("""
        INSERT INTO kenmerken(
            id,
            diepte,
            bron_diepte,
            bodemhoogte,
            breedte,
            --bodembreedte,
            bron_breedte,
            lengte,
            taludvoorkeur,
            steilste_talud,
            grondsoort,
            bron_grondsoort,
            hydro_id)
        SELECT 
            hydroobject_id as id,
            substr(hoogte_getabuleerd, instr(hoogte_getabuleerd, ' ')) as diepte, 
            keuze_profiel as bron_diepte,
            bodemhoogte_nap as bodemhoogte,
            substr(breedte_getabuleerd, instr(breedte_getabuleerd, ' ')) as waterbreedte,
            --substr(breedte_getabuleerd, 1, instr(breedte_getabuleerd, ' ')-1) as bodembreedte, 
            keuze_profiel as bron_breedte,
            shape_length as lengte,
            "" as talud_voorkeur,
            min(ws_talud_links, ws_talud_rechts) as steilste_talud,
            "" as grondsoort,
            "" as bron_grondsoort,
            hydroobject_id as hydro_id
          FROM imp_hydroobject
        """)

        # vullen hydroobjecten
        session.execute("""
        INSERT INTO hydroobject  (id, code, categorieoppwaterlichaam, streefpeil, geometry)
        SELECT 
            ho.hydroobject_id as id,
            min(ho.code),
            min(ho.categorieoppwaterlichaam),
            min(COALESCE(pgp.peil_wsa, pag.peil_wsa)) as streefpeil,
            min(ho.geometry)
        FROM imp_hydroobject ho
        JOIN  imp_peilgebiedpraktijk pgp ON st_intersects(ho.geometry, pgp.geometry)  
        LEFT OUTER JOIN  imp_peilafwijkinggebied pag ON st_intersects(ho.geometry, pag.geometry) 
        GROUP BY id
        """)

        # vullen waterdeel =
        session.execute("""
        INSERT INTO waterdeel  (id, shape_length, shape_area, geometry)
        SELECT ogc_fid as id, shape_length, shape_area, geometry
        FROM imp_waterdeel
        """)

        # duikersifonhevel
        session.execute("""
         INSERT INTO duikersifonhevel(
             id, 
             code, 
             categorie, 
             lengte, 
             hoogteopening, 
             breedteopening,
             hoogtebinnenonderkantbene,
             hoogtebinnenonderkantbov,
             vormkoker,
             debiet,
             geometry)
         SELECT 
             ogc_fid, 
             code, 
             ws_categorie, 
             lengte, 
             hoogteopening, 
             breedteopening,
             hoogtebinnenonderkantbene,
             hoogtebinnenonderkantbov,
             vormkoker,
             "0",
             geometry
         FROM imp_duikersifonhevel
         """)

        session.commit()

    def delete_imported_tables(self):
        session = self.db.get_session()
        for table in self.tables:
            session.execute("DROP TABLE IF EXISTS imp_{0} ;".format(table.lower()))
            session.execute("DROP TABLE IF EXISTS idx_imp_{0}_geometry;".format(table.lower()))
            session.execute("DROP TABLE IF EXISTS idx_imp_{0}_geometry_node;".format(table.lower()))
            session.execute("DROP TABLE IF EXISTS idx_imp_{0}_geometry_parent;".format(table.lower()))
            session.execute("DROP TABLE IF EXISTS idx_imp_{0}_geometry_rowid;".format(table.lower()))
            session.execute("DELETE FROM geometry_columns WHERE f_table_name = 'imp_{0}';".format(table.lower()))

        session.commit()
        # make space available by reducing filesize
        session.execute("VACUUM")
        session.commit()

    def add_default_settings(self):
        session = self.db.get_session()
        session.execute("INSERT INTO categorie(categorie, naam, variant_diepte_min, variant_diepte_max, default_talud) VALUES "
                        "(1, 'primair', 0.2, 5, 1.5),"
                        "(2, 'secundair', 0.2, 2.5, 1.5),"
                        "(3, 'tertaire', 0.2, 1, 1.5),"
                        "(4, 'overig', 0.2, 1, 1.5)")
        session.commit()

def main():
    test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'tests', 'data'))

    database_path = os.path.join(
        test_data_dir,
        "test_{0}.sqlite".format(str(datetime.datetime.today().strftime('%Y%m%d')))
    )

    filepath_DAMO = os.path.join(test_data_dir, 'DAMO.gdb')  # 'Hoekje_leggertool_database.gdb')
    filepath_HDB = os.path.join(test_data_dir, 'HDB.gdb')  # 'Hoekje_leggertool_HDB.gdb')

    legger_class = CreateLeggerSpatialite(
        filepath_DAMO,
        filepath_HDB,
        database_path
    )

    legger_class.full_import_ogr2ogr()



if __name__ == '__main__':
    main()
