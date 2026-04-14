# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_census_rest_batchline = fields.Char(
        string='Census API REST URL',
        size=255,
        help='Base URL of the IrriWEB Census REST API '
             '(e.g. https://irriweb.example.com)')

    census_apikey_header_batchline = fields.Char(
        string='API Key Header',
        size=100,
        help='Name of the HTTP header used for API key authentication '
             '(e.g. X-Api-Key)')

    census_apikey_value_batchline = fields.Char(
        string='API Key Value',
        size=255,
        help='Secret value sent in the API key header')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'url_census_rest_batchline',
            self.url_census_rest_batchline)
        values.set_default(
            'wua.irrigation.configuration',
            'census_apikey_header_batchline',
            self.census_apikey_header_batchline)
        values.set_default(
            'wua.irrigation.configuration',
            'census_apikey_value_batchline',
            self.census_apikey_value_batchline)

    @api.multi
    def action_census_sync_batchline(self):
        """Trigger a full partner census sync from the configuration form.

        Returns an act_window action opening the created sync log.
        """
        self.ensure_one()
        log = self.env['res.partner']._run_census_sync_batchline(
            trigger='manual')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Census Sync Log'),
            'res_model': 'wua.census.sync.log',
            'res_id': log.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
        }
