
# coding: utf-8

# In[239]:


import sys
import datetime
import os.path

# import fiona laten staan, anders worden er problemen gemeld met het laden van dll's
import fiona
import numpy as np
import pandas as pd
import geopandas as gpd

"""
weggooien

from leggertool.legger_sql_model import HydroObject as SqlHydroObject
from leggertool.legger_sql_model import Waterdeel as SqlWaterdeel, DuikerSifonHevel as SqlDuikerSifonHevel
from leggertool.legger_sql_model import Kenmerken as SqlKenmerken, Profielen as SqlProfielen, Profielpunten as SqlProfielpunten
from leggertool.legger_database import LeggerDatabase
"""


# In[12]:


def create_spatialite_database(filepath_DAMO, filepath_HDB, database_path):
    """
    Select "dump" or "export" .gdb files that come from DAMO and HDB
    This should be similar to the export that is send to the N&S datachecker and modelbuilder for this model revision.

    The output of this step is a legger_{polder}_{datetime}.sqlite file with all the necessary tables and data.
    Step 1: make empty legger database
    Step 2: Read DAMO and HDB (geopandas)
    Step 3: make dataframes from data according to right format
    Step 4: write dataframes to legger database (sqlalchemy)
    """
    
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


# In[18]:


## Step 1

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
try:
    #init_path = os.path.expanduser("~") # get path to respectively "user" folder
    init_path = os.path.abspath("../17.Mijzenpolder")
except TypeError:
    init_path = os.path.expanduser("~")
    

filepath_DAMO = init_path+"/01. DAMO HDB en Datachecker/DAMO.gdb"
filepath_HDB = init_path+"/01. DAMO HDB en Datachecker/HDB.gdb"

filename = "99. Extra Analyses/test_ " +str(datetime.datetime.today().strftime('%Y%m%d') ) +".sqlite"
database_path = os.path.abspath(os.path.join(init_path, filename))

create_spatialite_database(
    filepath_DAMO,
    filepath_HDB,
    database_path
)


# In[247]:


## Step 2

## Step 2: Read databases
## Read DAMO.gdb
# list_of_layers = fiona.listlayers(filepath_DAMO)
# 'DuikerSifonHevel', 'Profielen', 'Waterdeel', 'Profielpunten', 'HydroObject', 'Kenmerken'

## Kant en klaar
DuikerSifonHevel = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='DuikerSifonHevel')
Waterdeel = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Waterdeel')

## hydroobject en kenmerken
HydroObject = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='HydroObject')
PeilafwijkingGebied=gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='PeilafwijkingGebied')
PeilgebiedPraktijk=gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='PeilgebiedPraktijk')

## profielen en profielpunten
GW_PRO = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='GW_PRO')  # lijnelementen
GW_PRW = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='GW_PRW') # Z1 en Z2 verdeling
GW_PBP = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='GW_PBP') # Puntendatabase
IWS_GEO_BESCHR_PROFIELPUNTEN = gpd.read_file(filepath_DAMO, driver='OpenFileGDB', layer='IWS_GEO_BESCHR_PROFIELPUNTEN') 
#geo van punten

## HDB (nog ongebruikt maar goed om er nu even bij te zetten)
polderclusters = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='polderclusters')
Sturing_3di = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='Sturing_3di')
gemalen_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='gemalen_op_peilgrens')
duikers_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='duikers_op_peilgrens')
stuwen_op_peilgrens = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='stuwen_op_peilgrens')
hydro_deelgebieden = gpd.read_file(filepath_HDB, driver='OpenFileGDB', layer='hydro_deelgebieden')


# In[306]:


#fiona.listlayers(filepath_DAMO)


# In[117]:


def maak_tabel_profielpunten(gw_prw,gw_pbp,profielpunten):
    
    ## Drop geometry die is toch leeg
    gw_prw=gw_prw.drop(['geometry'],axis=1)
    gw_pbp=gw_pbp.drop(['geometry'],axis=1)
    
    ## Merge de geometrie (profielpunten) aan de database van profielpunten (gw_pbp)
    df1 = pd.merge(gw_pbp,
         profielpunten,
         how='inner',
         left_on='PBP_ID',
         right_on='PBP_PBP_ID')
    
    ## Merge de database van profielpunten aan de database die zegt of het Z1/Z2 (OSMOMSCH) is 
    ## aan welke dwarsdoorsnede hij refereert (PRO_ID)
    df2 = pd.merge(df1,gw_prw,how='inner',left_on='PRW_PRW_ID',right_on='PRW_ID')
    
    ## Voeg volgnummer objectid toe
    df2['objectid']=np.arange(len(df2))
    
    ## Filter kolommen
    df3=df2[['objectid','PBP_ID','PRW_ID','PBPIDENT','OSMOMSCH','IWS_VOLGNR','IWS_HOOGTE','IWS_AFSTAND','PRO_PRO_ID','geometry']]
    
    ## Hernoem kolommen
    df3.columns=['objectid','pbp_id','prw_id','pbpident','osmomsch','iws_volgnr','iws_hoogte','iws_afstand','pro_pro_id','geometry']
    
    return(df3)


# In[172]:


def maak_tabel_profielen(gw_pro,hydroobject):
    """
    Deze formule maakt van twee DAMO tabellen een tabel nodig voor de leggertool.
    De 'profielen' tabel van de leggertool bevat de locaties van de profielen, de ids en ook in welk hydrovak ze liggen
    
    
    Extra:
    Hele snelle plot maken
    geometry=GW_PRO.geometry
    gdf=gpd.GeoDataFrame(GW_PRO,crs=28992,geometry=geometry)

    gdf.plot()
    plt.show()
    """
    
    ## maak een spatial join waarbij de hydroobjecten aan de profielen worden gekoppeld
    df1=gpd.sjoin(gw_pro,hydroobject,how='inner',op='intersects')
    
    ## Filter op betrouwbaarheid
    df1=df1[df1['Betrouwbaar']=='1']
    
    ## Selecteer alleen de nodige kolommen, kies voor de shape length van de profielen (niet de hydroobjecten)
    df2=df1[['PROIDENT','OSMOMSCH','PRO_ID','HydroObject_ID','SHAPE_Length_left','geometry']]
    
    ## Volgnummers objectid en id
    df2['objectid'] = np.arange(len(df2))
    df2['id']=df2['objectid']+1
    
    ## Herorganiseer en hernoem kolommen
    df3=df2[['objectid','id','PROIDENT','OSMOMSCH','PRO_ID','HydroObject_ID','SHAPE_Length_left','geometry']]
    df3.columns=['objectid','id','proident','bron_profiel','pro_id','hydro_id','shape_length','geometry']
    
    return(df3)


# In[237]:


def maak_tabel_kenmerken(hydroobject):
    """
    Maakt een tabel met alle atrributen kenmerken per hydroobject
    """
    df1=hydroobject
    
    ## Bereken steilste talud
    df1.loc[:,'steilste_talud']=df1[['WS_TALUD_LINKS', 'WS_TALUD_RECHTS']].min(axis=1)

    ## Bepaal diepte
    df1.loc[:,'diepte']=df1['hoogte_getabuleerd'].str.split(expand=True)[1]
    
    ## Waterbreedte
    df1.loc[:,'waterbreedte']=df1['breedte_getabuleerd'].str.split(expand=True)[1]
    ## Bodembreedte 
    df1.loc[:,'bodembreedte']=df1['breedte_getabuleerd'].str.split(expand=True)[0]
    
    ## Bronnen toevoegen
    df1.loc[:,'bron_diepte']=df1['keuze_profiel']
    df1.loc[:,'bron_breedte']=df1['keuze_profiel']
    
    ## id = kopie hydroobjectid
    df1.loc[:,'id']=df1['HydroObject_ID']
    
    ## Voeg objectid volgnummer toe
    df1.loc[:,'objectid']=np.arange(len(df1))
    
    ## nog lege kolommen
    df1.loc[:,'taludvoorkeur']="" # zou gekozen moeten worden of op basis van grondsoort
    df1.loc[:,'grondsoort']="" # zou met behulp van de BGT kunnen --> maar is het echt nodig?
    df1.loc[:,'bron_grondsoort']=""
    
    ## Selecteer de juiste kolommen
    df2 = df1[['objectid',
           'id',
           'diepte',
           'bron_diepte',
           'bodemhoogte_NAP',
           'waterbreedte',
           'bodembreedte',
           'bron_breedte',
           'SHAPE_Length',
           'taludvoorkeur',
           'steilste_talud',
           'grondsoort',
           'bron_grondsoort',
           'HydroObject_ID',
           'geometry']]
    
    ## Hernoem de kolommen waar nodig
    df2.columns=['objectid',
           'id',
           'diepte',
           'bron_diepte',
           'bodemhoogte',
           'waterbreedte',
           'bodembreedte',
           'bron_breedte',
           'lengte',
           'taludvoorkeur',
           'steilste_talud',
           'grondsoort',
           'bron_grondsoort',
           'hydro_id',
           'geometry']
    
    return(df2)


# In[303]:


def maak_tabel_hydroobject(hydroobject,peilgebiedpraktijk,peilafwijkinggebied):
    
    ## Eerst een join met peilgebieden om de eerste streefpeilen te koppelen aan de hydroobjecten
    df1=gpd.sjoin(hydroobject,peilgebiedpraktijk[['NAAM','PEIL_WSA','geometry']],how='inner',op='intersects')
    df1.loc[:,'streefpeil']=df1['PEIL_WSA']
    
    ## Scheidt de tabellen weer door te filteren op kolommen
    df2=df1[['HydroObject_ID','CODE','CATEGORIEOPPWATERLICHAAM','streefpeil','SHAPE_Length','geometry']]
    
    ## Tweede join met peilafwijkingen om de eerdere peilen te overschrijven
    ## Hou rekening met een andere join, ook de hydroobjecten houden die niet in een peilafwijking liggen
    df3=gpd.sjoin(df2,PeilafwijkingGebied[['PEIL_WSA','geometry']],how='left',op='intersects')
    
    ## Filter op index waarbij alleen de streefpeilen worden overschreven waarbij de PEIL_WSA 'niet nul' is. 
    ## Anders worden de streefpeilen van hydro-objecten die buiten een peilafwijking vallen overschreven
    df4=df3
    df4.loc[df3[df3['PEIL_WSA'].notnull()].index,'streefpeil']=df3[df3['PEIL_WSA'].notnull()]['PEIL_WSA']
    
    ## Toevoegen de overige kolommen
    df4.loc[:,'objectid']=np.arange(len(df4))
    df4.loc[:,'id']=df4['HydroObject_ID']
    df4.loc[:,'debiet']=""
    df4.loc[:,'channel_id']=""
    df4.loc[:,'flowline_id']=""

    ## Filter op kolommen en geef een volgorde mee
    df4=df4[['objectid','id','CODE','CATEGORIEOPPWATERLICHAAM','streefpeil','debiet','channel_id','flowline_id','SHAPE_Length']]
    df4.columns=['objectid','id','code','categorieoppwaterlichaam','streefpeil','debiet','channel_id','flowline_id','shape_len']
    
    return(df4)


# In[ ]:


profielpunten_tabel=maak_tabel_profielpunten(GW_PRW,GW_PBP,IWS_GEO_BESCHR_PROFIELPUNTEN)


# In[173]:


profielen_tabel=maak_tabel_profielen(GW_PRO,HydroObject)


# In[242]:


kenmerken_tabel=maak_tabel_kenmerken(HydroObject)


# In[304]:


hydroobject_tabel=maak_tabel_hydroobject(HydroObject,PeilgebiedPraktijk,PeilafwijkingGebied)


# In[ ]:


## Stap 3: De overige tabellen die eigenlijk alleen gemodificeerd hoeven te worden
# (Een deel van de modificatie vindt al plaats in stap 2)

#
waterdeel_tabel = pd.DataFrame(Waterdeel[['ID', 'SHAPE_Length', 'SHAPE_Area', 'geometry']])
waterdeel_tabel = waterdeel_tabel.reset_index()
waterdeel_tabel.columns = ['objectid', 'id', 'shape_length', 'shape_area', 'geometry']

#
duikersifonhevel_tabel = pd.DataFrame(DuikerSifonHevel[['ID', 'CODE', 'CATEGORIE', 'LENGTE', 'HOOGTEOPENING',
                                                        'BREEDTEOPENING', 'HOOGTEBINNENONDERKANTBENE',
                                                        'HOOGTEBINNENONDERKANTBOV', 'VORMKOKER', 'DEBIET',
                                                        'geometry']])
duikersifonhevel_tabel = DuikerSifonHevel_table.reset_index()
duikersifonhevel_tabel.columns = ['objectid', 'id', 'code', 'categorie', 'lengte', 'hoogteopening',
                                  'breedteopening',
                                  'hoogtebinnenonderkantbene', 'hoogtebinnenonderkantbov', 'vormkoker',
                                  'debiet',
                                  'geometry']
duikersifonhevel_tabel.loc[:,'channel_id'] = ""
duikersifonhevel_tabel[:,'flowline_id'] = ""


# In[ ]:


### Volgende activiteiten:
## stap 1: aanmaken lege sqlite met de juiste tabellen en de juiste kolommen in tabellen lukt niet in mijn testomgeving. 
## Dit moet Bastiaan doen vanwege de testomgeving --> TODO

## Stap 2:
# Laad data uit DAMO en HDB en maak 'tabellen' van data die in de leggerdatabase moet --> GEDAAN


## Stap 3: als de data verzamelt is, dan moet deze zo omgeschreven (denk aan tabelnamen, kolomnamen, etc)
## opdat de data en de vorm matcht met wat in de leggersqlite verwacht wordt: schrijf de dataframes om --> GEDAAN

## Stap 4 todo:
# Schrijf de data met sqlalchemy weg in de sqlite 
## Met of door Bastiaan laten doen -- TODO


# In[11]:


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

