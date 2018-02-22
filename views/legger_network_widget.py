import logging
import os
import sys

import numpy as np
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QEvent, QMetaObject, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt4.QtGui import (QApplication, QColor, QDockWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem,
                         QTableView, QVBoxLayout, QWidget, QTreeView)
from legger.qt_models.legger_item import LeggerItemModel
from legger.utils.network import Network
from legger.utils.network_utils import LeggerDistancePropeter, LeggerMapVisualisation, NetworkTool
from qgis.core import (QgsMapLayerRegistry)
from qgis.networkanalysis import (QgsLineVectorLayerDirector)

from qgis.core import (QgsPoint, QgsRectangle, QgsCoordinateTransform,
                       QgsVectorLayer, QgsField, QgsFeature, QgsGeometry, QgsMapLayerRegistry,
                       QGis, QgsFeatureRequest, QgsDistanceArea, QgsCoordinateReferenceSystem)

from qgis.core import QgsDataSourceURI
from legger.qt_models.legger_tree import LeggerTreeModel

from legger.sql_models.legger import HydroObject
from legger.sql_models.legger_database import LeggerDatabase
from shapely.geometry import LineString
from legger.qt_models.profile import ProfileModel
from shapely.wkt import loads
from sqlalchemy.orm import joinedload

from legger.views.input_widget import NewWindow

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

    def eventFilter(self, widget, event):
        if widget is self.viewport():

            if QEvent is None:
                return QTableView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                row = self.indexAt(event.pos()).row()
                if row == 0 and self.model and row > self.model.rowCount():
                    row = None

            elif event.type() == QEvent.Leave:
                row = None
                self.hoverExitAllRows.emit()
            else:
                row = self._last_hovered_row

            if row != self._last_hovered_row:
                if self._last_hovered_row is not None:
                    try:
                        self.hover_exit(self._last_hovered_row)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_row)
                        # self.hoverExitRow.emit(self._last_hovered_row)
                # self.hoverEnterRow.emit(row)
                if row is not None:
                    try:
                        self.hover_enter(row)
                    except IndexError:
                        log.warning("Hover row index %s out of range", row),
                self._last_hovered_row = row
                pass
        return QTableView.eventFilter(self, widget, event)

    def hover_exit(self, row_nr):
        if row_nr >= 0:
            item = self.model.rows[row_nr]
            item.color.value = list(item.color.value)[:3] + [150]
            item.hover.value = False

    def hover_enter(self, row_nr):
        if row_nr >= 0:
            item = self.model.rows[row_nr]
            name = item.name.value
            self.hoverEnterRow.emit(name)
            item.color.value = list(item.color.value)[:3] + [220]
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

    def setMeasuredModel(self, model):
        # todo: remove listeners to old model?
        self.measured_model = model
        self.measured_model.dataChanged.connect(self.data_changed_measured)
        self.measured_model.rowsInserted.connect(self.on_insert)
        self.measured_model.rowsAboutToBeRemoved.connect(
            self.on_remove)

    def setVariantModel(self, model):
        # todo: remove listeners to old model?
        self.variant_model = model
        self.variant_model.dataChanged.connect(self.data_changed_variant)
        self.variant_model.rowsInserted.connect(self.on_insert)
        self.variant_model.rowsAboutToBeRemoved.connect(
            self.on_remove)

    def on_remove(self):
        self.draw_lines()

    def on_insert(self):
        self.draw_lines()

    def draw_lines(self):
        self.clear()

        models = [self.measured_model, self.variant_model]

        for model in models:
            for item in model.rows:
                if item.active.value:
                    midpoint = sum([p[0] for p in item.points.value[-2:]]) / 2

                    width = [p[0] - midpoint for p in item.points.value]
                    height = [p[1] for p in item.points.value]

                    plot_item = pg.PlotDataItem(
                        x=width,
                        y=height,
                        connect='finite',
                        pen=pg.mkPen(color=QColor(*item.color.value), width=1))

                    # keep reference
                    item._plot = plot_item
                    self.addItem(item._plot)

        self.autoRange()

    def data_changed_variant(self, index):
        self.data_changed(self.variant_model, index)

    def data_changed_measured(self, index):
        self.data_changed(self.measured_model, index)

    def data_changed(self, model, index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """
        if model.columns[index.column()].name == 'active':
            self.draw_lines()

        elif model.columns[index.column()].name == 'hover':
            for item in model.rows:
                item._plot.setPen(color=list(item.color.value)[:3] + [20],
                                  width=1)

            item = model.rows[index.row()]
            if item.hover.value:
                if item.active.value:
                    item._plot.setPen(color=item.color.value,
                                      width=2)
            else:
                # if item.active.value:
                for item in model.rows:
                    item._plot.setPen(color=item.color.value,
                                      width=1)


class LeggerTreeWidget(QTreeView):

    def __init__(self, parent=None, tree_model=None):
        super(LeggerTreeWidget, self).__init__(parent)

        if tree_model:
            self.setModel(tree_model)

        QtCore.QObject.connect(self.selectionModel(),
                               QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'),
                               self.select_leaf)

    @pyqtSlot("QItemSelection, QItemSelection")
    def select_leaf(self, selected, deselected):
        pass


class LeggerWidget(QDockWidget):
    closingWidget = pyqtSignal()

    def __init__(self, parent=None, iface=None, path_legger_db=None):
        """Constructor."""
        super(LeggerWidget, self).__init__(parent)
        self.iface = iface
        self.path_legger_db = path_legger_db

        # init class params
        self.network_tool_active = False
        self.measured_model = ProfileModel()
        self.variant_model = ProfileModel()
        self.legger_tree_model = LeggerTreeModel()

        # setup ui
        self.setup_ui(self)

        # self.model = LeggerItemModel()

        self.plot_item_table.setModel(self.variant_model)
        self.plot_widget.setVariantModel(self.variant_model)
        self.plot_widget.setMeasuredModel(self.measured_model)

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
        self.test_manual_input_button.clicked.connect(
            self.test_manual_input_window)

        db = LeggerDatabase(
            {
                'db_path': path_legger_db
            },
            'spatialite'
        )
        # db.create_and_check_fields()
        self.session = db.get_session()

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
            self.line_layer, director, id_field='id',
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
            self.path_legger_db,
            'hydroobjects_kenmerken',
            'geometry'
        )

    def unset_network_tool(self):
        pass

    def reset_network_tree(self):
        pass

    def test_manual_input_window(self):
        self._new_window = NewWindow()
        self._new_window.show()
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
            x, y = coordinate[0]
            dist = math.sqrt((x - xc) ** 2 + (y - yc) ** 2)
            return dist

        selected_coordinates = reduce(
            lambda accum, f: accum + [(f.geometry().vertexAt(0), f),
                                      (f.geometry().vertexAt(len(f.geometry().asPolyline()) - 1), f)],
            selected_features, [])

        if len(selected_coordinates) == 0:
            return

        closest_point, feature = min(selected_coordinates, key=distance)
        next_point = QgsPoint(closest_point)

        if len(selected_features) > 0:
            self.network.reset()
            self.network.add_point(next_point)

            # todo: add graph functions here

            field_idx = self.network._virtual_tree_layer.fieldNameIndex('line_id')
            ids = self.network._virtual_tree_layer.uniqueValues(field_idx)

            try:
                ids.remove(feature['id'])
            except AttributeError:
                pass
            except ValueError:
                pass

            hydro_objects = self.session.query(HydroObject).filter(HydroObject.id.in_(ids)).all()

            self.measured_model.removeRows(0, len(self.measured_model.rows))
            profs = []
            for obj in hydro_objects:
                for profile in obj.figuren.filter_by(type_prof='m').all():
                    profs.append({
                        'name': profile.profid,
                        'color': (128, 128, 128, 180),
                        'points': [p for p in loads(profile.coord).exterior.coords]
                    })

            hydro_object = self.session.query(HydroObject).filter_by(id=feature['id']).first()

            for profile in hydro_object.figuren.filter_by(type_prof='m').all():
                profs.append({
                    'name': profile.profid,
                    'color': (128, 128, 128, 256),
                    'points': [p for p in loads(profile.coord).exterior.coords]
                })

            self.measured_model.insertRows(profs)

            self.variant_model.removeRows(0, len(self.variant_model.rows))
            profs = []
            for profile in hydro_object.figuren.filter_by(type_prof='t').all():
                profs.append({
                    'name': profile.profid,
                    'color': (243, 132, 0, 180),
                    'points': [p for p in loads(profile.coord).exterior.coords]
                })
            self.variant_model.insertRows(profs)

            # hydro_object.figuren.filter_by(HydroObject.type_prof='m')

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
        self.test_manual_input_button.clicked.disconnect(
            self.test_manual_input_window)

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

        self.test_manual_input_button = QPushButton(self)
        self.button_bar_hlayout.addWidget(self.test_manual_input_button)

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

        # Tree
        self.legger_tree_widget = LeggerTreeWidget(self, self.legger_tree_model)
        self.contentLayout.addWidget(self.legger_tree_widget)

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
        self.test_manual_input_button.setText(_translate(
            "DockWidget", "Test Manual input", None))
