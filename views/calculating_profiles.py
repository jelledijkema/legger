# -*- coding: utf-8 -*-
from __future__ import division

import logging
import os
import urllib2

from PyQt4.QtCore import pyqtSignal, QSettings, QModelIndex, QThread
from PyQt4.QtGui import QWidget, QFileDialog, QComboBox
from PyQt4 import QtCore, QtGui

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


class ProfileCalculationWidget(QWidget):#, FORM_CLASS):
    """Dialog for selecting model (spatialite and result files netCDFs)"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, polder_datasource,
            parent_class):
        """Constructor

        :parent: Qt parent Widget
        :iface: QGiS interface
        :polder_datasource: Spatialite polder
        :parent_class: the tool class which instantiated this widget. Is used
             here for storing volatile information
        """
        super(ProfileCalculationWidget, self).__init__(parent)

        self.parent_class = parent_class
        self.iface = iface
        self.polder_datasource = polder_datasource

        self.setup_ui()

        # set models on table views and update view columns
        #self.resultTableView.setModel(self.polder_datasource)
        #self.polder_datasource.set_column_sizes_on_view(self.resultTableView)

    def closeEvent(self, event):
        """

        :return:
        """
        self.closingDialog.emit()
        self.close()
        event.accept()

    def save_spatialite(self):
        """
        Change active modelsource. Called by combobox when selected
        spatialite changed
        :param nr: integer, nr of item selected in combobox
        """

        self.polder_datasource = self.polderSpatialiteComboBox.currentText()
        self.close()

    def select_spatialite(self):
        """
        Open file dialog on click on button 'load model'
        :return: Boolean, if file is selected
        """

        # saves the last opened path
        settings = QSettings('last_used_spatialite_path', 'filepath') #todo: doesn't work yet

        # set initial path to right folder
        try:
            init_path = os.path.expanduser("~") # get path to respectively "user" folder
            init_path = os.path.abspath(os.path.join(init_path, ".qgis2/python/plugins/legger"))
        except TypeError:
            init_path = os.path.expanduser("~")


        filename = QFileDialog.getOpenFileName(
            self,
            'Open File',
            init_path,
            'Spatialite (*.sqlite)'
        )
        #dlg.setFileMode(QFileDialog.AnyFile)
        #dlg.setFilter('Spatialite (*.sqlite)')
        #filename = "hello"
        if filename == "":
            return False

        #self.polder_datasource.spatialite_filepath = filename
        #index = self.polderSpatialiteComboBox.findText(filename, QtCore.Qt.MatchFixedString)

        self.polderSpatialiteComboBox.addItem(filename)


        #if index < 0:
        #    self.polderSpatialiteComboBox.addItem(filename)
        #    index_nr = self.polderSpatialiteComboBox.findText(filename)

        #self.polderSpatialiteComboBox.setCurrentIndex(index_nr)

        settings.setValue('last_used_spatialite_path',
                          os.path.dirname(filename))
        return

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.information_row = QtGui.QHBoxLayout()
        self.information_row.setObjectName(_fromUtf8("Information row"))
        self.upper_row = QtGui.QHBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Upper row"))
        self.middle_row = QtGui.QHBoxLayout()
        self.middle_row.setObjectName(_fromUtf8("Middle row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))
        self.exit_row = QtGui.QHBoxLayout()
        self.exit_row.setObjectName(_fromUtf8("Exit row"))

        # Selected file name and location in information groupbox
        self.polder_filename = QtGui.QLineEdit(self)
        self.polder_filename.setText(self.polder_datasource)
        self.polder_filename.setObjectName(_fromUtf8("polder legger filename"))

        self.model_filename = QtGui.QLineEdit(self)
        self.model_filename.setText("model") #Todo replace
        self.model_filename.setObjectName(_fromUtf8("model filename"))

        self.result_filename = QtGui.QLineEdit(self)
        self.result_filename.setText("result") #Todo replace
        self.result_filename.setObjectName(_fromUtf8("result filename"))

        self.connection_filename = QtGui.QLineEdit(self)
        self.connection_filename.setText("connection") #Todo replace
        self.connection_filename.setObjectName(_fromUtf8("connection filename"))

        # Assembling information groubox
        self.box_info = QtGui.QVBoxLayout()
        self.box_info.addWidget(self.polder_filename) # intro text toevoegen aan box.
        self.box_info.addWidget(self.model_filename)
        self.box_info.addWidget(self.result_filename)
        self.box_info.addWidget(self.connection_filename)

        self.groupBox_info = QtGui.QGroupBox(self)
        self.groupBox_info.setTitle("Bestanden gekozen:")
        self.groupBox_info.setLayout(self.box_info) # box toevoegen aan groupbox
        self.information_row.addWidget(self.groupBox_info)

        # Assembling step 1 row
        self.step1_button = QtGui.QPushButton(self)
        self.step1_button.setObjectName(_fromUtf8("Perform"))
        self.step1_button.clicked.connect(self.close)
        self.groupBox_step1 = QtGui.QGroupBox(self)
        self.groupBox_step1.setTitle("Step1:")
        self.box_info = QtGui.QHBoxLayout()
        self.box_info.addWidget(self.step1_button)  # intro text toevoegen aan box.
        self.groupBox_step1.setLayout(self.box_info) # box toevoegen aan groupbox
        self.upper_row.addWidget(self.groupBox_step1)

        # connect signals
        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Cancel"))
        self.cancel_button.clicked.connect(self.close)
        self.exit_row.addWidget(self.cancel_button)

        self.save_button = QtGui.QPushButton(self)
        self.save_button.setObjectName(_fromUtf8("Save Database and Close"))
        self.save_button.clicked.connect(self.save_spatialite)
        self.exit_row.addWidget(self.save_button)



        # Lay-out in elkaar zetten.
        self.verticalLayout.addLayout(self.information_row)
        self.verticalLayout.addLayout(self.upper_row)
        self.verticalLayout.addLayout(self.middle_row)
        self.verticalLayout.addLayout(self.bottom_row)
        self.verticalLayout.addLayout(self.exit_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Bereken de varianten van polder ...", None)) #todo: maak een merge met de poldernaam.
        self.save_button.setText(_translate("Dialog", "Save Database and Close", None))
        self.step1_button.setText(_translate("Dialog", "Connect polder database to 3Di output", None))
        self.cancel_button.setText(_translate("Dialog", "Cancel", None))

