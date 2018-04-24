# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant
from qgis.core import (QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry, QgsVectorLayer, QgsPoint, NULL)
from qgis.networkanalysis import QgsArcProperter, QgsDistanceArcProperter, QgsGraphAnalyzer, QgsGraphBuilder
from legger.qt_models.legger_tree import hydrovak_class, TreeItem, LeggerTreeModel


def make_type(value, typ, default_value=None, round_digits=None):
    if value is None or value == NULL:
        return default_value
    try:
        output = typ(value)
        if round is not None:
            return round(output, round_digits)
        else:
            return output
    except TypeError:
        return default_value


class InverseProperter(QgsArcProperter):
    """custom properter"""

    def __init__(self, attribute, attribute_index):
        QgsArcProperter.__init__(self)
        self.attribute = attribute
        self.attribute_index = attribute_index

    def property(self, distance, feature):
        input = feature[self.attribute]
        try:
            output = 1 / float(input)
        except ValueError:
            output = 100

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


class Network(object):

    def __init__(self, line_layer, full_line_layer, director,
                 weight_properter=QgsDistanceArcProperter(),
                 distance_properter=QgsDistanceArcProperter(),
                 value_field="diepte",
                 variant_min_depth="min_diepte",
                 variant_max_depth="max_diepte",
                 streefpeil="streefpeil",
                 categorie_field="categorieoppwaterlichaam",
                 flow_field="debiet",
                 hydro_id='id'):

        self.line_layer = line_layer
        self.full_line_layer = full_line_layer
        self.director = director
        self.id_field = 'feat_id'

        if weight_properter is None:
            field_index = self.line_layer.fieldNameIndex('debiet')
            weight_properter = InverseProperter('debiet', field_index)

        # build graph for network
        properter_1 = weight_properter
        properter_2 = distance_properter
        properter_3 = AttributeProperter('feat_id', 0)

        self.director.addProperter(properter_1)
        self.director.addProperter(properter_2)
        self.director.addProperter(properter_3)

        self.fields = {}
        for field in ['value_field', 'variant_min_depth', 'variant_max_depth',
                      'streefpeil', 'categorie_field', 'flow_field', 'hydro_id']:
            field_name = locals()[field]
            field_index = self.line_layer.fieldNameIndex(field_name)

            properter = AttributeProperter(field_name, field_index)
            self.director.addProperter(properter)

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
        self.start_point_tree = None
        self.has_path = False
        self.cost = []
        self.tree = []
        self.path = []
        self.path_vertexes = []
        self.point_path = []
        self.tree_layer_up_to_date = False
        self._virtual_tree_layer = None
        self._endpoint_layer = None
        self._track_layer = None
        self._hover_layer = None
        self._hover_startpoint_layer = None
        self._selected_layer = None
        self.id_start_tree = None

        self.path_points = []

    def get_startpoint_nrs(self):

        start_p = []

        # todo: improve - problem are 2 way arcs
        for arc_nr in range(0, self.graph.vertexCount()):
            if len(self.graph.vertex(arc_nr).inArc()) == 0:
                start_p.append(arc_nr)
        # start_p +
        return [14] + start_p

    def get_startpoint_tree(self):

        startpoint_tree = {
            'children': []
        }

        for startpoint_nr in self.get_startpoint_nrs():
            self.set_tree_startpoint(startpoint_nr)
            tree, hydro_objects, endpoints = self.get_tree()
            startpoint_tree['children'].append(tree)

        return startpoint_tree

    def get_tree(self):

        endpoints = []

        def get_stat(branch_value, recursive_value, func=min):
            branch_value = make_type(branch_value, float, None)
            if recursive_value is None and branch_value is None:
                new_value = None
            else:
                new_value = func([val for val in [recursive_value, branch_value] if val is not None])
            return new_value

        def loop_recursive(
                area, parent_hydro_obj, parent_arc, child_arc_ids,
                target_level=None, category=None, distance=0):

            linked_arcs = []
            # get flow for most of the hydroobjects - used for ordering the branches
            for arc_id in child_arc_ids:
                arc = self.graph.arc(arc_id)
                flow = 0.0
                if arc.properties()[8] == NULL:
                    # if None, sum flows of upstream channels
                    for sub_arc_id in self.graph.vertex(arc.inVertex()).outArc():
                        sub_arc = self.graph.arc(sub_arc_id)
                        flow += sub_arc.properties()[8] if arc.properties()[8] != NULL else 0.0
                else:
                    flow = arc.properties()[8]

                linked_arcs.append((arc_id, arc, (flow, float)))

            # sort linked arcs from highest flow to lowest flow
            for i, (arc_id, arc, flow) in enumerate(reversed(sorted(linked_arcs, key=lambda a: a[2]))):
                # collect information and create
                branch_id = int(arc.properties()[2])
                request = QgsFeatureRequest().setFilterFid(branch_id)
                line_feature = self.full_line_layer.getFeatures(request).next()

                end_distance = distance + line_feature['lengte']

                # get
                branch_target_level = line_feature['streefpeil']
                branch_category = line_feature['categorieoppwaterlichaam']

                flow = make_type(flow, float, round_digits=2)
                hydro_id = line_feature['id']

                in_vertex_id = arc.inVertex()
                out_vertex_id = arc.outVertex()

                # endpoint feature
                do_loop = False

                # check if child link is not the reversed one of current arc (links with zero or None
                # flow are bi-directional, so filter these out
                linked_arcs = self.graph.vertex(in_vertex_id).outArc()
                linked_arcs = [ids for ids in linked_arcs
                               if self.graph.arc(ids).inVertex() != arc.outVertex()]

                if target_level is not None and branch_target_level != target_level:
                    endpoint_type = 'target'
                    vertex_id = arc.inVertex()
                    do_loop = True
                # elif category is not None and branch_category != category:
                #     endpoint_type = 'category'
                #     vertex_id = out_vertex_id
                else:
                    vertex_id = in_vertex_id
                    in_arc = self.tree[in_vertex_id]
                    if arc_id == in_arc and len(linked_arcs) > 0 and \
                            (parent_arc is None or self.tree[parent_arc.inVertex()] != self.tree[arc.inVertex()]):
                        endpoint_type = 'between'
                        do_loop = True
                    else:
                        # endpoint
                        endpoint_type = 'end'

                new_area = None
                if endpoint_type != 'between':

                    if endpoint_type == 'target':
                        new_area = {
                            'target_level': branch_target_level,
                            'distance': distance,
                            'point': self.graph.vertex(out_vertex_id).point(),
                            'vertex_id': out_vertex_id,
                            # 'parent': area,
                            'children': [],
                            'category': []
                        }
                        area['children'].append(new_area)

                    endpoints.append({
                        'vertex_id': vertex_id,
                        'arc_id': arc_id,
                        'type': endpoint_type,
                        'branch_id': branch_id,
                        'area': area
                    })

                hydro_obj = {
                    'hydro_id': hydro_id,
                    'arc_id': arc_id,
                    'flow': flow,
                    'start_distance': round(distance),
                    'end_distance': round(end_distance),
                    'endpoint_type': endpoint_type,
                    'area': area,
                    'feature': line_feature,
                    # 'in_vertex_id': in_vertex_id,
                    # 'out_vertex_id': out_vertex_id,
                    # 'parent': parent_hydro_obj,
                    'children': []
                }

                parent_hydro_obj['children'].append(hydro_obj)

                # loop over upstream links
                if do_loop:
                    if new_area is not None:
                        par_area = new_area
                    else:
                        par_area = area

                    loop_recursive(
                        par_area, hydro_obj, arc, linked_arcs,
                        branch_target_level, branch_category, end_distance
                    )

        hydro_objects = {'parent': None, 'children': []}
        startingpoint_tree = {'children': []}

        if self.id_start_tree is not None:
            start_point_vertex = self.graph.vertex(self.id_start_tree)
            endpoints.append({
                'vertex_id': self.id_start_tree,
                'arc_id': None,
                'type': 'startpoint',
                'branch_id': None
            })

            arc_id = self.graph.vertex(self.id_start_tree).outArc()[0]
            arc = self.graph.arc(arc_id)

            branch_id = int(arc.properties()[2])
            request = QgsFeatureRequest().setFilterFid(branch_id)
            line_feature = self.full_line_layer.getFeatures(request).next()

            startingpoint_tree = {
                'distance': 0,
                'vertex_id': self.id_start_tree,
                'target_level': line_feature['streefpeil'],
                'point': self.graph.vertex(self.id_start_tree).point(),
                'parent': None,
                'children': []}

            loop_recursive(startingpoint_tree, hydro_objects, None, start_point_vertex.outArc())

        return startingpoint_tree, hydro_objects, endpoints

    def add_point(self, qgs_point):
        """

        :param qgs_point: QgsPoint instances, additional point
        :return: tuple (boolean: successful added to path,
                        string: message)
        """
        id_point = self.graph.findVertex(qgs_point)
        if not id_point:
            return False, "point is not on a vertex of the route graph"
        else:
            distance = 0
            if len(self.path_points) > 0:
                # not first point, get path between previous point and point
                success, path, p = self.get_path(self.id_start_tree, id_point,
                                                 self.path_points[-1][2])

                if not success:
                    # not path found between previous point and point
                    msg = path
                    return False, msg

                self.path.append(path)
                distance = path[-1][1]

                self.path_vertexes.extend(p)
                self.has_path = True

            self.path_points.append((qgs_point, id_point, distance))

            # set (new) tree from last point
            self.set_tree_startpoint(id_point)

            return True, "point found and added to path"

    def get_id_of_point(self, qgs_point):

        return self.graph.findVertex(qgs_point)

    def set_tree_startpoint(self, id_start_point):
        """
        set point (initial or next point) for expending path
        :param qgs_start_point: QgsPoint instance, start point of tree for
                (extension) of path
        :return:
        """

        if id_start_point == -1:
            return False, "No valid point found"

        # else create tree from this tree startpoint
        self.id_start_tree = id_start_point
        self.start_point_tree = self.graph.vertex(id_start_point).point()

        (self.tree, self.cost) = QgsGraphAnalyzer.dijkstra(self.graph,
                                                           self.id_start_tree,
                                                           0)
        self.tree_layer_up_to_date = False

    def get_path(self, id_start_point, id_end_point, begin_distance=0):
        """
        get path between the to graph points
        :param id_start_point: graph identifier of start point of (sub)path
        :param id_end_point: graph identifier of end point of (sub) path
        :param begin_distance: start distance of cumulative path distance
        :return: tuple with 3 values:
                 - successful found a path
                 - Message in case of not succesful found a path or
                   a list of path line elements, represent as a tuple, with:
                   - begin distance of part (from initial start_point),
                   - end distance of part
                   - direction of path equal to direction of feature definition
                     1 in case ot is, -1 in case it is the opposite direction
                   - feature
                 - list of vertexes (graph nodes)
        """

        # check if end_point is connected to start point
        if self.tree[id_end_point] == -1:
            return False, "Path not found", None

        # else continue finding path
        p = []
        path_props = []
        cum_dist = begin_distance
        cur_pos = id_end_point
        while cur_pos != id_start_point:
            point = self.graph.vertex(self.graph.arc(
                self.tree[cur_pos]).inVertex()).point()
            p.append(point)

            dist = self.graph.arc(self.tree[cur_pos]).properties()[1]

            id_line = self.graph.arc(self.tree[cur_pos]).properties()[2]

            # filt = u'"%s" = %s' % (self.id_field, str(id_line))
            request = QgsFeatureRequest().setFilterFid(id_line)
            feature = self.line_layer.getFeatures(request).next()

            if point == feature.geometry().vertexAt(0):
                # current point on tree (end point of this line) is equal to
                # begin of original feature, so direction is opposite: -1
                route_direction_feature = -1
            else:
                route_direction_feature = 1

            path_props.insert(
                0, [None, None, dist, route_direction_feature, feature])

            cur_pos = self.graph.arc(self.tree[cur_pos]).outVertex()

        for path in path_props:
            path[0] = cum_dist
            cum_dist += path[2]
            path[1] = cum_dist

        p.append(self.start_point_tree)

        return True, path_props, reversed(p)

    def get_tree_data(self, root):
        """
        get LeggerTreeModel and update virtual layer with latest tree

        root (TreeItem): root element of LeggerTreeModel
        return:
        """
        # get layers and make them empty
        point_layer = self.get_endpoint_layer()

        ids = [feat.id() for feat in self._virtual_tree_layer.getFeatures()]
        self._virtual_tree_layer.dataProvider().deleteFeatures(ids)

        ids = [feat.id() for feat in point_layer.getFeatures()]
        point_layer.dataProvider().deleteFeatures(ids)

        features = []
        points = []

        def make_type(value, typ, default_value=None, round_digits=None):
            if value is None or value == NULL:
                return default_value
            try:
                output = typ(value)
                if round is not None:
                    return round(output, round_digits)
                else:
                    return output
            except TypeError:
                return default_value

        def get_stat(branch_value, recursive_value, func=min):
            branch_value = make_type(branch_value, float, None)
            if recursive_value is None and branch_value is None:
                new_value = None
            else:
                new_value = func([val for val in [recursive_value, branch_value] if val is not None])
            return new_value

        def add_line(line_feature, arc, depth, variant_min_depth, variant_max_depth, target_level, category):
            feat = QgsFeature()
            feat.setGeometry(line_feature.geometry())

            feat.setAttributes([
                float(arc.properties()[1]),
                int(arc.properties()[2]),
                make_type(depth, float),
                make_type(variant_min_depth, float),
                make_type(variant_max_depth, float),
                make_type(target_level, float),
                make_type(category, int),
            ])
            features.append(feat)
            return feat

        def add_point(arc, branch_id, typ, vertex_id):
            feat = QgsFeature()
            a = self.graph.vertex(
                vertex_id).point()
            feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(a[0], a[1])))

            feat.setAttributes([
                int(branch_id),
                str(branch_id),
                typ,
                vertex_id])
            points.append(feat)
            return feat

        def loop_recursive(
                grandparent_tree_item, parent_tree_item, parent_arc, linked_arc_ids, startpoint_feature,
                depth=None, variant_min_depth=None, variant_max_depth=None, target_level=None, category=None,
                distance=0):

            linked_arcs = [(arc_id, self.graph.arc(arc_id)) for arc_id in linked_arc_ids]

            linked_arcs = []
            for arc_id in linked_arc_ids:
                arc = self.graph.arc(arc_id)
                flow = 0.0
                if arc.properties()[8] == NULL:
                    # if None, sum flows of upstream channels
                    for sub_arc_id in self.graph.vertex(arc.inVertex()).outArc():
                        sub_arc = self.graph.arc(sub_arc_id)
                        flow += sub_arc.properties()[8] if arc.properties()[8] != NULL else 0.0
                else:
                    flow = arc.properties()[8]

                linked_arcs.append((arc_id, arc, flow))

            # sort on highest flow
            for i, (arc_id, arc, flow) in enumerate(reversed(sorted(linked_arcs, key=lambda a: a[2]))):

                # collect information and create
                branch_id = int(arc.properties()[2])
                request = QgsFeatureRequest().setFilterFid(branch_id)
                line_feature = self.full_line_layer.getFeatures(request).next()

                distance_end = distance + line_feature['lengte']
                branch_depth = make_type(arc.properties()[3], float, round_digits=2)
                branch_variant_min_depth = make_type(arc.properties()[4], float, round_digits=2)
                branch_variant_max_depth = make_type(arc.properties()[5], float, round_digits=2)
                branch_width = line_feature['breedte']
                branch_target_level = arc.properties()[6]
                branch_category = arc.properties()[7]
                flow = make_type(arc.properties()[8], float, round_digits=2)
                hydro_id = arc.properties()[9]
                new_depth = get_stat(branch_depth, depth, min)
                new_variant_min_depth = get_stat(branch_variant_min_depth, variant_min_depth, max)
                new_variant_max_depth = get_stat(branch_variant_max_depth, variant_max_depth, min)
                in_vertex_id = arc.inVertex()
                out_vertex_id = arc.outVertex()

                # endpoint feature
                do_loop = False
                linked_arcs = self.graph.vertex(in_vertex_id).outArc()
                if target_level is not None and branch_target_level != target_level:
                    endpoint_type = 'target'
                    vertex_id = out_vertex_id
                elif category is not None and branch_category != category:
                    endpoint_type = 'category'
                    vertex_id = out_vertex_id
                else:
                    vertex_id = in_vertex_id
                    # check if child link is not the reversed one of current arc (links with zero flow are bi-directional,
                    # soe we need to filter these out
                    linked_arcs = [ids for ids in linked_arcs
                                   if self.graph.arc(ids).inVertex() != arc.outVertex()]

                    in_arc = self.tree[in_vertex_id]
                    if arc_id == in_arc and len(linked_arcs) > 0 and \
                            (parent_arc is None or self.tree[parent_arc.inVertex()] != self.tree[arc.inVertex()]):
                        endpoint_type = 'between'
                        do_loop = True
                    else:
                        # endpoint
                        endpoint_type = 'end'

                endpoint_feature = add_point(arc, branch_id, endpoint_type, vertex_id)

                if not endpoint_type in ['target', 'category']:
                    # hydrovak line feature
                    feature = add_line(
                        line_feature, arc, new_depth, new_variant_min_depth, new_variant_max_depth,
                        branch_target_level, branch_category, )

                    hydrovak = hydrovak_class({
                        'feat_id': branch_id,
                        'hydro_id': hydro_id,
                        'name': arc_id,
                        'depth': branch_depth,
                        'width': branch_width,
                        'variant_min': branch_variant_min_depth,
                        'variant_max': branch_variant_max_depth,
                        'target_level': branch_target_level,
                        'category': branch_category,
                        'flow': flow,
                        'distance': round(distance_end),
                        'line_feature': line_feature,
                        'selected_depth': line_feature['geselecteerd_diepte'],
                        'selected_width': line_feature['geselecteerd_breedte'],
                        'new_depth': new_depth,
                        'new_variant_min_depth': new_variant_min_depth,
                        'new_variant_max_depth': new_variant_max_depth,
                        'in_vertex_id': in_vertex_id,
                        'out_vertex_id': out_vertex_id,
                    },
                        feature,
                        startpoint_feature,
                        endpoint_feature
                    )

                    if i == 0:
                        tree_item = TreeItem(hydrovak, grandparent_tree_item)
                        grandparent_tree_item.appendChild(tree_item)
                    elif i == 1:
                        tree_item = TreeItem(hydrovak, parent_tree_item)
                        parent_tree_item.appendChild(tree_item)
                    else:
                        # first insert dummy split
                        split_hydrovak = hydrovak_class(
                            {'hydro_id': 'tak {0}'.format(i),
                             'line_feature': line_feature,
                             'distance': round(distance)
                             },
                            feature,
                            startpoint_feature,
                            endpoint_feature)
                        split_item = TreeItem(split_hydrovak, parent_tree_item)
                        parent_tree_item.insertChild(i - 2, split_item)
                        tree_item = TreeItem(hydrovak, split_item)
                        split_item.appendChild(tree_item)

                    # loop over upstream links
                    if do_loop:
                        if i == 0:
                            loop_recursive(
                                grandparent_tree_item, tree_item, arc, linked_arcs, endpoint_feature,
                                new_depth, new_variant_min_depth, new_variant_max_depth,
                                branch_target_level, branch_category, distance_end
                            )
                        elif i == 1:
                            loop_recursive(
                                parent_tree_item, tree_item, arc, linked_arcs, endpoint_feature,
                                new_depth, new_variant_min_depth, new_variant_max_depth,
                                branch_target_level, branch_category, distance_end
                            )
                        else:
                            loop_recursive(
                                split_item, tree_item, arc, linked_arcs, endpoint_feature,
                                new_depth, new_variant_min_depth, new_variant_max_depth,
                                branch_target_level, branch_category, distance
                            )

        if self.id_start_tree is not None:
            start_point_vertex = self.graph.vertex(self.id_start_tree)
            startpoint_feature = add_point(None, -1, 'startpoint', self.id_start_tree)

            loop_recursive(root, root, None, start_point_vertex.outArc(), startpoint_feature)

        self._virtual_tree_layer.dataProvider().addFeatures(features)
        self._virtual_tree_layer.commitChanges()
        self._virtual_tree_layer.updateExtents()
        self._virtual_tree_layer.triggerRepaint()

        point_layer.dataProvider().addFeatures(points)
        point_layer.commitChanges()
        point_layer.updateExtents()
        point_layer.triggerRepaint()

        return True

    def get_virtual_tree_layer(self):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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
        :return: QgsVectorLayer in memory.
        """
        # Enter editing mode

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

    def reset(self):
        """
        reset found route
        :return:
        """

        self.id_start_tree = None
        # self.id_end = None
        self.start_point_tree = None
        self.cost = []
        self.tree = []
        self.has_path = False
        self.path_points = []
        self.path = []
        self.path_vertexes = []
