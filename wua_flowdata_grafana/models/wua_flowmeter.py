# -*- coding: utf-8 -*-
# 2025 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    flowdata_grafana_frame = fields.Text(
        string='Flowdata grafana',
        compute='_compute_flowdata_grafana_frame')

    def _compute_flowdata_grafana_frame(self):
        # Get config params
        flowdata_dashboard_path = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'flowdata_dashboard_path')
        flowdata_panel_id = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'flowdata_panel_id')
        if not flowdata_dashboard_path or not flowdata_panel_id:
            raise exceptions.ValidationError(
                _('The Flowdata Grafana config settings have not been set.'))
        # Get data
        panel = "panelId=" + str(flowdata_panel_id)
        db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        parcel = "var-parcel=" + self.name
        flowdata_values = self.env['wua.flowdata'].search(
            [('flowmerter_id', '=', self.id)],
            order='time')
        if flowdata_values:
            epoch_from = "from=" + str(int(datetime.datetime.strptime(
                flowdata_values[0].data_date,
                "%Y-%m-%d").strftime('%s')) * 1000)
            epoch_to = "to=" + str(int(datetime.datetime.strptime(
                flowdata_values[-1].data_date,
                "%Y-%m-%d").strftime('%s')) * 1000)
            # Construct frame src
            frame_src = flowdata_dashboard_path + '?' + datasource + '&' + parcel + \
                '&' + epoch_from + '&' + epoch_to + '&' + panel
            frame_params = 'width="100%" height="400"'
            frame_id = 'flowdata_grafana'
            # Get frame
            grafana_frame = self.env['board.grafana'].create_grafana_frame(
                frame_src, frame_id, frame_params)
        else:
            grafana_frame = _("Data not found")
        for record in self:
            record.flowdata_grafana_frame = grafana_frame
