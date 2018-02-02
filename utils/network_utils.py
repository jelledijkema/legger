from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor
from qgis.core import QGis, QgsCoordinateTransform, QgsDistanceArea, QgsFeatureRequest, QgsPoint, QgsRectangle
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker
from qgis.networkanalysis import QgsArcProperter

from .formats import python_value


class NetworkTool(QgsMapTool):
    def __init__(self, canvas, line_layer, callback_on_select):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.line_layer = line_layer
        self.callback_on_select = callback_on_select

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        pass

    def canvasReleaseEvent(self, event):
        # Get the click
        x = event.pos().x()
        y = event.pos().y()

        # use 5 pixels for selecting
        point_ll = self.canvas.getCoordinateTransform().toMapCoordinates(x - 5,
                                                                         y - 5)
        point_ru = self.canvas.getCoordinateTransform().toMapCoordinates(x + 5,
                                                                         y + 5)
        rect = QgsRectangle(min(point_ll.x(), point_ru.x()),
                            min(point_ll.y(), point_ru.y()),
                            max(point_ll.x(), point_ru.x()),
                            max(point_ll.y(), point_ru.y()))

        transform = QgsCoordinateTransform(
            self.canvas.mapSettings().destinationCrs(), self.line_layer.crs())

        rect = transform.transform(rect)
        filter = QgsFeatureRequest().setFilterRect(rect)
        selected = self.line_layer.getFeatures(filter)

        clicked_point = self.canvas.getCoordinateTransform(
        ).toMapCoordinates(x, y)
        # transform to wgs84 (lon, lat) if not already:
        transformed_point = transform.transform(clicked_point)

        selected_points = [s for s in selected]
        if len(selected_points) > 0:
            self.callback_on_select(selected_points, transformed_point)

    def activate(self):
        self.canvas.setCursor(QCursor(Qt.CrossCursor))

    def deactivate(self):
        self.deactivated.emit()
        self.canvas.setCursor(QCursor(Qt.ArrowCursor))

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False


class LeggerDistancePropeter(QgsArcProperter):
    """custom properter for graph layer"""

    def __init__(self, field=None):
        QgsArcProperter.__init__(self)
        self.field = 'distance' if field is None else field

    def property(self, distance, feature):

        if self.field == 'distance':
            value = distance  # feature['real_length']
            if python_value(value) is None:
                # provided distance is not correct, so do a correct calculation
                # value = distance
                d = QgsDistanceArea()
                value, unit = d.convertMeasurement(
                    feature.geometry().length(),
                    QGis.Degrees, QGis.Meters, False)
            return value
        else:
            return feature[self.field]


    def requiredAttributes(self):
        # Must be a list of the attribute indexes (int), not strings:
        attributes = []
        return attributes


class LeggerMapVisualisation(object):
    # self.line_layer.crs()
    def __init__(self, iface, source_crs):
        self.iface = iface

        self.source_crs = source_crs

        # temp layer for side profile trac
        self.rb = QgsRubberBand(self.iface.mapCanvas())
        self.rb.setColor(Qt.red)
        self.rb.setWidth(2)

        # temp layer for last selected point
        self.point_markers = []
        self.active_route = None

        self.hover_marker = QgsVertexMarker(self.iface.mapCanvas())
        self.hover_marker.setIconType(QgsVertexMarker.ICON_X)
        self.hover_marker.setColor(Qt.red)
        self.hover_marker.setPenWidth(6)

        self.dist_calc = QgsDistanceArea()

    def close(self):
        self.reset()
        self.iface.mapCanvas().scene().removeItem(self.hover_marker)

    def set_sideview_route(self, route):

        self.reset()

        self.active_route = route
        transform = QgsCoordinateTransform(
            self.source_crs,
            self.iface.mapCanvas().mapRenderer().destinationCrs())

        for pnt in route.path_vertexes:
            t_pnt = transform.transform(pnt)
            self.rb.addPoint(t_pnt)

        for point, point_id, dist in route.path_points:

            marker = QgsVertexMarker(self.iface.mapCanvas())
            marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            marker.setColor(Qt.red)
            marker.setPenWidth(4)
            marker.setCenter(transform.transform(point))
            self.point_markers.append(marker)

    def reset(self):
        self.rb.reset()
        self.active_route = None

        for marker in self.point_markers:
            self.iface.mapCanvas().scene().removeItem(marker)

        self.point_markers = []

        self.hover_marker.setCenter(QgsPoint(0.0, 0.0))

    def hover_graph(self, meters_from_start):

        transform = QgsCoordinateTransform(
            self.source_crs,
            self.iface.mapCanvas().mapRenderer().destinationCrs())

        if self.active_route is None:
            return

        if meters_from_start < 0.0:
            meters_from_start = 0.0
        elif (len(self.active_route.path) > 0 and
              meters_from_start > self.active_route.path[-1][-1][1]):
            meters_from_start = self.active_route.path[-1][-1][1]

        for route_part in self.active_route.path:
            if meters_from_start <= route_part[-1][1]:
                for part in route_part:
                    if meters_from_start <= part[1]:
                        if part[3] == 1:
                            distance_on_line = meters_from_start - part[0]
                        else:
                            distance_on_line = part[1] - meters_from_start

                        length, unit_type = self.dist_calc.convertMeasurement(
                            distance_on_line,
                            QGis.Meters, QGis.Degrees, False)  # QGis.Degrees

                        point = part[4].geometry().interpolate(length)
                        self.hover_marker.setCenter(
                            transform.transform(point.asPoint()))
                        return

    def hover_map(self, point_geometry):
        pass

    def show_selectable_points(self, graph_tree):
        pass

    def hide_selectable_points(self):
        pass
