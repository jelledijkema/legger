# -*- coding: utf-8 -*-
import os
from PyQt4.QtCore import QVariant
from qgis.core import QgsField, QgsVectorLayer, QgsDataSourceURI, QgsMapLayerRegistry


class LeggerMapManager(object):

    def __init__(self, path_legger_db):
        """
            path_legger_db (str): path to legger sqlite
         """

        self.path_legger_db = path_legger_db

        self._virtual_tree_layer = None
        self._endpoint_layer = None
        self._track_layer = None
        self._hover_layer = None
        self._hover_startpoint_layer = None
        self._selected_layer = None


    def get_line_layer(self,add_to_map=False, geometry_col='geometry'):
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
            'hydroobjects_kenmerken',
            geometry_col)

        # todo: remove this filter when bidirectional islands are supported
        layer.setSubsetString('"direction"!=3')

        if add_to_map:
            layer.loadNamedStyle(os.path.join(
                os.path.dirname(__file__), os.pardir,
                'layer_styles', 'legger', 'line.qml'))
            QgsMapLayerRegistry.instance().addMapLayer(layer)

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
            self._virtual_tree_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'tree_classified.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._virtual_tree_layer)

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
            self._endpoint_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'end_points.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._endpoint_layer)

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
            self._track_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'selected_traject.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._track_layer)

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
            self._hover_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'hover_hydro.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._hover_layer)

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
            self._selected_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'selected_hydro.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._selected_layer)

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
            self._hover_startpoint_layer.loadNamedStyle(os.path.join(
                os.path.dirname(os.path.realpath(__file__)), os.pardir,
                'layer_styles', 'legger', 'hover_startpoint.qml'))

            QgsMapLayerRegistry.instance().addMapLayer(self._hover_startpoint_layer)

        return self._hover_startpoint_layer
