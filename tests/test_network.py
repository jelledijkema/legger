import unittest

try:
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsPoint, QgsField, QgsGeometry)
except ImportError:
    pass

from legger.tests.utilities import get_qgis_app, TemporaryDirectory

QGIS_APP = get_qgis_app()

from random import shuffle
from qgis.networkanalysis import (QgsLineVectorLayerDirector)
from legger.utils.new_network import Network, AttributeProperter
from PyQt4.QtCore import QVariant


# @unittest.skipIf()
class TestTheoreticalNetwork(unittest.TestCase):

    def setUp(self):

        self.one_simple_line_network = [
            {'id': 1, 'debiet': 1.5, 'direction': 1, 'categorieoppwaterlichaam': 1, 'geometry': [(0, 1), (0, 0)]},
            {'id': 2, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': 2, 'geometry': [(0, 2), (0, 1)]},
            {'id': 3, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': None, 'geometry': [(1, 1), (0, 1)]},
            {'id': 4, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': 1, 'geometry': [(0, 3), (0, 2)]},
            {'id': 5, 'debiet': 1.0, 'direction': 1, 'categorieoppwaterlichaam': 3, 'geometry': [(0, 4), (0, 3)]},
        ]

    def test_startnrs_one_network(self):
        """ test init network en get start nrs  with one simple network
        network:
              o
              |
              v
        o <-- o <-- o <-- o <-- o
        """
        line_layer, director, distance_properter = self.get_line_layer_and_director(self.one_simple_line_network)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        vertex_nrs = network.get_start_vertex_nrs()
        point = network.graph.vertex(vertex_nrs[0]).point()
        arc_ids = [network.graph.arc(arc_nr).property(2)
                   for arc_nr in network.get_arc_nrs_of_vertex_nrs(vertex_nrs)]

        self.assertTupleEqual((0, 0), (point.x(), point.y()))
        self.assertListEqual([1], arc_ids)

    def test_startnrs_two_networks(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              |
              v
        o <-- o <-- o <-- o --> o
        """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[4]['direction'] = 2

        line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        vertex_nrs = network.get_start_vertex_nrs()
        arc_ids = [network.graph.arc(arc_nr).property(2)
                   for arc_nr in network.get_arc_nrs_of_vertex_nrs(vertex_nrs)]
        arc_ids.sort()

        self.assertEqual(2, len(vertex_nrs))
        self.assertListEqual([1, 5], arc_ids)

    def test_startnrs_one_shared_startpoint(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              |
              v
        o --> o <-- o <-- o <-- o
        """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[0]['direction'] = 2

        line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        vertex_nrs = network.get_start_vertex_nrs()
        point = network.graph.vertex(vertex_nrs[0]).point()
        arc_ids = [network.graph.arc(arc_nr).property(2)
                   for arc_nr in network.get_arc_nrs_of_vertex_nrs(vertex_nrs)]
        arc_ids.sort()

        self.assertEqual(1, len(vertex_nrs))
        self.assertTupleEqual((0, 1), (point.x(), point.y()))
        self.assertListEqual([1, 2, 3], arc_ids)

    def test_startnrs_splitted_stream(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              ^
              |
        o <-- o <-- o <-- o <-- o
        """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[3]['direction'] = 2

        line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        vertex_nrs = network.get_start_vertex_nrs()
        point = network.graph.vertex(vertex_nrs[0]).point()
        arc_ids = [network.graph.arc(arc_nr).property(2)
                   for arc_nr in network.get_arc_nrs_of_vertex_nrs(vertex_nrs)]
        arc_ids.sort()

        self.assertEqual(2, len(vertex_nrs))
        self.assertListEqual([1, 3], arc_ids)

    def test_startnrs_shuffled_input(self):
        """ test with network of test 'test_startnrs_one_shared_startpoint', with different
        input order (to make sure order of input don't influence results) """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[0]['direction'] = 2

        for i in range(0, 5):
            shuffle(layer_data)
            line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

            network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
            vertex_nrs = network.get_start_vertex_nrs()
            point = network.graph.vertex(vertex_nrs[0]).point()
            arc_ids = [network.graph.arc(arc_nr).property(2)
                       for arc_nr in network.get_arc_nrs_of_vertex_nrs(vertex_nrs)]
            arc_ids.sort()

            self.assertEqual(1, len(vertex_nrs))
            self.assertTupleEqual((0, 1), (point.x(), point.y()))
            self.assertListEqual([1, 2, 3], arc_ids)

    def test_build_tree_simple_network(self):
        """ test init network en get start nrs  with one simple network
        network:
              o
              |
              v
        o <-- o <-- o <-- o <-- o
        """
        line_layer, director, distance_properter = self.get_line_layer_and_director(self.one_simple_line_network)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        arc_dict, start_arcs = network.build_tree()

        self.assertEqual(1, len(start_arcs))
        self.assertEqual(5.5, start_arcs[0]['cum_weight'])

        elem_two = [arc for arc in arc_dict.values() if arc['branch_id'] == 2][0]
        self.assertEqual(1, elem_two['min_category_in_path'])

    def test_build_tree_splitted_stream(self):
        """ test get start nrs with one simple network with 2 end points
        network:
              o
              ^
              |
        o <-- o <-- o <-- o <-- o
        """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[2]['direction'] = 2
        layer_data[2]['debiet'] = 0.5

        line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        arc_dict, start_arcs = network.build_tree()

        self.assertEqual(2, len(start_arcs))
        self.assertEqual(1, arc_dict[start_arcs[0]['arc_nr']]['branch_id'])
        self.assertEqual(4.5, start_arcs[0]['cum_weight'])
        self.assertEqual(1, start_arcs[0]['min_category_in_path'])
        self.assertEqual(3, arc_dict[start_arcs[1]['arc_nr']]['branch_id'])
        self.assertEqual(0.5, start_arcs[1]['cum_weight'])
        self.assertEqual(4, start_arcs[1]['min_category_in_path'])

        elem_tree = [arc for arc in arc_dict.values() if arc['branch_id'] == 3][0]
        self.assertListEqual([], elem_tree['upstream_arcs'])

    def test_build_tree_small_bidirectional(self):
        """ test init network en get start nrs  with one simple network
        network:
              o
              |
              v
        o <-- o <-- o <-> o <-- o
        """
        layer_data = [row.copy() for row in self.one_simple_line_network]
        layer_data[3]['direction'] = 3
        layer_data[3]['debiet'] = None

        line_layer, director, distance_properter = self.get_line_layer_and_director(layer_data)

        network = Network(line_layer, line_layer, director, distance_properter, id_field='id')
        arc_dict, start_arcs = network.build_tree()

        self.assertEqual(1, len(start_arcs))
        self.assertEqual(5.5, start_arcs[0]['cum_weight'])

        elem_two = [arc for arc in arc_dict.values() if arc['branch_id'] == 2][0]
        self.assertEqual(1, elem_two['min_category_in_path'])


    def get_line_layer_and_director(self, line_list):
        """ help function to setup line layer and director """

        line_layer = QgsVectorLayer(
            "linestring?crs={0}".format(28992),
            "netwerk",
            "memory")

        dp = line_layer.dataProvider()

        dp.addAttributes([
            QgsField("id", QVariant.LongLong),
            QgsField("debiet", QVariant.Double),
            QgsField("direction", QVariant.Int),
            QgsField("categorieoppwaterlichaam", QVariant.Int),
            QgsField("length", QVariant.Double),
        ])
        line_layer.updateFields()
        features = []

        for l in line_list:
            feat = QgsFeature(dp.fields())
            feat['id'] = l['id']
            feat['debiet'] = l['debiet']
            feat['direction'] = l['direction']
            feat['categorieoppwaterlichaam'] = l['categorieoppwaterlichaam']
            geom = QgsGeometry().fromPolyline([QgsPoint(150000+p[0], 150000+p[1]) for p in l['geometry']])
            feat.setGeometry(geom)
            features.append(feat)
            feat['length'] = geom.length()
            # line_layer.addFeature(feat)

        line_layer.dataProvider().addFeatures(features)
        line_layer.updateExtents()
        # setup director which is direction sensitive
        field_nr = line_layer.fieldNameIndex('direction')
        director = QgsLineVectorLayerDirector(
            line_layer, field_nr, '2', '1', '3', 3)

        distance_properter = AttributeProperter('length', 0)

        return line_layer, director, distance_properter
