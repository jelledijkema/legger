import logging

import pyqtgraph as pg
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBrush, QColor
import numpy as np
from legger.sql_models.legger import HydroObject
from shapely.wkt import loads

log = logging.getLogger('legger.' + __name__)


class LeggerPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, name="", session=None, legger_model=None, variant_model=None):

        super(LeggerPlotWidget, self).__init__(parent)
        # init parameters
        self.series = {}
        self.variant_model = None
        self.legger_model = None

        # store arguments
        self.name = name
        self.session = session
        if legger_model:
            self.setLeggerModel(legger_model)
        if variant_model:
            self.setVariantModel(variant_model)

        # set other
        self.showGrid(True, True, 0.5)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")

    def setLeggerModel(self, model):
        # todo: remove listeners to old model?
        self.legger_model = model
        self.legger_model.dataChanged.connect(self.data_changed_legger)
        self.legger_model.rowsInserted.connect(self.data_changed_legger)
        self.legger_model.rowsAboutToBeRemoved.connect(
            self.data_changed_legger)

    def setVariantModel(self, model):
        # todo: remove listeners to old model?
        self.variant_model = model
        self.variant_model.dataChanged.connect(self.data_changed_variant)
        self.variant_model.rowsInserted.connect(self.data_changed_variant)
        self.variant_model.rowsAboutToBeRemoved.connect(
            self.data_changed_variant)

    def draw_lines(self):
        self.clear()

        # TODO: tot hier was ik

        # (self.measured_model, 0, 180)
        models = [(self.variant_model, 1, 20)]

        for model, variant, def_opacity in models:
            for item in model.rows:
                if not variant:
                    midpoint = sum([p[0] for p in item.points.value[-2:]]) / 2
                else:
                    midpoint = 0

                width = [p[0] - midpoint for p in item.points.value]
                height = [p[1] for p in item.points.value]

                plot_item = pg.PlotDataItem(
                    x=width,
                    y=height,
                    connect='finite',
                    pen=pg.mkPen(color=list(item.color.value)[:3] + [def_opacity], width=1))

                # keep reference
                item._plot = plot_item
                self.addItem(item._plot)

        self.autoRange()

    def data_changed_variant(self, index, to_index=None):
        """
         change graphs based on changes in locations
         :param index: index of changed field
         """
        model = self.variant_model
        if model.columns[index.column()].name == 'active':
            pass
            # self.draw_lines()

        elif model.columns[index.column()].name == 'hover':
            for item in model.rows:
                item._plot.setPen(color=list(item.color.value)[:3] + [20],
                                  width=1)

            item = model.rows[index.row()]
            if item.hover.value:
                item._plot.setPen(color=item.color.value,
                                  width=2)
            else:
                item._plot.setPen(color=list(item.color.value)[:3] + [20],
                                  width=1)

    def data_changed_legger(self, index, to_index=None):

        field = self.legger_model.column(index.column())['field']

        if field in ['ep', 'sp']:

            if self.legger_model.ep is not None:

                up = self.legger_model.ep.up(end=self.legger_model.sp)

                ids = []
                for line in reversed(up):
                    ids.append(line.hydrovak.get('hydro_id'))

                profs = []
                if len(ids):
                    hydro_objects = self.session.query(HydroObject).filter(HydroObject.id.in_(ids)).all()

                    # todo: self.measured_model.removeRows(0, len(self.measured_model.rows))

                    for obj in hydro_objects:
                        for profile in obj.figuren.filter_by(type_prof='m').all():
                            profs.append({
                                'name': profile.profid,
                                'color': (128, 128, 128),
                                'points': [p for p in loads(profile.coord).exterior.coords]
                            })

                    # todo: self.measured_model.insertRows(profs)

                print('refresh')


class LeggerSideViewPlotWidget(pg.PlotWidget):

    def __init__(self, parent=None, name="", session=None, legger_model=None, relative_depth=True):
        super(LeggerSideViewPlotWidget, self).__init__(parent)

        # init parameters
        self.legger_model = None
        self.variant_model = None
        self.series = {}

        # store arguments
        self.name = name
        self.session = session
        self.relative_depth = relative_depth
        if legger_model:
            self.setLeggerModel(legger_model)

        # set other
        self.showGrid(True, True, 0.5)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")
        self.disableAutoRange()

        self.target_level_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(color=[30, 144, 255, 150], width=2))

        self.depth_plot = pg.PlotDataItem(
            x=[], y=[],
            connect='finite',
            pen=pg.mkPen(color=[0, 100, 255, 150], width=2))

        self.water_fill = pg.FillBetweenItem(self.target_level_plot, self.depth_plot,
                                             brush=pg.mkBrush(color=[0, 100, 255, 25]))

        self.min_depth_plot = pg.PlotDataItem(
            x=[], y=[],
            connect='finite',
            pen=pg.mkPen(color=[246, 166, 0, 150], width=2))

        self.max_depth_plot = pg.PlotDataItem(
            x=[], y=[],
            connect='finite',
            pen=pg.mkPen(color=[246, 80, 0, 150], width=2))

        self.min_depth_plot_interpolated = pg.PlotDataItem(
            x=[], y=[],
            # connect='finite',
            pen=pg.mkPen(None))

        self.max_depth_plot_interpolated = pg.PlotDataItem(
            x=[], y=[],
            # connect='finite',
            pen=pg.mkPen(None))

        self.available_fill = pg.FillBetweenItem(self.min_depth_plot_interpolated, self.max_depth_plot_interpolated,
                                                 brush=pg.mkBrush(QBrush(QColor(246, 80, 0, 10), Qt.SolidPattern)))

        self.selected_depth_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(color=[0, 0, 0, 220], width=3))

        self.tmp_selected_depth_plot = pg.PlotDataItem(
            x=[],
            y=[],
            connect='finite',
            pen=pg.mkPen(color=[60, 60, 60, 120], width=3))

        self.hover_start = pg.InfiniteLine(None,
                                           pen=pg.mkPen(color=[40, 40, 40, 220], width=3))
        self.hover_end = pg.InfiniteLine(None,
                                         pen=pg.mkPen(color=[40, 40, 40, 220], width=3))
        # self.hover_fill = pg.FillBetweenItem(self.hover_start, self.hover_end,
        #                                    brush=pg.mkBrush(QBrush(QColor(100, 100, 100, 10), Qt.SolidPattern)))

        for item in [self.hover_start, self.hover_end,
                     self.water_fill, self.target_level_plot, self.depth_plot,
                     self.available_fill, self.min_depth_plot, self.max_depth_plot,
                     self.selected_depth_plot, self.tmp_selected_depth_plot]:
            self.addItem(item)

    def setLeggerModel(self, model):
        # todo: remove listeners to old model?
        self.legger_model = model
        self.legger_model.dataChanged.connect(self.data_changed_legger)
        self.legger_model.rowsInserted.connect(self.data_changed_legger)
        self.legger_model.rowsAboutToBeRemoved.connect(
            self.data_changed_legger)

    def draw_base_lines(self, data):

        dist = []
        depth = []
        min_depth = []
        max_depth = []
        target_level = []

        for item in data:
            if self.relative_depth:
                ref_level = 0
            else:
                ref_level = item['target_level']

            d = ref_level - item['depth'] if item['depth'] is not None else np.nan
            mind = ref_level - item['min_depth'] if item['min_depth'] is not None else np.nan
            maxd = ref_level - item['max_depth'] if item['max_depth'] is not None else np.nan

            dist.append(item['b_distance'])
            dist.append(item['e_distance'])
            depth.append(d)
            depth.append(d)
            min_depth.append(mind)
            min_depth.append(mind)
            max_depth.append(maxd)
            max_depth.append(maxd)
            target_level.append(ref_level)
            target_level.append(ref_level)

        self.depth_plot.setData(x=dist, y=depth)
        self.min_depth_plot.setData(x=dist, y=min_depth)
        self.max_depth_plot.setData(x=dist, y=max_depth)
        self.min_depth_plot_interpolated.setData(x=dist, y=min_depth)
        self.max_depth_plot_interpolated.setData(x=dist, y=max_depth)

        self.target_level_plot.setData(x=dist, y=target_level)

        self.autoRange()

    def draw_selected_lines(self, data):

        dist = []
        depth = []
        tmp_depth = []

        for item in data:
            if self.relative_depth:
                ref_level = 0
            else:
                ref_level = item['target_level']

            d = ref_level - item['selected_depth'] if item['selected_depth'] is not None else np.nan
            tmp_d = ref_level - item['selected_depth_tmp'] if item['selected_depth_tmp'] is not None else np.nan

            dist.append(item['b_distance'])
            dist.append(item['e_distance'])
            depth.append(d)
            depth.append(d)
            tmp_depth.append(tmp_d)
            tmp_depth.append(tmp_d)

        self.selected_depth_plot.setData(x=dist, y=depth)
        self.tmp_selected_depth_plot.setData(x=dist, y=tmp_depth)

    def data_changed_legger(self, index):

        model = self.legger_model
        field = model.column(index.column())['field']

        if field == 'hover':
            if self.legger_model.hover is None:
                self.hover_start.setValue(None)
                self.hover_end.setValue(None)
            else:
                self.disableAutoRange()
                if self.legger_model.hover.older().hydrovak is None:
                    dist = 0
                else:
                    dist = self.legger_model.hover.older().hydrovak.get('distance')

                self.hover_start.setValue(dist)
                self.hover_end.setValue(
                    self.legger_model.hover.hydrovak.get('distance'))

        elif field in ['sp', 'ep']:
            if self.legger_model.data(index, role=Qt.CheckStateRole) and self.legger_model.ep is not None:
                data = self._get_data()
                self.draw_base_lines(data)
                self.draw_selected_lines(data)
        elif field in ['selected_depth', 'selected_depth_tmp']:
            self.draw_selected_lines(self._get_data())


    def _get_data(self):
        if self.legger_model.ep is None:
            return []
        up = self.legger_model.ep.up(end=self.legger_model.sp)
        out = []
        before = up[-1].older()
        if before.hydrovak:
            dist = before.hydrovak.get('distance')
        else:
            dist = 0

        for line in reversed(up):
            out.append({
                'b_distance': dist,
                'e_distance': line.hydrovak.get('distance'),
                'depth': line.hydrovak.get('depth'),
                'target_level': line.hydrovak.get('target_level'),
                'min_depth': line.hydrovak.get('variant_min'),
                'max_depth': line.hydrovak.get('variant_max'),
                'selected_depth': line.hydrovak.get('selected_depth'),
                'selected_depth_tmp': line.hydrovak.get('selected_depth_tmp'),
            })
            dist = line.hydrovak.get('distance')

        return out
