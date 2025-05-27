# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import urllib
from odoo import models, fields, api, exceptions, _


class WuaPumpgroup(models.Model):
    _inherit = 'wua.pumpgroup'

    pumpgroup_energy_efficiency_grafana_frame = fields.Text(
        string='Energy efficiency Grafana',
        compute='_compute_pumpgroup_energy_efficiency_grafana_frame')

    @api.multi
    def _compute_pumpgroup_energy_efficiency_grafana_frame(self):
        # Get configured dashboard
        pumpgroup_dashboard_id = self.env["ir.values"].get_default(
            "wua.infrastructure.configuration", "pumpgroup_dashboard_id")
        pumpgroup_dashboard = self.env[
            "board.grafana.dashboard.storage"].browse(pumpgroup_dashboard_id)
        # Get pumpgroup dashboard
        pumpgroup_dashboard_path = pumpgroup_dashboard.dashboard_path
        if not pumpgroup_dashboard_path:
            raise exceptions.ValidationError(
                _('The Grafana Pumpgroup dashboard not found.'))
        # Get datasource
        grafana_default_datasource = self.env["ir.values"].get_default(
            "board.grafana.configuration", "grafana_default_datasource")
        if grafana_default_datasource:
            db_name = grafana_default_datasource
        else:
            db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        # Get pumpgroup
        pumpgroup_name = urllib.quote_plus(self.name.encode("UTF-8"))
        pumpgroup = "var-pumpgroup=" + pumpgroup_name
        # Get data
        pumpgroup_values = self.env['wua.pumpgroupmeasurement'].search(
            [('pumpgroup_id', '=', self.id),
             ('of_active_agriculturalseason', '=', True)],
            order='measurement_time')
        if pumpgroup_values:
            epoch_from = "from=" + str(int(datetime.datetime.strptime(
                pumpgroup_values[0].measurement_time,
                "%Y-%m-%d %H:%M:%S").strftime('%s')) * 1000)
            epoch_to = "to=" + str(int(datetime.datetime.strptime(
                pumpgroup_values[-1].measurement_time,
                "%Y-%m-%d %H:%M:%S").strftime('%s')) * 1000)
            # Construct frame src
            frame_src = pumpgroup_dashboard_path + '&' + datasource + '&' + \
                pumpgroup + '&' + epoch_from + '&' + epoch_to + '&'
            if pumpgroup_dashboard.frame_width:
                frame_width = \
                    " width=" + '"' + pumpgroup_dashboard.frame_width + '"'
            else:
                frame_width = " width=100%"
            if pumpgroup_dashboard.frame_height:
                frame_height = \
                    " height=" + '"' + pumpgroup_dashboard.frame_height + '"'
            else:
                frame_height = " height=600px"
            frame_params = frame_width + frame_height
            frame_id = 'energy_efficiency_grafana'
            # Get frame
            grafana_frame = self.env['board.grafana'].create_grafana_frame(
                frame_src, frame_id, frame_params)
        else:
            grafana_frame = _("Data not found")
        for record in self:
            record.pumpgroup_energy_efficiency_grafana_frame = grafana_frame

    @api.multi
    def action_see_graphs(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring_grafana.'
            'wua_pumpgroup_graphs_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Graphs Pumpgroup'),
            'res_model': 'wua.pumpgroup',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
            }
        return act_window
