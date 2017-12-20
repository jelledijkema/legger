import logging
import os

import numpy as np
import pyqtgraph as pg
from PyQt4.QtCore import QEvent, QMetaObject, QSize, Qt, pyqtSignal
from PyQt4.QtGui import (QApplication, QColor, QDockWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem,
                         QTableView, QVBoxLayout, QWidget)
from legger.qt_models.legger_item import LeggerItemModel
from legger.utils.network import Network
from legger.utils.network_utils import LeggerDistancePropeter, LeggerMapVisualisation, NetworkTool
from qgis.core import (QgsMapLayerRegistry)
from qgis.networkanalysis import (QgsLineVectorLayerDirector)

from qgis.core import (QgsPoint, QgsRectangle, QgsCoordinateTransform,
                       QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsMapLayerRegistry,
                       QGis, QgsFeatureRequest, QgsDistanceArea, QgsCoordinateReferenceSystem)

from qgis.core import QgsDataSourceURI

log = logging.getLogger('legger.' + __name__)

try:
    _encoding = QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class PlotItemTable(QTableView):
    hoverExitRow = pyqtSignal(int)
    hoverExitAllRows = pyqtSignal()  # exit the whole widget
    hoverEnterRow = pyqtSignal(str)

    def __init__(self, parent=None):
        super(PlotItemTable, self).__init__(parent)
        self.setStyleSheet("QTreeView::item:hover{background-color:#FFFF00;}")
        self.setMouseTracking(True)
        self.model = None

        self._last_hovered_row = None
        self.viewport().installEventFilter(self)

    def on_close(self):
        """
        unloading widget and remove all required stuff
        :return:
        """
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)

    def closeEvent(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.on_close()
        event.accept()

    # def eventFilter(self, widget, event):
    #     if widget is self.viewport():
    #
    #         if QEvent is None:
    #             return QTableView.eventFilter(self, widget, event)
    #         elif event.type() == QEvent.MouseMove:
    #             row = self.indexAt(event.pos()).row()
    #             if row == 0 and self.model and row > self.model.rowCount():
    #                 row = None
    #
    #         elif event.type() == QEvent.Leave:
    #             row = None
    #             self.hoverExitAllRows.emit()
    #         else:
    #             row = self._last_hovered_row
    #
    #         if row != self._last_hovered_row:
    #             if self._last_hovered_row is not None:
    #                 try:
    #                     self.hover_exit(self._last_hovered_row)
    #                 except IndexError:
    #                     log.warning("Hover row index %s out of range",
    #                                 self._last_hovered_row)
    #                     # self.hoverExitRow.emit(self._last_hovered_row)
    #             # self.hoverEnterRow.emit(row)
    #             if row is not None:
    #                 try:
    #                     self.hover_enter(row)
    #                 except IndexError:
    #                     log.warning("Hover row index %s out of range", row),
    #             self._last_hovered_row = row
    #             pass
    #     return QTableView.eventFilter(self, widget, event)

    def hover_exit(self, row_nr):
        if row_nr >= 0:
            item = self.model.rows[row_nr]
            item.color.value = item.color.value[:3] + [150]
            item.hover.value = False

    def hover_enter(self, row_nr):
        if row_nr >= 0:
            item = self.model.rows[row_nr]
            name = item.name.value
            self.hoverEnterRow.emit(name)
            item.color.value = item.color.value[:3] + [220]
            item.hover.value = True

    def setModel(self, model):
        super(PlotItemTable, self).setModel(model)

        self.model = model

        self.resizeColumnsToContents()
        self.model.set_column_sizes_on_view(self)


class LeggerPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, name=""):

        super(LeggerPlotWidget, self).__init__(parent)
        self.name = name
        self.showGrid(True, True, 0.5)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")

        self.series = {}

    def setModel(self, model):
        self.model = model
        self.model.dataChanged.connect(self.data_changed)
        self.model.rowsInserted.connect(self.on_insert)
        self.model.rowsAboutToBeRemoved.connect(
            self.on_remove)

    def on_remove(self):
        self.draw_lines()

    def on_insert(self):
        self.draw_lines()

    def draw_lines(self):
        self.clear()

        ts = self.model.ts

        zeros = np.zeros(shape=(np.size(ts, 0),))
        zero_serie = pg.PlotDataItem(
            x=ts,
            y=zeros,
            connect='finite',
            pen=pg.mkPen(color=QColor(0, 0, 0, 220), width=1))
        self.addItem(zero_serie)

        # todo: implement specific logic
        # plot_item = pg.PlotDataItem(
        #     x=width,
        #     y=height,
        #     connect='finite',
        #     pen=pg.mkPen(color=QColor(*item.color.value), width=1))

        # color = item.color.value
        # fill = pg.FillBetweenItem(prev_pldi,
        #                           plot_item,
        #                           pg.mkBrush(*color))

        # # keep reference
        # item._plots[dir] = plot_item
        # self.addItem(item._plots[dir])
        # self.addItem(item._plots[dir + 'fill'])

        self.autoRange()

    def data_changed(self, index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """
        if self.model.columns[index.column()].name == 'active':
            self.draw_lines()

        elif self.model.columns[index.column()].name == 'hover':
            item = self.model.rows[index.row()]
            if item.hover.value:
                if item.active.value:
                    if 'xx' in item._plots:
                        item._plots['xx'].setPen(color=item.color.value,
                                                 width=1)
                        item._plots['xxfill'].setBrush(
                            pg.mkBrush(item.color.value))
            else:
                if item.active.value:
                    if 'xx' in item._plots:
                        item._plots['xx'].setPen(color=item.color.value,
                                                 width=1)
                        item._plots['xxfill'].setBrush(
                            pg.mkBrush(item.color.value))


class LeggerWidget(QDockWidget):
    closingWidget = pyqtSignal()

    def __init__(self, parent=None, iface=None):
        """Constructor."""
        super(LeggerWidget, self).__init__(parent)
        self.iface = iface

        # init class params
        self.network_tool_active = False

        # setup ui
        self.setup_ui(self)

        self.model = LeggerItemModel()
        self.plot_item_table.setModel(self.model)
        self.plot_item_table.setModel(self.model)
        self.plot_widget.setModel(self.model)

        self.line_layer = self.get_line_layer()

        self.line_layer.loadNamedStyle(os.path.join(
            os.path.dirname(__file__), os.pardir,
            'layer_styles', 'legger', 'line.qml'))

        QgsMapLayerRegistry.instance().addMapLayer(self.line_layer)

        self.init_network_tool()

        # add listeners
        self.select_startpoint_button.toggled.connect(
            self.toggle_startpoint_button)
        self.reset_network_tree_button.clicked.connect(
            self.reset_network_tree)

        # initially turn on tool
        # self.select_startpoint_button.toggle()

    def init_network_tool(self, director_type='flow_direction'):
        # init network graph

        if director_type == 'connected':
            director = QgsLineVectorLayerDirector(
                self.line_layer, -1, '', '', '', 3)
        elif director_type == 'flow_direction':
            field_nr = self.line_layer.fieldNameIndex('direction')
            director = QgsLineVectorLayerDirector(
                self.line_layer, field_nr, '2', '1', '3', 3)
        else:
            raise NotImplementedError("director '%s' not implemented" % director_type)

        self.network = Network(
            self.line_layer, director, id_field='OGC_FID',
            weight_properter=LeggerDistancePropeter(),  # 'q_end'
            distance_properter=LeggerDistancePropeter())  # 'q_end'
        #

        #  link route map tool
        self.network_tool = NetworkTool(
            self.iface.mapCanvas(),
            self.line_layer,
            self.on_point_select)

        self.network_tool.deactivated.connect(self.unset_network_tool)

        self.map_visualisation = LeggerMapVisualisation(
            self.iface, self.line_layer.crs())

        # add tree layer to map (for fun and testing purposes)
        self.vl_tree_layer = self.network.get_virtual_tree_layer()

        self.vl_tree_layer.loadNamedStyle(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), os.pardir,
            'layer_styles', 'legger', 'tree_classified.qml'))

        QgsMapLayerRegistry.instance().addMapLayer(self.vl_tree_layer)

    def get_line_layer(self):

        def get_layer(spatialite_path, table_name, geom_column=''):
            uri2 = QgsDataSourceURI()
            uri2.setDatabase(spatialite_path)
            uri2.setDataSource('', table_name, geom_column)

            return QgsVectorLayer(uri2.uri(),
                                  table_name,
                                  'spatialite')

        return get_layer(
            os.path.join(
                os.path.dirname(__file__),
                os.path.pardir,
                'tests', 'data',
                'test_spatialite_with_3di_results.sqlite'
            ),
            'hydroobject_with_results',
            'GEOMETRY'
        )

    def unset_network_tool(self):
        pass

    def reset_network_tree(self):
        pass

    def unset_tool(self):
        pass

    def toggle_startpoint_button(self):
        if self.network_tool_active:
            self.network_tool_active = False
            self.iface.mapCanvas().unsetMapTool(self.network_tool)
        else:
            self.network_tool_active = True
            self.iface.mapCanvas().setMapTool(self.network_tool)

    def on_point_select(self, selected_features, clicked_coordinate):
        """Select and add the closest point from the list of selected features.

        Args:
            selected_features: list of features selected by click
            clicked_coordinate: (lon, lat) (transformed) of the click
        """

        def distance(coordinate):
            """Calculate the distance w.r.t. the clicked location."""
            import math
            xc, yc = clicked_coordinate
            x, y = coordinate
            dist = math.sqrt((x - xc) ** 2 + (y - yc) ** 2)
            return dist

        selected_coordinates = reduce(
            lambda accum, f: accum + [f.geometry().vertexAt(0),
                                      f.geometry().vertexAt(len(f.geometry().asPolyline())-1)],
            selected_features, [])

        if len(selected_coordinates) == 0:
            return

        closest_point = min(selected_coordinates, key=distance)
        next_point = QgsPoint(closest_point)

        if len(selected_features) > 0:
            self.network.reset()
            self.network.add_point(next_point)

    def accept(self):
        pass

    def reject(self):
        self.close()

    def closeEvent(self, event):
        # todo: disconnect
        if self.vl_tree_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_tree_layer)
        if self.line_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.line_layer)

        if self.network_tool_active:
            self.toggle_startpoint_button()
        self.select_startpoint_button.toggled.disconnect(
            self.toggle_startpoint_button)
        self.reset_network_tree_button.clicked.disconnect(
            self.reset_network_tree)

        self.closingWidget.emit()
        event.accept()

    def setup_ui(self, dock_widget):
        """
        initiate main Qt building blocks of interface
        :param dock_widget: QDockWidget instance
        """

        dock_widget.setObjectName("dock_widget")
        dock_widget.setAttribute(Qt.WA_DeleteOnClose)

        self.dock_widget_content = QWidget(self)
        self.dock_widget_content.setObjectName("dockWidgetContent")

        self.main_vlayout = QVBoxLayout(self)
        self.dock_widget_content.setLayout(self.main_vlayout)

        # add button to add objects to graphs
        self.button_bar_hlayout = QHBoxLayout(self)
        self.select_startpoint_button = QPushButton(self)
        self.select_startpoint_button.setCheckable(True)
        self.button_bar_hlayout.addWidget(self.select_startpoint_button)

        self.reset_network_tree_button = QPushButton(self)
        self.button_bar_hlayout.addWidget(self.reset_network_tree_button)

        self.import_treedi_button = QPushButton(self)
        self.button_bar_hlayout.addWidget(self.import_treedi_button)

        spacer_item = QSpacerItem(40,
                                  20,
                                  QSizePolicy.Expanding,
                                  QSizePolicy.Minimum)
        self.button_bar_hlayout.addItem(spacer_item)
        self.main_vlayout.addLayout(self.button_bar_hlayout)

        # add tabWidget for graphWidgets
        self.contentLayout = QHBoxLayout(self)

        # Graph
        self.plot_widget = LeggerPlotWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.plot_widget.sizePolicy().hasHeightForWidth())
        self.plot_widget.setSizePolicy(sizePolicy)
        self.plot_widget.setMinimumSize(QSize(250, 250))

        self.contentLayout.addWidget(self.plot_widget)

        # table
        self.plot_item_table = PlotItemTable(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.plot_item_table.sizePolicy().hasHeightForWidth())
        self.plot_item_table.setSizePolicy(sizePolicy)
        self.plot_item_table.setMinimumSize(QSize(250, 0))

        self.contentLayout.addWidget(self.plot_item_table)

        self.main_vlayout.addLayout(self.contentLayout)

        # add dockwidget
        dock_widget.setWidget(self.dock_widget_content)
        self.retranslate_ui(dock_widget)
        QMetaObject.connectSlotsByName(dock_widget)

    def retranslate_ui(self, dock_widget):
        pass
        dock_widget.setWindowTitle(_translate(
            "DockWidget", "Legger", None))
        self.select_startpoint_button.setText(_translate(
            "DockWidget", "Selecteer een startpunt", None))
        self.reset_network_tree_button.setText(_translate(
            "DockWidget", "Verberg netwerk op kaart", None))
