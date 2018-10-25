# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant
from legger.qt_models.legger_tree import LeggerTreeItem, hydrovak_class
from qgis.core import NULL, QgsFeature, QgsFeatureRequest, QgsField, QgsGeometry, QgsPoint, QgsVectorLayer
from qgis.networkanalysis import QgsArcProperter, QgsDistanceArcProperter, QgsGraphAnalyzer, QgsGraphBuilder

BRANCH_ID_PROPERTER_NR = 2
DEPTH_PROPERTER_NR = 3
MIN_DEPTH_PROPERTER_NR = 4
MAX_DEPTH_PROPERTER_NR = 5
TARGET_LEVEL_PROPERTER_NR = 6
CATEGORY_PROPERTER_NR = 7
FLOW_PROPERTER_NR = 8
HYDRO_ID_PROPERTER_NR = 9


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
        """
        get nrs of vertexes with no upstream nodes. With support for 'islands' of bidirectional arcs (in
        which case a random point in the island is selected)

        return (list of ints): list with vertex numbers
        """

        start_p = []
        startpoint_islands = []

        def startpoint_island_check(search_start_vertex):
            """
            check if there are no incoming arcs in an island of one or more bi-directional arcs.
            in global scope:
              - self.graph
              - startpoint_islands (checked points will be added to this list)

            search_start_vertex (int): vertex nr to start search
            return (bool): True if there are no incoming arcs
            """

            # for all in (not in previous out)
            # check in --> if in --> no startpoint
            # if all points checked, this is an island, select point

            vertexes = [search_start_vertex]
            i = 0
            ready = False
            while not ready:
                vertex_nr = vertexes[i]
                vertex = self.graph.vertex(vertex_nr)

                startpoint_islands.append(vertex_nr)

                if len(vertex.inArc()) > len(vertex.outArc()):
                    # there is a way in, so no startpoint island
                    return False
                else:
                    to_vertexes = [self.graph.arc(arc_id).inVertex()
                                   for arc_id in vertex.outArc()]
                    for arc_nr in vertex.inArc():
                        # check if 'to' arcs are all bi-directional

                        if self.graph.arc(arc_nr).outVertex() not in to_vertexes:
                            # if not, this is a non bi-directional way in, so no startpoint island
                            return False

                    # add additional points to list and continue
                    for arc_nr in vertex.inArc():
                        in_vertex_nr = self.graph.arc(arc_nr).outVertex()
                        if in_vertex_nr not in vertexes:
                            vertexes.append(in_vertex_nr)

                if i == len(vertexes) - 1:
                    ready = True
                    start_p.append(vertexes[-1])
                    return True

                i += 1

        for vertex_nr in range(0, self.graph.vertexCount()):
            vertex = self.graph.vertex(vertex_nr)
            if len(vertex.inArc()) == 0:
                # no 'to', this must be a startpoint
                start_p.append(vertex_nr)
            elif len(vertex.inArc()) > len(vertex.outArc()):
                # more 'to' then 'from', no need to check further
                continue
            elif vertex_nr in startpoint_islands:
                # point already checked by the 'startpoint island' check
                continue
            else:
                to_vertexes = [self.graph.arc(arc_id).inVertex()
                               for arc_id in vertex.outArc()]
                for arc_nr in vertex.inArc():
                    # check if 'to' arcs are all bi-directional
                    if self.graph.arc(arc_nr).outVertex() not in to_vertexes:
                        # if not, this is a non bi-directional way in
                        continue

                # startpoint island check
                startpoint_island_check(vertex_nr)

        return start_p

    def get_startpoint_tree(self):
        """
        get tree
        :return:
        """

        startpoint_tree = {
            'children': []
        }

        for startpoint_nr in self.get_startpoint_nrs():
            self.set_tree_startpoint(startpoint_nr)
            tree, hydro_objects, endpoints = self.get_tree()
            startpoint_tree['children'].extend(tree)

        return startpoint_tree

    def get_tree(self, start_vertex_nr=None):
        """
        refactor:
         - startpoints


        provide a 'flattend tree'. Channels with the highest flow will stay on the same 'tree level'


        start_vertex_nr (int): vertex nr of startpoint of tree. When no value provided, self.id_start_tree is used
        return (tuple): tuple with:
          1) startpoint tree (dictionary). Example of the structure:
            {
              'distance': 0,
              'vertex_id': <<vertex_nr>>,
              'target_level': <<'streefpeil'>>,
              'point': <<coordinates>>,
              'category': [],
              'children': [...]
            }
          2) tree if hydroobjects. Example of the structure:
            {
              'parent': None,
              'children': [{
                'hydro_id': hydro_id,
                'arc_id': arc_id,
                'flow': flow,
                'start_distance': round(distance),
                'end_distance': round(end_distance),
                'endpoint_type': 'startpoint'/ 'target' / 'between'/ 'end',
                'start_tree_item': start_tree_item,
                'feature': line_feature,
                # 'in_vertex_id': in_vertex_id,
                # 'out_vertex_id': out_vertex_id,
                # 'parent': parent_hydro_obj,
                'children': [..]
              },
              {...}]
            }
          3) list with startpoints, endpoints. Example of the structure:
            [{
              'vertex_id': ...,
              'arc_id': ...,
              'type': 'startpoint'/ 'target' / 'end',  // 'between' not in this list
              'branch_id': None,
            },
            ...]

        """

        endpoints = []
        checked_vertexes = {}

        def loop_recursive(
                parent_start_tree_item, parent_hydro_tree_item , parent_arc_id,
                target_level=None, category=None, distance=0):
            """
            recursive function for finding endpoints through walking through graph

            category not used yet (filter on layer is used to filter out nont primary water)
            global objects:
            - self.full_line_layer


            :param start_tree_item (dict): tree item of tree with start_lines. Used to store childs.
            :param hydro_tree_item (dict): tree item of tree of full tree with hydroobjects. Used to store childs.
            :param arc_id (int): arc number
            :param target_level:
            :param category:
            :param distance:
            :return:
            """

            parent_arc = self.graph.arc(parent_arc_id)
            parent_in_vertex_id = parent_arc.inVertex()
            parent_out_vertex_id = parent_arc.outVertex()
            parent_in_vertex = self.graph.vertex(parent_in_vertex_id)
            # filter reverse (bi-directional) arcs and circular arcs out
            child_arc_ids = [arc_id for arc_id in parent_in_vertex.outArc()
                             if not self.graph.arc(arc_id).inVertex() in checked_vertexes]
            # check if child link is not the reversed one of current arc (links with zero or None
            # flow are bi-directional, so filter these out
            # if arc_id == in_arc and len(linked_arcs) > 0 and \
            #         (parent_arc is None or self.tree[parent_arc.inVertex()] != self.tree[arc.inVertex()]):

            if len(child_arc_ids) == 0:
                branch_id = int(parent_arc.properties()[BRANCH_ID_PROPERTER_NR])
                endpoints.append({
                    'vertex_id': parent_out_vertex_id,
                    'arc_id': parent_arc_id,
                    'type': 'end',
                    'branch_id': branch_id,
                    'start_tree_item':  parent_start_tree_item,  # needed? - no use found in code
                })
                return

            # get category and flow for the hydroobjects - used for ordering the branches
            linked_arcs_sort = []
            for arc_id in child_arc_ids:
                arc = self.graph.arc(arc_id)

                arc_category = arc.properties()[CATEGORY_PROPERTER_NR] \
                    if arc.properties()[CATEGORY_PROPERTER_NR] is not None else 5.0

                flow = arc.properties()[FLOW_PROPERTER_NR]
                if flow == NULL:
                    # if flow is None, sum flows of upstream channels
                    flow = 0.0
                    for sub_arc_id in self.graph.vertex(arc.inVertex()).outArc():
                        sub_arc = self.graph.arc(sub_arc_id)
                        flow += sub_arc.properties()[FLOW_PROPERTER_NR] \
                            if sub_arc.properties()[FLOW_PROPERTER_NR] != NULL else 0.0

                linked_arcs_sort.append((arc_id, arc, flow, arc_category))

            # sort linked arcs on category and from highest flow to lowest flow
            linked_arcs_sort = reversed(sorted(linked_arcs_sort, key=lambda a: a[2] - 1000 * a[3]))

            for i, (arc_id, arc, flow, category) in enumerate(linked_arcs_sort):
                # collect information
                branch_id = int(arc.properties()[BRANCH_ID_PROPERTER_NR])
                request = QgsFeatureRequest().setFilterFid(branch_id)
                line_feature = self.full_line_layer.getFeatures(request).next()

                end_distance = distance + line_feature['lengte']
                branch_target_level = arc.properties()[TARGET_LEVEL_PROPERTER_NR]
                branch_category = arc.properties()[CATEGORY_PROPERTER_NR]
                flow = make_type(flow, float, round_digits=2)
                hydro_id = arc.properties()[HYDRO_ID_PROPERTER_NR]

                out_vertex_id = arc.outVertex()
                checked_vertexes[arc.inVertex()] = True

                start_tree_item = None
                if target_level is not None and branch_target_level != target_level:
                    endpoint_type = 'target'

                    start_tree_item = {
                        'target_level': branch_target_level,
                        'distance': distance,
                        'category': category,
                        'start_vertex_id': out_vertex_id,
                        'point': self.graph.vertex(out_vertex_id).point(),
                        'arc_id': arc_id,
                        'line_feature': line_feature,
                        'children': [],
                    }
                    parent_start_tree_item['children'].append(start_tree_item)
                else:
                    endpoint_type = 'between'

                hydro_tree_item = {
                    'hydro_id': hydro_id,
                    'arc_id': arc_id,
                    'flow': flow,
                    'start_distance': round(distance),
                    'end_distance': round(end_distance),
                    'endpoint_type': endpoint_type,
                    'start_tree_item':  parent_start_tree_item,  # needed? - no use found in code
                    'feature': line_feature,
                    # 'in_vertex_id': in_vertex_id,
                    # 'out_vertex_id': out_vertex_id,
                    # 'parent': parent_hydro_obj,
                    'children': []
                }

                parent_hydro_tree_item['children'].append(hydro_tree_item)

                # loop over upstream links
                if start_tree_item is not None:
                    par_start_tree_item = start_tree_item
                else:
                    par_start_tree_item = parent_start_tree_item

                loop_recursive(
                    par_start_tree_item, hydro_tree_item, arc_id,
                    branch_target_level, branch_category, end_distance
                )

        hydro_tree_item = {'parent': None, 'children': []}
        startingpoint_tree = []

        if start_vertex_nr is None:
            start_vertex_nr = self.id_start_tree

        if start_vertex_nr is not None:
            start_point_vertex = self.graph.vertex(start_vertex_nr)
            endpoints.append({
                'vertex_id': start_vertex_nr,
                'arc_id': None,
                'type': 'startpoint',
                'branch_id': None
            })

            for arc_id in self.graph.vertex(start_vertex_nr).outArc():
                arc = self.graph.arc(arc_id)

                branch_id = int(arc.properties()[BRANCH_ID_PROPERTER_NR])
                request = QgsFeatureRequest().setFilterFid(branch_id)
                line_feature = self.full_line_layer.getFeatures(request).next()

                category = arc.properties()[CATEGORY_PROPERTER_NR]
                target_level = line_feature['streefpeil']

                start_tree_item = {
                    'distance': 0,
                    'target_level': target_level,
                    'category': category,
                    'start_vertex_id': start_vertex_nr,
                    'point': self.graph.vertex(start_vertex_nr).point(),
                    'arc_id': arc_id,
                    'line_feature': line_feature,
                    'parent': None,
                    'children': []
                }
                startingpoint_tree.append(start_tree_item)

                loop_recursive(start_tree_item,
                               hydro_tree_item,
                               arc_id,
                               target_level=target_level,
                               category=category,
                               distance=0)

        return startingpoint_tree, hydro_tree_item, endpoints

    def add_point(self, qgs_point):
        """
        add point to selected Path

        qgs_point (QgsPoint): additional point
        return (tuple): tuple with:
                    0. boolean: successful added to path,
                    1. string: message
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

    def set_tree_startpoint(self, id_start_point):
        """
        set point (initial or next point) for expending path

        qgs_start_point (int): start point of tree for (extension) of path
        return: None
        """

        if id_start_point == -1:
            return

        # else create tree from this tree startpoint
        self.id_start_tree = id_start_point
        self.start_point_tree = self.graph.vertex(id_start_point).point()

        (self.tree, self.cost) = QgsGraphAnalyzer.dijkstra(self.graph,
                                                           self.id_start_tree,
                                                           0)
        self.tree_layer_up_to_date = False

    def set_tree_start_arc(self, id_start_arc):
        """
        set line (initial or next point) for expending path

        qgs_start_arc (QgsPoint): start point of tree for (extension) of path
        return: None
        """

        if id_start_arc == -1:
            return

        # else create tree from this tree startpoint
        arc = self.graph.arc(id_start_arc)
        self.id_start_tree = arc.inVertex()
        self.start_point_tree = self.graph.vertex(self.id_start_tree).point()

        (self.tree, self.cost) = QgsGraphAnalyzer.dijkstra(self.graph,
                                                           self.id_start_tree,
                                                           0)
        self.tree_layer_up_to_date = False

    def get_path(self, id_start_point, id_end_point, begin_distance=0):
        """
        get path between the to graph points

        id_start_point (int): graph identifier of start point of (sub)path
        id_end_point (int): graph identifier of end point of (sub) path
        begin_distance (float): start distance of cumulative path distance
        return (tuple): tuple with 3 values:
          0. successful found a path
          1. Message in case of not succesful found a path or
             a list of path line elements, represent as a tuple, with:
             0. begin distance of part (from initial start_point),
             1. end distance of part
             2. direction of path equal to direction of feature definition
                1 in case ot is, -1 in case it is the opposite direction
             3. feature
          2. list of vertexes (graph nodes)
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

            id_line = self.graph.arc(self.tree[cur_pos]).properties()[BRANCH_ID_PROPERTER_NR]

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

        root (LeggerTreeItem): root element of LeggerTreeModel
        return (bool): True if successful
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
                int(arc.properties()[BRANCH_ID_PROPERTER_NR]),
                int(arc.properties()[HYDRO_ID_PROPERTER_NR]),
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
                if arc.properties()[FLOW_PROPERTER_NR] == NULL:
                    # if None, sum flows of upstream channels
                    for sub_arc_id in self.graph.vertex(arc.inVertex()).outArc():
                        sub_arc = self.graph.arc(sub_arc_id)
                        flow += sub_arc.properties()[FLOW_PROPERTER_NR] \
                            if sub_arc.properties()[FLOW_PROPERTER_NR] != NULL else 0.0
                else:
                    flow = arc.properties()[FLOW_PROPERTER_NR]

                linked_arcs.append((arc_id, arc, flow))

            # sort on highest flow
            for i, (arc_id, arc, flow) in enumerate(reversed(sorted(linked_arcs, key=lambda a: a[2]))):

                # collect information and create
                branch_id = int(arc.properties()[BRANCH_ID_PROPERTER_NR])
                request = QgsFeatureRequest().setFilterFid(branch_id)
                line_feature = self.full_line_layer.getFeatures(request).next()

                distance_end = distance + line_feature['lengte']
                branch_depth = make_type(arc.properties()[DEPTH_PROPERTER_NR], float, round_digits=2)
                branch_variant_min_depth = make_type(arc.properties()[MIN_DEPTH_PROPERTER_NR], float, round_digits=2)
                branch_variant_max_depth = make_type(arc.properties()[MAX_DEPTH_PROPERTER_NR], float, round_digits=2)
                branch_width = line_feature['breedte']
                branch_target_level = arc.properties()[TARGET_LEVEL_PROPERTER_NR]
                branch_category = arc.properties()[CATEGORY_PROPERTER_NR]
                flow = make_type(arc.properties()[FLOW_PROPERTER_NR], float, round_digits=2)
                hydro_id = arc.properties()[HYDRO_ID_PROPERTER_NR]
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
                        branch_target_level, branch_category)

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
                        'selected_depth': (
                            line_feature['geselecteerd_diepte'] if line_feature[
                                                                       'geselecteerd_diepte'] != NULL else None),
                        'selected_width': (
                            line_feature['geselecteerd_breedte'] if line_feature[
                                                                        'geselecteerd_breedte'] != NULL else None),
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
                        tree_item = LeggerTreeItem(hydrovak, grandparent_tree_item)
                        grandparent_tree_item.appendChild(tree_item)
                    elif i == 1:
                        tree_item = LeggerTreeItem(hydrovak, parent_tree_item)
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
                        split_item = LeggerTreeItem(split_hydrovak, parent_tree_item)
                        parent_tree_item.insertChild(i - 2, split_item)
                        tree_item = LeggerTreeItem(hydrovak, split_item)
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

    def reset(self):
        """
        reset found route

        return: None
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
