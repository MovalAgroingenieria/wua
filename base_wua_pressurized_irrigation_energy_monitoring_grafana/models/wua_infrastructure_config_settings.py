# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    dashboard_id = fields.Char(
        string='Dashboard id',
        required=True,
        help='The id of the embebbed dashboard.')

    dashboard_path = fields.Char(
        compute="_compute_dashboard_path")

    @api.depends('dashboard_id')
    def _compute_dashboard_path(self):
        for record in self:
            path = '/d/' + record.dashboard_id + '/bombeos'
            record.dashboard_path = path

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'dashboard_id', self.dashboard_id)
        values.set_default('wua.infrastructure.configuration',
                           'dashboard_path', self.dashboard_path)
        super(WuaInfrastructureConfiguration, self).set_default_values()
