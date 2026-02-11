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
        string='Key (deprecated)',
        size=255,
        help='Secret key of the Sentinel-Hub account (deprecated, use OAuth2)')

    url_api_fis = fields.Char(
        string='API FIS (deprecated)',
        size=255,
        help='URL of the API FIS of Sentinel-Hub (deprecated)')

    url_wms = fields.Char(
        string='WMS Service',
        size=255,
        help='URL of the WMS service of Sentinel-Hub')

    initial_date = fields.Date(
        string='Initial Date',
        default='2021-01-01',
        help='Date of the first remote-sensing data capture')

    # OAuth2 credentials for Statistical API
    oauth_client_id = fields.Char(
        string='OAuth2 Client ID',
        size=255,
        help='Client ID for OAuth2 authentication with Sentinel-Hub')

    oauth_client_secret = fields.Char(
        string='OAuth2 Client Secret',
        size=255,
        help='Client Secret for OAuth2 authentication with Sentinel-Hub')

    url_api_statistical = fields.Char(
        string='Statistical API URL',
        size=255,
        default='https://services.sentinel-hub.com/api/v1/statistics',
        help='URL of the Statistical API of Sentinel-Hub')

    url_oauth_token = fields.Char(
        string='OAuth2 Token URL',
        size=255,
        default='https://services.sentinel-hub.com/auth/realms/main/protocol/'
                'openid-connect/token',
        help='URL for obtaining OAuth2 tokens from Sentinel-Hub')

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
        values.set_default('wua.vegetationindex.configuration',
                           'oauth_client_id',
                           self.oauth_client_id)
        values.set_default('wua.vegetationindex.configuration',
                           'oauth_client_secret',
                           self.oauth_client_secret)
        values.set_default('wua.vegetationindex.configuration',
                           'url_api_statistical',
                           self.url_api_statistical)
        values.set_default('wua.vegetationindex.configuration',
                           'url_oauth_token',
                           self.url_oauth_token)
