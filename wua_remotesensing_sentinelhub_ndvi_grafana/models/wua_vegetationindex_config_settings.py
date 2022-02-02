# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaVegetationindexConfiguration(models.TransientModel):
    _inherit = 'wua.vegetationindex.configuration'

    dashboard_id = fields.Char(
        string='Dashboard id',
        required=True,
        help='The id of the embebbed dashboard.')

    dashboard_path = fields.Char(
        compute="_compute_dashboard_path")

    panel_id = fields.Integer(
        string='Panel id',
        help='The id of the panel.')

    @api.depends('dashboard_id')
    def _compute_dashboard_path(self):
        for record in self:
            path = '/d-solo/' + record.dashboard_id + '/ndvi'
            record.dashboard_path = path

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.vegetationindex.configuration',
                           'dashboard_id', self.dashboard_id)
        values.set_default('wua.vegetationindex.configuration',
                           'dashboard_path', self.dashboard_path)
        values.set_default('wua.vegetationindex.configuration',
                           'panel_id', self.panel_id)
        super(WuaVegetationindexConfiguration, self).set_default_values()
