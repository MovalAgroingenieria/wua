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
        # Get config params
        grafana_org_id = self.env['ir.values'].get_default(
            'board.grafana.configuration', 'grafana_org_id')
        dashboard_path = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'dashboard_path')
        panel_id = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'panel_id_energy_efficiency')
        if not dashboard_path or not panel_id or not grafana_org_id:
            raise exceptions.ValidationError(
                _('The Grafana config settings have not been set.'))
        # Get data
        org_id = '?orgId=' + str(grafana_org_id)
        dashboard_path = dashboard_path + org_id
        db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        pump_name = urllib.quote_plus(self.name.encode("UTF-8"))
        pump = "var-bombeo=" + pump_name
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
            frame_src = dashboard_path + '&' + datasource + '&' + pump + \
                '&' + epoch_from + '&' + epoch_to
            frame_params = 'width="100%" height="600"'
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
