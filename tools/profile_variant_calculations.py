# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.
# bewerking threedi_result_selection.py van de ThreeDiToolbox QGis plugin

import logging
import os

from PyQt4.QtCore import Qt, QObject
from qgis.utils import plugins

from legger.views.calculating_profiles import ProfileCalculationWidget

log = logging.getLogger(__name__)


class ProfileCalculations(QObject):
    """QGIS Plugin Implementation."""

    tool_name = 'profile_variant_calculations'

    def __init__(self, iface, root_tool):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :param root_tool: A reference to the parent window where the reference to databases and files are declared.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        QObject.__init__(self)
        self.iface = iface
        self.root_tool = root_tool


        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.icon_path = ':/plugins/legger/media/calculator-icon.png'
        self.menu_text = u'Bereken de mogelijke leggerprofiel varianten'

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

        try:
            tdi_plugin = plugins['ThreeDiToolbox']
            ts_datasource = tdi_plugin.ts_datasource
        except:
            ts_datasource = "Kies eerst 3Di output (model, simulatie (nc), sqlite1)"

        if not self.is_active:

            self.is_active = True

            if self.dialog is None:
                # Create the dialog (after translation) and keep reference
                self.dialog = ProfileCalculationWidget(
                    parent=None,
                    iface=self.iface,
                    polder_datasource=self.root_tool.polder_datasource,
                    ts_datasource=ts_datasource,
                    parent_class=self)

            # connect to provide cleanup on closing of dockwidget
            self.dialog.closingDialog.connect(self.on_close_dialog)

            # show the widget
            self.dialog.show()
        else:
           self.dialog.setWindowState(
               self.dialog.windowState() & ~Qt.WindowMinimized |
               Qt.WindowActive)
           self.dialog.raise_()
