import logging
import os
import sys

import numpy as np
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QEvent, QMetaObject, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt4.QtGui import (QApplication, QColor, QDockWidget, QFormLayout,QHBoxLayout, QInputDialog,
                         QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
                         QTableView, QVBoxLayout, QWidget, QTreeView)

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

class NewWindow(QtGui.QWidget):
    def __init__(self):
        super(NewWindow, self).__init__()
        self._new_window = None

        self.setWindowIcon(QtGui.QIcon('C:\Users\Jelle\Pictures\cat.png'))

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))

        self.linker_kolom = QtGui.QVBoxLayout()
        self.linker_kolom.setObjectName(_fromUtf8("linker_kolom"))

        self.intro_text = QtGui.QTextEdit(self)
        self.intro_text.setText("Hier kun je zelf een profiel definieren.\n"
                                "Vul van boven naar beneden een waarde in voor:\n"
                                "- waterbreedte;\n"
                                "- waterdiepte;\n"
                                "- talud.")
        self.intro_text.setObjectName(_fromUtf8("introductie_text"))
        self.linker_kolom.addWidget(self.intro_text)

        self.spinBoxesgroup = QtGui.QGroupBox(self)
        self.spinBoxesgroup.setTitle("testje")
        self.linker_kolom.addWidget(self.spinBoxesgroup)

        self.invoer_waterbreedte_label = QtGui.QLabel(self.tr("test"))

        self.invoer_waterbreedte = QtGui.QDoubleSpinBox(self)
        self.invoer_waterbreedte.setSuffix(" m")
        self.invoer_waterbreedte.setSingleStep(0.1)
        self.invoer_waterbreedte.setObjectName(_fromUtf8("Invoer1"))

        self.linker_kolom.addWidget(self.invoer_waterbreedte_label)
        self.linker_kolom.addWidget(self.invoer_waterbreedte)

        self.invoer_waterdiepte = QtGui.QDoubleSpinBox(self)
        self.invoer_waterdiepte.setSuffix(" m")
        self.invoer_waterdiepte.setSingleStep(0.1)
        self.invoer_waterdiepte.setObjectName(_fromUtf8("invoer2"))
        self.linker_kolom.addWidget(self.invoer_waterdiepte)

        self.invoer_talud = QtGui.QDoubleSpinBox(self)
        self.invoer_talud.setSuffix(" m breedte / m hoogteverschil")
        self.invoer_talud.setSingleStep(0.1)
        self.invoer_talud.setObjectName(_fromUtf8("invoer3"))
        self.linker_kolom.addWidget(self.invoer_talud)

        self.invoer_bereken = QtGui.QPushButton(self)
        self.invoer_bereken.setObjectName(_fromUtf8("invoer_bereken"))
        self.linker_kolom.addWidget(self.invoer_bereken)

        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.linker_kolom.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.linker_kolom)

        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))

        self.output_info = QtGui.QTextEdit(self)
        self.output_info.setObjectName(_fromUtf8("output_info"))

        self.verticalLayout_2.addWidget(self.output_info)
        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.Figuur = QtGui.QTableWidget(self)
        self.Figuur.setObjectName(_fromUtf8("Figuur"))
        self.Figuur.setColumnCount(0)
        self.Figuur.setRowCount(0)
        self.verticalLayout.addWidget(self.Figuur)

        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))

        self.opslaan = QtGui.QPushButton(self)
        self.opslaan.setObjectName(_fromUtf8("opslaan"))
        self.horizontalLayout_3.addWidget(self.opslaan)

        self.sluiten = QtGui.QPushButton(self)
        self.sluiten.setObjectName(_fromUtf8("sluiten"))
        self.horizontalLayout_3.addWidget(self.sluiten)
        
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        
        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)
    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.invoer_bereken.setText(_translate("Dialog", "PushButton", None))
        self.opslaan.setText(_translate("Dialog", "PushButton", None))
        self.sluiten.setText(_translate("Dialog", "PushButton", None))
        #self.home()

    def home(self):
        # applicatie moet sluiten als je op Quit drukt
        quitfont = QtGui.QFont()
        quitfont.setPointSize(22)

        quitbtn = QtGui.QPushButton("Whoa bedankt voor deze vet op maat gemaakte optie", self)
        quitbtn.clicked.connect(self.close_application)

        quitbtn.setFont(quitfont)

        quitbtn.resize(quitbtn.sizeHint())  # or btn.resize(100,100)
        quitbtn.move(500, 500)

        lbl = QtGui.QLabel('Wat zijn de afmetingen van het nieuwe hydro-object?', self)
        lbl.resize(lbl.sizeHint())
        lbl.move(20,20)

        # Invoer velden

        self.invoer1 = QtGui.QLineEdit('Vul een waarde voor waterbreedte in',self)
        self.invoer1.resize(250,20)
        self.invoer1.move(20,50)

        self.invoer2 = QtGui.QLineEdit('Vul een waarde voor waterdiepte in', self)
        self.invoer2.resize(250,20)
        self.invoer2.move(20, 80)

        self.invoer3 = QtGui.QLineEdit('Vul een waarde voor talud in', self)
        self.invoer3.resize(250,20)
        self.invoer3.move(20, 110)

        # Output

        self.uitvoer1 = QtGui.QLineEdit('Er wordt nog niks berekend',self)
        self.uitvoer1.resize(500, 100)
        self.uitvoer1.move(400, 20)

        invoerbtn = QtGui.QPushButton("Maak een berekening", self)
        invoerbtn.clicked.connect(self.doe_berekening)
        invoerbtn.resize(invoerbtn.sizeHint())  # or btn.resize(100,100)
        invoerbtn.move(20, 140)

        self.show()

    def doe_berekening(self):
        try:
            input1 = self.invoer1.text()
            textvar1 = float(input1)

            input2 = self.invoer2.text()
            textvar2 = float(input2)

            input3 = self.invoer3.text()
            textvar3 = float(input3)

            textvar = textvar1*textvar2*textvar3
            textvar = str(textvar)

        except:
            textvar = "kan geen berekening doen."

        self.uitvoer1.setText(textvar)


        self.uitvoer1.setText(textvar)
        self.uitvoer1.resize(500, 100)
        self.uitvoer1.move(400, 20)


    def close_application(self):
        sys.exit()



if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()

