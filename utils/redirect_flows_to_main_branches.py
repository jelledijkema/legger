# todo:
#  - debiet koppeling op 'duiker' flowlines. werkt nu alleen op channels. Bijvoorbeeld hydroobject OAF-W-708 met flowline 2279
#  - korte zijslootjes worden nu gekoppeld op hoofdwatergangen. in koppelingscriteria iets van de lengte van de watergang meenemen


import logging

from legger.sql_models.legger_database import LeggerDatabase
from legger.sql_models.legger_database import load_spatialite
from legger.sql_models.legger_views import create_legger_views
from legger.utils.legger_map_manager import LeggerMapManager
from legger.utils.new_network import NewNetwork
from qgis.analysis import QgsVectorLayerDirector

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

    con_legger = load_spatialite(path_legger_db)

    create_legger_views(con_legger)

    layer_manager = LeggerMapManager(iface, path_legger_db)

    line_layer = layer_manager.get_line_layer()
    # init network
    line_direct = layer_manager.get_line_layer(geometry_col='line')
    field_nr = line_direct.fields().indexFromName('direction')
    director = QgsVectorLayerDirector(
        line_direct, field_nr, '2', '1', '3', 3)

    network = NewNetwork(
        line_direct, line_layer, director, None  # self.vl_tree_layer, self.vl_endpoint_layer
    )
    new_flows, arc_tree = network.re_distribute_flow()

    for arc in arc_tree.values():
        con_legger.execute("UPDATE hydroobject SET debiet = {0}, debiet_aangepast = {0} WHERE id = {1};".format(
            arc['flow_corrected'] if arc['flow_corrected'] is not None else 'NULL', arc['hydro_id']))

    log.info("Save redirecting flow result (update) to database ")
    con_legger.commit()
