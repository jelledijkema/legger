# -*- coding: utf-8 -*-
import os
from PyQt4.QtCore import QVariant
from qgis.core import QgsField, QgsVectorLayer, QgsDataSourceURI, QgsMapLayerRegistry
from legger.utils.map_layers import LayerManager


class LeggerMapManager(object):

    def __init__(self, iface, path_legger_db):
        """
            path_legger_db (str): path to legger sqlite
         """

        self.path_legger_db = path_legger_db
        self.iface = iface

        self.map_manager = LayerManager(self.iface, self.path_legger_db)
        self.map_manager.add_layers_to_map()

        self.network_layer_group, new = self.map_manager.get_or_create_networktool_root(clear=True)
        self.style_path = os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            'layer_styles', 'legger')

        self._virtual_tree_layer = None
        self._endpoint_layer = None
        self._track_layer = None
        self._hover_layer = None
        self._hover_startpoint_layer = None
        self._selected_layer = None

    def get_line_layer(self, add_to_map=False, geometry_col='geometry'):
        """ get QGis instance of hydrovak with kenmerken as layer

        add_to_map (bool): add layer to map, including default styling
        geometry_col (str): column used as geometry

        return (QgsVectorLayer): vector layer of hydrovak with kenmerken table
        """

        def get_layer(spatialite_path, table_name, geom_column=''):
            uri2 = QgsDataSourceURI()
            uri2.setDatabase(spatialite_path)
            uri2.setDataSource('', table_name, geom_column)

            return QgsVectorLayer(
                uri2.uri(),
                table_name,
                'spatialite')

        layer = get_layer(
            self.path_legger_db,
            'hydroobjects_kenmerken3',
            geometry_col)

        # todo: remove this filter when bidirectional islands are supported
        layer.setSubsetString('"direction"!=3')

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                layer,
                os.path.join(self.style_path, 'line.qml')
            )

        return layer

    def get_virtual_tree_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._virtual_tree_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
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

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._virtual_tree_layer,
                os.path.join(self.style_path, 'tree_classified.qml')
            )
        return self._virtual_tree_layer

    def get_endpoint_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._endpoint_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
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

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._endpoint_layer,
                os.path.join(self.style_path, 'end_points.qml')
            )

        return self._endpoint_layer

    def get_track_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._track_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
            self._track_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "Geselecteerde traject",
                "memory")

            self._track_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._track_layer.updateFields()

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._track_layer,
                os.path.join(self.style_path, 'selected_traject.qml')
            )

        return self._track_layer

    def get_hover_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._hover_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
            self._hover_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "hover",
                "memory")

            self._hover_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._hover_layer.updateFields()

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._hover_layer,
                os.path.join(self.style_path, 'hover_hydro.qml')
            )

        return self._hover_layer

    def get_selected_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._selected_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
            self._selected_layer = QgsVectorLayer(
                "linestring?crs={0}".format(crs),
                "geselecteerd",
                "memory")

            self._selected_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._selected_layer.updateFields()

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._selected_layer,
                os.path.join(self.style_path, 'selected_hydro.qml')
            )

        return self._selected_layer

    def get_hover_startpoint_layer(self, add_to_map=False):
        """
        return a (link to) an in memory QgsVectorLayer of the current active
        tree. The layer will be updated during when the tree (or tree start
        point) changes

        return (QgsVectorLayer): QgsVectorLayer in memory.
        """

        if not self._hover_startpoint_layer:
            # create_layer
            crs = self.get_line_layer().crs().authid()
            self._hover_startpoint_layer = QgsVectorLayer(
                "point?crs={0}".format(crs),
                "start_point_hover",
                "memory")

            self._hover_startpoint_layer.dataProvider().addAttributes([
                QgsField("line_id", QVariant.LongLong)])

            self._hover_startpoint_layer.updateFields()

        if add_to_map:
            self.map_manager.add_layer_to_group(
                self.network_layer_group,
                self._hover_startpoint_layer,
                os.path.join(self.style_path, 'hover_startpoint.qml')
            )

        return self._hover_startpoint_layer
