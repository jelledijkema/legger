# -*- coding: utf-8 -*-
from __future__ import division

import datetime
import logging
import os

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSettings, pyqtSignal
from PyQt4.QtGui import QFileDialog, QWidget
from legger.utils.read_data_and_make_leggerdatabase import CreateLeggerSpatialite

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
        import sys

        sys.path.append(os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            'scripts'
        ))

        try:
            init_path = os.path.expanduser("~")  # get path to respectively "user" folder
            init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger/tests/data"))
        except TypeError:
            init_path = os.path.expanduser("~")

        filename = "test_ " + str(datetime.datetime.today().strftime('%Y%m%d')) + ".sqlite"
        database_path = os.path.abspath(os.path.join(init_path, filename))

        # todo: select output location
        filepath_DAMO = self.var_text_DAMO.text()
        filepath_HDB = self.var_text_HDB.text()

        settings = QSettings('last_used_legger_spatialite_path', 'filepath')
        self.root_tool.polder_datasource = database_path
        self.var_text_leggerdatabase.setText(self.root_tool.polder_datasource)

        if self.root_tool.polder_datasource == "":
            return False

        settings.setValue('last_used_legger_spatialite_path',
                          os.path.dirname(self.root_tool.polder_datasource)) # verwijzing naar de class.variable in het hoofdscherm

        # test_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'tests', 'data'))
        #
        # database_path = os.path.join(
        #     test_data_dir,
        #     "test_{0}.sqlite".format(str(datetime.datetime.today().strftime('%Y%m%d')))
        # )
        #
        # filepath_DAMO = os.path.join(test_data_dir, 'DAMO.gdb')  # 'Hoekje_leggertool_database.gdb')
        # filepath_HDB = os.path.join(test_data_dir, 'HDB.gdb')  # 'Hoekje_leggertool_HDB.gdb')

        legger_class = CreateLeggerSpatialite(
            filepath_DAMO,
            filepath_HDB,
            database_path
        )

        legger_class.full_import_ogr2ogr()

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

