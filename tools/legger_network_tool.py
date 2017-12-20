import os.path
from PyQt4.QtCore import Qt
import qgis

from legger.views.legger_network_widget import LeggerWidget


class LeggerNetworkTool:
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
        self.menu_text = u'legger'

        self.dock_widget = None

    def on_unload(self):
        """
        on close of graph plugin
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
            self.dock_widget = LeggerWidget(iface=self.iface,
                                            parent=None)
            # connect cleanup on closing of dockwidget
            self.dock_widget.closingWidget.connect(self.on_close_widget)

            # show the dockwidget
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget)

        self.dock_widget.show()
