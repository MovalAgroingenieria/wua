# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaVegetationindexConfiguration(models.TransientModel):
    _inherit = 'wua.vegetationindex.configuration'

    grafana_host = fields.Char(
        string='Grafana URL',
        help='The URL of grafana host.')

    dashboard_id = fields.Char(
        string='Dashboard id',
        help='The id of the embebbed dashboard.')

    dashboard_url = fields.Char(
        string='Dashboard URL',
        compute="_compute_dashboard_url",
        help='Full dashboard URL.')

    panel_id = fields.Integer(
        string='Panel id',
        help='The id of the panel.')

    @api.depends('grafana_host', 'dashboard_id')
    def _compute_dashboard_url(self):
        for record in self:
            if record.grafana_host and record.dashboard_id:
                if record.grafana_host.endswith("/"):
                    dashboard_url = record.grafana_host + 'd-solo/'
                else:
                    dashboard_url = record.grafana_host + '/d-solo/'
                dashboard_url += record.dashboard_id + "/ndvi?orgId=1"
                record.dashboard_url = dashboard_url

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.vegetationindex.configuration',
                           'grafana_host', self.grafana_host)
        values.set_default('wua.vegetationindex.configuration',
                           'dashboard_id', self.dashboard_id)
        values.set_default('wua.vegetationindex.configuration',
                           'dashboard_url', self.dashboard_url)
        values.set_default('wua.vegetationindex.configuration',
                           'panel_id', self.panel_id)
        super(WuaVegetationindexConfiguration, self).set_default_values()
