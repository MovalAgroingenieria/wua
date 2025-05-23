# -*- coding: utf-8 -*-
# 2025 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = "wua.flowmeter"

    flowdata_grafana_frame = fields.Text(
        string="Flowdata grafana",
        compute="_compute_flowdata_grafana_frame")

    @api.multi
    def _compute_flowdata_grafana_frame(self):
        # Get configured dashboard
        flowdata_dashboard_id = self.env["ir.values"].get_default(
            "wua.infrastructure.configuration", "flowdata_dashboard_id")
        flowdata_dashboard = \
            self.env["board.grafana.dashboard.storage"].browse(
                flowdata_dashboard_id)
        # Get flowdata dashboard
        flowdata_dashboard_path = flowdata_dashboard.dashboard_path
        if not flowdata_dashboard_path:
            raise exceptions.ValidationError(
                _("The Grafana Flow dashboard not found."))
        # Get datasource
        grafana_default_datasource = self.env["ir.values"].get_default(
            "board.grafana.configuration", "grafana_default_datasource")
        if grafana_default_datasource:
            db_name = grafana_default_datasource
        else:
            db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        # Get flowmeter
        flowmeter = "var-flowmeter=" + self.name
        # Get flow data
        flowdata_values = self.env["wua.flowdata"].search(
            [("flowmeter_id", "=", self.id)], limit=1)
        if flowdata_values:
            # Construct frame src (use default dashboard parameters)
            frame_src = flowdata_dashboard_path + "&" + datasource + "&" + \
                flowmeter
            frame_params = 'width="100%" height="600"'
            frame_id = "flowdata_grafana"
            # Get frame
            grafana_frame = self.env["board.grafana"].create_grafana_frame(
                frame_src, frame_id, frame_params)
        else:
            grafana_frame = _("Data not found")
        for record in self:
            record.flowdata_grafana_frame = grafana_frame
