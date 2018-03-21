# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'manual_input2.ui'
#
# Created: Wed Feb 14 14:51:54 2018
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(744, 571)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))

        self.intro_text = QtGui.QTextEdit(Dialog)
        self.intro_text.setObjectName(_fromUtf8("intro_text"))
        self.verticalLayout_3.addWidget(self.intro_text)

        self.Invoer1 = QtGui.QDoubleSpinBox(Dialog)
        self.Invoer1.setObjectName(_fromUtf8("Invoer1"))
        self.verticalLayout_3.addWidget(self.Invoer1)

        self.invoer2 = QtGui.QDoubleSpinBox(Dialog)
        self.invoer2.setObjectName(_fromUtf8("invoer2"))
        self.verticalLayout_3.addWidget(self.invoer2)
        self.invoer3 = QtGui.QDoubleSpinBox(Dialog)
        self.invoer3.setObjectName(_fromUtf8("invoer3"))
        self.verticalLayout_3.addWidget(self.invoer3)
        self.invoer_bereken = QtGui.QPushButton(Dialog)
        self.invoer_bereken.setObjectName(_fromUtf8("invoer_bereken"))
        self.verticalLayout_3.addWidget(self.invoer_bereken)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.output_info = QtGui.QTextEdit(Dialog)
        self.output_info.setObjectName(_fromUtf8("output_info"))
        self.verticalLayout_2.addWidget(self.output_info)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.Figuur = QtGui.QTableWidget(Dialog)
        self.Figuur.setObjectName(_fromUtf8("Figuur"))
        self.Figuur.setColumnCount(0)
        self.Figuur.setRowCount(0)
        self.verticalLayout.addWidget(self.Figuur)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.opslaan = QtGui.QPushButton(Dialog)
        self.opslaan.setObjectName(_fromUtf8("opslaan"))
        self.horizontalLayout_3.addWidget(self.opslaan)
        self.sluiten = QtGui.QPushButton(Dialog)
        self.sluiten.setObjectName(_fromUtf8("sluiten"))
        self.horizontalLayout_3.addWidget(self.sluiten)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.invoer_bereken.setText(_translate("Dialog", "PushButton", None))
        self.opslaan.setText(_translate("Dialog", "PushButton", None))
        self.sluiten.setText(_translate("Dialog", "PushButton", None))

