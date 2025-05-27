# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    pumpgroup_dashboard_id = fields.Many2one(
        string='Pumpgroup dashboard',
        comodel_name='board.grafana.dashboard.storage',
        domain="[('integrated_dashboard', '=', True)]",
        ondelete='restrict',
        help="The dashboard to be used for flow data.")

    @api.multi
    def set_default_values(self):
        values = self.env["ir.values"].sudo()
        values.set_default("wua.infrastructure.configuration",
                           "pumpgroup_dashboard_id",
                           self.pumpgroup_dashboard_id.id)
        super(WuaInfrastructureConfiguration, self).set_default_values()
