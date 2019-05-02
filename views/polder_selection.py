# -*- coding: utf-8 -*-
from __future__ import division

import logging
import os

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSettings, pyqtSignal
from PyQt4.QtGui import QFileDialog, QWidget
from legger.sql_models.legger_views import create_legger_views
from legger.utils.read_data_and_make_leggerdatabase import CreateLeggerSpatialite
from legger.utils.user_message import messagebar_message
from pyspatialite import dbapi2 as dbapi

log = logging.getLogger(__name__)

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


class PolderSelectionWidget(QWidget):  # , FORM_CLASS):
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
        self.var_text_leggerdatabase.setText(
            self.root_tool.polder_datasource)  # De tekst verwijst naar de tekst in de root_tool totdat deze geupdated wordt.

    def closeEvent(self, event):
        """

        :return:
        """
        self.closingDialog.emit()
        self.close()
        event.accept()

    def explain_leggerdatabase(self):
        self.msg_upper_row = QtGui.QMessageBox(self)
        self.msg_upper_row.setIcon(QtGui.QMessageBox.Information)
        self.msg_upper_row.setText("<b>Het selecteren van een leggerdatabase<b>")
        self.msg_upper_row.setInformativeText(
            "Voor de toewijzing van leggerprofielen wordt een aparte 'leggerdatabase' "
            "gemaakt. Deze database is een aparte .sqlite bestand waar data uit "
            "DAMO en de Hydrologendatabase (HDB) gecombineerd wordt als randvoorwaarden "
            "voor de leggerprofielen, zoals breedte en talud per hydro-object.\n"
            "Wanneer een nieuwe leggerdatabase gemaakt moet worden, selecteer dan bij "
            "voorkeur de DAMO en HDB die ook voor de opbouw van het 3di model zijn "
            "gebruikt.\n"
            "Is er al een 'leggerdatabase' aangemaakt, sla deze stap dan over en zorg "
            "dat dit bestand (met als extentie .sqlite) in de tweede stap geselecteerd "
            "wordt. Let wel op: opnieuw uitgevoerde stappen en leggerkeuzes zullen "
            "bestaande data overschrijven.")
        self.box_explanation.addWidget(self.msg_upper_row)

    def select_DAMO(self):
        """
        Select a dump or export of the DAMO database (.gdb)
        :return:
        """
        settings = QSettings('leggertool', 'filepaths')
        try:
            init_path = settings.value('last_used_DAMO_path', type=str)
        except:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder

        DAMO_datasource = QFileDialog.getExistingDirectory(
            self,
            'Selecteer DAMO FileGeoDatabase (.gdb) van polder',
            init_path
        )

        if DAMO_datasource:
            self.var_text_DAMO.setText(DAMO_datasource)
            settings.setValue('last_used_DAMO_path',
                              os.path.dirname(DAMO_datasource))
        return

    def select_HDB(self):
        """
        Select a dump or export of the HDB (Dutch: Hydrologen database) (.gdb)

        :return:
        """
        settings = QSettings('leggertool', 'filepaths')
        try:
            init_path = settings.value('last_used_HDB_path', type=str)
        except:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder

        HDB_datasource = QFileDialog.getExistingDirectory(
            self,
            'Selecteer Hydrologen fileGeoDatabase (.gdb) van polder',
            init_path
        )

        if HDB_datasource:
            self.var_text_HDB.setText(HDB_datasource)
            settings.setValue('last_used_HDB_path',
                              os.path.dirname(
                                  HDB_datasource))  # verwijzing naar de class.variable in het hoofdscherm
        return

    def select_spatialite(self):
        """
        Open file dialog on click on button 'load
        :return: Boolean, if file is selected
        """
        settings = QSettings('leggertool', 'filepaths')
        try:
            init_path = settings.value('last_used_legger_spatialite_path', type=str)
        except:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder

        database = QFileDialog.getOpenFileName(
            self,
            'Selecteer leggerdatabase',
            init_path,
            'Spatialite (*.sqlite)'
        )

        if database:
            self.root_tool.polder_datasource = database
            self.var_text_leggerdatabase.setText(database)

            settings.setValue('last_used_legger_spatialite_path',
                              os.path.dirname(database))
        return

    def create_spatialite_database(self):
        # todo:
        #  feedback if input is incorrect.

        settings = QSettings('leggertool', 'filepaths')
        try:
            init_path = settings.value('last_used_legger_spatialite_path', type=str)
        except:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder

        database = QFileDialog.getSaveFileName(
            self,
            'Selecteer bestandslocatie voor nieuwe leggerdatabase',
            init_path,
            'Spatialite (*.sqlite)'
        )

        if not database:
            return

        self.var_text_leggerdatabase.setText(database)

        settings.setValue('last_used_legger_spatialite_path',
                          os.path.dirname(database))

        database_path = self.var_text_leggerdatabase.text()
        filepath_DAMO = self.var_text_DAMO.text()
        filepath_HDB = self.var_text_HDB.text()

        if not os.path.exists(filepath_DAMO):
            messagebar_message(
                'Aanmaken leggerdatabase mislukt',
                'Opgegeven DAMO database bestaat niet',
                level=2,
                duration=10)

            raise Exception('Geselecteerde DAMO database mist')

        legger_class = CreateLeggerSpatialite(
            filepath_DAMO,
            filepath_HDB,
            database_path,
        )

        legger_class.full_import_ogr2ogr()

        # set root_tool as last, because this triggers other actions
        self.root_tool.polder_datasource = database

        # create views
        con_legger = dbapi.connect(self.root_tool.polder_datasource)
        create_legger_views(con_legger)

        messagebar_message(
            'Aanmaken leggerdatabase',
            'Aanmaken leggerdatabase is gelukt',
            level=3,
            duration=10)

    def setup_ui(self):
        self.setMinimumWidth(700)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.explanation_row = QtGui.QVBoxLayout()
        self.explanation_row.setObjectName(_fromUtf8("Uitleg row"))
        self.maak_leggerdatabase_row = QtGui.QVBoxLayout()
        self.maak_leggerdatabase_row.setObjectName(_fromUtf8("Maak leggerdatabase row"))
        self.kies_leggerdatabase_row = QtGui.QVBoxLayout()
        self.kies_leggerdatabase_row.setObjectName(_fromUtf8("Kies leggerdatabase row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))

        # connect signals
        # select input files for the creation of legger database
        self.load_DAMO_dump_button = QtGui.QPushButton(self)
        self.load_DAMO_dump_button.setObjectName(_fromUtf8("Load DAMO"))
        self.load_DAMO_dump_button.clicked.connect(self.select_DAMO)
        self.load_DAMO_dump_button.setMinimumWidth(190)

        self.load_HDB_dump_button = QtGui.QPushButton(self)
        self.load_HDB_dump_button.setObjectName(_fromUtf8("Load HDB"))
        self.load_HDB_dump_button.clicked.connect(self.select_HDB)
        self.load_HDB_dump_button.setMinimumWidth(190)

        self.explanation_button = QtGui.QPushButton(self)
        self.explanation_button.setObjectName(_fromUtf8("Explain"))
        self.explanation_button.clicked.connect(self.explain_leggerdatabase)

        # make database routine
        self.create_leggerdatabase_button = QtGui.QPushButton(self)
        self.create_leggerdatabase_button.setObjectName(_fromUtf8("Create database"))
        self.create_leggerdatabase_button.clicked.connect(self.create_spatialite_database)

        # select legger database
        self.load_leggerdatabase_button = QtGui.QPushButton(self)
        self.load_leggerdatabase_button.setObjectName(_fromUtf8("Load"))
        self.load_leggerdatabase_button.clicked.connect(self.select_spatialite)
        self.load_leggerdatabase_button.setMinimumWidth(190)

        # close screen
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

        # Assembling
        # explanation button pop-up row
        self.box_explanation = QtGui.QVBoxLayout()
        self.box_explanation.addWidget(self.explanation_button)

        # Create buttons with functions to select damo and hdb and database creation and add it to rows
        self.box_leggerdatabase_create = QtGui.QVBoxLayout()
        self.hbox_DAMO = QtGui.QHBoxLayout()
        self.hbox_DAMO.addWidget(self.var_text_DAMO)
        self.hbox_DAMO.addWidget(self.load_DAMO_dump_button)
        self.box_leggerdatabase_create.addLayout(self.hbox_DAMO)

        self.hbox_HDB = QtGui.QHBoxLayout()
        self.hbox_HDB.addWidget(self.var_text_HDB)
        self.hbox_HDB.addWidget(self.load_HDB_dump_button)
        self.box_leggerdatabase_create.addLayout(self.hbox_HDB)

        self.box_leggerdatabase_create.addWidget(self.create_leggerdatabase_button)

        self.box_leggerdatabase_input = QtGui.QVBoxLayout()
        self.hbox_LDB = QtGui.QHBoxLayout()
        self.hbox_LDB.addWidget(self.var_text_leggerdatabase)
        self.hbox_LDB.addWidget(self.load_leggerdatabase_button)
        self.box_leggerdatabase_input.addLayout(self.hbox_LDB)

        # Create groupbox and add H or VBoxes to it
        self.groupBox_explanation = QtGui.QGroupBox(self)
        self.groupBox_explanation.setTitle("Uitleg")
        self.groupBox_explanation.setLayout(self.box_explanation)

        self.groupBox_leggerdatabase_create = QtGui.QGroupBox(self)
        self.groupBox_leggerdatabase_create.setTitle("GDB bestanden voor aanmaken leggerdatabase")
        self.groupBox_leggerdatabase_create.setLayout(self.box_leggerdatabase_create)

        self.groupBox_leggerdatabase_input = QtGui.QGroupBox(self)
        self.groupBox_leggerdatabase_input.setTitle("Leggerdatabase kiezen als deze al bestaat")
        self.groupBox_leggerdatabase_input.setLayout(self.box_leggerdatabase_input)

        # Add groupbox to row
        self.explanation_row.addWidget(self.groupBox_explanation)
        self.maak_leggerdatabase_row.addWidget(self.groupBox_leggerdatabase_create)
        self.kies_leggerdatabase_row.addWidget(self.groupBox_leggerdatabase_input)

        # Add row to ui
        self.verticalLayout.addLayout(self.explanation_row)
        self.verticalLayout.addLayout(self.maak_leggerdatabase_row)
        self.verticalLayout.addLayout(self.kies_leggerdatabase_row)
        self.verticalLayout.addLayout(self.bottom_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Selecteer en/of maak de leggerdatabase van de polder", None))
        self.explanation_button.setText(_translate("Dialog", "Klik hier voor meer uitleg", None))
        self.load_DAMO_dump_button.setText(_translate("Dialog", "Selecteer DAMO gdb", None))
        self.load_HDB_dump_button.setText(_translate("Dialog", "Selecteer HDB gdb", None))
        self.create_leggerdatabase_button.setText(_translate("Dialog", "Aanmaken database", None))
        self.load_leggerdatabase_button.setText(_translate("Dialog", "Selecteer leggerdb", None))
        self.cancel_button.setText(_translate("Dialog", "Sluiten", None))
