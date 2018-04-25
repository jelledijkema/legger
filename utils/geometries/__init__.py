from line import LineString


def shape(geometry):

    if geometry['type'].lower() == 'linestring':
        return LineString(geometry['coordinates'])
    # todo: support others or create shapely geometry
