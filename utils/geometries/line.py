from shapely.geometry import LineString as SLineString
from shapely.geometry import Point as SPoint

import logging
log = logging.getLogger(__name__)


class LineString(SLineString):

    def __init__(self, *args, **kwargs):
        self._length_array = None
        super(LineString, self).__init__(*args, **kwargs)

    def startpoint(self):
        return SPoint(self.coords[0])

    def endpoint(self):
        return SPoint(self.coords[-1])
