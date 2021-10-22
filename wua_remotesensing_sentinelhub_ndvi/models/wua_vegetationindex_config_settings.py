# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaVegetationindexConfiguration(models.TransientModel):
    _inherit = 'wua.vegetationindex.configuration'

    layer_ndvi = fields.Char(
        string='NDVI Layer',
        size=255,
        help='NDVI layer, in the Sentinel-Hub account')

    band_ndvi = fields.Char(
        string='NDVI Band',
        size=255,
        help='NDVI band (C4, for example)')

    max_cloud_cover_ndvi = fields.Integer(
        string='Maximum Cloud Cover (%)',
        default=5,
        help='Maximum cloud cover, in percentage; if higher, data will be '
             'ignored')

    resolution_ndvi = fields.Integer(
        string='Resolution (m)',
        default=10,
        help='Resolution of the satellite images')

    _sql_constraints = [
        ('valid_max_cloud_cover_ndvi',
         'CHECK (max_cloud_cover_ndvi >= 0 and max_cloud_cover_ndvi <= 100)',
         'The maximun cloud cover must be a percentage value '
         '(from 0 to 100).'),
        ('valid_resolution_ndvi',
         'CHECK (resolution_ndvi > 0)',
         'The resolution must be a positive value.'),
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.vegetationindex.configuration',
                           'layer_ndvi',
                           self.layer_ndvi)
        values.set_default('wua.vegetationindex.configuration',
                           'band_ndvi',
                           self.band_ndvi)
        values.set_default('wua.vegetationindex.configuration',
                           'max_cloud_cover_ndvi',
                           self.max_cloud_cover_ndvi)
        values.set_default('wua.vegetationindex.configuration',
                           'resolution_ndvi',
                           self.resolution_ndvi)
        super(WuaVegetationindexConfiguration, self).set_default_values()
