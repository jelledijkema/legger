from base import BaseCollection

LINESTRING = 'linestring'



class LineCollection(BaseCollection):

    def __init__(self, *args, **kwargs):
        super(LineCollection, self).__init__(*args, **kwargs)
        self.geometry_type = LINESTRING

    def get_line_with_points(self, points):
        """
        points (list of geometry_tools.Point):
        return:
        """
        pass




