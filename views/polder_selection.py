# -*- coding: utf-8 -*-
from __future__ import division

import logging
import os
import urllib2


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
        """

        try:
            init_path = os.path.expanduser("~") # get path to respectively "user" folder
            init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger/tests/data"))
        except TypeError:
            init_path = os.path.expanduser("~")

        filename = "test_"+str(datetime.datetime.today().strftime('%Y%m%d'))+".sqlite"
        database_path = os.path.join(init_path,filename)

        if os.path.exists(database_path):
            os.remove(database_path)

        drv = ogr.GetDriverByName('SQLite')
        db = drv.CreateDataSource(database_path, ["SPATIALITE=YES"])

        engine = create_engine(str('sqlite:///')+str(database_path))

        Base = declarative_base()
        class Waterdeel(Base):
            __tablename__ = 'waterdeel'
            extend_existing = True

            objectid = Column(Integer)
            id = Column(Integer, primary_key=True)
            shape_length = Column(Float)
            shape_area = Column(Float)
            #geometry = Column("GEOMETRY", Geometry(geometry_type='POLYGON', srid=28992))

            def __str__(self):
                return u'Waterdeel {0}'.format(
                    self.id)

        class HydroObject(Base):
            __tablename__ = 'hydroobject'
            extend_existing = True

            objectid = Column(Integer)
            id = Column(Integer, primary_key=True)
            #geometry = Column("GEOMETRY", Geometry(geometry_type='LINESTRING', srid=28992))
            code = Column(String(50), index=True)
            categorieoppwaterlichaam = Column(Integer)
            streefpeil = Column(Float)
            debiet = Column(Float)
            channnel_id = Column(Integer)  # link to 3di id
            flowline_id = Column(Integer)  # link to 3di id
            # shape_length = Column(Float)

            def __str__(self):
                return u'Hydro object {0}'.format(
                    self.code)

        class Profielen(Base):
            __tablename__ = 'profielen'

            objectid = Column(Integer)
            id = Column(Integer, primary_key=True)  # varchar??
            proident = Column(String(24))
            bron_profiel = Column(String(50))
            pro_id = Column(Integer, index=True)
            hydro_id = Column(Integer,
                              ForeignKey(HydroObject.__tablename__ + ".id"))
            # shape_lengte = Column(Float)

            profielpunten = relationship(
                "Profielpunten",
                back_populates="profiel")

            def __str__(self):
                return u'profiel {0} - {1}'.format(
                    self.id, self.proident)

        class Profielpunten(Base):
            __tablename__ = 'profielpunten'

            objectid = Column(Integer, primary_key=True)
            pbp_id = Column(Integer)
            prw_id = Column(Integer)
            pbpident = Column(String(24))
            osmomsch = Column(String(60))
            iws_volgnr = Column(Integer)
            iws_hoogte = Column(Float)
            afstand = Column(Float)
            pro_pro_id = Column(Integer,
                                ForeignKey(Profielen.__tablename__ + '.pro_id'))
            #geometry = Column("GEOMETRY", Geometry(geometry_type='POINT', srid=28992))

            def __str__(self):
                return u'profielpunt {0}'.format(
                    self.pbpident)

        class Kenmerken(Base):
            __tablename__ = 'kenmerken'

            objectid = Column(Integer)
            id = Column(Integer, primary_key=True)
            diepte = Column(Float)
            bron_diepte = Column(String(50))
            bodemhoogte = Column(Float)
            breedte = Column(Float)
            bron_breedte = Column(String(50))
            lengte = Column(Float)
            taludvoorkeur = Column(Float)
            steilste_talud = Column(Float)
            grondsoort = Column(String(50))
            bron_grondsoort = Column(String(50))
            hydro_id = Column(Integer,
                              ForeignKey(HydroObject.__tablename__ + ".objectid"))

            def __str__(self):
                return u'kenmerken {0}'.format(
                    self.id)

        class Varianten(Base):
            __tablename__ = 'varianten'

            id = Column(String(), primary_key=True)
            diepte = Column(Float)
            waterbreedte = Column(Float)
            bodembreedte = Column(Float)
            talud = Column(Float)
            # maatgevend_debiet = Column(Float)
            verhang_bos_bijkerk = Column(Float)
            opmerkingen = Column(String())
            hydro_id = Column(Integer,
                              ForeignKey(HydroObject.__tablename__ + ".id"))

            # geselecteerd = relationship("GeselecteerdeProfielen",
            #                        back_populates="variant")

            def __str__(self):
                return u'profiel_variant {0}'.format(
                    self.id)

        class GeselecteerdeProfielen(Base):
            __tablename__ = 'geselecteerd'

            hydro_id = Column(Integer,
                              ForeignKey(HydroObject.__tablename__ + ".id"),
                              primary_key=True)
            variant_id = Column(String(),
                                ForeignKey(Varianten.__tablename__ + ".id"))
            selected_on = Column(DateTime, default=datetime.datetime.utcnow)

            variant = relationship(Varianten)
            # back_populates="geselecteerd")

        class ProfielFiguren(Base):
            __tablename__ = 'profielfiguren'

            # object_id = Column(Integer, primary_key=True)
            hydro_id = Column('id_hydro', Integer,
                              ForeignKey(HydroObject.__tablename__ + ".id"))
            profid = Column(String(16), primary_key=True)
            type_prof = Column(String(1))
            coord = Column(String())
            peil = Column(Float)
            t_talud = Column(Float)
            t_waterdiepte = Column(Float)
            t_bodembreedte = Column(Float)
            t_fit = Column(Float)
            t_afst = Column(Float)
            g_rest = Column(Float)
            t_overdiepte = Column(Float)
            t_overbreedte_l = Column(Float)
            t_overbreedte_r = Column(Float)

            def __str__(self):
                return u'profiel_figuren {0} - {1}'.format(
                    self.hydro_id, self.profid)

        class DuikerSifonHevel(Base):
            __tablename__ = 'duikersifonhevel'
            extend_existing = True

            objectid = Column(Integer)
            id = Column(Integer, primary_key=True)
            #geometry = Column("GEOMETRY", Geometry(geometry_type='LINESTRING', srid=28992))
            code = Column(String(50), index=True)
            categorie = Column(Integer)
            lengte = Column(Float)
            hoogteopening = Column(Float)
            breedteopening = Column(Float)
            hoogtebinnenonderkantbene = Column(Float)
            hoogtebinnenonderkantbov = Column(Float)
            vormkoker = Column(Float)
            # shape_lengte = Column(Float)

            debiet = Column(Float)  # extra?
            channnel_id = Column(Integer)  # extra?
            flowline_id = Column(Integer)  # extra?

            def __str__(self):
                return u'DuikerSifonHevel {0}'.format(
                    self.code)

        Base.metadata.create_all(engine)

    def select_spatialite(self):
        """
        Open file dialog on click on button 'load
        :return: Boolean, if file is selected
        """

        # saves the last opened path
        settings = QSettings('last_used_spatialite_path', 'filepath')

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

        settings.setValue('last_used_spatialite_path',
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
        ## Create buttons with functions and add it to rows
        self.box_leggerdatabase_create = QtGui.QVBoxLayout()
        self.box_leggerdatabase_create.addWidget(self.load_DAMO_dump_button)
        self.box_leggerdatabase_create.addWidget(self.load_HDB_dump_button)
        self.box_leggerdatabase_create.addWidget(self.create_leggerdatabase_button)

        self.feedback_box_leggerdatabase_create = QtGui.QVBoxLayout()
        self.feedback_box_leggerdatabase_create.addWidget(self.var_text_DAMO)
        self.feedback_box_leggerdatabase_create.addWidget(self.var_text_HDB)

        self.box_leggerdatabase_input = QtGui.QHBoxLayout()
        self.box_leggerdatabase_input.addWidget(self.load_leggerdatabase_button)

        self.feedback_box_leggerdatabase_select = QtGui.QVBoxLayout()
        self.feedback_box_leggerdatabase_select.addWidget(self.var_text_leggerdatabase)

        ## Create groupbox and add HBoxes to it
        self.groupBox_leggerdatabase_create = QtGui.QGroupBox(self)
        self.groupBox_leggerdatabase_create.setTitle("Maak legger database:")
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

