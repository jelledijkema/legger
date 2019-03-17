import logging
import os

from PyQt4.QtCore import QMetaObject, QSize, Qt, pyqtSignal
from PyQt4.QtGui import (QApplication, QDockWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem, QTabWidget,
                         QVBoxLayout, QWidget, QComboBox, QPlainTextEdit)
from legger.qt_models.area_tree import AreaTreeItem, AreaTreeModel, area_class
from legger.qt_models.legger_tree import LeggerTreeModel, LeggerTreeItem
from legger.qt_models.profile import ProfileModel
from legger.sql_models.legger import GeselecteerdeProfielen, HydroObject, Varianten, BegroeiingsVariant
from legger.sql_models.legger_database import LeggerDatabase
from legger.utils.network_utils import LeggerMapVisualisation
from legger.views.input_widget import NewWindow
from network_graph_widgets import LeggerPlotWidget, LeggerSideViewPlotWidget
from qgis.core import QgsDataSourceURI, QgsFeature, QgsGeometry, QgsMapLayerRegistry, QgsPoint, QgsVectorLayer
from qgis.networkanalysis import QgsLineVectorLayerDirector
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_

from .network_table_widgets import LeggerTreeWidget, VariantenTable, StartpointTreeWidget
from legger.utils.new_network import NewNetwork
from legger.utils.legger_map_manager import LeggerMapManager

log = logging.getLogger('legger.' + __name__)

precision = 0.000001

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class LeggerWidget(QDockWidget):
    """Legger Network widget with tree tables, cross section and sideview and
    legger profile selection"""
    # todo:
    #   - category filter on map and tree instead of shortcut
    #   - improve performance 'initial loop tree'

    closingWidget = pyqtSignal()

    def __init__(self, parent=None, iface=None, path_legger_db=None):
        """Constructor."""
        super(LeggerWidget, self).__init__(parent)

        # store arguments
        self.iface = iface
        self.path_legger_db = path_legger_db

        # init parameters
        self.measured_model = ProfileModel()
        self.variant_model = ProfileModel()
        self.legger_model = LeggerTreeModel()
        self.area_model = AreaTreeModel()

        # create session (before setup_ui)
        db = LeggerDatabase(
            {'db_path': path_legger_db},
            'spatialite'
        )
        db.create_and_check_fields()
        self.session = db.get_session()

        # setup ui
        self.setup_ui(self)

        self.legger_model.setTreeWidget(self.legger_tree_widget)
        self.area_model.setTreeWidget(self.startpoint_tree_widget)

        self.category_combo.insertItems(0, ['4', '3', '2', '1'])
        self.category_combo.setCurrentIndex(0)
        self.category_filter = 4

        strategies = ['alle', 'opgegeven']
        strategies.extend([v.naam for v in self.session.query(BegroeiingsVariant)])
        self.begroeiings_combo.insertItems(
            0, strategies)

        self.begroeiings_strategy_combo.insertItems(0, [
            'dit hydrovak', 'benedenstr. altijd', 'benedenstr. of meer'
        ])
        self.begroeiings_strategy_combo.setCurrentIndex(0)

        # create line layer and add to map
        self.layer_manager = LeggerMapManager(self.iface, self.path_legger_db)

        self.line_layer = self.layer_manager.get_line_layer(add_to_map=True)
        self.vl_tree_layer = self.layer_manager.get_virtual_tree_layer(add_to_map=True)
        self.vl_endpoint_layer = self.layer_manager.get_endpoint_layer(add_to_map=True)
        self.vl_track_layer = self.layer_manager.get_track_layer(add_to_map=True)
        self.vl_hover_layer = self.layer_manager.get_hover_layer(add_to_map=True)
        self.vl_selected_layer = self.layer_manager.get_selected_layer(add_to_map=True)
        self.vl_startpoint_hover_layer = self.layer_manager.get_hover_startpoint_layer(add_to_map=True)

        self.map_visualisation = LeggerMapVisualisation(
            self.iface, self.line_layer.crs())

        # init network
        line_direct = self.layer_manager.get_line_layer(geometry_col='line')
        field_nr = line_direct.fieldNameIndex('direction')
        director = QgsLineVectorLayerDirector(
            line_direct, field_nr, '2', '1', '3', 3)

        self.network = NewNetwork(
            line_direct, self.line_layer, director, None, self.vl_tree_layer, self.vl_endpoint_layer
        )

        # add listeners
        self.category_combo.currentIndexChanged.connect(self.category_change)
        self.variant_model.dataChanged.connect(self.data_changed_variant)
        self.legger_model.dataChanged.connect(self.data_changed_legger_tree)
        self.area_model.dataChanged.connect(self.data_changed_area_model)
        self.show_manual_input_button.clicked.connect(
            self.show_manual_input_window)

        # create and init startpoint (AreaTree) model
        def loop_over(parent, data):
            for child in data['children']:
                area = area_class(child)
                item = AreaTreeItem(area, parent)
                parent.appendChild(item)
                loop_over(item, child)

        # get startingpoints and select first
        sp_tree = self.network.get_start_arc_tree()

        root = AreaTreeItem(None, None)
        loop_over(root, sp_tree)
        self.area_model.setNewTree(root.childs)

        # initial, select first area
        first_area = root.child(0)
        self.area_model.setDataItemKey(first_area, 'selected', True)

    def category_change(self, nr):
        """
        set current selected parameter and trigger refresh of graphs
        nr: nr of selected option of combobox
        return: -
        """
        # todo: change this current shortcut way of category filtering
        self.category_filter = int(self.category_combo.currentText())
        root = LeggerTreeItem(None, None)
        self.network.get_tree_data(root, self.category_filter)
        self.legger_model.setNewTree(root.childs)
        self.legger_model.set_column_sizes_on_view(self.legger_tree_widget)
        if len(root.childs) > 0:
            self.initial_loop_tree(root.childs[0])

    def show_manual_input_window(self):
        self._new_window = NewWindow(
            self.legger_model.selected,
            self.session,
            callback_on_save=self.update_available_profiles)
        self._new_window.show()

    def initial_loop_tree(self, node):
        """
        recursive loop over younger items where depth can be applied according to
        available profiles
        :param node:
        :return:
        """
        # todo: function is very slow. Can be improved?
        # todo: checked till here

        depth = node.hydrovak.get('selected_depth')

        if depth is not None:
            profile_variant = self.session.query(Varianten).filter(
                Varianten.hydro_id == node.hydrovak.get('hydro_id'),
                Varianten.diepte < depth + precision,
                Varianten.diepte > depth - precision
            )

            over_depth = node.hydrovak.get('depth') - depth if node.hydrovak.get('depth') is not None else None

            if profile_variant.count() > 0:
                profile = profile_variant.first()
                width = profile.waterbreedte
                self.legger_model.setDataItemKey(node, 'selected_width', width)

                over_width = node.hydrovak.get('width') - width \
                    if node.hydrovak.get('width') is not None else None

                figuren = profile.figuren
                score = None
                if len(figuren) > 0:
                    figuur = figuren[0]
                    over_width = "{0:.2f}*".format(figuur.t_overbreedte_l + figuur.t_overbreedte_r) \
                        if figuur.t_overbreedte_l is not None else over_width
                    score = "{0:.2f}".format(figuur.t_fit)
                    over_depth = "{0:.2f}*".format(
                        figuur.t_overdiepte) if figuur.t_overdiepte is not None else over_depth

                self.legger_model.setDataItemKey(node, 'over_depth', over_depth)
                self.legger_model.setDataItemKey(node, 'over_width', over_width)
                self.legger_model.setDataItemKey(node, 'score', score)

        for young in node.younger():
            self.initial_loop_tree(young)

    def data_changed_legger_tree(self, index, to_index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """

        # activate draw
        node = self.legger_model.data(index, role=Qt.UserRole)

        if self.legger_model.columns[index.column()].get('field') == 'hover':
            ids = [feat.id() for feat in self.vl_hover_layer.getFeatures()]
            self.vl_hover_layer.dataProvider().deleteFeatures(ids)

            if node.hydrovak.get('hover'):
                features = []

                feat = QgsFeature()
                feat.setGeometry(node.hydrovak.get('feature').geometry())

                feat.setAttributes([
                    node.hydrovak.get('feature')['id']])

                features.append(feat)
                self.vl_hover_layer.dataProvider().addFeatures(features)

            self.vl_hover_layer.commitChanges()
            self.vl_hover_layer.updateExtents()
            self.vl_hover_layer.triggerRepaint()

        elif self.legger_model.columns[index.column()].get('field') == 'selected':
            ids = [feat.id() for feat in self.vl_selected_layer.getFeatures()]
            self.vl_selected_layer.dataProvider().deleteFeatures(ids)

            if node.hydrovak.get('selected'):
                features = []

                feat = QgsFeature()
                feat.setGeometry(node.hydrovak.get('feature').geometry())

                feat.setAttributes([
                    node.hydrovak.get('feature')['id']])

                features.append(feat)
                self.vl_selected_layer.dataProvider().addFeatures(features)

            self.vl_selected_layer.commitChanges()
            self.vl_selected_layer.updateExtents()
            self.vl_selected_layer.triggerRepaint()

            if node.hydrovak.get('selected'):
                self.on_select_edit_hydrovak(self.legger_model.data(index, role=Qt.UserRole))
                self.show_manual_input_button.setDisabled(False)
            elif (self.legger_model.selected is None or
                    self.legger_model.data(index, role=Qt.UserRole) == self.legger_model.selected):
                self.variant_model.removeRows(0, len(self.variant_model.rows))
                self.show_manual_input_button.setDisabled(True)

        elif self.legger_model.columns[index.column()].get('field') in ['ep', 'sp']:
            ids = [feat.id() for feat in self.vl_track_layer.getFeatures()]
            self.vl_track_layer.dataProvider().deleteFeatures(ids)

            if self.legger_model.sp and self.legger_model.ep:
                features = []

                def loop_rec(node):
                    feat = QgsFeature()
                    feat.setGeometry(node.hydrovak.get('feature').geometry())

                    feat.setAttributes([
                        node.hydrovak.get('feature')['id']])

                    features.append(feat)

                    if node != self.legger_model.sp:
                        loop_rec(node.older())

                loop_rec(self.legger_model.ep)

                self.vl_track_layer.dataProvider().addFeatures(features)
                self.vl_track_layer.commitChanges()
                self.vl_track_layer.updateExtents()
                self.vl_track_layer.triggerRepaint()

    def data_changed_area_model(self, index, to_index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """

        if self.area_model.columns[index.column()].get('field') == 'selected':
            # clear display elements
            self.variant_model.removeRows(0, len(self.variant_model.rows))
            self.legger_model.set_column_value('hover', False)
            self.legger_model.set_column_value('selected', False)
            self.legger_model.set_column_value('ep', False)
            self.legger_model.set_column_value('sp', False)

            area_item = self.area_model.data(index, role=Qt.UserRole)

            self.network.set_tree_start_arc(area_item.area.get('arc_nr'))

            self.legger_model.clear()

            root = LeggerTreeItem(None, None)
            self.network.get_tree_data(root, self.category_filter)
            self.legger_model.setNewTree(root.childs)
            self.legger_model.set_column_sizes_on_view(self.legger_tree_widget)
            if len(root.childs) > 0:
                self.initial_loop_tree(root.childs[0])

            canvas = self.iface.mapCanvas()
            canvas.setExtent(self.vl_tree_layer.extent())
        elif self.area_model.columns[index.column()].get('field') == 'hover':
            ids = [feat.id() for feat in self.vl_startpoint_hover_layer.getFeatures()]
            self.vl_startpoint_hover_layer.dataProvider().deleteFeatures(ids)

            value = self.area_model.data(index, role=Qt.DisplayRole)

            if self.area_model.data(index, role=Qt.CheckStateRole) == Qt.Checked:
                features = []

                node = self.area_model.data(index, role=Qt.UserRole)
                feat = QgsFeature()

                feat.setGeometry(QgsGeometry.fromPoint(node.area.get('point')))
                feat.setAttributes([
                    node.area.get('vertex_id')])
                features.append(feat)

                self.vl_startpoint_hover_layer.dataProvider().addFeatures(features)

            self.vl_startpoint_hover_layer.commitChanges()
            self.vl_startpoint_hover_layer.updateExtents()
            self.vl_startpoint_hover_layer.triggerRepaint()

    def data_changed_variant(self, index):
        """
        change graphs based on changes in locations
        :param index: index of changed field
        """
        item = self.variant_model.rows[index.row()]
        if self.variant_model.columns[index.column()].name == 'active':
            if item.active.value:
                # only one selected at the time
                item.color.value = list(item.color.value)[:3] + [255]
                for row in self.variant_model.rows:
                    if row.active.value and row != item:
                        row.active.value = False

                depth = item.depth.value
                selected_variant_id = item.name.value

                def loop(node):
                    """
                    recursive loop over younger items where depth can be applied according to
                    available profiles
                    :param node:
                    :return:
                    """
                    profile_variant = self.session.query(Varianten).filter(
                        Varianten.hydro_id == node.hydrovak.get('hydro_id'),
                        or_(Varianten.hydro.has(HydroObject.begroeiingsvariant_id == Varianten.begroeiingsvariant_id),
                            and_(Varianten.hydro.has(HydroObject.begroeiingsvariant_id == None),
                                 Varianten.begroeiingsvariant.has(is_default=True))),
                        Varianten.diepte < depth + precision,
                        Varianten.diepte > depth - precision
                    )

                    if profile_variant.count() > 0:
                        profilev = profile_variant.first()

                        self.legger_model.setDataItemKey(self.legger_model.selected, 'selected_depth', depth)
                        self.legger_model.setDataItemKey(
                            self.legger_model.selected, 'selected_variant_id', profilev.id)

                        over_depth = node.hydrovak.get('depth') - depth if node.hydrovak.get(
                            'depth') is not None else None


                        width = profilev.waterbreedte
                        self.legger_model.setDataItemKey(node, 'selected_width', width)

                        over_width = node.hydrovak.get('width') - width \
                            if node.hydrovak.get('width') is not None else None

                        figuren = profilev.figuren
                        score = None
                        if len(figuren) > 0:
                            figuur = figuren[0]
                            over_width = "{0:.2f}*".format(figuur.t_overbreedte_l + figuur.t_overbreedte_r) \
                                if figuur.t_overbreedte_l is not None else over_width
                            score = "{0:.2f}".format(figuur.t_fit)
                            over_depth = "{0:.2f}*".format(
                                figuur.t_overdiepte) if figuur.t_overdiepte is not None else over_depth

                        self.legger_model.setDataItemKey(node, 'over_depth', over_depth)
                        self.legger_model.setDataItemKey(node, 'over_width', over_width)
                        self.legger_model.setDataItemKey(node, 'score', score)

                        # save
                        selected = self.session.query(GeselecteerdeProfielen).filter(
                            GeselecteerdeProfielen.hydro_id == node.hydrovak.get('hydro_id')).first()
                        if selected:
                            selected.variant = profilev
                        else:
                            selected = GeselecteerdeProfielen(
                                hydro_id=node.hydrovak.get('hydro_id'),
                                variant_id=profilev.id
                            )

                        self.session.add(selected)
                        print(selected)
                        # todo: score

                    else:
                        log.warn('no variant found for hydrovak %s', node.hydrovak.get('hydro_id'))

                    for young in node.younger():
                        if (young.hydrovak.get('variant_min_depth') is None or
                                young.hydrovak.get('variant_max_depth') is None or
                                (depth >= young.hydrovak.get('variant_min_depth') - precision and
                                 depth <= young.hydrovak.get('variant_max_depth') + precision)):
                            self.legger_model.setDataItemKey(young, 'selected_depth', depth)

                            loop(young)

                loop(self.legger_model.selected)
                self.session.commit()
            else:
                item.color.value = list(item.color.value)[:3] + [20]

        elif self.variant_model.columns[index.column()].name == 'hover':
            if item.hover.value:
                depth = item.depth.value
                ids = []

                def loop(node):
                    """
                    recursive loop over younger items where depth can be applied according to
                    available profiles
                    :param node:
                    :return:
                    """
                    for young in node.younger():
                        if (young.hydrovak.get('variant_min_depth') is None or
                                young.hydrovak.get('variant_max_depth') is None or
                                (depth >= young.hydrovak.get('variant_min_depth') - precision and
                                 depth <= young.hydrovak.get('variant_max_depth') + precision)):
                            # index = self.legger_model.createIndex(young.row(), 0, young)
                            self.legger_model.setDataItemKey(young, 'selected_depth_tmp', depth)
                            ids.append(str(young.hydrovak.get('hydro_id')))
                            loop(young)

                self.legger_model.set_column_value('selected_depth_tmp', None)
                self.legger_model.setDataItemKey(self.legger_model.selected, 'selected_depth_tmp', depth)
                loop(self.legger_model.selected)

                self.network._virtual_tree_layer.setSubsetString(
                    '"hydro_id" in (\'{ids}\')'.format(ids='\',\''.join(ids)))
            else:
                self.network._virtual_tree_layer.setSubsetString('')
                self.legger_model.set_column_value('selected_depth_tmp', None)

    def on_select_edit_hydrovak(self, item):
        """
        set elements after selection of a hydrovak for profile selection
        item (LeggerTreeItem): selected hydrovak LeggerTreeItem
        return: None
        """

        hydro_object = self.session.query(HydroObject).filter_by(id=item.hydrovak.get('hydro_id')).first()
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
        #todo: store selected variant id instead of depth!
        selected_depth = item.hydrovak.get('selected_depth')
        selected_variant_id = item.hydrovak.get('selected_variant_id')

        for profile in hydro_object.varianten.options(joinedload(Varianten.begroeiingsvariant)).order_by(Varianten.diepte):
            active = selected_variant_id == profile.id
            profs.append({
                'name': profile.id,
                'active': active,  # digits differ far after the
                'depth': profile.diepte,
                'begroeiingsvariant': profile.begroeiingsvariant.naam,
                'color': (243, 132, 0, 255) if active else (243, 132, 0, 20),
                'points': [
                    (-0.5 * profile.waterbreedte, hydro_object.streefpeil),
                    (-0.5 * profile.bodembreedte, hydro_object.streefpeil - profile.diepte),
                    (0.5 * profile.bodembreedte, hydro_object.streefpeil - profile.diepte),
                    (0.5 * profile.waterbreedte, hydro_object.streefpeil),
                ]
            })
        self.variant_model.insertRows(profs)

    def update_available_profiles(self, item, variant):

        # update variant table
        self.on_select_edit_hydrovak(item)
        diepte = float(variant.diepte)

        if item.hydrovak.get('variant_max_depth') is None or diepte > item.hydrovak.get('variant_max_depth'):
            self.legger_model.setDataItemKey(item, 'variant_max_depth', diepte)

        if item.hydrovak.get('variant_min_depth') is None or diepte < item.hydrovak.get('variant_min_depth'):
            self.legger_model.setDataItemKey(item, 'variant_min_depth', diepte)

    def on_hover_profile(self):
        pass

    def on_select_profile(self):
        pass

    def closeEvent(self, event):
        """
        close event for widget, including removal of layers and disconnection of listeners
        event: close event
        return: None
        """
        if self.vl_tree_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_tree_layer)
        if self.line_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.line_layer)
        if self.vl_endpoint_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_endpoint_layer)
        if self.vl_track_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_track_layer)
        if self.vl_hover_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_hover_layer)
        if self.vl_selected_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_selected_layer)
        if self.vl_startpoint_hover_layer in QgsMapLayerRegistry.instance().mapLayers().values():
            QgsMapLayerRegistry.instance().removeMapLayer(self.vl_startpoint_hover_layer)

        self.category_combo.currentIndexChanged.disconnect(self.category_change)
        self.show_manual_input_button.clicked.disconnect(self.show_manual_input_window)
        self.variant_model.dataChanged.disconnect(self.data_changed_variant)
        self.legger_model.dataChanged.disconnect(self.data_changed_legger_tree)
        self.area_model.dataChanged.disconnect(self.data_changed_area_model)

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

        self.show_manual_input_button = QPushButton(self)
        self.button_bar_hlayout.addWidget(self.show_manual_input_button)
        self.show_manual_input_button.setDisabled(True)

        self.category_combo = QComboBox(self)
        self.button_bar_hlayout.addWidget(self.category_combo)

        spacer_item = QSpacerItem(40,
                                  20,
                                  QSizePolicy.Expanding,
                                  QSizePolicy.Minimum)
        self.button_bar_hlayout.addItem(spacer_item)
        self.main_vlayout.addLayout(self.button_bar_hlayout)

        # add tabWidget for graphWidgets
        self.contentLayout = QHBoxLayout(self)

        self.tree_table_tab = QTabWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tree_table_tab.sizePolicy().hasHeightForWidth())
        self.tree_table_tab.setSizePolicy(sizePolicy)
        self.tree_table_tab.setMinimumSize(QSize(750, 0))

        self.contentLayout.addWidget(self.tree_table_tab)

        # startpointTree
        self.startpoint_tree_widget = StartpointTreeWidget(self, self.area_model)
        # sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(
        #     self.legger_tree_widget.sizePolicy().hasHeightForWidth())
        # self.legger_tree_widget.setSizePolicy(sizePolicy)
        # self.legger_tree_widget.setMinimumSize(QSize(750, 0))

        self.tree_table_tab.addTab(self.startpoint_tree_widget, 'startpunten')

        # LeggerTree
        self.legger_tree_widget = LeggerTreeWidget(self, self.legger_model)
        # sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(
        #     self.legger_tree_widget.sizePolicy().hasHeightForWidth())
        # self.legger_tree_widget.setSizePolicy(sizePolicy)
        # self.legger_tree_widget.setMinimumSize(QSize(750, 0))

        self.tree_table_tab.addTab(self.legger_tree_widget, 'hydrovakken')

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

        self.graph_vlayout.addWidget(self.plot_widget, 2)

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

        self.contentLayout.addLayout(self.graph_vlayout, 2)

        self.rightVstack = QVBoxLayout(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(
        #     self.rightVstack.sizePolicy().hasHeightForWidth())
        self.rightVstack.minimumSize()
        #self.rightVstack.minimumSize(QSize(300, 0))

        self.begroeiings_combo = QComboBox(self)
        self.rightVstack.addWidget(self.begroeiings_combo)
        self.begroeiings_strategy_combo = QComboBox(self)
        self.rightVstack.addWidget(self.begroeiings_strategy_combo)

        # variantentable
        self.plot_item_table = VariantenTable(self, variant_model=self.variant_model)

        self.rightVstack.addWidget(self.plot_item_table)

        self.selected_variant_remark = QPlainTextEdit(self)
        self.selected_variant_remark.setFixedHeight(100)

        self.rightVstack.addWidget(self.selected_variant_remark)

        self.contentLayout.addLayout(self.rightVstack, 0)

        self.main_vlayout.addLayout(self.contentLayout)

        # add dockwidget
        dock_widget.setWidget(self.dock_widget_content)
        self.retranslate_ui(dock_widget)
        QMetaObject.connectSlotsByName(dock_widget)

    def retranslate_ui(self, dock_widget):
        pass
        dock_widget.setWindowTitle(_translate(
            "DockWidget", "Legger", None))
        self.show_manual_input_button.setText(_translate(
            "DockWidget", "Voeg profiel toe", None))
