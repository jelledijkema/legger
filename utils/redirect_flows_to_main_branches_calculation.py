# todo:
#  - debiet koppeling op 'duiker' flowlines. werkt nu alleen op channels. Bijvoorbeeld hydroobject OAF-W-708 met flowline 2279
#  - korte zijslootjes worden nu gekoppeld op hoofdwatergangen. in koppelingscriteria iets van de lengte van de watergang meenemen


import logging

from legger.utils.new_network import NewNetwork
from qgis.analysis import QgsVectorLayerDirector

log = logging.getLogger(__name__)


# suggestions for improvement:
# - limit max_link_distance related to length of line (no somtimes small lines at end and
#   begin point link.


def redirect_flow_calculation(line_direct, line_layer):

    field_nr = line_direct.fields().indexFromName('direction')
    director = QgsVectorLayerDirector(
        line_direct, field_nr, '2', '1', '3', 3)

    network = NewNetwork(
        line_direct, line_layer, director, None  # self.vl_tree_layer, self.vl_endpoint_layer
    )
    new_flows, arc_tree = network.re_distribute_flow()

    return new_flows, arc_tree
