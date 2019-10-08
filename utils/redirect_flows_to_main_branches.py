# todo:
#  - debiet koppeling op 'duiker' flowlines. werkt nu alleen op channels. Bijvoorbeeld hydroobject OAF-W-708 met flowline 2279
#  - korte zijslootjes worden nu gekoppeld op hoofdwatergangen. in koppelingscriteria iets van de lengte van de watergang meenemen


import json
import logging
import math

from qgis.core import QgsGeometry, QgsLineStringV2, QgsPoint

try:
    from ThreeDiToolbox.datasource.netcdf_groundwater_h5py import \
        NetcdfGroundwaterDataSourceH5py as NetcdfGroundwaterDataSource
except ImportError:
    from ThreeDiToolbox.datasource.netcdf_groundwater import NetcdfGroundwaterDataSource

from legger.sql_models.legger_views import create_legger_views
from legger.utils.new_network import NewNetwork
from legger.utils.geom_collections.lines import LineCollection
from legger.utils.geometries import LineString
from legger.utils.geometries import shape
from legger.sql_models.legger import DuikerSifonHevel, HydroObject
from legger.sql_models.legger_database import LeggerDatabase
from pyspatialite import dbapi2 as dbapi
from qgis.networkanalysis import QgsLineVectorLayerDirector
from legger.utils.legger_map_manager import LeggerMapManager

log = logging.getLogger(__name__)


# suggestions for improvement:
# - limit max_link_distance related to length of line (no somtimes small lines at end and
#   begin point link.


def redirect_flows(iface, path_legger_db):
    db = LeggerDatabase(
        {
            'db_path': path_legger_db
        },
        'spatialite'
    )
    db.create_and_check_fields()

    con_legger = dbapi.connect(path_legger_db)

    create_legger_views(con_legger)

    layer_manager = LeggerMapManager(iface, path_legger_db)

    line_layer = layer_manager.get_line_layer(add_to_map=False)
    # init network
    line_direct = layer_manager.get_line_layer(geometry_col='line')
    field_nr = line_direct.fieldNameIndex('direction')
    director = QgsLineVectorLayerDirector(
        line_direct, field_nr, '2', '1', '3', 3)

    network = NewNetwork(
        line_direct, line_layer, director, None # self.vl_tree_layer, self.vl_endpoint_layer
    )
    new_flows, arc_tree = network.re_distribute_flow()

    for arc in arc_tree.values():
        con_legger.execute("UPDATE hydroobject SET debiet = {0}, debiet_aangepast = {0} WHERE id = {1};".format(
            arc['flow_corrected'] if arc['flow_corrected'] is not None else 'NULL', arc['hydro_id']))


    log.info("Save redirecting flow result (update) to database ")
    con_legger.commit()
