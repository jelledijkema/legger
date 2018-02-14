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

class NewWindow(QtGui.QMainWindow):
    def __init__(self):
        super(NewWindow, self).__init__()
        self._new_window = None
        self.setGeometry(50,50,500,300)
        self.setWindowTitle("Handmatige legger input")
        self.setWindowIcon(QtGui.QIcon('C:\Users\Jelle\Pictures\cat.png'))

        self.home()

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

        #Plot Widget
        """
        input_widgetLayout = QHBoxLayout()

        plot_input_widget = LeggerPlotWidget(self)
        size = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size.setHorizontalStretch(1)
        size.setVerticalStretch(1)
        size.setHeightForWidth(
        plot_input_widget.size().hasHeightForWidth())
        plot_input_widget.setSizePolicy(size)
        plot_input_widget.setMinimumSize(QSize(250, 250))

        input_widgetLayout.addWidget(self.plot_input_widget)
        """




    def close_application(self):
        sys.exit()



if __name__ == '__main__':
    app = QtGui.QApplication([])
    gui = NewWindow()
    gui.show()
    app.exec_()