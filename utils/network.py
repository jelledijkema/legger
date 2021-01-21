# -*- coding: utf-8 -*-
import logging
import sqlite3
from collections import OrderedDict
from typing import List

DISTANCE_PROPERTER_NR = 0
FEAT_ID_PROPERTER_NR = 1

min_flow = 0.0000001

logger = logging.getLogger(__name__)


def set_spatial_extension(con, connection_record):
    """Load spatialite extension as described in
    https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html"""
    import sqlite3

    con.enable_load_extension(True)
    cur = con.cursor()
    libs = [
        # SpatiaLite >= 4.2 and Sqlite >= 3.7.17, should work on all platforms
        ("mod_spatialite", "sqlite3_modspatialite_init"),
        # SpatiaLite >= 4.2 and Sqlite < 3.7.17 (Travis)
        ("mod_spatialite.so", "sqlite3_modspatialite_init"),
        # SpatiaLite < 4.2 (linux)
        ("libspatialite.so", "sqlite3_extension_init"),
    ]
    found = False
    for lib, entry_point in libs:
        try:
            cur.execute("select load_extension('{}', '{}')".format(lib, entry_point))
        except sqlite3.OperationalError:
            logger.exception(
                "Loading extension %s from %s failed, trying the next", entry_point, lib
            )
            continue
        else:
            logger.info("Successfully loaded extension %s from %s.", entry_point, lib)
            found = True
            break
    if not found:
        raise RuntimeError("Cannot find any suitable spatialite module")
    cur.close()
    con.enable_load_extension(False)


def load_spatialite(path: str):
    con = sqlite3.connect(path)
    set_spatial_extension(con, '')
    return con


def merge_dicts(x, y):
    """merge two dictionaries into a new dictionary (for python 2.x).
    For python 3.x use {**x, **y}"""
    z = x.copy()
    z.update(y)
    return z


class Definitions(object):
    DEBIET_3DI = '3di'
    DEBIET_CORRECTED = 'corrected'
    FORCED = 'forced'


class Line(Definitions):

    def __init__(self, oid, startnode_id, endnode_id, category, length,
                 debiet_3di, debiet_modified, has_startnode=False, **extra):
        self.graph = None
        self.nr = None
        self.id = oid
        self.startnode_id = startnode_id
        self.endnode_id = endnode_id
        self.startnode_nr = None
        self.endnode_nr = None
        self.has_startnode = has_startnode

        self.category = category
        self.length = length
        self.debiet_3di = debiet_3di
        self.debiet_modified = debiet_modified

        self.reversed = False
        self.forced_direction = False

        self.extra_data = {
            **extra
        }

    def start_node(self):
        return self.graph.node(self.startnode_nr)

    def end_node(self):
        return self.graph.node(self.endnode_nr)

    def debiet(self, modus=Definitions.DEBIET_3DI):
        if modus == Definitions.DEBIET_CORRECTED:
            return self.debiet_modified
        else:
            return self.debiet_3di

    def set_debiet_modified(self, debiet):
        if debiet is not None and self.debiet_3di is not None and self.debiet_3di < 0 and not self.forced_direction:
            self.debiet_modified = -debiet
        else:
            self.debiet_modified = debiet

    def inflow_node(self, modus=Definitions.DEBIET_3DI):
        if self.debiet(modus) is None or self.debiet(modus) >= 0 or (
                modus == Definitions.FORCED and self.forced_direction):
            return self.graph.node(self.startnode_nr)
        else:
            return self.graph.node(self.endnode_nr)

    def outflow_node(self, modus=Definitions.DEBIET_3DI):
        if self.debiet(modus) is None or self.debiet(modus) >= 0 or (
                modus == Definitions.FORCED and self.forced_direction):
            return self.graph.node(self.endnode_nr)
        else:
            return self.graph.node(self.startnode_nr)

    def weight(self):
        if self.debiet_3di is None:
            return self.length
        elif self.debiet_3di > 0:
            return self.length / 5
        else:  # self.debiet_3di < 0:
            return self.length * 5

    def weight_rev(self):
        if self.debiet_3di is None:
            return self.length
        elif self.debiet_3di > 0:
            return self.length * 5
        else:  # self.debiet_3di < 0:
            return self.length / 5

    def reverse(self):
        self.reversed = not self.reversed
        if self.debiet_3di is not None:
            self.debiet_3di = -self.debiet_3di
        if self.debiet_modified is not None:
            self.debiet_modified = -self.debiet_modified

        start_node = self.start_node()
        end_node = self.end_node()

        # remove links on nodes on both sides
        start_node.outgoing_nrs = [nr for nr in start_node.outgoing_nrs if nr != self.nr]
        end_node.incoming_nrs = [nr for nr in end_node.incoming_nrs if nr != self.nr]

        # switch
        self.startnode_id, self.endnode_id = self.endnode_id, self.startnode_id
        self.startnode_nr, self.endnode_nr = self.endnode_nr, self.startnode_nr
        start_node, end_node = end_node, start_node

        # add links on nodes on both sides
        start_node.outgoing_nrs.append(self.nr)
        end_node.incoming_nrs.append(self.nr)


class Node(Definitions):

    def __init__(self, oid, **extra):
        self.graph = None
        self.nr = None
        self.id = oid

        self.min_category = 999

        self.incoming_nrs = []
        self.outgoing_nrs = []

    def incoming(self):
        return [self.graph.line(nr) for nr in self.incoming_nrs]

    def outgoing(self):
        return [self.graph.line(nr) for nr in self.outgoing_nrs]

    def waterbalance(self, modus=Definitions.DEBIET_3DI):
        flow = self.flow(modus)

        return flow.get('outflow_debiet') - flow.get('inflow_debiet')

    def inflow(self, modus=Definitions.DEBIET_3DI, include_nones=False):
        out = []
        forced = modus == Definitions.FORCED
        for line in self.incoming():
            flow = line.debiet(modus)
            if flow is None or flow >= 0.0 or (forced and line.forced_direction):
                # keep defined direction
                out.append(line)
        for line in self.outgoing():
            flow = line.debiet(modus)
            if include_nones and flow is None:
                out.append(line)
            elif flow is not None and flow < 0.0 and (not forced or not line.forced_direction):
                out.append(line)
        return out

    def outflow(self, modus=Definitions.DEBIET_3DI, include_nones=False):
        out = []
        forced = modus == Definitions.FORCED
        for line in self.outgoing():
            flow = line.debiet(modus)
            if flow is None or flow >= 0.0 or (forced and line.forced_direction):
                # keep defined direction
                out.append(line)
        for line in self.incoming():
            flow = line.debiet(modus)
            if include_nones and flow is None:
                out.append(line)
            if flow is not None and flow < 0.0 and (not forced or not line.forced_direction):
                out.append(line)
        return out

    def flow(self, modus=Definitions.DEBIET_3DI):
        inflow = self.inflow(modus)
        outflow = self.outflow(modus)

        if modus == Definitions.DEBIET_CORRECTED:
            field = 'debiet_modified'
        else:
            field = 'debiet_3di'

        return {
            'inflow_nr': len(inflow),
            'outflow_nr': len(outflow),
            'inflow_debiet': sum([(abs(getattr(l, field)) if getattr(l, field) is not None else 0) for l in inflow]),
            'outflow_debiet': sum([(abs(getattr(l, field)) if getattr(l, field) is not None else 0) for l in outflow]),
        }

    def flow_modified(self):
        return self.flow('debiet_modified')


class Graph(Definitions):

    def __init__(self, nodes: List[Node], lines: List[Line]):
        self.nodes = nodes
        self.lines = lines

        self.manual_startnodes = []

        # set nr and update links
        for nr, node in enumerate(self.nodes):
            node.nr = nr
            node.graph = self
        for nr, line in enumerate(self.lines):
            line.nr = nr
            line.graph = self

        nodes_dict = {node.id: node for node in nodes}

        for line in lines:
            start_node = nodes_dict[line.startnode_id]
            start_node: Node
            line.startnode_nr = start_node.nr
            start_node.outgoing_nrs.append(line.nr)

            end_node = nodes_dict[line.endnode_id]
            end_node: Node
            line.endnode_nr = end_node.nr
            end_node.incoming_nrs.append(line.nr)

            start_node.min_category = min(start_node.min_category, line.category) \
                if line.category is not None else start_node.min_category
            end_node.min_category = min(end_node.min_category, line.category) \
                if line.category is not None else end_node.min_category

            if line.has_startnode:
                self.manual_startnodes.append(line.outflow_node())
        self.manual_startnodes = list(set(self.manual_startnodes))

    def node(self, nr):
        return self.nodes[nr]

    def line(self, nr):
        return self.lines[nr]

    def correct_direction_on_debiet_3di(self):
        for line in self.lines:
            if line.debiet_3di is not None and line.debiet_3di < 0:
                line.reverse()

    def correct_direction_on_debiet_modified(self):
        for line in self.lines:
            if line.debiet_modified is not None and line.debiet_modified < 0:
                line.reverse()

    def get_startnodes(self, modus=Definitions.DEBIET_3DI, ignore_manual=False) -> List[Node]:
        if not ignore_manual and len(self.manual_startnodes) > 0:
            return self.manual_startnodes

        start_nodes = []
        for node in self.nodes:
            if len(node.outflow(modus)) == 0:
                start_nodes.append(node)
        return start_nodes

    def get_endnodes(self, modus=Definitions.DEBIET_3DI) -> List[Node]:
        end_nodes = []
        for node in self.nodes:
            if len(node.inflow(modus)) == 0:
                end_nodes.append(node)
        return end_nodes


class Network(object):
    """Network class for providing network functions and direrequired for Legger tool"""

    # todo:
    #     - better support bidirectional islands (if needed and exmaples popup in tests/ usage)
    #     - move virtual_layer and endpoint_layer outside this class
    #     - set endpoints on 90% or 10 meter before endpoint of hydrovak

    def __init__(self, spatialite_path, graph=None):
        """
        spatialite_path (str): path to spatialite
        """

        self.spatialite_path = spatialite_path

        self._cursor = None

        self._graph = graph

        # init class attributes
        self.start_arcs = None  # list of dicts with arc_nr, point (x, y), list childs, parent
        self.start_arc_tree = None

    @property
    def db_cursor(self):
        if not self._cursor:
            con_legger = load_spatialite(self.spatialite_path)
            self._cursor = con_legger.cursor()

        return self._cursor

    def save_network_values(self):
        start_nodes = [n.id for n in self.graph.get_startnodes(modus=Definitions.DEBIET_3DI)]

        self.db_cursor.executemany("""
            UPDATE hydroobject SET
                eindpunt_potentieel=?,
                geforceerd_omgedraaid=?,
                routing_gewicht=?,
                debiet_aangepast=?
            WHERE 
                id=?      
        """, [(l.outflow_node().id in start_nodes, l.forced_direction, l.extra_data.get('weight'),
               -l.debiet_modified if l.debiet_modified is not None and l.reversed else l.debiet_modified,
               l.id) for l in self.graph.lines])

        self.db_cursor.executemany("""
            UPDATE graph_nodes SET
                org_wb=?,
                new_wb=?
            WHERE 
                id=?      
        """, [(n.waterbalance(modus=Definitions.DEBIET_3DI), n.waterbalance(modus=Definitions.DEBIET_CORRECTED), n.id)
              for n in self.graph.nodes])

        self.db_cursor.execute("""
                    UPDATE graph_nodes 
                    SET
                        wb_diff= (org_wb - new_wb)      
                """)

        self.db_cursor.execute("""SELECT UpdateLayerStatistics(\'hydroobject\');""")
        self.db_cursor.connection.commit()

    def build_graph_tables(self):

        self.db_cursor.executescript("""
        -- maak alle begin en eindpunten
            DROP TABLE IF EXISTS tmp_line_nodes
            ;

            CREATE TABLE tmp_line_nodes AS
            SELECT ROW_NUMBER() OVER (ORDER BY hydro_id, type DESC) as id, line_nodes.*
            FROM
            (SELECT id || 's' as ids, id as hydro_id, 'start' as type,  ST_Startpoint(GEOMETRY) AS geometry
                FROM hydroobject
                UNION ALL
                SELECT id || 'e' as ids, id as hydro_id, 'eind' as type,  ST_Endpoint(GEOMETRY) AS geometry
                FROM hydroobject) AS line_nodes
            ;

            -- registreer de geometry (alleen bij debuggen)
            --SELECT RecoverGeometryColumn( 'tmp_line_nodes' , 'geometry' , 28992 , 'POINT' );

            -- combineer begin en eindpunten tot unieke punten voor elke locatie 
            DROP TABLE IF EXISTS graph_nodes
            ;

            CREATE TABLE graph_nodes AS
            SELECT 
            ROW_NUMBER() OVER (ORDER BY id) as id, 
            geometry, 
            0.0 as org_wb, 
            0.0 as new_wb, 
            0.0 as wb_diff,
            group_concat(id) as tmp_line_node_id, group_concat(ids) as tmp_line_node_ids
            FROM
            tmp_line_nodes
            GROUP BY geometry
            ORDER BY id
            ;

            -- registreer de geometry
            SELECT RecoverGeometryColumn( 'graph_nodes' , 'geometry' , 28992 , 'POINT' );

            -- de graph lines als verlengde van de hydrovakken
            DROP TABLE IF EXISTS graph_lines
            ;

            CREATE TABLE graph_lines AS
            SELECT 
            ho.id as hydro_id, gns.id as startnode_id, gns.tmp_line_node_ids, gne.id as endnode_id, gne.tmp_line_node_ids
            FROM
            hydroobject ho
            INNER JOIN tmp_line_nodes tlns ON tlns.hydro_id =  ho.id AND tlns.type = 'start'
            INNER JOIN graph_nodes gns ON tlns.geometry = gns.geometry
            INNER JOIN tmp_line_nodes tlne ON tlne.hydro_id =  ho.id AND tlne.type = 'eind'
            INNER JOIN graph_nodes gne ON tlne.geometry = gne.geometry
            ;

            -- ruim tijdelijke tabellen op
            DROP TABLE IF EXISTS tmp_line_nodes
            ;
        """)
        self.db_cursor.execute('vacuum')

        return

    @property
    def graph(self):
        if self._graph is None:
            self.db_cursor.execute("""
                SELECT id FROM graph_nodes
            """)

            nodes = [Node(nr=nr, oid=r[0]) for nr, r in enumerate(self.db_cursor.fetchall())]

            self.db_cursor.execute("""
                SELECT gl.hydro_id as hydro_id, gl.startnode_id, gl.endnode_id, ho.categorieoppwaterlichaam, ST_LENGTH(ho.geometry), ho.debiet_3di, ho.eindpunt_geselecteerd
                FROM 
                    graph_lines gl
                INNER JOIN hydroobject ho ON ho.id = gl.hydro_id
            """)
            lines = [
                Line(nr=nr, oid=r[0], startnode_id=r[1], endnode_id=r[2], category=r[3], length=r[4], debiet_3di=r[5],
                     debiet_modified=None, has_startnode=r[6]) for nr, r in enumerate(self.db_cursor.fetchall())]

            self._graph = Graph(
                lines=lines,
                nodes=nodes
            )
        return self._graph

    def force_direction(self):
        # line_nr, weight, freeze
        tree = [[None, float("inf"), False, n.min_category] for n in self.graph.nodes]

        # node, tot_weight
        primary_start_nodes = [[n, 0] for n in self.graph.get_startnodes() if n.min_category == 1]

        queue = primary_start_nodes

        # first see what can be reached using the current directions or in case of None values be walking over these
        # primary weight is length and in case of none debiet 2x length
        while len(queue) > 0:
            node, tot_weight = queue.pop()
            for line in node.inflow(include_nones=True):
                line: Line
                if line.category == 1:
                    to_node = line.inflow_node()
                    if line.debiet_3di is None:
                        factor = 2
                    else:
                        factor = 1
                    weight = tot_weight + factor * line.length
                    if weight < tree[to_node.nr][1]:
                        tree[to_node.nr][0] = line.nr
                        tree[to_node.nr][1] = weight
                        queue.append([to_node, weight])

        # freeze all values made based on connection with
        tree = [[line_nr, weight, line_nr is not None, min_cat] for line_nr, weight, freeze, min_cat in tree]

        # second, force primary not yet reached by routing
        # primary weight is length, in case of none debiet 2x length and in case of negative debiet 3x length
        # now add 'shortest' route algoritm for 'shortest' path to both flow locations
        # include all done nodes in queue
        queue = [[self.graph.node(node_nr), weight] for node_nr, [line_nr, weight, freeze, min_cat] in enumerate(tree)
                 if line_nr is not None and min_cat == 1]
        while len(queue) > 0:
            node, tot_weight = queue.pop()
            for line in node.outgoing():
                line: Line
                if line.category == 1:
                    to_node = line.end_node()
                    if tree[to_node.nr][2]:
                        # freezed, so skip
                        continue
                    if line.debiet_3di is None:
                        factor = 2
                    elif line.debiet_3di >= 0:
                        factor = 1
                    else:
                        factor = 3
                    weight = tot_weight + factor * line.length
                    if weight < tree[to_node.nr][1]:
                        tree[to_node.nr][0] = line.nr
                        tree[to_node.nr][1] = weight
                        queue.append([to_node, weight])

            for line in node.incoming():
                line: Line
                if line.category == 1:
                    to_node = line.start_node()
                    if tree[to_node.nr][2]:
                        # freezed, so skip
                        continue
                    if line.debiet_3di is None:
                        factor = 2
                    elif line.debiet_3di <= 0:
                        factor = 1
                    else:
                        factor = 3
                    weight = tot_weight + factor * line.length
                    if weight < tree[to_node.nr][1]:
                        tree[to_node.nr][0] = line.nr
                        tree[to_node.nr][1] = weight
                        queue.append([to_node, weight])

        # freeze all values made based on connection with
        tree = [[line_nr, weight, line_nr is not None, min_cat] for line_nr, weight, freeze, min_cat in tree]

        # third, link other categories following the flow_direction.
        # category 2 weight is 1.5 X length, other categories are 2 x length
        # for debiet is none values x 2
        # include all done nodes in queue
        queue = [[self.graph.node(node_nr), weight] for node_nr, [line_nr, weight, freeze, min_cat] in enumerate(tree)
                 if line_nr is not None]

        while len(queue) > 0:
            node, tot_weight = queue.pop()
            if node.id == 113:
                a = 1

            for line in node.inflow(include_nones=True):
                line: Line
                to_node = line.inflow_node()
                if tree[to_node.nr][2]:
                    # freezed, so skip
                    continue

                if line.debiet_3di is None:
                    factor = 2
                else:
                    factor = 1
                if line.category == 2:
                    factor *= 1.5
                else:
                    factor *= 2
                weight = tot_weight + factor * line.length
                if weight < tree[to_node.nr][1]:
                    tree[to_node.nr][0] = line.nr
                    tree[to_node.nr][1] = weight
                    queue.append([to_node, weight])

        # freeze all values made based on connection with
        tree = [[line_nr, weight, line_nr is not None, min_cat] for line_nr, weight, freeze, min_cat in tree]

        # last, force water not yet reached by routing
        # category 2 weight is 1.5 X length, other categories are 2 x length
        # for debiet is none values x 2, in case of negative debiet x 3
        # now add 'shortest' route algoritm for 'shortest' path to both flow locations
        # include all done nodes in queue
        queue = [[self.graph.node(node_nr), weight] for node_nr, [line_nr, weight, freeze, min_cat] in enumerate(tree)
                 if line_nr is not None]
        while len(queue) > 0:
            node, tot_weight = queue.pop()
            if node.id == 113:
                a = 1

            for line in node.outgoing():
                line: Line
                to_node = line.end_node()
                if tree[to_node.nr][2]:
                    # freezed, so skip
                    continue
                if line.debiet_3di is None:
                    factor = 2
                elif line.debiet_3di >= 0:
                    factor = 1
                else:
                    factor = 3

                if line.category == 2:
                    factor *= 1.5
                else:
                    factor *= 2

                weight = tot_weight + factor * line.length
                if weight < tree[to_node.nr][1]:
                    tree[to_node.nr][0] = line.nr
                    tree[to_node.nr][1] = weight
                    queue.append([to_node, weight])

            for line in node.incoming():
                line: Line
                to_node = line.start_node()
                if tree[to_node.nr][2]:
                    # freezed, so skip
                    continue
                if line.debiet_3di is None:
                    factor = 2
                elif line.debiet_3di <= 0:
                    factor = 1
                else:
                    factor = 3

                if line.category == 2:
                    factor *= 1.5
                else:
                    factor *= 2

                weight = tot_weight + factor * line.length
                if weight < tree[to_node.nr][1]:
                    tree[to_node.nr][0] = line.nr
                    tree[to_node.nr][1] = weight
                    queue.append([to_node, weight])

        for node_nr, [line_nr, weight, _, _] in enumerate(tree):
            if line_nr is not None:
                line = self.graph.line(line_nr)
                if line.id == 1084919:
                    a = 1

                line.extra_data['weight'] = weight
                if line.inflow_node().nr != node_nr:
                    if line.debiet_3di is None or line.debiet_3di > 0:
                        line.reverse()
                    line.forced_direction = True
        for line in self.graph.lines:
            if line.extra_data.get('weight') is None:
                if line.id == 1084919:
                    a = 1
                weight_inflow = tree[line.inflow_node().nr][1]
                weight_outflow = tree[line.outflow_node().nr][1]
                if weight_inflow is not None and weight_outflow is not None:
                    if True and line.debiet_3di is not None:
                        line.extra_data['weight'] = weight_outflow
                    elif weight_inflow < weight_outflow:
                        line.extra_data['weight'] = weight_outflow
                        if line.debiet_3di is None or line.debiet_3di > 0:
                            line.reverse()
                        line.forced_direction = True
                    else:
                        line.extra_data['weight'] = weight_inflow
                    line.extra_data['tree_end'] = True

        return tree

    def re_distribute_flow(self):

        node_done = [False for i in self.graph.nodes]

        # set initial vertex_queue on points with no upstream vertexes
        node_queue = OrderedDict([(node.id, node) for node in self.graph.get_endnodes(modus=Definitions.FORCED)])
        # remove duplicates

        last_node = list(node_queue.values())[-1]

        c_last_repeated = 0

        while len(node_queue) > 0:
            node = node_queue.popitem(last=False)[1]
            # if node == last_added_node:
            #     break

            if 340156 in [l.id for l in node.outflow(modus=Definitions.FORCED)]:
                a = 1

            flow = node.flow(modus=Definitions.FORCED)
            flow_3di = node.flow(modus=Definitions.DEBIET_3DI)
            added_flow_on_point = flow_3di['outflow_debiet'] - flow_3di['inflow_debiet']
            if flow['inflow_nr'] == 0:
                node_done[node.nr] = True
                for line in node.outflow(modus=Definitions.FORCED):
                    line.set_debiet_modified(max(min_flow,
                                                 added_flow_on_point) if line.debiet_3di is not None else min_flow)
                    add_node = line.outflow_node(modus=Definitions.FORCED)
                    if not node_done[add_node.nr]:
                        node_queue[add_node.id] = add_node
                if len(node_queue) > 0:
                    last_node = [*node_queue.values()][-1]
            elif flow['outflow_nr'] == 0:
                # end, ready
                node_done[node.nr] = True
                if len(node_queue) > 0:
                    last_node = [*node_queue.values()][-1]
            else:
                all_inflows_not_known = len(
                    [l for l in node.inflow(modus=Definitions.FORCED) if l.debiet_modified is None])
                if 1084919 in [l.id for l in node.inflow(modus=Definitions.FORCED)] and all_inflows_not_known == 0:
                    a = 1

                if all_inflows_not_known == 0:
                    # all inflows are known, so we can process this node
                    modified_flow_in = sum(
                        [abs(l.debiet_modified) for l in node.inflow(modus=Definitions.FORCED)]) + added_flow_on_point
                    if modified_flow_in < 0:
                        # this can not happen
                        modified_flow_in = 0
                    primary_out = [l for l in node.outflow(modus=Definitions.FORCED) if
                                   l.category == 1 and l.debiet_modified is None]
                    other_out = [l for l in node.outflow(modus=Definitions.FORCED) if
                                 l.category != 1 and l.debiet_modified is None]
                    if len(primary_out) == 1:
                        primary_out[0].set_debiet_modified(max(modified_flow_in, min_flow))
                        for line in other_out:
                            line.set_debiet_modified(min_flow)
                    elif len(primary_out) == 0:
                        if len(other_out) == 1:
                            other_out[0].set_debiet_modified(max(modified_flow_in, min_flow))
                        else:
                            # multiple other.....
                            # filter out None values and zet minimum to min_flow (for example when direction is forced)
                            total_outflow = sum([max(min_flow, abs(l.debiet_3di if l.debiet_3di is not None else 0))
                                                 for l in other_out])
                            if total_outflow > 0:
                                factor = modified_flow_in / total_outflow
                            else:
                                factor = None
                            for line in other_out:
                                if factor is None:
                                    line.set_debiet_modified(min_flow)
                                else:
                                    flow = max(min_flow, abs(line.debiet_3di) if line.debiet_3di else min_flow)
                                    line.set_debiet_modified(flow * factor if flow != min_flow else min_flow)
                    else:
                        # multiple primary.....
                        # filter out None values and zet minimum to min_flow (for example when direction is forced)
                        total_primary_outflow = sum([max(min_flow, abs(l.debiet_3di if l.debiet_3di is not None else 0))
                                                     for l in primary_out])
                        if total_primary_outflow > 0:
                            factor = modified_flow_in / total_primary_outflow
                        else:
                            factor = None
                        for line in primary_out:
                            if factor is None:
                                line.set_debiet_modified(min_flow)
                            else:
                                flow = max(min_flow, abs(line.debiet_3di) if line.debiet_3di else min_flow)
                                line.set_debiet_modified(flow * factor if flow != min_flow else min_flow)

                        for line in other_out:
                            line.set_debiet_modified(min_flow)

                    node_done[node.nr] = True
                    for line in primary_out + other_out:
                        add_node = line.outflow_node(modus=Definitions.FORCED)
                        if not node_done[add_node.nr]:
                            node_queue[add_node.id] = add_node

                    if len(node_queue) > 0:
                        last_node = [*node_queue.values()][-1]
                else:
                    # wait with this node. add it to the end of the stack.
                    node_queue[node.id] = node
                    if node == last_node:
                        print(node.nr)

                        for node in [*node_queue.values()]:
                            # for circulars set tree end parts in current endnode list to minflow
                            for line in node.inflow(modus=Definitions.FORCED):
                                if line.extra_data.get('tree_end'):
                                    line.set_debiet_modified(min_flow)

                        if c_last_repeated in [25, 40]:
                            # for larger circulars set all tree end parts to minflow and add these endpoints to the queue

                            for line in self.graph.lines:
                                if line.extra_data.get('tree_end') and line.debiet_modified is None:
                                    line.set_debiet_modified(min_flow)
                                    add_node = line.outflow_node(modus=Definitions.FORCED)
                                    if not node_done[add_node.nr]:
                                        node_queue[add_node.id] = add_node
                            if len(node_queue) > 0:
                                last_node = [*node_queue.values()][-1]

                        c_last_repeated += 1
                        if c_last_repeated > 50:
                            print(
                                "loop over 'open' nodes, without fixing one. seems we are in an endless loop. Probably "
                                "there is a loop flow.")
                            return False, node_queue

        return True, []

    def build_tree(self):
        """
        function that analyses tree and creates tree structure of network.
        Sets self.arc_tree and self.start_arcs

        returns (tuple): tuple with dictionary of arc_tree en list of start arc_nrs
        """

        pass
