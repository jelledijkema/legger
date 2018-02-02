import json
import logging

from ThreeDiToolbox.datasource.netcdf import NetcdfDataSource
from geometry_tools.geom_collections.lines import LineCollection
from geometry_tools.geometries import LineString
from geometry_tools.geometries import shape
from legger.sql_models.legger import DuikerSifonHevel, HydroObject
from legger.sql_models.legger_database import LeggerDatabase
from pyspatialite import dbapi2 as dbapi

log = logging.getLogger(__name__)


# suggestions for improvement:
# - limit max_link_distance related to length of line (no somtimes small lines at end and
#   begin point link.


def read_tdi_results(path_model_db, path_result_db,
                     path_result_nc, path_legger_db,
                     max_link_distance=1.0,
                     match_criteria=3):
    """ joins hydoobjects to 3di-flowlines (through channels) and add the discharge of the last timestep

    path_model_db (string): filepath to sqlite database with 3di model
    path_result_db (string): filepath to sqlite database linked to the 3di results (.sqlite1 file)
    path_result_nc (string):  filepath to netcdf with 3di results (same directory must include the idmapping and
                              aggregated netcdf file)
    path_legger_db (string): filepath to sqlite database with legger data
    max_link_distance (float): maximum distance in meters between hydroobject
    match_criteria (float):
    returns:
        list of dictionaries with model results of hydroobjects

    notes:
    - function uses rdnew (EPSG:28992), so only usable in the Netherlands
    - functions of the ThreeDiToolbox qgis-plugin are used, so make sure this plugin is available
    """

    con_model = dbapi.connect(path_model_db)
    con_res = dbapi.connect(path_result_db)
    con_legger = dbapi.connect(path_legger_db)

    result_ds = NetcdfDataSource(path_result_nc)

    # make sure we got dictionaries returned
    con_model.row_factory = dbapi.Row
    con_res.row_factory = dbapi.Row
    con_legger.row_factory = dbapi.Row

    channel_cursor = con_model.execute(
        'SELECT '
        'id,'
        'ASWKT(TRANSFORM(the_geom, 28992)) AS wkt, '
        'ASGEOJSON(TRANSFORM(the_geom, 28992)) AS geojson, '
        'ST_LENGTH(TRANSFORM(the_geom, 28992)) AS length '
        'FROM v2_channel '
        # 'WHERE id=7119 ' # for testing and debugging
    )

    # read discharge of last timestep. Returns numpy array with index number is idx.
    # to link to model channels, the id mapping is needed.
    qend = result_ds.get_values_by_timestep_nr('q', len(result_ds.timestamps) - 1)

    channel_col = LineCollection()

    for channel in channel_cursor.fetchall():
        flowlines = []

        # get flowlines on channel, including start distance and end distance of flowline on channel
        flowline_cursor = con_res.execute(
            "SELECT fl.id, fl.spatialite_id, fl.type, "
            "Line_Locate_Point(GEOMFROMTEXT(:wkt), TRANSFORM(sn.the_geom, 28992)) * :length AS start_distance, "
            "Line_Locate_Point(GEOMFROMTEXT(:wkt), TRANSFORM(en.the_geom, 28992)) * :length AS end_distance "
            "FROM flowlines fl "
            "LEFT OUTER JOIN nodes sn ON fl.start_node_idx = sn.id "
            "LEFT OUTER JOIN nodes en ON fl.end_node_idx = en.id "
            "WHERE fl.type = 'v2_channel' AND fl.spatialite_id = :id;",
            {
                'id': channel['id'],
                'wkt': channel['wkt'],
                'length': channel['length']
            }
        )

        # append flowlines to channel, including flow on last timestep
        for fl in flowline_cursor.fetchall():
            flowline = {
                'id': fl['id'],
                'spatialite_id': fl['spatialite_id'],
                'start_distance': fl['start_distance'],
                'end_distance': fl['end_distance'],
                'q_end': qend[fl['id']]  # todo: check correct (with +1 etc.)
            }

            flowlines.append(flowline)

        # write channel to collection
        channel_col.write({
            'geometry': json.loads(channel['geojson']),
            'properties': {
                'id': channel['id'],
                'length': channel['length'],
                'flowlines': flowlines
            }
        })

    hydro_cursor = con_legger.execute(
        'SELECT '
        'id, '
        'ASGEOJSON(geometry) AS geojson, '
        'ST_LENGTH(geometry) AS length '
        'FROM hydroobject '
        # 'WHERE objectid=454401 ' # for testing and debugging
    )
    hydroobjects = []

    # loop over all hydroobjects and find flowline through link with channel
    for hydroobject in hydro_cursor.fetchall():

        line = LineString(
            json.loads(hydroobject['geojson'])['coordinates'])

        bbox = line.bounds
        bbox = (
            bbox[0] - max_link_distance,
            bbox[1] - max_link_distance,
            bbox[2] + max_link_distance,
            bbox[3] + max_link_distance,
        )

        # create 9 point on the line to check matching geometries
        points_on_line = [
            line.interpolate(dist * 0.1, normalized=True)
            for dist in range(1, 10)
        ]
        candidates = []

        for channel in channel_col.filter(bbox=bbox):
            geom_channel = shape(channel['geometry'])
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
            # hydroobject can have an other orientation than channel
            dist1 = geom_channel.project(line.startpoint())
            dist2 = geom_channel.project(line.endpoint())
            dist_startpoint = min(dist1, dist2)
            dist_endpoint = max(dist1, dist2)
            if dist2 < dist1:
                factor = -1
            else:
                factor = 1
            # get best flowline

            flowline_candidates = []

            for fl in selected['properties']['flowlines']:
                if (dist_startpoint <= fl['end_distance'] and
                            dist_endpoint >= fl['start_distance']):
                    matching_length = (min(dist_endpoint, fl['end_distance'] -
                                           max(dist_startpoint, fl['start_distance'])))

                    flowline_candidates.append((
                        matching_length,
                        fl
                    ))

            if len(flowline_candidates) == 0:
                log.warning(
                    'Hydroboject %i was linked to channel %i, but it was not possible to '
                    'link both. Maybe hydroobject is small line at begin or end',
                    hydroobject['id'],
                    selected['properties']['id'])

            else:
                matching_length, selected_fl = sorted(
                    flowline_candidates,
                    key=lambda item: item[0],
                    reverse=True
                )[0]

                hydroobjects.append({
                    'id': hydroobject['id'],
                    'qend': selected_fl['q_end'] * factor,
                    'channel_id': selected['properties']['id'],
                    'flowline_id': selected_fl['id'],
                    'nr_candidates': len(candidates),
                    'score': score
                })

    return hydroobjects


def write_tdi_results_to_db(hydroobject_results, path_legger_db):
    db = LeggerDatabase(
        {
            'db_path': path_legger_db
        },
        'spatialite'
    )
    db.create_and_check_fields()
    session = db.get_session()

    results = {hydro['id']: hydro for hydro in hydroobject_results}

    for hydroobj in session.query(HydroObject):
        if hydroobj.id in results:
            result = results[hydroobj.id]
            hydroobj.debiet = result['qend']
            hydroobj.channel_id = result['channel_id']
            hydroobj.flowline_id = result['flowline_id']

    log.info("Save 3di results (update hydro objects) to database ")
    session.commit()


def read_tdi_culvert_results(path_model_db,
                             path_result_nc, path_legger_db):

    con_model = dbapi.connect(path_model_db)
    con_legger = dbapi.connect(path_legger_db)

    result_ds = NetcdfDataSource(path_result_nc)

    # make sure we got dictionaries returned
    con_model.row_factory = dbapi.Row
    con_legger.row_factory = dbapi.Row

    # read discharge of last timestep. Returns numpy array with index number is idx.
    # to link to model channels, the id mapping is needed.
    qend = result_ds.get_values_by_timestep_nr('q', len(result_ds.timestamps) - 1)

    culverts = []

    for tp in ['v2_culvert', 'v2_orifice']:

        cursor = con_model.execute(
            'SELECT '
            'id, code '
            'FROM ' + tp
        )

        id_mapping = result_ds.id_mapping.get(tp, {})

        for culvert in cursor.fetchall():
            idx = id_mapping.get(str(culvert['id']))

            culverts.append({
                'code': culvert['code'],
                'id': culvert['id'],
                'source': tp,
                'idx': idx,
                'qend': qend[idx]
            })

    return culverts


def write_tdi_culvert_results_to_db(culvert_results, path_legger_db):
    db = LeggerDatabase(
        {
            'db_path': path_legger_db
        },
        'spatialite'
    )
    db.create_and_check_fields()
    session = db.get_session()

    results = {culvert['id']: culvert for culvert in culvert_results}

    for culvert in session.query(DuikerSifonHevel):
        if culvert.id in results:
            culvert.debiet = results[culvert.id]['qend']
            # culvert['source']
            # culvert['code']

    log.info("Save 3di result (update) to database ")
    session.commit()
