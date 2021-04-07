import json
import logging
import math
import os
import sqlite3
import subprocess
import sys

from legger.sql_models.legger import HydroObject
from legger.sql_models.legger_database import LeggerDatabase
from legger.sql_models.legger_database import load_spatialite
from legger.utils.geom_collections.lines import LineCollection
from qgis.core import QgsGeometry, QgsPointXY

log = logging.getLogger(__name__)


# suggestions for improvement:
# - limit max_link_distance related to length of line (no somtimes small lines at end and
#   begin point link.

def create_geom_line(coordinates, maincall=True):
    """recursive function to make QgsPoints from coordinates (point, linestring, multilinestring)"""
    if len(coordinates) > 0 and type(coordinates[0]) == list:
        list_of_geoms = [create_geom_line(coord, False) for coord in coordinates]

        if maincall:
            if type(list_of_geoms[0]) == QgsPointXY:
                return QgsGeometry.fromPolylineXY(list_of_geoms)
            else:
                return QgsGeometry.fromMultiPolylineXY(list_of_geoms)
        else:
            return list_of_geoms
    else:
        return QgsPointXY(coordinates[0], coordinates[1])


def load_layer_into_existing_sqlite(path_source, layer_source, path_spatialite, dest_table):
    # ogr exe from python install
    ogr_exe = os.path.abspath(os.path.join(sys.executable, os.pardir, os.pardir, 'bin', 'ogr2ogr.exe'))

    # "-overwrite"
    cmd = '"{ogr_exe}" -a_srs EPSG:28992 -f SQLite -dsco SPATIALITE=YES -append ' \
          '-lco GEOMETRY_NAME=geometry -nln {dest_table}' \
          ' "{spatialite_path}" "{path_source}" {layer_source}'.format(
        ogr_exe=ogr_exe,
        path_source=path_source,
        layer_source=layer_source,
        spatialite_path=path_spatialite,
        dest_table=dest_table, )
    print(cmd)
    log.info(cmd)

    ret = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if ret != 0:
        msg = "ogr2ogr return code was '{ret}' unequal to 0 for table import of {layer_source} " \
              "to {path_spatialite}-{dest_table}".format(
            ret=ret,
            layer_source=layer_source,
            path_spatialite=path_spatialite,
            dest_table=dest_table
        )
        log.error(msg)

        return False

    return True


# if __name__ == '__main__':
#     load_layer_into_existing_sqlite(
#         r'D:\werk\P2021\21.04 - Leggertool met aanvoer - HHNK\data\modeldebieten.gpkg',
#         'BWN_HR_channels_v2',
#         r'D:\tmp\legger\legger_castricum.sqlite',
#         'test_load'
#     )


def read_tdi_results_from_shape(
        path_source,
        layer_source,
        path_legger_db,
        max_link_distance=1.0,
        match_criteria=3):
    """ joins hydoobjects to 3di-flowlines (through channels) and add the discharge of the selected timestep

    path_source (str): filepath to shapefile with 3di results
    layer_source (str): layer or table in source file
    path_legger_db (str): filepath to sqlite database with legger data
    max_link_distance (float): maximum distance in meters between hydroobject
    match_criteria (float):
    returns:
        list of dictionaries with model results of hydroobjects

    notes:
    - function uses rdnew (EPSG:28992), so only usable in the Netherlands
    - functions of the ThreeDiToolbox qgis-plugin are used, so make sure this plugin is available
    """
    table = '3di_results'
    success = load_layer_into_existing_sqlite(path_source, layer_source, path_legger_db, '3di_results')

    if not success:
        return None

    con_legger = load_spatialite(path_legger_db)

    # make sure we got dictionaries returned
    con_legger.row_factory = sqlite3.Row

    # read discharge of timestep. Returns numpy array with index number is idx.
    # to link to model channels, the id mapping is needed.

    # get all 3di channels (for linking to flowlines and hydrovakken)
    channel_cursor = con_legger.execute(
        'SELECT '
        'ogc_fid as id,'
        'CASE WHEN richting > 0 THEN q_m3_s ELSE -1 * q_m3_s END as flow, '
        'ASGEOJSON(geometry) AS geojson, '
        'ST_LENGTH(geometry) AS length '
        'FROM {} '.format(table)
        # 'WHERE id=7119 ' # for testing and debugging
    )

    channel_col = LineCollection()

    for channel in channel_cursor.fetchall():
        # write channel to collection
        channel_col.write({
            'geometry': json.loads(channel['geojson']),
            'properties': {
                'id': channel['id'],
                'length': channel['length'],
                'q_end': channel['flow'],
            }
        })

    hydro_cursor = con_legger.execute(
        'SELECT '
        'id, '
        'ASGEOJSON(geometry) AS geojson, '
        'ST_LENGTH(geometry) AS length '
        'FROM hydroobject '
    )
    hydroobjects = []

    # loop over all hydroobjects and find flowline through link with channel
    for hydroobject in hydro_cursor.fetchall():

        line = create_geom_line(json.loads(hydroobject['geojson'])['coordinates'])
        # with shapely
        # line = LineString(
        #     json.loads(hydroobject['geojson'])['coordinates'])

        bbox = line.boundingBox()
        bbox = bbox.buffered(max_link_distance)
        bbox = [bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum()]
        # with shapely
        # bbox = line.bounds
        # bbox = (
        #     bbox[0] - max_link_distance,
        #     bbox[1] - max_link_distance,
        #     bbox[2] + max_link_distance,
        #     bbox[3] + max_link_distance,
        # )

        # create 9 point on the line to check matching geometries
        length = line.length()
        # with shapely
        # length = line.length

        points_on_line = [
            line.interpolate((float(nr) / 10.0) * length)  # normalized=True
            for nr in range(1, 10)
        ]

        # print(', '.join([str(point.x) for point in points_on_line]))

        candidates = []

        for channel in channel_col.filter(bbox=bbox):

            geom_channel = create_geom_line(channel['geometry']['coordinates'])
            # with shapely
            # geom_channel = shape(channel['geometry'])

            distances = [
                geom_channel.distance(point)
                for point in points_on_line
            ]

            # check how many points are matching
            nr_matches = sum([1 for distance in distances if distance <= max_link_distance])

            if nr_matches >= match_criteria:
                # lower score is better
                score = sum([
                    min(dist, max_link_distance)
                    for dist in distances
                ]) / max_link_distance
                candidates.append((
                    score,
                    channel,
                    geom_channel
                ))

        if len(candidates) > 0:
            score, selected, geom_channel = sorted(candidates, key=lambda item: item[0])[0]

            # get orientation of hydroobject vs channel
            if line.isMultipart():
                vertexes = line.asMultiPolyline()
                d1, p1, v1, o1 = geom_channel.closestSegmentWithContext(vertexes[0][0])
                d2, p2, v2, o2 = geom_channel.closestSegmentWithContext(vertexes[-1][-1])
            else:
                vertexes = line.asPolyline()
                d1, p1, v1, o1 = geom_channel.closestSegmentWithContext(vertexes[0])
                d2, p2, v2, o2 = geom_channel.closestSegmentWithContext(vertexes[-1])

            dist1 = geom_channel.distanceToVertex(v1) - math.sqrt(geom_channel.sqrDistToVertexAt(p1, v1))
            dist2 = geom_channel.distanceToVertex(v2) - math.sqrt(geom_channel.sqrDistToVertexAt(p2, v2))

            if dist2 < dist1:
                factor = -1
            else:
                factor = 1

            hydroobjects.append({
                'id': hydroobject['id'],
                'qend': selected['properties']['q_end'] * factor,
                'channel_id': selected['properties']['id'],
                'nr_candidates': len(candidates),
                'score': score
            })

        else:
            log.warning('no match for hydroobject %s', hydroobject['id'])

    return hydroobjects


def write_tdi_results_to_db(hydroobject_results, path_legger_db):
    db = LeggerDatabase(
        {
            'db_path': path_legger_db
        },
        'spatialite'
    )
    # db.create_and_check_fields()
    session = db.get_session()

    results = {hydro['id']: hydro for hydro in hydroobject_results}

    for hydroobj in session.query(HydroObject):
        if hydroobj.id in results:
            result = results[hydroobj.id]
            hydroobj.debiet_3di = result['qend']
            hydroobj.debiet = hydroobj.debiet_3di
            hydroobj.channel_id = result['channel_id']
            hydroobj.flowline_id = result['flowline_id']
            hydroobj.score = result['score']

    log.info("Save 3di results (update hydro objects) to database ")
    session.commit()
