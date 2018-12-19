# -*- coding: utf-8 -*-
from __future__ import division

import logging
import os
import urllib2
import geopandas as gpd
import pandas as pd
import fiona

from PyQt4.QtCore import pyqtSignal, QSettings, QModelIndex, QThread
from PyQt4.QtGui import QWidget, QFileDialog, QComboBox
from PyQt4 import QtCore, QtGui
log = logging.getLogger(__name__)
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column,  Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import ogr

from legger.sql_models.legger import HydroObject, Waterdeel, DuikerSifonHevel
from legger.sql_models.legger import Kenmerken, Profielen, Profielpunten
from legger.sql_models.legger_database import LeggerDatabase

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class PolderSelectionWidget(QWidget):#, FORM_CLASS):
    """Dialog for selecting model (spatialite and result files netCDFs)"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, parent_class, root_tool):
        """Constructor

        :parent: Qt parent Widget
        :iface: QGiS interface
        :polder_datasource: Polder spatialite instance
        :parent_class: the tool class which instantiated this widget. Is used
             here for storing volatile information
        """
        super(PolderSelectionWidget, self).__init__(parent)

        self.parent_class = parent_class
        self.iface = iface
        self.setup_ui()

        self.root_tool = root_tool  # "root tool meegeven aan nieuw scherm. Verwijzing naar een class, i.p.v. een nieuwe variabele"

        self.var_text_DAMO.setText("...")
        self.var_text_HDB.setText("...")
        self.var_text_leggerdatabase.setText(self.root_tool.polder_datasource) # De tekst verwijst naar de tekst in de root_tool totdat deze geupdated wordt.

    def closeEvent(self, event):
        """

        :return:
        """
        self.closingDialog.emit()
        self.close()
        event.accept()


    def select_DAMO(self):
        """
        Select a dump or export of the DAMO database (.gdb)

        :return:
        """
        # saves last opened datadump path
        settings = QSettings('last_used_DAMO_path','filepath')

        # set initial path to right folder
        try:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder
        except TypeError:
            init_path = os.path.expanduser("~")

        DAMO_datasource = QFileDialog.getExistingDirectory(
            self,
            'Open Directory',
            init_path
        )

        self.var_text_DAMO.setText(DAMO_datasource)
        settings.setValue('last_used_DAMO_path',
                          os.path.dirname(
                              DAMO_datasource))  # verwijzing naar de class.variable in het hoofdscherm
        return

    def select_HDB(self):
        """
        Select a dump or export of the HDB (Dutch: Hydrologen database) (.gdb)

        :return:
        """
        # saves last opened datadump path
        settings = QSettings('last_used_HDB_path','filepath')

        # set initial path to right folder
        try:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder
        except TypeError:
            init_path = os.path.expanduser("~")

        HDB_datasource = QFileDialog.getExistingDirectory(
            self,
            'Open Directory',
            init_path
        )

        self.var_text_HDB.setText(HDB_datasource)
        settings.setValue('last_used_HDB_path',
                          os.path.dirname(
                              HDB_datasource))  # verwijzing naar de class.variable in het hoofdscherm
        return

    def create_spatialite_database(self):
        """
        Select a "dump" or "export" that is send to the N&S datachecker to create a spatialite database based on this.
        The output of this step is a legger_{polder}_{datetime}.sqlite file with all the necessary tables and data.
        Step 1: make empty legger database
        Step 2: Read DAMO and HDB (geopandas)
        Step 3: make dataframes from data according to right format
        Step 4: write dataframes to legger database (sqlalchemy)
        """

        try:
            init_path = os.path.expanduser("~") # get path to respectively "user" folder
            init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger/tests/data"))
        except TypeError:
            init_path = os.path.expanduser("~")

        filename = "test_"+str(datetime.datetime.today().strftime('%Y%m%d'))+".sqlite"
        database_path = os.path.abspath(os.path.join(init_path,filename))

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

        ## Saves the database path so it can be used in the calculation screen
        settings = QSettings('last_used_legger_spatialite_path', 'filepath')
        self.root_tool.polder_datasource=database_path
        self.var_text_leggerdatabase.setText(self.root_tool.polder_datasource)

        if self.root_tool.polder_datasource == "":
            return False

        settings.setValue('last_used_legger_spatialite_path',
                          os.path.dirname(self.root_tool.polder_datasource)) # verwijzing naar de class.variable in het hoofdscherm


        ## Step 2: Read databases
        ## Read DAMO.gdb
        filepath_DAMO = self.var_text_DAMO.text()
        # list_of_layers = fiona.listlayers(filepath_DAMO)
        # 'DuikerSifonHevel', 'Profielen', 'Waterdeel', 'Profielpunten', 'HydroObject', 'Kenmerken'

        DuikerSifonHevel = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='DuikerSifonHevel')
        Profielen = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Profielen')
        Waterdeel = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Waterdeel')
        Profielpunten = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Profielpunten')
        HydroObject = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='HydroObject')
        Kenmerken = gdp.read_file(filepath_DAMO, driver='OpenFileGDB', layer='Kenmerken')

        ## inlezen HDB.gdp
        filepath_HDB = self.var_text_HDB.text()
        # list_of_layers = fiona.listlayers(filepath_HDB)
        # 'vaste_dammen', 'polderclusters', 'Sturing_3Di', 'gemalen_op_peilgrens', 'duikers_op_peilgrens',
        # 'stuwen_op_peilgrens', 'hydro_deelgebieden'

        # vaste_dammen = gdp.read_file(filepath_HDB,driver='OpenFileGDB',layer='vaste_dammen')
        # doet het niet
        polderclusters = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='polderclusters')
        Sturing_3di = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='Sturing_3di')
        gemalen_op_peilgrens = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='gemalen_op_peilgrens')
        duikers_op_peilgrens = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='duikers_op_peilgrens')
        stuwen_op_peilgrens = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='stuwen_op_peilgrens')
        hydro_deelgebieden = gdp.read_file(filepath_HDB, driver='OpenFileGDB', layer='hydro_deelgebieden')

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
            hydroobject.append(HydroObject(
                objectid=HydroObject_table.object_id[i],
                id=HydroObject_table.id[i],
                code=HydroObject_table.code[i],
                categorieoppwaterlichaam=HydroObject_table.categorieoppwaterlichaam[i],
                streefpeil=HydroObject_table.streefpeil[i],
                debiet=HydroObject_table.debiet[i],
                channel_id=HydroObject_table.channel_id[i],
                flowline_id=HydroObject_table.flowline_id[i],
                geometry=HydroObject_table.geometry[i]
            ))

        session.execute("Delete from {0}".format(HydroObject.__tablename__))
        session.bulk_save_objects(hydroobject)
        session.commit()

        session = db.get_session()
        waterdeel = []
        for i, rows in Waterdeel_table.iterrows():
            waterdeel.append(Waterdeel(
                obejctid=Waterdeel_table.objectid[i],
                id=Waterdeel_table.id[i],
                shape_length=Waterdeel_table.shape_length[i],
                shape_area=Waterdeel_table.shape_area[i],
                geometry=Waterdeel_table.geometry[i]
            ))

        session.execute("Delete from {0}".format(Waterdeel.__tablename__))
        session.bulk_save_objects(waterdeel)
        session.commit()

        session = db.get_session()
        duikersifonhevel = []
        for i, rows in DuikerSifonHevel_table.iterrows():
            duikersifonhevel.append(DuikerSifonHevel(
                objectid=DuikerSifonHevel_table.objectid[i],
                id=DuikerSifonHevel_table.id[i],
                code=DuikerSifonHevel_table.code[i],
                categorie=DuikerSifonHevel_table.categorie[i],
                lengte=DuikerSifonHevel_table.lengte[i],
                hoogteopening=DuikerSifonHevel_table.hoogteopening[i],
                breedteopening=DuikerSifonHevel_table.breedteopening[i],
                hoogtebinnenonderkantbene=DuikerSifonHevel_table.hoogtebinnenonderkantbene[i],
                hoogtebinnenonderkantbov=DuikerSifonHevel_table.hoogtebinnenonderkantbov[i],
                vormkoker=DuikerSifonHevel_table.vormkoker[i],
                debiet=DuikerSifonHevel_table.debiet[i],
                channel_id=DuikerSifonHevel_table.channel_id[i],
                flowline_id=DuikerSifonHevel_table.flowline_id[i],
                geometry=DuikerSifonHevel_table.geometry[i]
            ))

        session.execute("Delete from {0}".format(DuikerSifonHevel.__tablename__))
        session.bulk_save_objects(duikersifonhevel)
        session.commit()

        session = db.get_session()
        profielpunten = []
        for i, rows in Profielpunten_table.iterrows():
            profielpunten.append(Profielpunten(
                objectid=Profielpunten_table.objectid[i],
                pbp_id=Profielpunten_table.pbp_id[i],
                prw_id=Profielpunten_table.prw_id[i],
                pbpident=Profielpunten_table.pbpident[i],
                osmomsch=Profielpunten_table.osmomsch[i],
                iws_volgnr=Profielpunten_table.iws_volgnr[i],
                iws_hoogte=Profielpunten_table.iws_hoogte[i],
                pro_pro_id=Profielpunten_table.pro_pro_id[i],
                geometry=Profielpunten_table.geometry[i]
            ))

        session.execute("Delete from {0}".format(Profielpunten.__tablename__))
        session.bulk_save_objects(profielpunten)
        session.commit()

        session = db.get_session()
        kenmerken = []
        for i, rows in Kenmerken_table.iterrows():
            kenmerken.append(Kenmerken(
                objectid=Kenmerken_table.objectid[i],
                id=Kenmerken_table.id[i],
                diepte=Kenmerken_table.diepte[i],
                bron_diepte=Kenmerken_table.bron_diepte[i],
                bodemhoogte=Kenmerken_table.bodemhoogte[i],
                breedte=Kenmerken_table.breedte[i],
                bron_breedte=Kenmerken_table.bron_breedte[i],
                lengte=Kenmerken_table.lengte[i],
                breedte=Kenmerken_table.breedte[i],
                taludvoorkeur=Kenmerken_table.taludvoorkeur[i],
                steilste_talud=Kenmerken_table.steilste_talud[i],
                grondsoort=Kenmerken_table.grondsoort[i],
                bron_grondsoort=Kenmerken_table.bron_grondsoort[i],
                hydro_id=Kenmerken_table.hydro_id[i]
            ))

        session.execute("Delete from {0}".format(Kenmerken.__tablename__))
        session.bulk_save_objects(kenmerken)
        session.commit()

        session = db.get_session()
        profielen = []
        for i, rows in Profielen_table.iterrows():
            profielen.append(Profielen(
                obejctid=Profielen_table.objectid[i],
                id=Profielen_table.id[i],
                proident=Profielen_table.proident[i],
                bron_profiel=Profielen_table.bron_profiel[i],
                pro_id=Profielen_table.pro_id[i],
                hydro_id=Profielen_table.hydro_id[i]
            ))

        session.execute("Delete from {0}".format(Profielen.__tablename__))
        session.bulk_save_objects(profielen)
        session.commit()
        return

    def select_spatialite(self):
        """
        Open file dialog on click on button 'load
        :return: Boolean, if file is selected
        """

        # saves the last opened path
        settings = QSettings('last_used_legger_spatialite_path', 'filepath')

        # set initial path to right folder
        try:
            init_path = os.path.expanduser("~") # get path to respectively "user" folder
            init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger/tests/data"))
        except TypeError:
            init_path = os.path.expanduser("~")

        self.root_tool.polder_datasource = QFileDialog.getOpenFileName(
            self,
            'Open File',
            init_path,
            'Spatialite (*.sqlite)'
        )

        self.var_text_leggerdatabase.setText(self.root_tool.polder_datasource)
        if self.root_tool.polder_datasource == "":
            return False

        settings.setValue('last_used_legger_spatialite_path',
                          os.path.dirname(self.root_tool.polder_datasource)) # verwijzing naar de class.variable in het hoofdscherm
        return

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.maak_leggerdatabase_row = QtGui.QVBoxLayout()
        self.maak_leggerdatabase_row.setObjectName(_fromUtf8("Maak leggerdatabase row"))
        self.kies_leggerdatabase_row = QtGui.QVBoxLayout()
        self.kies_leggerdatabase_row.setObjectName(_fromUtf8("Kies leggerdatabase row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))

        ## connect signals
        ## select input files for the creation of legger database
        self.load_DAMO_dump_button = QtGui.QPushButton(self)
        self.load_DAMO_dump_button.setObjectName(_fromUtf8("Load DAMO"))
        self.load_DAMO_dump_button.clicked.connect(self.select_DAMO)

        self.load_HDB_dump_button = QtGui.QPushButton(self)
        self.load_HDB_dump_button.setObjectName(_fromUtf8("Load HDB"))
        self.load_HDB_dump_button.clicked.connect(self.select_HDB)

        ## make database routine
        self.create_leggerdatabase_button = QtGui.QPushButton(self)
        self.create_leggerdatabase_button.setObjectName(_fromUtf8("Create database"))
        self.create_leggerdatabase_button.clicked.connect(self.create_spatialite_database)

        ## select legger database
        self.load_leggerdatabase_button = QtGui.QPushButton(self)
        self.load_leggerdatabase_button.setObjectName(_fromUtf8("Load"))
        self.load_leggerdatabase_button.clicked.connect(self.select_spatialite)

        ## close screen
        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Close"))
        self.cancel_button.clicked.connect(self.close)
        self.bottom_row.addWidget(self.cancel_button)

        # Feedback what document is chosen
        self.var_text_DAMO = QtGui.QLineEdit(self)
        self.var_text_DAMO.setText("leeg")

        self.var_text_HDB = QtGui.QLineEdit(self)
        self.var_text_HDB.setText("leeg")

        self.var_text_leggerdatabase = QtGui.QLineEdit(self)
        self.var_text_leggerdatabase.setText("leeg")

        ## Assembling
        ## Create buttons with functions to select damo and hdb and database creation and add it to rows
        self.box_leggerdatabase_create = QtGui.QVBoxLayout()
        self.box_leggerdatabase_create.addWidget(self.load_DAMO_dump_button)
        self.box_leggerdatabase_create.addWidget(self.load_HDB_dump_button)
        self.box_leggerdatabase_create.addWidget(self.var_text_DAMO)
        self.box_leggerdatabase_create.addWidget(self.var_text_HDB)

        self.feedback_box_leggerdatabase_create = QtGui.QVBoxLayout()

        self.box_leggerdatabase_input = QtGui.QVBoxLayout()
        self.box_leggerdatabase_input.addWidget(self.create_leggerdatabase_button)
        self.box_leggerdatabase_input.addWidget(self.load_leggerdatabase_button)

        self.feedback_box_leggerdatabase_select = QtGui.QVBoxLayout()
        self.feedback_box_leggerdatabase_select.addWidget(self.var_text_leggerdatabase)

        ## Create groupbox and add HBoxes to it
        self.groupBox_leggerdatabase_create = QtGui.QGroupBox(self)
        self.groupBox_leggerdatabase_create.setTitle("Selecteer bestanden voor legger database:")
        self.groupBox_leggerdatabase_create.setLayout(self.box_leggerdatabase_create)

        self.groupBox_leggerdatabase_input = QtGui.QGroupBox(self)
        self.groupBox_leggerdatabase_input.setTitle("Database legger:")
        self.groupBox_leggerdatabase_input.setLayout(self.box_leggerdatabase_input)

        ## Add groupbox to row
        self.maak_leggerdatabase_row.addWidget(self.groupBox_leggerdatabase_create)
        self.maak_leggerdatabase_row.addLayout(self.feedback_box_leggerdatabase_create)

        self.kies_leggerdatabase_row.addWidget(self.groupBox_leggerdatabase_input)
        self.kies_leggerdatabase_row.addLayout(self.feedback_box_leggerdatabase_select)

        ## Add row to ui
        self.verticalLayout.addLayout(self.maak_leggerdatabase_row)
        self.verticalLayout.addLayout(self.kies_leggerdatabase_row)
        self.verticalLayout.addLayout(self.bottom_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Maak en/of Selecteer de database van de Polder", None))
        self.load_DAMO_dump_button.setText(_translate("Dialog", "Load DAMO", None))
        self.load_HDB_dump_button.setText(_translate("Dialog", "Load HDB", None))
        self.create_leggerdatabase_button.setText(_translate("Dialog", "Create database", None))
        self.load_leggerdatabase_button.setText(_translate("Dialog", "Load leggerdatabase", None))
        self.cancel_button.setText(_translate("Dialog", "Close", None))

