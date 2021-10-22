# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaVegetationindexConfiguration(models.TransientModel):
    _inherit = 'wua.vegetationindex.configuration'

    layer_moisture = fields.Char(
        string='Moisture-Index Layer',
        size=255,
        help='Moisture-Index layer, in the Sentinel-Hub account')

    band_moisture = fields.Char(
        string='Moisture-Index Band',
        size=255,
        help='Moisture-Index band (C4, for example)')

    max_cloud_cover_moisture = fields.Integer(
        string='Maximum Cloud Cover (%)',
        default=5,
        help='Maximum cloud cover, in percentage; if higher, data will be '
             'ignored')

    resolution_moisture = fields.Integer(
        string='Resolution (m)',
        default=10,
        help='Resolution of the satellite images')

    _sql_constraints = [
        ('valid_max_cloud_cover_moisture',
         'CHECK (max_cloud_cover_moisture >= 0 and '
         'max_cloud_cover_moisture <= 100)',
         'The maximun cloud cover must be a percentage value '
         '(from 0 to 100).'),
        ('valid_resolution_moisture',
         'CHECK (resolution_moisture > 0)',
         'The resolution must be a positive value.'),
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.vegetationindex.configuration',
                           'layer_moisture',
                           self.layer_moisture)
        values.set_default('wua.vegetationindex.configuration',
                           'band_moisture',
                           self.band_moisture)
        values.set_default('wua.vegetationindex.configuration',
                           'max_cloud_cover_moisture',
                           self.max_cloud_cover_moisture)
        values.set_default('wua.vegetationindex.configuration',
                           'resolution_moisture',
                           self.resolution_moisture)
        super(WuaVegetationindexConfiguration, self).set_default_values()
