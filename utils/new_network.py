# -*- coding: utf-8 -*-
from legger.qt_models.legger_tree import LeggerTreeItem, hydrovak_class, transform_none
from qgis.core import NULL, QgsFeature, QgsFeatureRequest, QgsGeometry, QgsPoint
from qgis.networkanalysis import QgsArcProperter, QgsDistanceArcProperter, QgsGraphBuilder

DISTANCE_PROPERTER_NR = 0
FEAT_ID_PROPERTER_NR = 1


def make_type(value, typ, default_value=None, round_digits=None, factor=1):
    """transform value (also Qt NULL values) to specified type or default value if None.
    Can also round value or multiply value

    value (any type): input value to transform to other type
    typ (python type): python type object like int, str or float
    default_value (any): default value returned when value is None or NULL
    round_digits (int): Number of digits to round value on.
    factor (float or int): Multiplication factor

    return (any): transformed value
    """
    if value is None or value == NULL:
        return default_value
    try:
        output = typ(value)
        if typ in (float, int,):
            if round is not None:
                return round(factor * output, round_digits)
            else:
                return factor * output
        else:
            return output

    except TypeError:
        return default_value


def merge_dicts(x, y):
    """merge two dictionaries into a new dictionary (for python 2.x).
    For python 3.x use {**x, **y}"""
    z = x.copy()
    z.update(y)
    return z


class AttributeProperter(QgsArcProperter):
    """custom properter which returns property of input layer"""

    def __init__(self, attribute, attribute_index):
        """
        attribute (str): field name. Provide 'feat_id' to get feature id (requested through feature.id())
        attribute_index (list of int): List of field indexes of fields used by property function
        """
        QgsArcProperter.__init__(self)
        self.attribute = attribute
        self.attribute_index = attribute_index

    def property(self, distance, feature):
        if self.attribute == 'feat_id':
            value = feature.id()
        else:
            value = feature[self.attribute]
        return value

    def requiredAttributes(self):
        # Must be a list of the attribute indexes (int), not strings:
        return self.attribute_index


class NewNetwork(object):
    """Network class for providing network required for Legger tool"""

    # todo:
    #     - support bidirectional islands
    #     - move virtual_layer and endpoint_layer outside this class
    #     - set endpoints on 90% or 10 meter before endpoint of hydrovak
    #     - add startpoint within tree (change target_levels)
    #     - calc distance from start and set correct distance at start points

    def __init__(self, line_layer, full_line_layer, director,
                 distance_properter,
                 virtual_tree_layer=None, endpoint_layer=None,
                 id_field="feat_id"):
        """
        line_layer (QgsVectorLayer): input vector layer, with as geometry straight lines without in between vertexes
        full_line_layer (QgsVectorLayer): input vector layer, with original geometry (with in between vertexes)
        director (QgsLineVectorLayerDirector):
        distance_properter (Qgs Properter type): properter to get distance. used for shortest path at bidirectional islandes
        virtual_tree_layer (QgsVectorLayer): layer used to visualize active tree
        endpoint_layer (QgsVectorLayer): layer used ot visualize endpoints of tree
        id_field (str): field used by features to identification field
        """

        self.line_layer = line_layer
        self.full_line_layer = full_line_layer
        self.director = director
        self._virtual_tree_layer = virtual_tree_layer
        self._endpoint_layer = endpoint_layer
        self.id_field = id_field

        # build graph for network
        properter_1 = distance_properter or QgsDistanceArcProperter()
        properter_2 = AttributeProperter(id_field, [line_layer.dataProvider().fieldNameIndex(id_field)])

        self.director.addProperter(properter_1)
        self.director.addProperter(properter_2)

        if not self.line_layer.isValid():
            raise AttributeError('Linelayer is not valid')

        crs = self.line_layer.crs()
        # todo: correct this in the source line layer hydroobjects with results
        if not crs.authid():
            crs.createFromId(28992)
            self.line_layer.setCrs(crs)

        self.builder = QgsGraphBuilder(crs)
        self.director.makeGraph(self.builder, [])
        self.graph = self.builder.graph()

        # init class attributes
        self.start_arc_tree = None
        self.arc_tree = None  # dictionary with tree data in format {[arc_nr]: {**arc_data}}
        self.start_arcs = None  # list of dicts with arc_nr, point (x, y), list childs, parent


    def get_structure_bidirectional_group(self, arc_dict, group_vertexes):
        """

        :return:

        # situations:
        # 1a. no way out, no way in --> skip
        # 1b. no way out, one way in --> start at way in and stop on corner.
        # 1c. no way out, multiple ways in --> start at ways in and stop on corners or when sides met.
        # 2. one way out --> link everything to this point based on distance
        # 3. multiple ways out --> shared flow over branches and found out main structure or something like that

        idea - for all situations, use shortest distance
        """
        # todo: make this function...

        def get_all_bidirectional_arcs(vertexes):
            arcs = []
            for vertex in vertexes:
                arcs.extend([arc_nr for arc_nr in vertex.outArc() if arc_dict[arc_nr]['direction'] == 3])

        arcs = []

        in_arcs = [arc_nr for arc_nr in self.get_in_arc_nrs_of_vertex_nrs(group_vertexes)
                   if arc_dict[arc_nr]['direction'] != 3]
        out_arcs = [arc_nr for arc_nr in self.get_out_arc_nrs_of_vertex_nrs(group_vertexes)
                    if arc_dict[arc_nr]['direction'] != 3]

        if len(out_arcs) == 0:
            # no way out
            if len(in_arcs) == 0:
                # remove all arcs
                return get_all_bidirectional_arcs(group_vertexes), {}
            elif len(in_arcs) == 1:
                pass
            else:
                pass

        elif len(out_arcs) == 1:
            # one way out
            pass

        else:
            # multiple ways out
            pass

        return [], {}
        # (self.tree, self.cost) = QgsGraphAnalyzer.dijkstra(self.graph,
        #                                                    self.id_start_tree,
        #                                                    0)

    def build_tree(self):
        """
        function that creates tree structure of network. Sets self.arc_tree and self.start_arcs

        returns (tuple): tuple with dictionary of arc_tree en list of start arc_nrs
        """
        arc_tree = {}
        start_arcs = []

        # create dicts with lines (arcs), required information and mark vertexes in bi-directional islands
        for arc_nr in range(0, self.graph.arcCount()):
            arc = self.graph.arc(arc_nr)
            feat_id = int(arc.properties()[FEAT_ID_PROPERTER_NR])
            request = QgsFeatureRequest().setFilterFid(feat_id)
            line_feature = self.full_line_layer.getFeatures(request).next()

            direction = line_feature['direction']
            if direction == 3:
                # both directions
                pass
                # todo: add support here

            arc_tree[arc_nr] = hydrovak_class(
                data_dict={
                    # basic information
                    'feat_id': feat_id,
                    'arc_nr': arc_nr,
                    'in_vertex': arc.inVertex(),
                    'out_vertex': arc.outVertex(),
                    'weight': (line_feature['debiet'] or 0) * arc.properties()[DISTANCE_PROPERTER_NR],
                    # info need to be generated later
                    'downstream_arc': None,
                    'upstream_arcs': None,
                    'min_category_in_path': 4,
                    'cum_weight': 0,
                },
                feature=line_feature,
            )

        # set downstream arc. When multiple, select one with highest flow.
        # also identify start arcs
        for arc_nr, arc in arc_tree.items():
            out_vertex = self.graph.vertex(arc['out_vertex'])
            # link arc with highest flow
            arc['downstream_arc'] = next(
                iter(sorted(out_vertex.inArc(), key=lambda nr: arc_tree[nr]['flow'], reverse=True)), None)
            if arc['downstream_arc'] is None:
                start_arcs.append({
                    'arc_nr': arc_nr,
                    'point': out_vertex.point(),
                    'children': [],
                    'parent': None,
                    # attributes to be filled later
                    'distance': None,
                    'cum_weight': None,
                    'min_category_in_path': None

                })

        # set upstream arcs. Set only the one, who has the current arc as downstream arc (so joining
        # streams are forced into a tree structure with no alternative paths to same point
        for arc_nr, arc in arc_tree.items():
            arc['upstream_arcs'] = [
                nr for nr in self.graph.vertex(arc['in_vertex']).outArc()
                if arc_tree[nr]['downstream_arc'] == arc_nr]

        # order upstream arcs based on 'cum weight'. An (arbitrary) weight to select the long bigger flows as
        # main branch
        def get_cum_weight_min_category(arc):
            """sub-function for recursive weight calculation"""
            arc_cum_weight = arc['weight']
            arc_min_category = 4 if arc['category'] is None else arc['category']
            for upstream_arc_nr in arc['upstream_arcs']:
                cum_weight, min_category = get_cum_weight_min_category(arc_tree[upstream_arc_nr])
                arc_cum_weight += cum_weight
                arc_min_category = min(arc_min_category, min_category)
            arc['cum_weight'] = max(arc['cum_weight'], arc_cum_weight)
            arc['min_category_in_path'] = min(arc['min_category_in_path'], arc_min_category)
            return arc_cum_weight, arc_min_category

        # get cum_weight and sort upstream_arcs
        for start_arc in start_arcs:
            start_arc['cum_weight'], start_arc['min_category_in_path'] = get_cum_weight_min_category(
                arc_tree[start_arc['arc_nr']])
            start_arc['target_level'] = arc_tree[start_arc['arc_nr']]['target_level']
            # todo: set distance correct
            start_arc['distance'] = start_arc['cum_weight']

        for arc in arc_tree.values():
            arc['upstream_arcs'].sort(key=lambda nr: arc_tree[nr]['cum_weight'], reverse=True)

        # sort start arcs
        start_arcs.sort(key=lambda arc_d: arc_d['cum_weight'], reverse=True)

        # store tree and start points
        self.arc_tree = arc_tree
        self.start_arcs = start_arcs

        return arc_tree, start_arcs

    def get_tree_data(self, root_node, category=4):
        # todo: move part outside of this class?
        # called when startpoint has been selected
        # get layers and make them empty
        if self.start_arc_tree is None:
            return

        if self.arc_tree is None:
            self.build_tree()

        ids = [feat.id() for feat in self._virtual_tree_layer.getFeatures()]
        self._virtual_tree_layer.dataProvider().deleteFeatures(ids)

        ids = [feat.id() for feat in self._endpoint_layer.getFeatures()]
        self._endpoint_layer.dataProvider().deleteFeatures(ids)

        features = []
        points = []

        def add_line(hydrovak):
            feat = QgsFeature()
            feat.setGeometry(hydrovak['feature'].geometry())

            feat.setAttributes([
                hydrovak['length'],
                int(hydrovak.get('feat_id')),
                int(hydrovak.get('hydro_id')),
                make_type(hydrovak.get('depth'), float),
                make_type(hydrovak.get('variant_min_depth'), float),
                make_type(hydrovak.get('variant_max_depth'), float),
                make_type(hydrovak.get('target_level'), float),
                make_type(hydrovak.get('category'), int),
            ])
            features.append(feat)
            return feat

        def add_point(feat_id, typ, vertex_id):
            """create endpoint and add to addpoint layer"""
            p = self.graph.vertex(vertex_id).point()
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(p[0], p[1])))
            feat.setAttributes([
                int(feat_id),
                str(feat_id),
                typ,
                vertex_id])
            points.append(feat)
            return feat

        def get_stat(branch_value, recursive_value, func=min):
            branch_value = make_type(branch_value, float, None)
            if recursive_value is None and branch_value is None:
                new_value = None
            else:
                new_value = func([val for val in [recursive_value, branch_value] if val is not None])
            return new_value

        def loop_upstream_arcs(hydrovak, parent_tree_item, tree_item, target_level, distance):
            hydrovak['end_arc_type'] = ''

            for i, upstream_arc_nr in enumerate(hydrovak['upstream_arcs']):
                new_parent_tree_item = None
                upstream_hydrovak = self.arc_tree[upstream_arc_nr]

                if upstream_hydrovak['target_level'] is not None and \
                        upstream_hydrovak['target_level'] != target_level:
                    # do something with keeping last target_level
                    endpoint_feature = add_point(hydrovak['feat_id'], 'target', hydrovak['in_vertex'])
                    # stop for this branch
                    hydrovak['end_arc_type'] = 'target'
                    continue
                elif upstream_hydrovak['min_category_in_path'] > category:
                    continue

                upstream_hydrovak.update({
                    'new_depth': get_stat(upstream_hydrovak['depth'], hydrovak['new_depth'], min),
                    'new_variant_min_depth': get_stat(upstream_hydrovak['variant_min_depth'],
                                                      hydrovak['new_variant_min_depth'], max),
                    'new_variant_max_depth': get_stat(upstream_hydrovak['variant_max_depth'],
                                                      hydrovak['new_variant_max_depth'], min),
                    'distance': distance
                })

                feature = add_line(upstream_hydrovak)

                if i == 0:
                    new_tree_item = LeggerTreeItem(upstream_hydrovak, parent_tree_item)
                    if parent_tree_item is None:
                        a = 1

                    parent_tree_item.appendChild(new_tree_item)
                    new_parent_tree_item = parent_tree_item
                elif i == 1:
                    new_tree_item = LeggerTreeItem(upstream_hydrovak, tree_item)
                    tree_item.appendChild(new_tree_item)
                    new_parent_tree_item = tree_item
                else:
                    # first insert dummy split
                    split_hydrovak = hydrovak_class(
                        {'hydro_id': 'tak {0}'.format(i),
                         'line_feature': upstream_hydrovak['feature'],  # todo: correct??
                         'distance': round(distance)
                         },
                        feature=feature)
                    split_item = LeggerTreeItem(split_hydrovak, parent_tree_item)
                    tree_item.insertChild(i - 1, split_item)
                    new_tree_item = LeggerTreeItem(hydrovak, split_item)
                    split_item.appendChild(new_tree_item)
                    new_parent_tree_item = split_item

                if len(upstream_hydrovak['upstream_arcs']) == 0:
                    endpoint_feature = add_point(upstream_hydrovak['feat_id'], 'end', upstream_hydrovak['in_vertex'])
                    upstream_hydrovak['end_arc_type'] = 'end'

                loop_upstream_arcs(
                    upstream_hydrovak,
                    new_parent_tree_item,
                    new_tree_item,
                    (upstream_hydrovak['target_level']
                     if upstream_hydrovak['target_level'] is not None else target_level),
                    distance + hydrovak['length']
                )

        hydrovak = self.arc_tree[self.start_arc_tree]

        hydrovak.update({
            'new_depth': hydrovak['depth'],
            'new_variant_min_depth': hydrovak['variant_min_depth'],
            'new_variant_max_depth': hydrovak['variant_max_depth'],
            'distance': 0
        })

        feature = add_line(hydrovak)

        new_tree_item = LeggerTreeItem(hydrovak, root_node)
        root_node.appendChild(new_tree_item)

        loop_upstream_arcs(
            hydrovak,
            root_node,
            new_tree_item,
            hydrovak['target_level'],
            0
        )

        self._virtual_tree_layer.dataProvider().addFeatures(features)
        self._virtual_tree_layer.commitChanges()
        self._virtual_tree_layer.updateExtents()
        self._virtual_tree_layer.triggerRepaint()

        self._endpoint_layer.dataProvider().addFeatures(points)
        self._endpoint_layer.commitChanges()
        self._endpoint_layer.updateExtents()
        self._endpoint_layer.triggerRepaint()

        return True

    def get_in_arc_nrs_of_vertex_nrs(self, vertex_nrs):
        """
        help function to get all outarc of list of vertexes.

        :return:
        """
        arc_nrs = []
        for vertex_nr in vertex_nrs:
            arc_nrs.extend(self.graph.vertex(vertex_nr).outArc())

        return arc_nrs

    def get_out_arc_nrs_of_vertex_nrs(self, vertex_nrs):
        """
        help function to get all outarc of list of vertexes.

        :return:
        """
        arc_nrs = []
        for vertex_nr in vertex_nrs:
            arc_nrs.extend(self.graph.vertex(vertex_nr).inArc())

        return arc_nrs

    def get_start_arc_tree(self):
        """
        get tree with startarcs.
        return: start_arc_tree, example of structure
            {
                'children': [
                   ...startpoints,
                   {
                    'children': []
                ]
            }
        """
        if self.arc_tree is None:
            self.build_tree()

        # todo: target level change arcs ...
        start_arc_tree = {
            'children': self.start_arcs
        }

        return start_arc_tree

    def set_tree_start_arc(self, id_start_arc):
        """
        set point (initial or next point) for expending path

        qgs_start_point (int): start point of tree for (extension) of path
        return: None
        """

        if id_start_arc == -1:
            return

        self.start_arc_tree = id_start_arc
