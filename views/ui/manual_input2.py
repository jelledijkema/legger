# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'manual_input2.ui'
#
# Created: Wed Feb 14 14:51:54 2018
#      by: qgis.PyQt UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from qgis.PyQt import QtCore, QtWidgets

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(744, 571)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        self.intro_text = QtWidgets.QTextEdit(Dialog)
        self.intro_text.setObjectName("intro_text")
        self.verticalLayout_3.addWidget(self.intro_text)

        self.Invoer1 = QtWidgets.QDoubleSpinBox(Dialog)
        self.Invoer1.setObjectName("Invoer1")
        self.verticalLayout_3.addWidget(self.Invoer1)

        self.invoer2 = QtWidgets.QDoubleSpinBox(Dialog)
        self.invoer2.setObjectName("invoer2")
        self.verticalLayout_3.addWidget(self.invoer2)
        self.invoer3 = QtWidgets.QDoubleSpinBox(Dialog)
        self.invoer3.setObjectName("invoer3")
        self.verticalLayout_3.addWidget(self.invoer3)
        self.invoer_bereken = QtWidgets.QPushButton(Dialog)
        self.invoer_bereken.setObjectName("invoer_bereken")
        self.verticalLayout_3.addWidget(self.invoer_bereken)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.output_info = QtWidgets.QTextEdit(Dialog)
        self.output_info.setObjectName("output_info")
        self.verticalLayout_2.addWidget(self.output_info)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.Figuur = QtWidgets.QTableWidget(Dialog)
        self.Figuur.setObjectName("Figuur")
        self.Figuur.setColumnCount(0)
        self.Figuur.setRowCount(0)
        self.verticalLayout.addWidget(self.Figuur)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.opslaan = QtWidgets.QPushButton(Dialog)
        self.opslaan.setObjectName("opslaan")
        self.horizontalLayout_3.addWidget(self.opslaan)
        self.sluiten = QtWidgets.QPushButton(Dialog)
        self.sluiten.setObjectName("sluiten")
        self.horizontalLayout_3.addWidget(self.sluiten)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.invoer_bereken.setText(_translate("Dialog", "PushButton", None))
        self.opslaan.setText(_translate("Dialog", "PushButton", None))
        self.sluiten.setText(_translate("Dialog", "PushButton", None))

