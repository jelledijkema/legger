# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.
# bewerking threedi_result_selection.py van de ThreeDiToolbox QGis plugin

import logging
import os

from PyQt4.QtCore import Qt, QObject
from qgis.utils import plugins
from qgis.gui import QgsMessageBar
from PyQt4.QtGui import QAction, QIcon, QMenu

from legger.utils.user_message import messagebar_message
from legger.views.calculating_profiles import ProfileCalculationWidget

log = logging.getLogger(__name__)


class SetBegroeiingsvariant(QObject):
    """QGIS Plugin Implementation."""

    tool_name = 'zet begroeiingsvariant'

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
        self.menu_text = u'Zet begroeiingsvariant voor selectie'

        self.is_active = False
        self.dialog = None

    def get_action(self):

        self.action_base = QAction(u"zet begroeiing", self.iface.mainWindow())
        self.action1 = QAction(u"Sterk begroeiid", self.iface.mainWindow())
        self.action2 = QAction(u"Matig begroeiid", self.iface.mainWindow())
        self.action3 = QAction(u"Normaal", self.iface.mainWindow())

        self.popupMenu = QMenu(self.iface.mainWindow())
        self.popupMenu.addAction(self.action1)
        self.popupMenu.addAction(self.action2)
        self.popupMenu.addAction(self.action3)

        self.action1.triggered.connect(self.attach_variant)
        self.action2.triggered.connect(self.attach_variant)
        self.action3.triggered.connect(self.attach_variant)

        self.action_base.setMenu(self.popupMenu)

        # self.iface.addToolBarIcon(self.action_base)
        return self.action_base

    def attach_variant(self):
        a = 1
        for layer in self.iface.legendInterface().selectedLayers():
            if any([a.name() == 'begroeiingsvariant_id' for a in layer.pendingFields()]):
                # if not layer.isEditable():
                #     messagebar_message('Fout', 'Laag is niet bewerkbaar', QgsMessageBar.WARNING, 15)
                #     return

                features = layer.selectedFeatures()
                layer.startEditing()
                count = 0
                for feature in features:
                    feature['begroeiingsvariant_id'] = 1
                    count += 1

                layer.commitChanges()
                messagebar_message('Gelukt', '{0} features op begroeiingsvariant gezet.'.format(count),
                                   QgsMessageBar.INFO, 15)

            else:
                pass
                # todo: select editable layer with link to begroeiingsVariant
                messagebar_message('Fout', 'Laag bevat geen link naar begroeiingsVariant', QgsMessageBar.WARNING, 15)
                return

    def on_unload(self):
        """Cleanup necessary items here when dialog is closed"""

        pass
        # disconnects
        # if self.dialog:
        #     self.dialog.close()

    def on_close_dialog(self):
        """Cleanup necessary items here when dialog is closed"""

        self.dialog.closingDialog.disconnect(self.on_close_dialog)

        self.dialog = None
        self.is_active = False

    def run(self):
        """Run method that loads and starts the plugin"""

        try:
            tdi_plugin = plugins['ThreeDiToolbox']
        except:
            raise ImportError("For Leggertool the ThreeDiToolbox plugin must be installed, "
                              "version xxx or higher")

        try:
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
