# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant
from legger.qt_models.legger_tree import LeggerTreeItem, hydrovak_class
from qgis.core import NULL, QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry, QgsPoint, QgsVectorLayer
from qgis.networkanalysis import QgsArcProperter, QgsDistanceArcProperter, QgsGraphAnalyzer, QgsGraphBuilder

DISTANCE_PROPERTER_NR = 0
BRANCH_ID_PROPERTER_NR = 1
DEPTH_PROPERTER_NR = 2
MIN_DEPTH_PROPERTER_NR = 3
MAX_DEPTH_PROPERTER_NR = 4
TARGET_LEVEL_PROPERTER_NR = 5
CATEGORY_PROPERTER_NR = 6
FLOW_PROPERTER_NR = 7
HYDRO_ID_PROPERTER_NR = 8


def make_type(value, typ, default_value=None, round_digits=None, factor=1):
    if value is None or value == NULL:
        return default_value
    try:
        output = typ(value)
        if round is not None:
            return round(factor * output, round_digits)
        else:
            return factor * output
    except TypeError:
        return default_value

def transform_none(value):
    if value == NULL:
        return None
    else:
        return value

def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

class InverseProperter(QgsArcProperter):
    """custom properter"""

    def __init__(self, attribute, attribute_index):
        QgsArcProperter.__init__(self)
        self.attribute = attribute
        self.attribute_index = attribute_index

    def property(self, distance, feature):
        input = feature[self.attribute]
        try:
            output = 1.0 / float(input) / distance
        except (ValueError, TypeError):
            output = 500 / distance

        return output

    def requiredAttributes(self):
        # Must be a list of the attribute indexes (int), not strings:
        attributes = [self.attribute_index]
        return attributes


class AttributeProperter(QgsArcProperter):
    """custom properter"""

    def __init__(self, attribute, attribute_index):
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
        attributes = [self.attribute_index]
        return attributes


class NewNetwork(object):

    def __init__(self, line_layer, full_line_layer, director,
                 distance_properter=QgsDistanceArcProperter(),
                 id_field="feat_id",
                 flow_field="debiet",
                 value_field="diepte",
                 variant_min_depth="min_diepte",
                 variant_max_depth="max_diepte",
                 streefpeil="streefpeil",
                 categorie_field="categorieoppwaterlichaam",
                 hydro_id='id'):

        """

        :param line_layer:
        :param full_line_layer:
        :param director:
        :param weight_properter:
        :param distance_properter:
        :param value_field:
        :param variant_min_depth:
        :param variant_max_depth:
        :param streefpeil:
        :param categorie_field:
        :param flow_field:
        :param hydro_id:
        """

        self.line_layer = line_layer
        self.full_line_layer = full_line_layer
        self.director = director
        self.id_field = id_field

        # build graph for network
        properter_1 = distance_properter
        properter_2 = AttributeProperter(id_field, 0)

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
        self.tree_layer_up_to_date = False
        self.arc_tree = None
        self.start_arcs = None

        self._virtual_tree_layer = None
        self._endpoint_layer = None
        self._track_layer = None
        self._hover_layer = None
        self._hover_startpoint_layer = None
        self._selected_layer = None


    def get_structure_bidirectional_group(self, arc_dict, group_vertexes):
        """

        :return:

        # situations
        # 1a. no way out, no way in --> skip
        # 1b. no way out, one way in --> start at way in and stop on corner.
        # 1c. no way out, multiple ways in --> start at ways in and stop on corners or when sides met.
        # 2. one way out --> link everything to this point based on distance
        # 3. multiple ways out --> shared flow over branches and found out main structure or something like that

        todo: make algoritme for situation
        """

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

    def build_tree(self, weight_function=None):
        """
        function that creates tree structure of network upstream of given vertex

        :param start_vertex_nr:
        :return:
        """

        # vertex list with key = vertex_nr and value = {startp, endp, weight, cum_weight, }
        arc_dict = {}
        start_arcs = []

        vertexes_in_group = {}

        # create dicts with lines (arcs), required information and mark vertexes in bi-directional islands
        for arc_nr in range(0, self.graph.arcCount()):
            arc = self.graph.arc(arc_nr)
            branch_id = int(arc.properties()[BRANCH_ID_PROPERTER_NR])
            request = QgsFeatureRequest().setFilterFid(branch_id)
            line_feature = self.full_line_layer.getFeatures(request).next()

            direction = line_feature['direction']
            if direction == 3:
                # both directions
                pass
                # if arc.inVertex() in vertexes_in_group:
                #     vertexes_in_group[arc.inVertex()].append(arc_nr)
                # else:
                #     vertexes_in_group[arc.inVertex()] = [arc_nr]

            arc_dict[arc_nr] = {
                # basic information
                'branch_id': branch_id,
                'direction': direction,
                'arc_id': arc_nr,
                'in_vertex': arc.inVertex(),
                'out_vertex': arc.outVertex(),
                'category': line_feature['categorieoppwaterlichaam'],
                'flow': line_feature['debiet'],
                'weight': (line_feature['debiet'] or 0) * arc.properties()[DISTANCE_PROPERTER_NR],
                'target_level': line_feature['streefpeil'],
                # other characteristics
                'feat_id': branch_id,
                'name': arc_nr,
                'hydro_id': line_feature['id'],
                'length': line_feature['lengte'],  # line_feature.geometry().length(),
                'depth': line_feature['diepte'],
                'width': line_feature['breedte'],
                'variant_min_depth': line_feature['min_diepte'],
                'variant_max_depth': line_feature['max_diepte'],
                'selected_depth': transform_none(line_feature['geselecteerd_diepte']),
                'selected_width': transform_none(line_feature['geselecteerd_breedte']),
                'line_feature': line_feature,
            # info need to be generated later
                'downstream_arc': None,
                'upstream_arcs': None,
                'min_category_in_path': 4,
                'cum_weight': 0,
            }


        # vertex_group = {nr: None for nr in vertexes_in_group.keys()}

        # # # group vertexes in the same bi-directional islands
        # def find_group(vertex_nr, bidirectional_arcs, group_nr):
        #     vertex_group[vertex_nr] = group_nr
        #     for arc_nr in bidirectional_arcs:
        #         nr = self.graph.arc(arc_nr).outVertex()
        #         if vertex_group[nr] is None:
        #             find_group(nr, vertexes_in_group[nr], group_nr)
        #
        #     del vertexes_in_group[vertex_nr]
        #
        # group_nr = -1
        # while len(vertexes_in_group) > 0:
        #     group_nr += 1
        #     vertex_nr, arc_nrs = next(vertexes_in_group.iteritems())
        #     find_group(vertex_nr, arc_nrs, group_nr)
        #
        # groups = set(vertex_group.values())
        #
        # groups_vertexes = {group_nr: [] for group_nr in groups}
        # for vertex_nr, group_nr in vertex_group.items():
        #     groups_vertexes[group_nr].append(vertex_nr)
        #
        # for group_nr in groups:
        #     remove_arcs, update_arcs = self.get_structure_bidirectional_group(arc_dict, groups_vertexes[group_nr])

        # set next arc
        # set downstream arc. When multiple, select one with highest flow.
        # also identify start arcs
        for arc_nr, arc in arc_dict.items():
            out_vertex = self.graph.vertex(arc['out_vertex'])
            # link arc with highest flow
            arc['downstream_arc'] = next(
                iter(sorted(out_vertex.inArc(), key=lambda nr: arc_dict[nr]['flow'], reverse=True)), None)
            if arc['downstream_arc'] is None:
                start_arcs.append({
                    'arc_nr': arc_nr,
                    'point': out_vertex.point(),
                    'children': [],
                    'parent': None
                })

        # set upstream arcs. Set only the one, who has the current arc as downstream arc (so joining
        # streams are forced into a tree structure with no alternative paths to same point
        for arc_nr, arc in arc_dict.items():
            arc['upstream_arcs'] = [
                nr for nr in self.graph.vertex(arc['in_vertex']).outArc()
                if arc_dict[nr]['downstream_arc'] == arc_nr]

        # order upstream arcs based on 'cum weight'. An arbitrary weight to select the long bigger flows as
        # main branch
        def get_cum_weight_min_category(arc):
            arc_cum_weight = arc['weight']
            arc_min_category = 4 if arc['category'] == NULL else arc['category']
            for upstream_arc_nr in arc['upstream_arcs']:
                cum_weight, min_category = get_cum_weight_min_category(arc_dict[upstream_arc_nr])
                arc_cum_weight += cum_weight
                arc_min_category = min(arc_min_category, min_category)
            arc['cum_weight'] = max(arc['cum_weight'], arc_cum_weight)
            arc['min_category_in_path'] = min(arc['min_category_in_path'], arc_min_category)
            # todo: min_category_in_path is not correct if min_catogory is not of start arc of 'main branch'.
            return arc_cum_weight, arc_min_category

        # get cum_weight and sort upstream_arcs
        for start_arc in start_arcs:
            start_arc['cum_weight'], start_arc['min_category_in_path'] = get_cum_weight_min_category(
                arc_dict[start_arc['arc_nr']])
            start_arc['target_level'] = arc_dict[start_arc['arc_nr']]['target_level']
            start_arc['distance'] = start_arc['cum_weight']

        for arc in arc_dict.values():
            arc['upstream_arcs'].sort(key=lambda nr: arc_dict[nr]['cum_weight'], reverse=True)

        # sort start arcs
        start_arcs.sort(key=lambda arc_d: arc_d['cum_weight'], reverse=True)

        self.arc_tree = arc_dict
        self.start_arcs = start_arcs

        return arc_dict, start_arcs

    def reset(self):
        pass

        self.start_arc_tree = None

    def get_tree_data(self, root_node, category=4):
        # called when startpoint has been selected
        # get layers and make them empty
        if self.start_arc_tree is None:
            return

        if self.arc_tree is None:
            self.build_tree()

        point_layer = self.get_endpoint_layer()

        ids = [feat.id() for feat in self._virtual_tree_layer.getFeatures()]
        self._virtual_tree_layer.dataProvider().deleteFeatures(ids)

        ids = [feat.id() for feat in point_layer.getFeatures()]
        point_layer.dataProvider().deleteFeatures(ids)

        features = []
        points = []

        def add_line(line_feature, item_dict):
            feat = QgsFeature()
            feat.setGeometry(line_feature.geometry())

            feat.setAttributes([
                item_dict['length'],
                int(item_dict.get('branch_id')),
                int(item_dict.get('hydro_id')),
                make_type(item_dict.get('depth'), float),
                make_type(item_dict.get('variant_min_depth'), float),
                make_type(item_dict.get('variant_max_depth'), float),
                make_type(item_dict.get('target_level'), float),
                make_type(item_dict.get('category'), int),
            ])
            features.append(feat)
            return feat

        def add_point(branch_id, typ, vertex_id):
            """create endpoint and add to addpoint layer"""
            p = self.graph.vertex(vertex_id).point()
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(p[0], p[1])))
            feat.setAttributes([
                int(branch_id),
                str(branch_id),
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

        def loop_upstream_arcs(item_dict, parent_tree_item, tree_item, target_level, distance):


            for i, upstream_arc_nr in enumerate(item_dict['upstream_arcs']):
                new_parent_tree_item = None
                upstream_item_dict = self.arc_tree[upstream_arc_nr]

                if upstream_item_dict['target_level'] is not None and upstream_item_dict['target_level'] != target_level:
                    # do something with keeping last target_level
                    endpoint_feature = add_point(item_dict['branch_id'], 'target', item_dict['in_vertex'])
                    # stop for this branch
                    continue
                elif upstream_item_dict['min_category_in_path'] > category:
                    continue


                upstream_item_dict.update({
                    'new_depth': get_stat(upstream_item_dict['depth'], item_dict['new_depth'], min),
                    'new_variant_min_depth': get_stat(upstream_item_dict['variant_min_depth'], item_dict['new_variant_min_depth'], max),
                    'new_variant_max_depth': get_stat(upstream_item_dict['variant_max_depth'], item_dict['new_variant_max_depth'], min),
                    'distance': distance
                })
                # todo: update attributes based on updates of source

                request = QgsFeatureRequest().setFilterFid(upstream_item_dict['branch_id'])
                line_feature = self.full_line_layer.getFeatures(request).next()

                feature = add_line(line_feature, upstream_item_dict)
                hydrovak = hydrovak_class(upstream_item_dict, feature)

                if i == 0:
                    new_tree_item = LeggerTreeItem(hydrovak, parent_tree_item)
                    if parent_tree_item is None:
                        a = 1

                    parent_tree_item.appendChild(new_tree_item)
                    new_parent_tree_item = parent_tree_item
                elif i == 1:
                    new_tree_item = LeggerTreeItem(hydrovak, tree_item)
                    tree_item.appendChild(new_tree_item)
                    new_parent_tree_item = tree_item
                else:
                    # first insert dummy split
                    split_hydrovak = hydrovak_class(
                        {'hydro_id': 'tak {0}'.format(i),
                         'line_feature': line_feature,
                         'distance': round(distance)
                         },
                        feature=feature)
                    split_item = LeggerTreeItem(split_hydrovak, parent_tree_item)
                    tree_item.insertChild(i - 1, split_item)
                    new_tree_item = LeggerTreeItem(hydrovak, split_item)
                    split_item.appendChild(new_tree_item)
                    new_parent_tree_item = split_item

                if len(upstream_item_dict['upstream_arcs']) == 0:
                    endpoint_feature = add_point(upstream_item_dict['branch_id'], 'end', upstream_item_dict['in_vertex'])

                loop_upstream_arcs(
                    upstream_item_dict,
                    new_parent_tree_item,
                    new_tree_item,
                    (upstream_item_dict['target_level']
                        if upstream_item_dict['target_level'] is not None else target_level),
                    distance + item_dict['length']
                )

        item_dict = self.arc_tree[self.start_arc_tree]

        item_dict.update({
            'new_depth': item_dict['depth'],
            'new_variant_min_depth': item_dict['variant_min_depth'],
            'new_variant_max_depth': item_dict['variant_max_depth'],
            'distance': 0
        })

        request = QgsFeatureRequest().setFilterFid(item_dict['branch_id'])
        line_feature = self.full_line_layer.getFeatures(request).next()

        feature = add_line(line_feature, item_dict)
        hydrovak = hydrovak_class(item_dict, feature)

        new_tree_item = LeggerTreeItem(hydrovak, root_node)
        root_node.appendChild(new_tree_item)

        loop_upstream_arcs(
            item_dict,
            root_node,
            new_tree_item,
            item_dict.get('target_level'),
            0
        )

        self._virtual_tree_layer.dataProvider().addFeatures(features)
        self._virtual_tree_layer.commitChanges()
        self._virtual_tree_layer.updateExtents()
        self._virtual_tree_layer.triggerRepaint()

        point_layer.dataProvider().addFeatures(points)
        point_layer.commitChanges()
        point_layer.updateExtents()
        point_layer.triggerRepaint()

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

        start_arc_tree = {
            'children': self.start_arcs
        }
        # todo: add

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
        self.tree_layer_up_to_date = False
        # (self.tree, self.cost) = QgsGraphAnalyzer.dijkstra(self.graph,
        #                                                    self.id_start_tree,
        #                                                    0)



    def get_virtual_tree_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._virtual_tree_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._virtual_tree_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "Verbonden hydrovakken",
                "memory")

            self._virtual_tree_layer.dataProvider().addAttributes([
                QgsField("weight", QVariant.Double),
                QgsField("line_id", QVariant.LongLong),
                QgsField("hydro_id", QVariant.LongLong),
                QgsField("min_depth", QVariant.Double),
                QgsField("var_min_depth", QVariant.Double),
                QgsField("var_max_depth", QVariant.Double),
                QgsField("target_level", QVariant.Double),
                QgsField("category", QVariant.Int)])

            self._virtual_tree_layer.updateFields()

        return self._virtual_tree_layer

    def get_endpoint_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._endpoint_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._endpoint_layer = QgsVectorLayer(
                "point?crs={0}".format(crs),
                "endpoints",
                "memory")

            self._endpoint_layer.dataProvider().addAttributes([
                QgsField("id", QVariant.LongLong),
                QgsField("hydro_id", QVariant.String),
                QgsField("typ", QVariant.String),
                QgsField("vertex_id", QVariant.LongLong)])

            self._endpoint_layer.updateFields()

        return self._endpoint_layer

    def get_track_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._track_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._track_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "Geselecteerde traject",
                "memory")

            self._track_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._track_layer.updateFields()

        return self._track_layer

    def get_hover_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._hover_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._hover_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "hover",
                "memory")

            self._hover_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._hover_layer.updateFields()

        return self._hover_layer

    def get_selected_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._selected_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._selected_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "geselecteerd",
                "memory")

            self._selected_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._selected_layer.updateFields()

        return self._selected_layer

    def get_hover_startpoint_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._hover_startpoint_layer:
            # create_layer
            crs = self.line_layer.crs().authid()
            self._hover_startpoint_layer = QgsVectorLayer(
                "point?crs={0}".format(crs),
                "start_point_hover",
                "memory")

            self._hover_startpoint_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._hover_startpoint_layer.updateFields()

        return self._hover_startpoint_layer
