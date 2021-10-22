# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaVegetationindexConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.vegetationindex.configuration'
    _description = 'Configuration of base_wua_remotesensing_sentinelhub module'

    enable_remotesensing = fields.Boolean(
        default=False,
        required=True,
        string='Enabled Remote-Sensing')

    remotesensing_key = fields.Char(
        string='Key',
        size=255,
        help='Secret key of the Sentinel-Hub account')

    url_api_fis = fields.Char(
        string='API FIS',
        size=255,
        help='URL of the API FIS of Sentinel-Hub')

    url_wms = fields.Char(
        string='WMS Service',
        size=255,
        help='URL of the WMS service of Sentinel-Hub')

    initial_date = fields.Date(
        string='Initial Date',
        default='2021-01-01',
        help='Date of the first remote-sensing data capture')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.vegetationindex.configuration',
                           'enable_remotesensing',
                           self.enable_remotesensing)
        values.set_default('wua.vegetationindex.configuration',
                           'remotesensing_key',
                           self.remotesensing_key)
        values.set_default('wua.vegetationindex.configuration',
                           'url_api_fis',
                           self.url_api_fis)
        values.set_default('wua.vegetationindex.configuration',
                           'url_wms',
                           self.url_wms)
        values.set_default('wua.vegetationindex.configuration',
                           'initial_date',
                           self.initial_date)
