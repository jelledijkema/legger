import logging

import pyqtgraph as pg
import numpy as np

log = logging.getLogger('legger.' + __name__)


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

        # TODO: tot hier was ik

        models = [(self.measured_model, 0, 180), (self.variant_model, 1, 20)]

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


class LeggerSideViewPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, name=""):

        super(LeggerSideViewPlotWidget, self).__init__(parent)
        self.name = name
        self.showGrid(True, True, 0.5)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")

        self.series = {}

    def set_data(self, data):
        self.data = data
        self.draw_lines()

    def on_remove(self):
        self.draw_lines()

    def on_insert(self):
        self.draw_lines()

    def draw_lines(self):
        self.clear()

        dist = []
        depth = []
        min_depth = []
        max_depth = []
        target_level = []

        for item in self.data:
            d = item['target_level'] - item['depth'] if item['depth'] is not None else np.nan
            mind = item['target_level'] - item['min_depth'] if item['min_depth'] is not None else np.nan
            maxd = item['target_level'] - item['max_depth'] if item['max_depth'] is not None else np.nan

            dist.append(item['b_distance'])
            dist.append(item['e_distance'])
            depth.append(d)
            depth.append(d)
            min_depth.append(mind)
            min_depth.append(mind)
            max_depth.append(maxd)
            max_depth.append(maxd)
            target_level.append(item['target_level'])
            target_level.append(item['target_level'])

        plot = pg.PlotDataItem(
            x=dist,
            y=depth,
            connect='finite',
            pen=pg.mkPen(color=[40, 60, 80, 90], width=3))

        self.addItem(plot)

        plot = pg.PlotDataItem(
            x=dist,
            y=min_depth,
            connect='finite',
            pen=pg.mkPen(color=[0, 136, 86, 90], width=2))

        self.addItem(plot)

        plot = pg.PlotDataItem(
            x=dist,
            y=max_depth,
            connect='finite',
            pen=pg.mkPen(color=[246, 166, 0, 90], width=2))

        self.addItem(plot)

        plot = pg.PlotDataItem(
            x=dist,
            y=target_level,
            connect='finite',
            pen=pg.mkPen(color=[30, 144, 255, 90], width=2))

        self.addItem(plot)

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
