# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = "wua.infrastructure.configuration"

    flowdata_dashboard_id = fields.Char(
        string="Dashboard id",
        required=True,
        help="The id of the embebbed dashboard.")

    flowdata_dashboard_path = fields.Char(
        compute="_compute_flowdata_dashboard_path")

    flowdata_panel_id = fields.Integer(
        string="Panel id",
        help="The id of the panel.")

    @api.depends("flowdata_dashboard_id")
    def _compute_flowdata_dashboard_path(self):
        for record in self:
            path = "/d-solo/" + record.flowdata_dashboard_id + "/flowdata"
            record.flowdata_dashboard_path = path

    @api.multi
    def set_default_values(self):
        values = self.env["ir.values"].sudo()
        values.set_default("wua.infrastructure.configuration",
                           "flowdata_dashboard_id", self.flowdata_dashboard_id)
        values.set_default("wua.infrastructure.configuration",
                           "flowdata_dashboard_path",
                           self.flowdata_dashboard_path)
        values.set_default("wua.infrastructure.configuration",
                           "flowdata_panel_id", self.flowdata_panel_id)
        super(WuaInfrastructureConfiguration, self).set_default_values()
