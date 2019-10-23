from pandas import DataFrame
from pyspatialite import dbapi2 as sql

import logging
import numpy as np
import pandas as pd
from legger.sql_models.legger import Varianten, get_or_create

log = logging.getLogger('legger.' + __name__)

"""
Boundary Conditions
"""

Km = 25  # Manning coefficient in m**(1/3/s)
Kb = 23  # Bos and Bijkerk coefficient in 1/s

ini_waterdepth = 0.30  # Initial water depth (m).
default_minimal_waterdepth = ini_waterdepth
min_ditch_bottom_width = 0.5  # (m) Ditch bottom width can not be smaller dan 0,5m.
default_minimal_bottom_width = min_ditch_bottom_width

"""
General Definitions
"""


def read_spatialite(cursor):
    """
    Read the database where all the information on hydro objects for the legger
    calculations are found.
    Return a database to be used in Python.

    Following information is collected:
    - object id
    - normative_flow
    - ditch depth
    - slope (talud), initial and maximum
    - maximum ditch width
    - length of hydro object
    - soil type of area ditch is located
    """

    cursor.execute("Select ho.id, km.diepte, km.breedte, ho.categorieoppwaterlichaam, km.taludvoorkeur, km.grondsoort, "
                   "ST_LENGTH(ST_TRANSFORM(ho.geometry, 28992)) as length, ho.debiet "
                   "from hydroobject ho "
                   "left outer join kenmerken km on ho.id = km.hydro_id ")

    all_hits = cursor.fetchall()

    df = DataFrame(
        all_hits,
        columns=[
            'object_id',
            'DIEPTE',
            'max_ditch_width',
            'category',
            'slope',
            'grondsoort',
            'length',
            'normative_flow']
    )

    df.slope = pd.to_numeric(df.slope)

    return df


def calc_bos_bijkerk(normative_flow, ditch_bottom_width, water_depth, slope, friction_bos_bijkerk=Kb):
    """
    A calculation of the formula for gradient in the water level according to De Bos and Bijkerk.
    Based on physical parameters like normative flow, ditch width, water depth and slope.
    """
    ditch_circumference = (ditch_bottom_width
                           + (np.sqrt(water_depth ** 2 + (slope * water_depth) ** 2))
                           + (np.sqrt(water_depth ** 2 + (slope * water_depth) ** 2)))

    ditch_cross_section_area = (ditch_bottom_width * water_depth
                                + (0.5 * (water_depth * slope) * water_depth)
                                + (0.5 * (water_depth * slope) * water_depth))

    # Formule: Hydraulische Straal = Nat Oppervlak/ Natte Omtrek
    hydraulic_radius = ditch_cross_section_area / ditch_circumference

    # Formule: Gradient = Q / (((A*Kb*(waterdiepte^1/3))*(hydraulische straal^1/2)^2)*100000)
    gradient_bos_bijkerk = ((normative_flow / (
            ditch_cross_section_area * friction_bos_bijkerk * (water_depth ** 0.333333) *
            (hydraulic_radius ** 0.5))) ** 2) * 100000

    return gradient_bos_bijkerk


def calc_manning(normative_flow, ditch_bottom_width, water_depth, slope, friction_manning=Km):
    ditch_circumference = (ditch_bottom_width
                           + (np.sqrt(water_depth ** 2 + (slope * water_depth) ** 2))
                           + (np.sqrt(water_depth ** 2 + (slope * water_depth) ** 2)))

    ditch_cross_section_area = (ditch_bottom_width * water_depth
                                + (0.5 * (water_depth * slope) * water_depth)
                                + (0.5 * (water_depth * slope) * water_depth))

    # Formule: Hydraulische Straal = Nat Oppervlak/ Natte Omtrek
    hydraulic_radius = ditch_cross_section_area / ditch_circumference

    # Furmule: Verhang = ((Q / (A*Km*(hydraulische straal^(2/3)))^2)*100000
    gradient_manning = ((normative_flow /
                         (ditch_cross_section_area * friction_manning * (hydraulic_radius ** 0.666667))) ** 2) * 100000

    return gradient_manning


def calc_profile_variants_for_all(hydro_objects,
                                  gradient_norm,
                                  minimal_waterdepth=default_minimal_waterdepth,
                                  minimal_bottom_width=None,
                                  store_all_from_depth=None,
                                  store_all_to_depth=None,
                                  depth_mapping_field=None,
                                  friction_bos_bijkerk=None,
                                  friction_manning=None):
    variants_table = DataFrame(columns=['object_id', 'object_waterdepth_id', 'slope',
                                        'water_depth', 'ditch_width', 'ditch_bottom_width',
                                        'normative_flow', 'gradient_bos_bijkerk', 'friction_bos_bijkerk',
                                        'surge'])

    for row in hydro_objects.itertuples():

        if depth_mapping_field and type(store_all_from_depth) == dict:
            from_depth = store_all_from_depth.get(getattr(row, depth_mapping_field), default_minimal_waterdepth)
        else:
            from_depth = store_all_from_depth
        if depth_mapping_field and type(store_all_to_depth) == dict:
            to_depth = store_all_to_depth.get(getattr(row, depth_mapping_field), 8)
        else:
            to_depth = store_all_to_depth

        to_depth = max(to_depth, row.DIEPTE * 1.2 if pd.notnull(row.DIEPTE) else None)

        try:
            variants_table = variants_table.append(
                calc_profile_variants_for_hydro_object(
                    hydro_object=row,
                    gradient_norm=gradient_norm,
                    minimal_waterdepth=minimal_waterdepth,
                    minimal_bottom_width=minimal_bottom_width,
                    store_from_depth=from_depth,
                    store_to_depth=to_depth,
                    friction_bos_bijkerk=friction_bos_bijkerk,
                    friction_manning=friction_manning
                ),
                ignore_index=True
            )
        except ValueError as e:
            log.info('can not calculate variant for profile %s', row.object_id)

    variants_table = variants_table.reset_index(drop=True)
    return variants_table


def calc_profile_variants_for_hydro_object(
        hydro_object,
        gradient_norm,
        minimal_waterdepth=default_minimal_waterdepth,
        minimal_bottom_width=None,
        store_from_depth=None,
        store_to_depth=None,
        friction_bos_bijkerk=None,
        friction_manning=None):
    """
    In this formula the different variants of suitable profiles are generated.
    The output is twofold:
    - a table where every variant is added.
    """
    if friction_bos_bijkerk is None and friction_manning is None:
        raise ValueError('friction bos_bijkerk or manning are both None, at least one must be provided. ')

    slope = hydro_object.slope
    max_ditch_width = hydro_object.max_ditch_width
    normative_flow = hydro_object.normative_flow
    object_id = hydro_object.object_id
    length = hydro_object.length

    # if max_ditch_width is None:
    #     raise ValueError("hydro object value 'max_ditch_width' must be a value (not None or 0).")
    if normative_flow is None or pd.isnull(normative_flow):
        raise ValueError("hydro object value 'normative_flow' must be a value (not None or 0).")

    # a table where variants are saved.
    variants_table = DataFrame(columns=['object_id', 'object_waterdepth_id', 'slope',
                                        'water_depth', 'ditch_width', 'ditch_bottom_width',
                                        'normative_flow', 'gradient_bos_bijkerk', 'friction_bos_bijkerk',
                                        'surge'])

    # minus 0.10, because in loop this is added
    water_depth = store_from_depth - 0.10

    go_on = True
    while go_on:
        # water_depth for this while loop
        if water_depth <= 1:
            water_depth = water_depth + 0.10
        elif water_depth <= 3:
            water_depth = water_depth + 0.20
        else:
            water_depth = water_depth + 0.50

        # initial values for finding profile which fits
        gradient_bos_bijkerk = 1000
        gradient_manning = 1000
        # minus 0.10, because in loop 0.10 is added
        ditch_bottom_width = minimal_bottom_width - 0.10
        ditch_width = None

        # make sure this loop runs at least one time to calculate values
        while gradient_bos_bijkerk > gradient_norm or gradient_manning > gradient_norm:

            ditch_bottom_width = ditch_bottom_width + 0.10
            try:
                ditch_width = ditch_bottom_width + water_depth * slope * 2.0
            except Exception as e:
                a = 1
                raise e

            if friction_bos_bijkerk is not None:
                gradient_bos_bijkerk = calc_bos_bijkerk(
                    normative_flow, ditch_bottom_width, water_depth, slope, friction_bos_bijkerk)
            else:
                gradient_bos_bijkerk = 0

            if friction_manning is not None:
                gradient_manning = calc_manning(
                    normative_flow, ditch_bottom_width, water_depth, slope, friction_manning)
            else:
                gradient_manning = 0

            # loop until gradient is lower than norm or profile gets wider than max_width
            # if first try is wider, this (to wide) profile is stored
            if ditch_width + 0.05 > max_ditch_width:
                break

        # store
        object_waterdepth_id = "{0}_{1:.2f}-{2:.1f}".format(
            object_id, water_depth, friction_bos_bijkerk)

        obj = [
            object_id,
            object_waterdepth_id,
            slope,
            water_depth,
            ditch_width,
            ditch_bottom_width,
            normative_flow,
            gradient_bos_bijkerk,
            friction_bos_bijkerk,
            length * gradient_bos_bijkerk / 1000,
        ]

        variants_table = variants_table.append(
            pd.DataFrame([obj], columns=variants_table.columns))

        if water_depth >= store_to_depth and gradient_bos_bijkerk < gradient_norm:
            go_on = False

    variants_table.reset_index()
    return variants_table


def create_theoretical_profiles(legger_db_filepath, gradient_norm, bv):
    """
    main function for calculation of theoretical profiles

    legger_db_filepath (str): path to legger profile
    gradient_norm (float): maximal allowable gradient in waterway in cm/km
    bv (Begroeiingsvariant model instance): Begroeiingsvariant (with friction value) for calculation

    return: calculated profile variant
    """

    conn = sql.connect(legger_db_filepath)
    conn.row_factory = sql.Row
    cursor = conn.cursor()

    # Part 1: read SpatiaLite
    # The original Spatialite database is read into Python for further analysis.
    hydro_objects = read_spatialite(cursor)
    log.debug("Finished 1: SpatiaLite Database read successfully %i objects\n", len(hydro_objects.object_id))

    # Part 2: set minimal slope and get depth ranges
    cursor.execute("Select * from categorie")
    all_categories = cursor.fetchall()

    min_depth_settings = {cat['categorie']: cat['variant_diepte_min'] for cat in all_categories
                          if cat['variant_diepte_min'] is not None}

    max_depth_settings = {cat['categorie']: cat['variant_diepte_max'] for cat in all_categories
                          if cat['variant_diepte_max'] is not None}

    # additional: set max on 1.2 times th maximal depth within the specific category
    cursor.execute(
        "Select categorieoppwaterlichaam, max(diepte) as max_diepte from hydroobjects_kenmerken GROUP BY categorieoppwaterlichaam ")
    categories_max_depth = cursor.fetchall()
    for cat in categories_max_depth:
        if cat['categorieoppwaterlichaam'] in max_depth_settings:
            max_depth_settings[cat['categorieoppwaterlichaam']] = min(
                cat['max_diepte'] * 1.2, max_depth_settings[cat['categorieoppwaterlichaam']])
        else:
            max_depth_settings[cat['categorieoppwaterlichaam']] = cat['max_diepte'] * 1.2

    default_slope = {cat['categorie']: cat['default_talud'] for cat in all_categories
                     if cat['default_talud'] is not None}

    for category, default_slope in default_slope.items():
        hydro_objects.loc[
            (pd.isnull(hydro_objects.slope)) & (hydro_objects.category == category), 'slope'] = default_slope

    hydro_objects.loc[(hydro_objects.grondsoort == "veenweide") & (hydro_objects.slope < 3.0), 'slope'] = 3.0
    hydro_objects.loc[(pd.isnull(hydro_objects.slope)), 'slope'] = 2.0
    # Part 3: calculate variants
    # todo. get store_all_.... from userinput
    # todo. add manning to friction table
    profile_variants = calc_profile_variants_for_all(
        hydro_objects=hydro_objects,
        gradient_norm=gradient_norm,
        minimal_waterdepth=default_minimal_waterdepth,
        minimal_bottom_width=default_minimal_bottom_width,
        depth_mapping_field='category',
        store_all_from_depth=min_depth_settings,
        store_all_to_depth=max_depth_settings,
        friction_bos_bijkerk=bv.friction,
        friction_manning=None)

    log.info("All potential profiles are created\n")
    return profile_variants


def write_theoretical_profile_results_to_db(session, profile_results, gradient_norm, bv):
    log.info("Writing output to db...\n")

    for row in profile_results.itertuples():
        # todo: add for manning
        if row.gradient_bos_bijkerk > gradient_norm:
            opmerkingen = "voldoet niet aan de norm."
        else:
            opmerkingen = ""

        variant, new = get_or_create(
            session,
            Varianten,
            id=row.object_waterdepth_id,
            defaults={
                'hydro_id': row.object_id,
                'begroeiingsvariant': bv,
                'talud': row.slope,
                'diepte': row.water_depth
            }
        )
        # todo: store more results
        variant.begroeiingsvariant = bv
        variant.diepte = row.water_depth
        variant.waterbreedte = row.ditch_width
        variant.bodembreedte = row.ditch_bottom_width
        variant.verhang_bos_bijkerk = row.gradient_bos_bijkerk
        variant.opmerkingen = opmerkingen

    session.commit()
