import sys
import datetime
import os.path

# sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
# sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, 'ThreeDiToolbox', 'external'))
# print(sys.path)

# import fiona laten staan, anders worden er problemen gemeld met het laden van dll's
import fiona

import pandas as pd
import geopandas as gpd

from legger.sql_models.legger import HydroObject as SqlHydroObject
from legger.sql_models.legger import Waterdeel as SqlWaterdeel, DuikerSifonHevel as SqlDuikerSifonHevel
from legger.sql_models.legger import Kenmerken as SqlKenmerken, Profielen as SqlProfielen, Profielpunten as SqlProfielpunten
from legger.sql_models.legger_database import LeggerDatabase


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



def create_spatialite_database(filepath_DAMO, filepath_HDB, database_path):
    """
    Select a "dump" or "export" that is send to the N&S datachecker to create a spatialite database based on this.
    The output of this step is a legger_{polder}_{datetime}.sqlite file with all the necessary tables and data.
    Step 1: make empty legger database
    Step 2: Read DAMO and HDB (geopandas)
    Step 3: make dataframes from data according to right format
    Step 4: write dataframes to legger database (sqlalchemy)
    """


    ## Delete existing database
    if os.path.exists(database_path):
        os.remove(database_path)

    ## Make new database
    db = LeggerDatabase(
        {
            'db_file': database_path,
            'db_path': database_path # N&S inconsistent gebruik van  :-O
        },
        'spatialite'
    )

    db.create_db()

    ## Step 2: Read databases
    ## Read DAMO.gdb
    # list_of_layers = fiona.listlayers(filepath_DAMO)
    # 'DuikerSifonHevel', 'Profielen', 'Waterdeel', 'Profielpunten', 'HydroObject', 'Kenmerken'

    DuikerSifonHevel = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='DuikerSifonHevel')
    Profielen = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Profielen')
    Waterdeel = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Waterdeel')
    Profielpunten = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Profielpunten')
    HydroObject = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='HydroObject')
    Kenmerken = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Kenmerken')

    ## inlezen HDB.gpd
    # list_of_layers = fiona.listlayers(filepath_HDB)
    # 'vaste_dammen', 'polderclusters', 'Sturing_3Di', 'gemalen_op_peilgrens', 'duikers_op_peilgrens',
    # 'stuwen_op_peilgrens', 'hydro_deelgebieden'

    # vaste_dammen = gpd.read_file(filepath_HDB,driver='OpenFileGDB',layer='vaste_dammen')
    # doet het niet
    polderclusters = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='polderclusters')
    Sturing_3di = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='Sturing_3di')
    gemalen_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='gemalen_op_peilgrens')
    duikers_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='duikers_op_peilgrens')
    stuwen_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='stuwen_op_peilgrens')
    hydro_deelgebieden = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='hydro_deelgebieden')

    ## Step 3: dataframes from databases
    ## met geo
    #
    HydroObject_table = pd.DataFrame(HydroObject[['ID', 'CODE', 'CATEGORIEOPPWATERLICHAAM', 'STREEFPEIL',
                                                  'DEBIET', 'CHANNEL_ID', 'FLOWLINE_ID', 'geometry']])
    HydroObject_table = HydroObject_table.reset_index()
    HydroObject_table.columns = ['objectid', 'id', 'code', 'categorieoppwaterlichaam', 'streefpeil',
                                 'debiet', 'channel_id', 'flowline_id', 'geometry']
    #
    Waterdeel_table = pd.DataFrame(Waterdeel[['ID', 'SHAPE_Length', 'SHAPE_Area', 'geometry']])
    Waterdeel_table = Waterdeel_table.reset_index()
    Waterdeel_table.columns = ['objectid', 'id', 'shape_length', 'shape_area', 'geometry']

    #
    DuikerSifonHevel_table = pd.DataFrame(DuikerSifonHevel[['ID', 'CODE', 'CATEGORIE', 'LENGTE', 'HOOGTEOPENING',
                                                            'BREEDTEOPENING', 'HOOGTEBINNENONDERKANTBENE',
                                                            'HOOGTEBINNENONDERKANTBOV', 'VORMKOKER', 'DEBIET',
                                                            'geometry']])
    DuikerSifonHevel_table = DuikerSifonHevel_table.reset_index()
    DuikerSifonHevel_table.columns = ['objectid', 'id', 'code', 'categorie', 'lengte', 'hoogteopening',
                                      'breedteopening',
                                      'hoogtebinnenonderkantbene', 'hoogtebinnenonderkantbov', 'vormkoker',
                                      'debiet',
                                      'geometry']
    DuikerSifonHevel_table['channel_id'] = ""
    DuikerSifonHevel_table['flowline_id'] = ""

    #
    Profielpunten_table = Profielpunten.reset_index()
    Profielpunten_table.columns = ['objectid', 'pbp_id', 'prw_id', 'pbpident', 'osmomsch', 'iws_volgnr',
                                   'iws_hoogte', 'pro_pro_id', 'geometry']
    ## zonder geo
    Kenmerken_table = pd.DataFrame(Kenmerken[['ID', 'DIEPTE', 'BRON_DIEPTE', 'BODEMHOOGTE', 'BREEDTE',
                                              'BRON_BREEDTE', 'LENGTE', 'TALUDVOORKEUR', 'STEILSTE_TALUD',
                                              'GRONDSOORT', 'BRON_GRONDSOORT', 'HYDRO_ID']])
    Kenmerken_table = Kenmerken_table.reset_index()
    Kenmerken_table.columns = ['objectid', 'id', 'diepte', 'bron_diepte', 'bodemhoogte', 'breedte',
                               'bron_breedte', 'lengte', 'taludvoorkeur', 'steilste_talud',
                               'grondsoort', 'bron_grondsoort', 'hydro_id']

    Profielen_table = pd.DataFrame(Profielen[['ID', 'PROIDENT', 'BRON_PROFIEL', 'PRO_ID', 'HYDRO_ID']])
    Profielen_table = Profielen_table.reset_index()
    Profielen_table.columns = ['objectid', 'id', 'proident', 'bron_profiel', 'pro_id', 'hydro_id']

    ## Stap 4: write dataframes to leggerdatabase
    db.create_and_check_fields()

    session = db.get_session()
    hydroobject = []
    for i, rows in HydroObject_table.iterrows():
        hydroobject.append(SqlHydroObject(
            objectid=nonint(HydroObject_table.objectid[i]),
            id=nonint(HydroObject_table.id[i]),
            code=HydroObject_table.code[i],
            categorieoppwaterlichaam=nonint(HydroObject_table.categorieoppwaterlichaam[i]),
            streefpeil=nonfloat(HydroObject_table.streefpeil[i]),
            # debiet=HydroObject_table.debiet[i],
            # channel_id=HydroObject_table.channel_id[i],
            # flowline_id=HydroObject_table.flowline_id[i],
            geometry=nonwkt(HydroObject_table.geometry[i])
        ))

    session.execute("Delete from {0}".format(SqlHydroObject.__tablename__))
    session.bulk_save_objects(hydroobject)
    session.commit()

    session = db.get_session()
    waterdeel = []
    for i, rows in Waterdeel_table.iterrows():
        waterdeel.append(SqlWaterdeel(
            objectid=nonint(Waterdeel_table.objectid[i]),
            id=nonint(Waterdeel_table.id[i]),
            shape_length=nonfloat(Waterdeel_table.shape_length[i]),
            shape_area=nonfloat(Waterdeel_table.shape_area[i]),
            geometry=nonwkt(Waterdeel_table.geometry[i])
        ))

    session.execute("Delete from {0}".format(SqlWaterdeel.__tablename__))
    session.bulk_save_objects(waterdeel)
    session.commit()

    session = db.get_session()
    duikersifonhevel = []
    for i, rows in DuikerSifonHevel_table.iterrows():
        duikersifonhevel.append(SqlDuikerSifonHevel(
            objectid=nonint(DuikerSifonHevel_table.objectid[i]),
            id=nonint(DuikerSifonHevel_table.id[i]),
            code=DuikerSifonHevel_table.code[i],
            categorie=nonint(DuikerSifonHevel_table.categorie[i]),
            lengte=DuikerSifonHevel_table.lengte[i],
            hoogteopening=DuikerSifonHevel_table.hoogteopening[i],
            breedteopening=DuikerSifonHevel_table.breedteopening[i],
            hoogtebinnenonderkantbene=DuikerSifonHevel_table.hoogtebinnenonderkantbene[i],
            hoogtebinnenonderkantbov=DuikerSifonHevel_table.hoogtebinnenonderkantbov[i],
            vormkoker=DuikerSifonHevel_table.vormkoker[i],
            debiet=DuikerSifonHevel_table.debiet[i],
            channel_id=DuikerSifonHevel_table.channel_id[i],
            flowline_id=DuikerSifonHevel_table.flowline_id[i],
            geometry=nonwkt(DuikerSifonHevel_table.geometry[i])
        ))

    session.execute("Delete from {0}".format(SqlDuikerSifonHevel.__tablename__))
    session.bulk_save_objects(duikersifonhevel)
    session.commit()

    session = db.get_session()
    profielpunten = []
    for i, rows in Profielpunten_table.iterrows():
        profielpunten.append(SqlProfielpunten(
            objectid=nonint(Profielpunten_table.objectid[i]),
            pbp_id=nonint(Profielpunten_table.pbp_id[i]),
            prw_id=nonint(Profielpunten_table.prw_id[i]),
            pbpident=Profielpunten_table.pbpident[i],
            osmomsch=Profielpunten_table.osmomsch[i],
            iws_volgnr=nonint(Profielpunten_table.iws_volgnr[i]),
            iws_hoogte=Profielpunten_table.iws_hoogte[i],
            pro_pro_id=nonint(Profielpunten_table.pro_pro_id[i]),
            geometry=nonwkt(Profielpunten_table.geometry[i])
        ))

    session.execute("Delete from {0}".format(SqlProfielpunten.__tablename__))
    session.bulk_save_objects(profielpunten)
    session.commit()

    session = db.get_session()
    kenmerken = []
    for i, rows in Kenmerken_table.iterrows():
        kenmerken.append(SqlKenmerken(
            objectid=nonint(Kenmerken_table.objectid[i]),
            id=nonint(Kenmerken_table.id[i]),
            diepte=nonfloat(Kenmerken_table.diepte[i]),
            bron_diepte=Kenmerken_table.bron_diepte[i],
            bodemhoogte=nonfloat(Kenmerken_table.bodemhoogte[i]),
            breedte=nonfloat(Kenmerken_table.breedte[i]),
            bron_breedte=Kenmerken_table.bron_breedte[i],
            lengte=nonfloat(Kenmerken_table.lengte[i]),
            taludvoorkeur=nonfloat(Kenmerken_table.taludvoorkeur[i]),
            steilste_talud=nonfloat(Kenmerken_table.steilste_talud[i]),
            grondsoort=Kenmerken_table.grondsoort[i],
            bron_grondsoort=Kenmerken_table.bron_grondsoort[i],
            hydro_id=nonint(Kenmerken_table.hydro_id[i])
        ))

    session.execute("Delete from {0}".format(SqlKenmerken.__tablename__))
    session.bulk_save_objects(kenmerken)
    session.commit()

    session = db.get_session()
    profielen = []
    for i, rows in Profielen_table.iterrows():
        profielen.append(SqlProfielen(
            objectid=nonint(Profielen_table.objectid[i]),
            id=nonint(Profielen_table.id[i]),
            proident=Profielen_table.proident[i],
            bron_profiel=Profielen_table.bron_profiel[i],
            pro_id=nonint(Profielen_table.pro_id[i]),
            hydro_id=nonint(Profielen_table.hydro_id[i])
        ))

    session.execute("Delete from {0}".format(SqlProfielen.__tablename__))
    session.bulk_save_objects(profielen)
    session.commit()
    return

def main():
    try:
        init_path = os.path.expanduser("~") # get path to respectively "user" folder
        init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger/tests/data"))
    except TypeError:
        init_path = os.path.expanduser("~")

    filename = "test_ " +str(datetime.datetime.today().strftime('%Y%m%d') ) +".sqlite"
    database_path = os.path.abspath(os.path.join(init_path, filename))

    filepath_DAMO = r'C:\Users\basti\.qgis2\python\plugins\legger\tests\data\Hoekje_leggertool_database.gdb'
    filepath_HDB = r'C:\Users\basti\.qgis2\python\plugins\legger\tests\data\Hoekje_leggertool_HDB.gdb'

    create_spatialite_database(
        filepath_DAMO,
        filepath_HDB,
        database_path
    )

if __name__ == '__main__':
    main()
