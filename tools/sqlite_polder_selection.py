# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.
# bewerking threedi_result_selection.py van de ThreeDiToolbox QGis plugin

import logging
import os

from qgis.PyQt.QtCore import Qt, QObject

from legger.views.polder_selection import PolderSelectionWidget

log = logging.getLogger(__name__)


class DatabaseSelection(QObject):
    """QGIS Plugin Implementation."""

    tool_name = 'sqlite_polder_selection'

    def __init__(self, iface, ref_root_tool):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :param ref_root_tool: A reference to the parent window where the reference to databases and files are declared.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        QObject.__init__(self)
        self.iface = iface
        self.root_tool = ref_root_tool

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.icon_path = ':/plugins/legger/media/icon_add_datasource.png'
        self.menu_text = u'Selecteer de spatialite database met de database van de hydro-objecten van de polder'

        self.is_active = False
        self.dialog = None

    def on_unload(self):
        """Cleanup necessary items here when dialog is closed"""

        # disconnects
        if self.dialog:
            self.dialog.close()

    def on_close_dialog(self):
        """Cleanup necessary items here when dialog is closed"""

        self.dialog.closingDialog.disconnect(self.on_close_dialog)

        self.dialog = None
        self.is_active = False

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.is_active:

            self.is_active = True

            if self.dialog is None:
                # Create the dialog (after translation) and keep reference
                self.dialog = PolderSelectionWidget(
                    parent=None,
                    iface=self.iface,
                    parent_class=self,
                    root_tool=self.root_tool)

            # connect to provide cleanup on closing of dockwidget
            self.dialog.closingDialog.connect(self.on_close_dialog)

            # show the widget
            self.dialog.show()
        else:
           # todo: fix this code for qgis3
           # self.dialog.setWindowState(
           #     self.dialog.windowState() & ~Qt.WindowMinimized |
           #     Qt.WindowActive)
           self.dialog.raise_()
