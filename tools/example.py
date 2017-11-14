import logging
import os.path


log = logging.getLogger(__name__)


class ExampleTool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface, ts_datasource):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.ts_datasource = ts_datasource

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.icon_path = ':/plugins/legger/media/icon_legger.png'
        self.menu_text = u'legger'

        self.plugin_is_active = False
        self.widget = None

        self.toolbox = None
        self.modeldb_engine = None
        self.modeldb_meta = None
        self.db = None

    def on_unload(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        pass


    def run(self, *args, **kwargs):
        """
        """
        # todo
        log.error("not implemented yet")



