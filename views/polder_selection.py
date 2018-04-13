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
        #self.var_text.setText(self.root_tool.polder_datasource) # De tekst verwijst naar de tekst in de root_tool totdat deze geupdated wordt.
        self.var_text.setText(self.root_tool.ts_datasource)

    def closeEvent(self, event):
        """

        :return:
        """
        self.closingDialog.emit()
        self.close()
        event.accept()

    def select_spatialite(self):
        """
        Open file dialog on click on button 'load model'
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

        self.var_text.setText(self.root_tool.polder_datasource)
        if self.root_tool.polder_datasource == "":
            return False

        settings.setValue('last_used_spatialite_path',
                          os.path.dirname(self.root_tool.polder_datasource)) # verwijzing naar de class.variable in het hoofdscherm
        return

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.upper_row = QtGui.QVBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Upper row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))

        # connect signals
        self.load_button = QtGui.QPushButton(self)
        self.load_button.setObjectName(_fromUtf8("Load"))
        self.load_button.clicked.connect(self.select_spatialite)

        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Cancel"))
        self.cancel_button.clicked.connect(self.close)
        self.bottom_row.addWidget(self.cancel_button)


        # Feedback what document is chosen
        self.var_text = QtGui.QLineEdit(self)
        self.var_text.setText("leeg")


        # Assembling
        self.box_input = QtGui.QHBoxLayout()
        self.box_input.addWidget(self.load_button)

        self.feedback_box = QtGui.QVBoxLayout()
        self.feedback_box.addWidget(self.var_text)


        self.groupBox_input = QtGui.QGroupBox(self)
        self.groupBox_input.setTitle("Database:")
        self.groupBox_input.setLayout(self.box_input)

        self.upper_row.addWidget(self.groupBox_input)
        self.upper_row.addLayout(self.feedback_box)
        self.verticalLayout.addLayout(self.upper_row)
        self.verticalLayout.addLayout(self.bottom_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Selecteer de database van de Polder", None))
        self.load_button.setText(_translate("Dialog", "Load", None))
        self.cancel_button.setText(_translate("Dialog", "Close", None))

