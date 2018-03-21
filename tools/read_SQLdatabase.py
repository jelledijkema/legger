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



import os.path
from PyQt4.QtCore import Qt
import qgis

from legger.views.legger_network_widget import LeggerWidget
from legger.views.input_widget import NewWindow


class ConnectToDatabase:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        iface (QgsInterface): An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.icon_path = ':/plugins/legger/media/icon_legger.png'
        self.menu_text = u'database inlezen'

        self.dock_widget = None

    def on_unload(self):
        """
        on close of graph plugin, cleans up when closed
        """
        if self.dock_widget is not None:
            self.dock_widget.close()

    def on_close_widget(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # close widget
        self.dock_widget.closingWidget.disconnect(self.on_close_widget)

        self.dock_widget = None

    def run(self):
        """
        Run method that loads and starts the plugin (docked graph widget)
        """
        # create the dockwidget
        if self.dock_widget is None:
            self.dock_widget = LeggerWidget(
                iface=self.iface,
                parent=None,
                path_legger_db=os.path.join(
                    os.path.dirname(__file__),
                    os.path.pardir,
                    'tests', 'data',
                    'test_spatialite_with_matchprof.sqlite'
                )
            )
            # connect cleanup on closing of dockwidget
            self.dock_widget.closingWidget.connect(self.on_close_widget)

            # show the dockwidget
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget)

        self.session = "a"
        self.dock_widget = NewWindow(self.session)
        self.dock_widget.show()