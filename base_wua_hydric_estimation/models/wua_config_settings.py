# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api

DEFAULT_STANDARD_APPLICATION_EFFICIENCY = 0.95
DEFAULT_CONTROL_PERIODICITY = 7
DEFAULT_KC_NDVI_A = 0.0
DEFAULT_KC_NDVI_B = 1.44
DEFAULT_KC_NDVI_C = -0.1
MAX_OFFSET_ALTERNATIVE_NDVI = 14
# AERIAL_IMAGE_LAYERS = 'pnoa,cropunit_perimeter'
AERIAL_IMAGE_LAYERS = 'catastro,parcel_dark_perimeter_dotted,'\
                      'cropunit_dark_perimeter'
AERIAL_IMAGE_WIDTH = 0
AERIAL_IMAGE_HEIGHT = 288
AERIAL_IMAGE_ZOOM = 1.5
AERIAL_IMAGE_FORMAT = 'png'
HYDRIC_EST_NDVI_MODEL = 'wua.parcel.vegetationindex.ndvi'
KC_LOWER_SATURATION = 0.05
KC_UPPER_SATURATION = 1.5


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    default_standard_application_efficiency = fields.Float(
        string='Default Standard Application Efficiency',
        default=DEFAULT_STANDARD_APPLICATION_EFFICIENCY,
        digits=(32, 2),
        required=True,
        help='Coefficient to calculate gross irrigation requirements from '
             'net requirements',
    )

    default_control_periodicity = fields.Integer(
        string='Default Control Periodicity',
        default=DEFAULT_CONTROL_PERIODICITY,
        required=True,
        help='Number of days in each control period',
    )

    default_kc_ndvi_a = fields.Float(
        string='Default value for the coefficient a in the quadratic '
               'function of Kc',
        default=DEFAULT_KC_NDVI_A,
        digits=(32, 4),
        required=True,
        help='Default value for the coefficient a in the quadratic '
             'function of Kc',
    )

    default_kc_ndvi_b = fields.Float(
        string='Default value for the coefficient b in the quadratic '
               'function of Kc',
        default=DEFAULT_KC_NDVI_B,
        digits=(32, 4),
        required=True,
        help='Default value for the coefficient b in the quadratic '
             'function of Kc',
    )

    default_kc_ndvi_c = fields.Float(
        string='Default value for the coefficient c in the quadratic '
               'function of Kc',
        default=DEFAULT_KC_NDVI_C,
        digits=(32, 4),
        required=True,
        help='Default value for the coefficient c in the quadratic '
             'function of Kc',
    )

    max_offset_alternative_ndvi = fields.Integer(
        string='Maximum offset for find an alternative NDVI',
        default=MAX_OFFSET_ALTERNATIVE_NDVI,
        required=True,
        help='Maximum delay to find an alternative NDVI if it is not found '
             'within the control period.',
    )

    hydric_est_ndvi_model = fields.Char(
        string='Model name for the vegetation index',
        default=HYDRIC_EST_NDVI_MODEL,
        size=255,
        help='The model name for the vegetation index is usually '
             'wua.parcel.vegetationindex.ndvi (model for the NDVI index, '
             'necessary for hydric estimates)',
    )

    hydric_est_et0_sensor_type = fields.Many2one(
        string='Sensor type for ET0 values',
        comodel_name='mdm.measurement.device.sensor.type',
        domain=[('requires_exclusivity', '=', True)],
        help='Sensor type for ET0 values (necessary for hydric estimates)',
    )

    hydric_est_pe_sensor_type = fields.Many2one(
        string='Sensor type for Pe values',
        comodel_name='mdm.measurement.device.sensor.type',
        domain=[('requires_exclusivity', '=', True)],
        help='Sensor type for Pe values (necessary for hydric estimates)',
    )

    kc_lower_saturation = fields.Float(
        string='Lower saturation for Kc',
        default=KC_LOWER_SATURATION,
        digits=(32, 2),
        required=True,
        help='If Kc is lower than this parameter, it will be truncated to '
             'the parameter value.',
    )

    kc_upper_saturation = fields.Float(
        string='Upper saturation for Kc',
        default=KC_UPPER_SATURATION,
        digits=(32, 2),
        required=True,
        help='If Kc is higher than this parameter, it will be truncated to '
             'the parameter value.',
    )

    aerial_image_wms = fields.Char(
        string='WMS service for aerial image',
        size=255,
        help='URL of the WMS service used to obtain aerial images',
    )

    aerial_image_layers = fields.Char(
        string='WMS layers for the aerial image',
        default=AERIAL_IMAGE_LAYERS,
        size=255,
        help='WMS service layers to build the aerial image; the layer names '
             'must be separated by commas, and the last layer name must '
             'have the _perimeter suffix',
    )

    aerial_image_width = fields.Integer(
        string='Width, in pixels, of the aerial image',
        default=AERIAL_IMAGE_WIDTH,
        required=True,
        help='Width, in pixels, of the aerial image; if its value is 0, the '
             'image width will be auto-adjusted to maintain the proportions',
    )

    aerial_image_height = fields.Integer(
        string='Height, in pixels, of the aerial image',
        default=AERIAL_IMAGE_HEIGHT,
        required=True,
        help='Height, in pixels, of the aerial image; if its value is 0, the '
             'image height will be auto-adjusted to maintain the proportions',
    )

    aerial_image_zoom = fields.Float(
        string='Zoom to apply to the aerial image',
        default=AERIAL_IMAGE_ZOOM,
        digits=(32, 2),
        required=True,
        help='This value should be around 1; if it is greater than 1, the '
             'image will be zoomed out, and if it is less than 1, it will '
             'be zoomed in (if it is 1, no zoom will be applied)',
    )

    aerial_image_format = fields.Char(
        string='Graphic format of the aerial image',
        size=10,
        help='Graphic format of the aerial image (jpeg, png, etc)',
    )

    _sql_constraints = [
        ('valid_default_standard_application_efficiency',
         'CHECK (default_standard_application_efficiency >= 0 '
         'and default_standard_application_efficiency <= 1)',
         'The default standard application efficiency must be a value between '
         '0 and 1.'),
        ('valid_default_control_periodicity',
         'CHECK (default_control_periodicity > 0)',
         'The number of days in each control period must be a '
         'strictly positive value.'),
        ('valid_max_offset_alternative_ndvi',
         'CHECK (max_offset_alternative_ndvi > 0)',
         'The maximum offset for find an alternative NDVI must be a '
         'strictly positive value.'),
        ('valid_saturation_kc',
         'CHECK (kc_lower_saturation >= 0 and kc_upper_saturation >= 0 '
         'and kc_upper_saturation > kc_lower_saturation)',
         'Incorrect Kc saturation values.'),
        ('valid_aerial_image_width_height',
         'CHECK (aerial_image_width >= 0 and aerial_image_height >= 0 '
         'and not (aerial_image_width = 0 and aerial_image_height = 0))',
         'The width and height of the aerial image cannot be negative values. '
         'In addition, both cannot be 0 at the same time.'),
        ('valid_aerial_image_zoom',
         'CHECK (aerial_image_zoom > 0)',
         'The zoom of the aerial image must be a strictly positive value.'),
    ]

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.configuration',
                           'default_standard_application_efficiency',
                           self.default_standard_application_efficiency)
        values.set_default('wua.configuration',
                           'default_control_periodicity',
                           self.default_control_periodicity)
        values.set_default('wua.configuration',
                           'default_kc_ndvi_a',
                           self.default_kc_ndvi_a)
        values.set_default('wua.configuration',
                           'default_kc_ndvi_b',
                           self.default_kc_ndvi_b)
        values.set_default('wua.configuration',
                           'default_kc_ndvi_c',
                           self.default_kc_ndvi_c)
        values.set_default('wua.configuration',
                           'max_offset_alternative_ndvi',
                           self.max_offset_alternative_ndvi)
        values.set_default('wua.configuration',
                           'hydric_est_ndvi_model',
                           self.hydric_est_ndvi_model)
        values.set_default('wua.configuration',
                           'hydric_est_et0_sensor_type',
                           self.hydric_est_et0_sensor_type.id)
        values.set_default('wua.configuration',
                           'hydric_est_pe_sensor_type',
                           self.hydric_est_pe_sensor_type.id)
        values.set_default('wua.configuration',
                           'kc_lower_saturation',
                           self.kc_lower_saturation)
        values.set_default('wua.configuration',
                           'kc_upper_saturation',
                           self.kc_upper_saturation)
        values.set_default('wua.configuration',
                           'aerial_image_wms',
                           self.aerial_image_wms)
        values.set_default('wua.configuration',
                           'aerial_image_layers',
                           self.aerial_image_layers)
        values.set_default('wua.configuration',
                           'aerial_image_width',
                           self.aerial_image_width)
        values.set_default('wua.configuration',
                           'aerial_image_height',
                           self.aerial_image_height)
        values.set_default('wua.configuration',
                           'aerial_image_zoom',
                           self.aerial_image_zoom)
        values.set_default('wua.configuration',
                           'aerial_image_format',
                           self.aerial_image_format)
