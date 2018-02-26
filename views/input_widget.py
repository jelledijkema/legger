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


from legger.utils.theoretical_profiles import calc_bos_bijkerk

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

        # Scherm bestaat uit een paar hoofdonderdelen:
        # VerticalLayout als hoofd layout, bestaande uit 3 rijen:
        #   - Bovenste rij bestaat uit een Horizontal Layout met 3 kolommen:
        #       - linkerkolom bestaat uit een Vertical Layout met introtext
        #       - middenkolom bestaante uit een Vertical Layout met invoer label, invoer parameters, en Bereken knop:
        #           - invoer parameters worden als spinbox in aparte groupbox toegevoegd om een net label te geven.
        #       - en rechterkolom bestaande uit een Vertical Layout met uitvoer textbox
        #   - Middelste rij met grafische weergave van de dwarsdoorsnede als Figuur
        #   - Onderste rij is ook en Horizontal Layout met 2 knoppen naast elkaar: Opslaan en Annuleren


        # Hoofd layout definieren
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        # Bovenste rij in hoofd layout definieren
        self.upper_row = QtGui.QHBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Bovenste rij"))

        # Linker kolom in bovenste rij definitie
        self.left_column = QtGui.QVBoxLayout()
        self.left_column.setObjectName(_fromUtf8("linker_kolom"))

        # Intro text
        self.intro_text = QtGui.QTextEdit(self)
        self.intro_text.setText("Hier kun je zelf een profiel definieren.\n"
                                "Vul van boven naar beneden een waarde in voor:\n"
                                "- Waterbreedte;\n"
                                "- Waterdiepte;\n"
                                "- Talud.\n\n"
                                "Met de knop 'Bereken' kun je het nieuwe profiel doorrekenen.\n"
                                "Als het profiel naar behoeven is, druk dan op 'Opslaan' om het profiel op te nemen in de database.\n"
                                "Om het scherm te verlaten kan op 'Annuleren' gedrukt worden.")
        self.intro_text.setObjectName(_fromUtf8("introductie_text"))

        self.left_column.addWidget(self.intro_text) # introtext toevoegen aan linkerkolom

        # Middelste kolom in bovenste rij
        self.middle_column = QtGui.QVBoxLayout()
        self.middle_column.setObjectName(_fromUtf8("middelste_kolom"))

        # Invoer van parameters
        # Titel
        self.invoer_label = QtGui.QLabel(self.tr("Invoer van parameters:"))
        self.middle_column.addWidget(self.invoer_label) # label toevoegen aan middenkolom

        # Spinbox waterbreedte
        self.invoer_waterbreedte = QtGui.QDoubleSpinBox(self)
        self.invoer_waterbreedte.setSuffix(" m")
        self.invoer_waterbreedte.setSingleStep(0.1)
        self.invoer_waterbreedte.setObjectName(_fromUtf8("Invoer_waterbreedte"))

        self.groupBox_waterbreedte = QtGui.QGroupBox(self)
        self.groupBox_waterbreedte.setTitle("Waterbreedte")

        self.vbox_waterbreedte = QtGui.QVBoxLayout()
        self.vbox_waterbreedte.addWidget(self.invoer_waterbreedte)
        self.groupBox_waterbreedte.setLayout(self.vbox_waterbreedte)

        self.middle_column.addWidget(self.groupBox_waterbreedte) # waterbreedte spinner toevoegen

        #Spinbox waterdiepte
        self.invoer_waterdiepte = QtGui.QDoubleSpinBox(self)
        self.invoer_waterdiepte.setSuffix(" m")
        self.invoer_waterdiepte.setSingleStep(0.1)
        self.invoer_waterdiepte.setObjectName(_fromUtf8("Invoer_waterdiepte"))

        self.groupBox_waterdiepte = QtGui.QGroupBox(self)
        self.groupBox_waterdiepte.setTitle("Waterdiepte")

        self.vbox_waterdiepte = QtGui.QVBoxLayout()
        self.vbox_waterdiepte.addWidget(self.invoer_waterdiepte)
        self.groupBox_waterdiepte.setLayout(self.vbox_waterdiepte)

        self.middle_column.addWidget(self.groupBox_waterdiepte) # waterdiepte spinner toevoegen aan midden kolom

        #Spinbox talud
        self.invoer_talud = QtGui.QDoubleSpinBox(self)
        self.invoer_talud.setSuffix(" m breedte / m hoogteverschil")
        self.invoer_talud.setSingleStep(0.1)
        self.invoer_talud.setValue(1) # initieel 1:1
        self.invoer_talud.setObjectName(_fromUtf8("Invoer_talud"))

        self.groupBox_talud = QtGui.QGroupBox(self)
        self.groupBox_talud.setTitle("Talud")

        self.vbox_talud = QtGui.QVBoxLayout()
        self.vbox_talud.addWidget(self.invoer_talud)
        self.groupBox_talud.setLayout(self.vbox_talud)

        self.middle_column.addWidget(self.groupBox_talud) # talud spinner toevoegen aan midden kolom

        # Bereken
        self.bereken_knop = QtGui.QPushButton()
        self.bereken_knop.setObjectName(_fromUtf8("Bereken_knop"))
        self.bereken_knop.clicked.connect(self.doe_berekening)
        self.middle_column.addWidget(self.bereken_knop) # bereken knop toevoegen aan midden kolom

        # Rechterkolom
        self.right_column = QtGui.QVBoxLayout()
        self.right_column.setObjectName(_fromUtf8("Rechter Kolom"))

        self.output_info = QtGui.QTextEdit(self)
        self.output_info.setObjectName(_fromUtf8("output_info"))

        self.right_column.addWidget(self.output_info)

        # Verticale kolommen toevoegen aan de bovenste rij (horizontale lay-out)
        self.upper_row.addLayout(self.left_column) # kolom met introtext en invoer parameters toevoegen
        self.upper_row.addLayout(self.middle_column)
        self.upper_row.addLayout(self.right_column) # kolom met output toevoegen



        # Horizontale bovenste rij toevoegen aan bovenkant verticale HOOFD layout.
        self.verticalLayout.addLayout(self.upper_row)

        #spacerItem = QtGui.QSpacerItem(5, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        #self.verticalLayout.addItem(spacerItem)

        # FIGUREN MAKEN
        # Figuur vlak aanmaken
        self.Figuur = QtGui.QTableWidget(self)
        self.Figuur.setObjectName(_fromUtf8("Figuur"))
        self.Figuur.setColumnCount(0)
        self.Figuur.setRowCount(0)

        # Figuurvlak toevoegen in het MIDDEN van de HOOFD lay-out.
        self.verticalLayout.addWidget(self.Figuur)


        # OPSLAAN / ANNULEREN KNOPPEN
        # Vlak maken voor de knoppen
        self.horizontalLayout_3 = QtGui.QHBoxLayout() # knoppen komen naast elkaar dus een horizontal layout.
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))

        # Opslaan knop
        self.opslaan = QtGui.QPushButton(self)
        self.opslaan.setObjectName(_fromUtf8("opslaan"))
        self.horizontalLayout_3.addWidget(self.opslaan)

        # Sluiten knop
        self.sluiten = QtGui.QPushButton(self)
        self.sluiten.setObjectName(_fromUtf8("sluiten"))
        self.horizontalLayout_3.addWidget(self.sluiten)


        # Opslaan / Annuleer knoppen toevoegen aan onderkant verticale HOOFD layout
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        
        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))

        self.bereken_knop.setText(_translate("Dialog", "Berekenen", None))
        self.opslaan.setText(_translate("Dialog", "Opslaan", None))
        self.sluiten.setText(_translate("Dialog", "Annuleer", None))

    def doe_berekening(self):
        try:
            waterbreedte = float(self.invoer_waterbreedte.value())
            waterdiepte = float(self.invoer_waterdiepte.value())
            talud = float(self.invoer_talud.value())

            bodembreedte = waterbreedte-(talud*waterdiepte)


            placeholder_norm_flow = 0.5

            textvar = calc_bos_bijkerk(placeholder_norm_flow,bodembreedte,waterdiepte,talud)
            textvar = str(textvar) +str("   ") + str(bodembreedte)


        except:
            textvar = "kan geen berekening doen."

        self.output_info.setText(textvar)




    def close_application(self):
        sys.exit()



if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()

