# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base_wua_hydric_estimation.models import wua_config_settings
import logging

# Short aliases for config keys (avoid E501 in call sites)
DEFAULT_STANDARD_APPLICATION_EFFICIENCY = (
    wua_config_settings.DEFAULT_STANDARD_APPLICATION_EFFICIENCY)
CONTROL_PERIODICITY = wua_config_settings.CONTROL_PERIODICITY
PERIOD_START_DAY = wua_config_settings.PERIOD_START_DAY
AUTOMATIC_CALCULATION = wua_config_settings.AUTOMATIC_CALCULATION
DEFAULT_KC_NDVI_A = wua_config_settings.DEFAULT_KC_NDVI_A
DEFAULT_KC_NDVI_B = wua_config_settings.DEFAULT_KC_NDVI_B
DEFAULT_KC_NDVI_C = wua_config_settings.DEFAULT_KC_NDVI_C
MAX_OFFSET_ALTERNATIVE_NDVI = wua_config_settings.MAX_OFFSET_ALTERNATIVE_NDVI
AERIAL_IMAGE_LAYERS = wua_config_settings.AERIAL_IMAGE_LAYERS
AERIAL_IMAGE_WIDTH = wua_config_settings.AERIAL_IMAGE_WIDTH
AERIAL_IMAGE_HEIGHT = wua_config_settings.AERIAL_IMAGE_HEIGHT
AERIAL_IMAGE_ZOOM = wua_config_settings.AERIAL_IMAGE_ZOOM
AERIAL_IMAGE_FORMAT = wua_config_settings.AERIAL_IMAGE_FORMAT
HYDRIC_EST_NDVI_MODEL = wua_config_settings.HYDRIC_EST_NDVI_MODEL
KC_LOWER_SATURATION = wua_config_settings.KC_LOWER_SATURATION
KC_UPPER_SATURATION = wua_config_settings.KC_UPPER_SATURATION

from odoo import api, SUPERUSER_ID
from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_agriculturalseason_active_idx", "wua_agriculturalseason",
         "CREATE INDEX IF NOT EXISTS wua_agriculturalseason_active_idx "
         "ON wua_agriculturalseason (active_agriculturalseason) "
         "WHERE active_agriculturalseason = true"),
        ("wua_monitoringperiod_agriculturalseason_state_idx",
         "wua_monitoringperiod",
         "CREATE INDEX IF NOT EXISTS wua_monitoringperiod_agriculturalseason_state_idx "
         "ON wua_monitoringperiod (agriculturalseason_id, state)"),
        ("wua_cropunit_agriculturalseason_parcel_idx", "wua_cropunit",
         "CREATE INDEX IF NOT EXISTS wua_cropunit_agriculturalseason_parcel_idx "
         "ON wua_cropunit (agriculturalseason_id, parcel_id, cultivation_id)"),
    ]
    run_performance_indexes(
        cr, _logger, 'base_wua_hydric_estimation', indexes)


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _build_gis_tables(env)


def post_init_hook(cr, registry):
    create_performance_indexes(cr)
    env = api.Environment(cr, SUPERUSER_ID, {})
    _update_parameters(env)
    _update_wua_irrigationsystem(env)
    _update_wua_cultivation(env)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _delete_parameters(env)
    _delete_gis_tables(env)


def _update_parameters(env):
    values = env['ir.values'].sudo()
    values.set_default('wua.configuration',
                       'default_standard_application_efficiency',
                       DEFAULT_STANDARD_APPLICATION_EFFICIENCY)
    values.set_default('wua.configuration',
                       'control_periodicity',
                       CONTROL_PERIODICITY)
    values.set_default('wua.configuration',
                       'period_start_day',
                       PERIOD_START_DAY),
    values.set_default('wua.configuration',
                       'automatic_calculation',
                       AUTOMATIC_CALCULATION),
    values.set_default('wua.configuration',
                       'default_kc_ndvi_a',
                       DEFAULT_KC_NDVI_A)
    values.set_default('wua.configuration',
                       'default_kc_ndvi_b',
                       DEFAULT_KC_NDVI_B)
    values.set_default('wua.configuration',
                       'default_kc_ndvi_c',
                       DEFAULT_KC_NDVI_C)
    values.set_default('wua.configuration',
                       'max_offset_alternative_ndvi',
                       MAX_OFFSET_ALTERNATIVE_NDVI)
    values.set_default('wua.configuration',
                       'hydric_est_ndvi_model',
                       HYDRIC_EST_NDVI_MODEL)
    hydric_est_et0_sensor_type_id = 0
    hydric_est_pe_sensor_type_id = 0
    sensor_types = env['mdm.measurement.device.sensor.type'].search(
        [('requires_exclusivity', '=', True)])
    for sensor_type in (sensor_types or []):
        if sensor_type.sensor_ids:
            if ((not hydric_est_et0_sensor_type_id) or
               (not hydric_est_pe_sensor_type_id)):
                for sensor in sensor_type.sensor_ids:
                    sensor_name = sensor.name.upper()[:2]
                    if (sensor_name == 'ET' and
                       (not hydric_est_et0_sensor_type_id)):
                        hydric_est_et0_sensor_type_id = sensor_type.id
                    if ((sensor_name == 'PE' or sensor_name == 'ER') and
                       (not hydric_est_pe_sensor_type_id)):
                        hydric_est_pe_sensor_type_id = sensor_type.id
            else:
                break
    if hydric_est_et0_sensor_type_id:
        values.set_default('wua.configuration',
                           'hydric_est_et0_sensor_type',
                           hydric_est_et0_sensor_type_id)
    if hydric_est_pe_sensor_type_id:
        values.set_default('wua.configuration',
                           'hydric_est_pe_sensor_type',
                           hydric_est_pe_sensor_type_id)
    values.set_default('wua.configuration',
                       'kc_lower_saturation',
                       KC_LOWER_SATURATION)
    values.set_default('wua.configuration',
                       'kc_upper_saturation',
                       KC_UPPER_SATURATION)
    aerial_image_wms = env['ir.values'].get_default('wua.configuration',
                                                    'url_gis_viewer_wms')
    if aerial_image_wms:
        values.set_default('wua.configuration',
                           'aerial_image_wms',
                           aerial_image_wms)
    values.set_default('wua.configuration',
                       'aerial_image_layers',
                       AERIAL_IMAGE_LAYERS)
    values.set_default('wua.configuration',
                       'aerial_image_width',
                       AERIAL_IMAGE_WIDTH)
    values.set_default('wua.configuration',
                       'aerial_image_height',
                       AERIAL_IMAGE_HEIGHT)
    values.set_default('wua.configuration',
                       'aerial_image_zoom',
                       AERIAL_IMAGE_ZOOM)
    values.set_default('wua.configuration',
                       'aerial_image_format',
                       AERIAL_IMAGE_FORMAT)


def _build_gis_tables(env):
    # EPSG code.
    epsg = 25830
    env.cr.execute("""
        SELECT value FROM ir_values
        WHERE model='wua.configuration' and name='url_gis_viewer_epsg_code'""")
    query_results = env.cr.dictfetchall()
    if (query_results and
       query_results[0].get('value') is not None):
        raw_epsg = query_results[0].get('value').splitlines()[0]
        if raw_epsg[0] == 'I' and len(raw_epsg) > 1:
            raw_epsg = raw_epsg[1:]
            if raw_epsg.isdigit():
                epsg = int(raw_epsg)
    # Creation of the "wua_gis_cropunit" table.
    env.cr.execute("""
        CREATE SEQUENCE IF NOT EXISTS public.wua_gis_cropunit_gid_seq
            INCREMENT 1
            START 1
            MINVALUE 1
            MAXVALUE 2147483647
            CACHE 1""")
    env.cr.execute("""
        CREATE TABLE IF NOT EXISTS public.wua_gis_cropunit(
            gid INTEGER NOT NULL DEFAULT NEXTVAL(
                'wua_gis_cropunit_gid_seq'::regclass),
            name CHARACTER VARYING(255) NOT NULL,
            geom POSTGIS.GEOMETRY(MultiPolygon, %s),
            UNIQUE(name),
            CHECK (name <> ''),
            CONSTRAINT wua_gis_cropunit_pkey PRIMARY KEY (gid))""", (epsg,))
    env.cr.execute("""
        CREATE INDEX IF NOT EXISTS wua_gis_cropunit_idx
        ON public.wua_gis_cropunit USING gist (geom)""")


def _update_wua_irrigationsystem(env):
    updates = {
        'base_wua.irrigationsystem_01': 0.95,
        'base_wua.irrigationsystem_02': 0.90,
        'base_wua.irrigationsystem_03': 0.60,
        'base_wua.irrigationsystem_04': 0.95,
    }
    for xml_id, value in updates.items():
        try:
            rec = env.ref(xml_id)
        except ValueError:
            continue
        rec.write({'standard_application_efficiency': value})


def _update_wua_cultivation(env):
    crop_families = {
        1: [15, 17, 34, 35, 37, 54, 82, 83, 107, 137, 142, 143, 144],
        2: [8, 63, 84, 95, 106, 111, 131, 141],
        3: [1, 4, 6, 13, 21, 22, 25, 27, 28, 36, 47, 48, 50, 52, 53, 55, 69,
            76, 80, 89, 94, 103, 119, 121, 122, 127, 128, 132, 133, 134, 139,
            140, 151],
        4: [115, 123, 125],
        5: [45, 78, 85, 96, 97, 108, 126],
        6: [145, 146, 147],
        7: [3, 5, 9, 11, 16, 31, 33, 38, 40, 43, 44, 62, 68, 75, 86, 87, 88,
            90, 92, 93, 98, 99, 100, 101, 102, 112, 120, 124],
        8: [12, 60, 64, 65, 66, 67, 73, 74, 77, 104, 148],
        9: [26, 49, 61, 105, 136],
        10: [20, 23, 113, 117],
        11: [29, 130],
        12: [2, 10, 18, 30, 79, 81, 109, 129, 138],
        13: [70, 116],
        14: [7, 24, 46, 56],
        15: [72],
        16: [39],
        17: [14, 110, 118],
        18: [19, 51, 71, 135],
        19: [32, 41, 91, 149, 150],
        20: [114],
        21: [42, 57, 58, 59],
    }
    for cropfamily_index, cultivations_index in crop_families.items():
        cropfamily = None
        cropfamily_xml_id = 'base_wua_hydric_estimation.cropfamily_' + \
                            str(cropfamily_index).rjust(3, '0')
        try:
            cropfamily = env.ref(cropfamily_xml_id)
        except ValueError:
            continue
        for cultivation_index in cultivations_index:
            cultivation = None
            cultivation_xml_id = 'base_wua.cultivation_' + \
                str(cultivation_index).rjust(3, '0')
            try:
                cultivation = env.ref(cultivation_xml_id)
            except ValueError:
                continue
            cultivation.write({'cropfamily_id': cropfamily.id})


def _delete_parameters(env):
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.configuration' AND
            (name = 'default_standard_application_efficiency' OR
             name = 'control_periodicity' OR
             name = 'period_start_day' OR
             name = 'automatic_calculation' OR
             name = 'default_kc_ndvi_a' OR
             name = 'default_kc_ndvi_b' OR
             name = 'default_kc_ndvi_c' OR
             name = 'max_offset_alternative_ndvi' OR
             name = 'hydric_est_ndvi_model' OR
             name = 'hydric_est_et0_sensor_type' OR
             name = 'hydric_est_pe_sensor_type' OR
             name = 'kc_lower_saturation' OR
             name = 'kc_upper_saturation' OR
             name = 'aerial_image_wms' OR
             name = 'aerial_image_layers' OR
             name = 'aerial_image_width' OR
             name = 'aerial_image_height' OR
             name = 'aerial_image_zoom' OR
             name = 'aerial_image_format')""")
        env.cr.commit()
    except (Exception,):
        env.cr.rollback()


def _delete_gis_tables(env):
    env.cr.execute('DROP TABLE IF EXISTS public.wua_gis_cropunit CASCADE')
