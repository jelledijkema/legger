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


class PolderSelectionWidget(QWidget):#, FORM_CLASS):
    """Dialog for selecting model (spatialite and result files netCDFs)"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, polder_datasource,parent_class):
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

        # set models on table views and update view columns
        self.polder_datasource = polder_datasource
        self.filename = None
        #self.resultTableView.setModel(self.polder_datasource)
        #self.polder_datasource.set_column_sizes_on_view(self.resultTableView)

    def on_close(self):
        """
        Close
        """
        self.close()

    def save_spatialite(self):
        """
        Change active modelsource. Called by combobox when selected
        spatialite changed
        :param nr: integer, nr of item selected in combobox
        """

        #self.var_text.setText(self.filename)
        self.polder_datasource = self.polderSpatialiteComboBox.currentText()

        self.var_text.setText(self.polder_datasource)
        #self.close()

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


        self.filename = QFileDialog.getOpenFileName(
            self,
            'Open File',
            init_path,
            'Spatialite (*.sqlite)'
        )
        #dlg.setFileMode(QFileDialog.AnyFile)
        #dlg.setFilter('Spatialite (*.sqlite)')
        #filename = "hello"
        if self.filename == "":
            return False

        #self.polder_datasource.spatialite_filepath = filename
        #index = self.polderSpatialiteComboBox.findText(filename, QtCore.Qt.MatchFixedString)

        self.polderSpatialiteComboBox.addItem(self.filename)


        #if index < 0:
        #    self.polderSpatialiteComboBox.addItem(filename)
        #    index_nr = self.polderSpatialiteComboBox.findText(filename)

        #self.polderSpatialiteComboBox.setCurrentIndex(index_nr)

        settings.setValue('last_used_spatialite_path',
                          os.path.dirname(self.filename))
        return

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.upper_row = QtGui.QHBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Upper row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))

        # Combobox
        self.polderSpatialiteComboBox = QtGui.QComboBox()


        # connect signals
        self.load_button = QtGui.QPushButton(self)
        self.load_button.setObjectName(_fromUtf8("Load"))
        self.load_button.clicked.connect(self.select_spatialite)

        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Cancel"))
        self.cancel_button.clicked.connect(self.on_close)
        self.bottom_row.addWidget(self.cancel_button)

        self.save_button = QtGui.QPushButton(self)
        self.save_button.setObjectName(_fromUtf8("Save Database and Close"))
        self.save_button.clicked.connect(self.save_spatialite)
        self.bottom_row.addWidget(self.save_button)


        #test
        self.var_text = QtGui.QTextEdit(self)
        self.var_text.setText("bl")


        # Assembling
        self.box_input = QtGui.QHBoxLayout()
        self.box_input.addWidget(self.polderSpatialiteComboBox)
        self.box_input.addWidget(self.load_button)
        self.box_input.addWidget(self.var_text)


        self.groupBox_input = QtGui.QGroupBox(self)
        self.groupBox_input.setTitle("Database:")
        self.groupBox_input.setLayout(self.box_input)

        self.upper_row.addWidget(self.groupBox_input)  # talud spinner toevoegen aan midden kolom
        self.verticalLayout.addLayout(self.upper_row)
        self.verticalLayout.addLayout(self.bottom_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Selecteer de database van de Polder", None))
        self.load_button.setText(_translate("Dialog", "Load", None))
        self.save_button.setText(_translate("Dialog", "Save Database and Close", None))
        self.cancel_button.setText(_translate("Dialog", "Cancel", None))

