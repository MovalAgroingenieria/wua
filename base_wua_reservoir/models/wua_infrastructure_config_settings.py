# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    measurements_in_height = fields.Boolean(
        string="Measurements in height",
        help="Indicates whether the readings are height or volume.")

    to_vol_coef_a = fields.Float(
        string='Vol. coefficient A',
        digits=(32, 4))

    to_vol_coef_b = fields.Float(
        string='Vol. coefficient B',
        digits=(32, 4))

    to_vol_coef_c = fields.Float(
        string='Vol. coefficient C',
        digits=(32, 4))

    url_gis_viewer_reservoir_param = fields.Char(
        string='Param for water reservoir',
        size=20,
        help='Name of water reservoir param in the GIS viewer url')

    _sql_constraints = [
        ('to_vol_coef_a_positive', 'CHECK (to_vol_coef_a >= 0)',
         'Vol. coefficient A must be a positive number'),
        ('to_vol_coef_b_positive', 'CHECK (to_vol_coef_b >= 0)',
         'Vol. coefficient B must be a positive number'),
        ('to_vol_coef_c_positive', 'CHECK (to_vol_coef_c >= 0)',
         'Vol. coefficient C must be a positive number'),
        ]

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'measurements_in_height',
                           self.measurements_in_height)
        values.set_default('wua.infrastructure.configuration',
                           'to_vol_coef_a', self.to_vol_coef_a)
        values.set_default('wua.infrastructure.configuration',
                           'to_vol_coef_b', self.to_vol_coef_b)
        values.set_default('wua.infrastructure.configuration',
                           'to_vol_coef_c', self.to_vol_coef_c)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_reservoir_param',
                           self.url_gis_viewer_reservoir_param)
