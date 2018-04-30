from base import BaseCollection

LINESTRING = 'linestring'


class PointCollection(BaseCollection):
    def __init__(self, *args, **kwargs):
        super(PointCollection, self).__init__(*args, **kwargs)
        self.geometry_type = LINESTRING

    def get_points_on_line(self, line, precision=6):
        """

        line (geometry_tools.Line):
        :return:
        """

        pass

