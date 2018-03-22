import logging
import os
import sys

import numpy as np
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QEvent, QMetaObject, QSize, Qt, pyqtSignal, pyqtSlot, QModelIndex
from PyQt4.QtGui import (QApplication, QColor, QDockWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem,
                         QTableView, QVBoxLayout, QWidget, QTreeWidget, QTreeView, QTreeWidgetItem)
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
from graph_widgets import LeggerSideViewPlotWidget, LeggerPlotWidget

from legger.qt_models.legger_tree import TreeItem, LeggerTreeModel

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
    hoverEnterRow = pyqtSignal(int)

    def __init__(self, parent=None, variant_model=None):
        super(PlotItemTable, self).__init__(parent)

        self._last_hovered_row = None

        if variant_model is not None:
            self.setModel(variant_model)

        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)

        self.setStyleSheet("QTableView::item:hover{background-color:#FFFF00;}")

    def closeEvent(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)
        event.accept()

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            if QEvent is None:
                return QTableView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                row = self.indexAt(event.pos()).row()
                if row == 0 and self.model() and row > self.model().rowCount():
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
                        self.hoverExitRow.emit(self._last_hovered_row)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_row)
                if row is not None:
                    try:
                        self.hover_enter(row)
                        self.hoverEnterRow.emit(row)
                    except IndexError:
                        log.warning("Hover row index %s out of range", row),
                self._last_hovered_row = row

        return QTableView.eventFilter(self, widget, event)

    def hover_exit(self, row_nr):
        if row_nr >= 0:
            item = self.model().rows[row_nr]
            item.color.value = list(item.color.value)[:3] + [20]
            item.hover.value = False

    def hover_enter(self, row_nr):
        if row_nr >= 0:
            item = self.model().rows[row_nr]
            item.color.value = list(item.color.value)[:3] + [255]
            item.hover.value = True

    def setModel(self, model):
        super(PlotItemTable, self).setModel(model)

        self.resizeColumnsToContents()
        self.model().set_column_sizes_on_view(self)


class LeggerTreeWidget(QTreeView):
    hoverExitIndex = pyqtSignal(QModelIndex)
    hoverExitAll = pyqtSignal()  # exit the whole widget
    hoverEnterIndex = pyqtSignal(QModelIndex)

    def __init__(self, parent=None, legger_model=None, on_select=None):
        super(LeggerTreeWidget, self).__init__(parent)
        self.on_select = on_select

        self._last_hovered_item = None

        if legger_model is None:
            legger_model = LeggerTreeModel()
        self.setModel(legger_model)

        # set signals
        QtCore.QObject.connect(self.selectionModel(),
                               QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'),
                               self.select_leaf)
        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)

        # set other
        self.setAlternatingRowColors(True)

    def closeEvent(self, event):
        """
        overwrite of QDockWidget class to emit signal
        :param event: QEvent
        """
        self.setMouseTracking(False)
        self.viewport().removeEventFilter(self)
        event.accept()

    @pyqtSlot("QItemSelection, QItemSelection")
    def select_leaf(self, selected, deselected):
        for it in selected.indexes():
            if it.column() == 0:
                item = self.model().data(it, Qt.UserRole)
                ids = item.hydrovak.get('hydro_id')
                name = item.hydrovak.get('name')
                log.info('selected hydrovak %s', ids)
                self.on_select(item, name)

    def eventFilter(self, widget, event):
        if widget is self.viewport():
            if QEvent is None:
                return QTreeView.eventFilter(self, widget, event)
            elif event.type() == QEvent.MouseMove:
                index = self.indexAt(event.pos())
                if not index.isValid():
                    index = None
            elif event.type() == QEvent.Leave:
                index = None
                self.hoverExitAll.emit()
            else:
                index = self._last_hovered_item

            if index != self._last_hovered_item:
                if self._last_hovered_item is not None:
                    try:
                        self.hover_exit(self._last_hovered_item)
                        self.hoverExitIndex.emit(self._last_hovered_item)
                    except IndexError:
                        log.warning("Hover row index %s out of range",
                                    self._last_hovered_item)

                if index is not None:
                    try:
                        self.hover_enter(index)
                        self.hoverEnterIndex.emit(index)
                    except IndexError:
                        log.warning("Hover row index %s out of range", index.row()),
                self._last_hovered_item = index

        return QTreeView.eventFilter(self, widget, event)

    def hover_exit(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', None)

    def hover_enter(self, index):
        item = index.internalPointer()
        self.model().setDataItemKey(item, 'hover', True)

    def setModel(self, model):
        super(LeggerTreeWidget, self).setModel(model)

        self.model().set_column_sizes_on_view(self)


class LeggerWidget(QDockWidget):
    closingWidget = pyqtSignal()

    def __init__(self, parent=None, iface=None, path_legger_db=None):
        """Constructor."""
        super(LeggerWidget, self).__init__(parent)

        # store arguments
        self.iface = iface
        self.path_legger_db = path_legger_db

        # init parameters
        self.ep = None
        self.sp = None
        self.selected_hydrovak = None
        self.network_tool_active = False
        self.measured_model = ProfileModel()
        self.variant_model = ProfileModel()
        self.legger_model = LeggerTreeModel()

        # create session (before setup_ui)
        db = LeggerDatabase(
            {
                'db_path': path_legger_db
            },
            'spatialite'
        )
        # db.create_and_check_fields()
        self.session = db.get_session()

        # setup ui
        self.setup_ui(self)

        self.legger_model.setTreeWidget(self.legger_tree_widget)

        # create line layer and add to map
        # todo: move to map manager?
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
        self.variant_model.dataChanged.connect(self.data_changed_variant)
        self.legger_model.dataChanged.connect(self.data_changed_legger_tree)
        self.test_manual_input_button.clicked.connect(
            self.test_manual_input_window)

        # initially turn on tool
        # self.select_startpoint_button.toggle()

    def init_network_tool(self, director_type='flow_direction'):
        # init network graph

        # line_direct = self.get_line_layer(geometry_col='line')
        line_direct = self.get_line_layer(geometry_col='line')
        full_line_layer = self.get_line_layer(geometry_col='geometry')

        if director_type == 'connected':
            director = QgsLineVectorLayerDirector(
                line_direct, -1, '', '', '', 3)
        elif director_type == 'flow_direction':
            field_nr = line_direct.fieldNameIndex('direction')
            director = QgsLineVectorLayerDirector(
                line_direct, field_nr, '2', '1', '3', 3)
        else:
            raise NotImplementedError("director '%s' not implemented" % director_type)

        self.network = Network(
            line_direct, full_line_layer, director,
            weight_properter=LeggerDistancePropeter(),  # 'q_end'
            distance_properter=LeggerDistancePropeter())  # 'q_end'
        #

        #  link route map tool
        self.network_tool = NetworkTool(
            self.iface.mapCanvas(),
            line_direct,
            # self.line_layer,  # for tool, the original one for consistent selection of lines equal to layer visible for user
            self.on_start_point_select)

        self.network_tool.deactivated.connect(self.unset_network_tool)

        self.map_visualisation = LeggerMapVisualisation(
            self.iface, line_direct.crs())

        # todo: move to map manage?
        # add tree layer to map (for fun and testing purposes)
        self.vl_tree_layer = self.network.get_virtual_tree_layer()

        self.vl_tree_layer.loadNamedStyle(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), os.pardir,
            'layer_styles', 'legger', 'tree_classified.qml'))

        QgsMapLayerRegistry.instance().addMapLayer(self.vl_tree_layer)

        # add tree layer to map (for fun and testing purposes)
        self.vl_endpoint_layer = self.network.get_endpoint_layer()

        self.vl_endpoint_layer.loadNamedStyle(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), os.pardir,
            'layer_styles', 'legger', 'end_points.qml'))

        QgsMapLayerRegistry.instance().addMapLayer(self.vl_endpoint_layer)

    def get_line_layer(self, geometry_col='geometry'):
        # todo: move to map manage?

        def get_layer(spatialite_path, table_name, geom_column=''):
            uri2 = QgsDataSourceURI()
            uri2.setDatabase(spatialite_path)
            uri2.setDataSource('', table_name, geom_column)

            return QgsVectorLayer(uri2.uri(),
                                  table_name,
                                  'spatialite')

        layer = get_layer(
            self.path_legger_db,
            'hydroobjects_kenmerken14',
            geometry_col
        )

        layer.setSubsetString('"categorieoppwaterlichaam"=1')
        return layer

    def unset_network_tool(self):
        pass

    def reset_network_tree(self):
        pass

    def test_manual_input_window(self):
        self._new_window = NewWindow(self.session)
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

    def select_profile(self, item):
        pass

    def data_changed_legger_tree(self, index, to_index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """

        # activate draw
        pass

    def data_changed_variant(self, index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """
        item = self.variant_model.rows[index.row()]
        if self.variant_model.columns[index.column()].name == 'active':
            if item.active.value:
                # only one selected at the time
                for row in self.variant_model.rows:
                    if row.active.value and row != item:
                        row.active.value = False
                depth = item.depth.value

                def loop(node):
                    """
                    recursive loop over younger items where depth can be applied according to
                    available profiles
                    :param node:
                    :return:
                    """
                    for young in node.younger():
                        if (young.hydrovak.get('variant_min') is None or
                                young.hydrovak.get('variant_max') is None or
                                (depth >= young.hydrovak.get('variant_min') and
                                 depth <= young.hydrovak.get('variant_max'))):
                            self.legger_model.setDataItemKey(young, 'selected_depth', depth)
                            loop(young)

                self.legger_model.setDataItemKey(self.selected_hydrovak, 'selected_depth', depth)
                loop(self.selected_hydrovak)

        elif self.variant_model.columns[index.column()].name == 'hover':
            if item.hover.value:
                depth = item.depth.value

                def loop(node):
                    """
                    recursive loop over younger items where depth can be applied according to
                    available profiles
                    :param node:
                    :return:
                    """
                    for young in node.younger():
                        if (young.hydrovak.get('variant_min') is None or
                                young.hydrovak.get('variant_max') is None or
                                (depth >= young.hydrovak.get('variant_min') and
                                 depth <= young.hydrovak.get('variant_max'))):
                            # index = self.legger_model.createIndex(young.row(), 0, young)
                            self.legger_model.setDataItemKey(young, 'selected_depth_tmp', depth)
                            loop(young)

                self.legger_model.set_column_value('selected_depth_tmp', None)
                self.legger_model.setDataItemKey(self.selected_hydrovak, 'selected_depth_tmp', depth)
                loop(self.selected_hydrovak)

                # self.network._virtual_tree_layer.setSubsetString(
                #     '"var_min_depth"<={depth} AND "var_max_depth">={depth}'.format(depth=depth))
            else:
                self.network._virtual_tree_layer.setSubsetString('')

    # def start_end_point_changed(self):
    #     pass

    def on_start_point_select(self, selected_features, clicked_coordinate):
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

        self.legger_model.clear()

        root = TreeItem(None, None)
        self.network.get_tree_data(root)
        self.legger_model.setNewTree(root.childs)
        self.legger_model.set_column_sizes_on_view(self.legger_tree_widget)

    def on_select_edit_hydrovak(self, item, arc_id):

        self.selected_hydrovak = item
        ids = item.hydrovak.get('hydro_id')
        hydro_object = self.session.query(HydroObject).filter_by(id=item.hydrovak.get('hydro_id')).first()
        # todo: improve this quick fix
        if hydro_object is None:
            return None

        # for profile in hydro_object.figuren.filter_by(type_prof='m').all():
        #     profs.append({
        #         'name': profile.profid,
        #         'color': (128, 128, 128, 256),
        #         'points': [p for p in loads(profile.coord).exterior.coords]
        #     })

        self.variant_model.removeRows(0, len(self.variant_model.rows))
        profs = []
        for profile in hydro_object.varianten.all():
            profs.append({
                'name': profile.id,
                'depth': profile.diepte,
                'color': (243, 132, 0, 20),
                'points': [
                    (-0.5 * profile.waterbreedte, hydro_object.streefpeil),
                    (-0.5 * profile.bodembreedte, hydro_object.streefpeil - profile.diepte),
                    (0.5 * profile.bodembreedte, hydro_object.streefpeil - profile.diepte),
                    (0.5 * profile.waterbreedte, hydro_object.streefpeil),
                ]
            })
        self.variant_model.insertRows(profs)
        pass

    def on_hover_profile(self):
        pass

    def on_select_profile(self):
        pass

    def closeEvent(self, event):
        # todo: disconnect
        if self.vl_tree_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_tree_layer)
        if self.line_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.line_layer)
        if self.vl_endpoint_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_endpoint_layer)

        if self.network_tool_active:
            self.toggle_startpoint_button()
        self.select_startpoint_button.toggled.disconnect(
            self.toggle_startpoint_button)
        self.reset_network_tree_button.clicked.disconnect(
            self.reset_network_tree)
        self.test_manual_input_button.clicked.disconnect(
            self.test_manual_input_window)

        self.variant_model.dataChanged.disconnect(self.data_changed_variant)
        self.legger_model.dataChanged.disconnect(self.data_changed_legger_tree)

        self.legger_model.setTreeWidget(None)

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
        self.legger_tree_widget = LeggerTreeWidget(self, self.legger_model, self.on_select_edit_hydrovak)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.legger_tree_widget.sizePolicy().hasHeightForWidth())
        self.legger_tree_widget.setSizePolicy(sizePolicy)
        self.legger_tree_widget.setMinimumSize(QSize(750, 0))

        self.contentLayout.addWidget(self.legger_tree_widget)

        # graphs
        self.graph_vlayout = QVBoxLayout(self)

        # Graph
        self.plot_widget = LeggerPlotWidget(
            self, session=self.session,
            legger_model=self.legger_model,
            variant_model=self.variant_model)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.plot_widget.sizePolicy().hasHeightForWidth())
        self.plot_widget.setSizePolicy(sizePolicy)
        self.plot_widget.setMinimumSize(QSize(250, 150))

        self.graph_vlayout.addWidget(self.plot_widget)

        # Sideview Graph
        self.sideview_widget = LeggerSideViewPlotWidget(
            self, session=self.session,
            legger_model=self.legger_model)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(
            self.sideview_widget.sizePolicy().hasHeightForWidth())
        self.sideview_widget.setSizePolicy(sizePolicy)
        self.sideview_widget.setMinimumSize(QSize(250, 150))

        self.graph_vlayout.addWidget(self.sideview_widget)

        self.contentLayout.addLayout(self.graph_vlayout)

        # table
        self.plot_item_table = PlotItemTable(self, variant_model=self.variant_model)
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
