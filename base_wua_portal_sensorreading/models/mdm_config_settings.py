# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MDMConfigSettings(models.TransientModel):
    _inherit = 'mdm.config.settings'

    portal_user_sensorreading_dashboard_id = fields.Many2one(
        string='Portal User Sensorreading dashboard',
        comodel_name='board.grafana.dashboard.storage',
        ondelete='restrict',
        help="The dashboard to be used for portal sensorreading data.")

    portal_user_sensorreading_dashboard_histogram_id = fields.Many2one(
        string='Portal User Sensorreading Histogram dashboard',
        comodel_name='board.grafana.dashboard.storage',
        ondelete='restrict',
        help="The dashboard to be used for portal sensorreading data for "
             "histograms.")

    @api.multi
    def set_default_values(self):
        values = self.env["ir.values"].sudo()
        values.set_default(
            "mdm.config.settings", "portal_user_sensorreading_dashboard_id",
            self.portal_user_sensorreading_dashboard_id.id)
        values.set_default(
            "mdm.config.settings", "portal_user_sensorreading_dashboard_id",
            self.portal_user_sensorreading_dashboard_id.id)
        values.set_default(
            "mdm.config.settings",
            "portal_user_sensorreading_dashboard_histogram_id",
            self.portal_user_sensorreading_dashboard_histogram_id.id)
