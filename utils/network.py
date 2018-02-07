# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant
from qgis.core import (QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry, QgsVectorLayer)
from qgis.networkanalysis import QgsArcProperter, QgsDistanceArcProperter, QgsGraphAnalyzer, QgsGraphBuilder


class AttributeProperter(QgsArcProperter):
    """custom properter"""

    def __init__(self, attribute, attribute_index):
        QgsArcProperter.__init__(self)
        self.attribute = attribute
        self.attribute_index = attribute_index

    def property(self, distance, feature):
        if self.attribute == 'OGC_FID':
            value = feature.id()
        else:
            value = feature[self.attribute]
        return value

    def requiredAttributes(self):
        # Must be a list of the attribute indexes (int), not strings:
        attributes = [self.attribute_index]
        return attributes


class Network(object):

    def __init__(self, line_layer, director,
                 weight_properter=QgsDistanceArcProperter(),
                 distance_properter=QgsDistanceArcProperter(),
                 id_field="id",
                 value_field="diepte",
                 direction_field="direction"):

        self.line_layer = line_layer
        self.director = director
        self.id_field = id_field
        self.id_field_index = self.line_layer.fieldNameIndex(self.id_field)

        self.value_field = value_field
        self.value_field_index = self.line_layer.fieldNameIndex(self.value_field)

        self.direction_field = direction_field
        self.direction_field_index = self.line_layer.fieldNameIndex(self.direction_field)

        # build graph for network
        properter_1 = weight_properter
        properter_2 = distance_properter
        properter_3 = AttributeProperter(self.id_field, self.id_field_index)
        properter_4 = AttributeProperter(self.value_field, self.value_field_index)
        properter_5 = AttributeProperter(self.direction_field, self.direction_field_index)
        self.director.addProperter(properter_1)
        self.director.addProperter(properter_2)
        self.director.addProperter(properter_3)
        self.director.addProperter(properter_4)
        self.director.addProperter(properter_5)

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
        self.id_start_tree = None

        self.path_points = []

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

    def scan_point(self, qgs_point):

        # returns path, without adding point to path
        pass

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
        if self._virtual_tree_layer:
            self.update_virtual_tree_layer()

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

            filt = u'"%s" = %s' % (self.id_field, str(id_line))
            request = QgsFeatureRequest().setFilterExpression(filt)
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

    def update_virtual_tree_layer(self):
        """
        update virtual layer with latest tree
        :return: boolean, successful updated
        """

        if not self._virtual_tree_layer:
            # not yet created
            return True

        if self.tree_layer_up_to_date:
            # layer already up to date
            return True

        ids = [feat.id() for feat in self._virtual_tree_layer.getFeatures()]
        self._virtual_tree_layer.dataProvider().deleteFeatures(ids)

        features = []
        done_in_vertex_ids = []

        def add_line(arc, value):
            feat = QgsFeature()
            a = self.graph.vertex(
                arc.inVertex()).point()
            b = self.graph.vertex(
                arc.outVertex()).point()
            feat.setGeometry(QgsGeometry.fromPolyline([a, b]))

            feat.setAttributes([
                float(arc.properties()[1]),
                int(arc.properties()[2]),
                value,
                int(arc.properties()[4])])
            features.append(feat)

        def loop_recursive(arc_ids, value):

            for arc_id in arc_ids:

                arc = self.graph.arc(arc_id)
                # if self.tree[arc.outVertex()] == -1:
                #     # link is not part of tree (tree taking direction as part of input)
                #     continue

                branch_id = int(arc.properties()[2])
                branch_value = arc.properties()[3]
                if branch_value:
                    branch_value = float(branch_value)
                if value is None and branch_value is None:
                    new_value = None
                else:
                    new_value = min([val for val in [value, branch_value] if val is not None])
                add_line(arc, new_value)
                in_vertex_id = arc.inVertex()

                if in_vertex_id in done_in_vertex_ids:
                    # prevent recursive infinitive loop
                    # end point
                    continue

                done_in_vertex_ids.append(in_vertex_id)

                in_arcs = self.graph.vertex(in_vertex_id).inArc()
                linked_arcs = self.graph.vertex(in_vertex_id).outArc()

                if arc_id in in_arcs:
                    loop_recursive(
                        linked_arcs,
                        new_value
                    )
                # request property from branch
            pass

        if self.id_start_tree is not None:
            start_point_vertex = self.graph.vertex(self.id_start_tree)

            loop_recursive(start_point_vertex.outArc(), None)

        self._virtual_tree_layer.dataProvider().addFeatures(features)
        self._virtual_tree_layer.commitChanges()
        self._virtual_tree_layer.updateExtents()
        self._virtual_tree_layer.triggerRepaint()
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
                "temporary_lines",
                "memory")

            self._virtual_tree_layer.dataProvider().addAttributes([
                QgsField("weight", QVariant.Double),
                QgsField("line_id", QVariant.LongLong),
                QgsField("value", QVariant.Double),
                QgsField("direction", QVariant.Int)])

            self._virtual_tree_layer.commitChanges()

        if not self.tree_layer_up_to_date:
            self.update_virtual_tree_layer()

        return self._virtual_tree_layer

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
