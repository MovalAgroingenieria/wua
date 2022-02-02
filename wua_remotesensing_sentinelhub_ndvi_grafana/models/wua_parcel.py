# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    ndvi_grafana_frame = fields.Text(
        string='NDVI grafana',
        compute='_compute_ndvi_grafana_frame')

    def _compute_ndvi_grafana_frame(self):
        # Get config params
        grafana_org_id = self.env['ir.values'].get_default(
            'board.grafana.configuration', 'grafana_org_id')
        dashboard_path = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'dashboard_path')
        panel_id = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'panel_id')
        if not dashboard_path or not panel_id or not grafana_org_id:
            raise exceptions.ValidationError(
                _('The NDVI Grafana config settings have not been set.'))
        # Get data
        org_id = '?orgId=' + str(grafana_org_id)
        dashboard_path = dashboard_path + org_id
        panel = "panelId=" + str(panel_id)
        db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        parcel = "var-parcel=" + self.name
        ndvi_values = self.env['wua.parcel.vegetationindex.ndvi'].search(
                [('parcel_id', '=', self.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
        epoch_from = "from=" + str(int(datetime.datetime.strptime(
            ndvi_values[0].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
        epoch_to = "to=" + str(int(datetime.datetime.strptime(
            ndvi_values[-1].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
        # Construct frame src
        frame_src = dashboard_path + '&' + datasource + '&' + parcel + '&' + \
            epoch_from + '&' + epoch_to + '&' + panel
        frame_params = 'width="100%" height="400"'
        # Get frame
        grafana_frame = self.env['board.grafana'].create_grafana_frame(
            frame_src, frame_params)
        for record in self:
            record.ndvi_grafana_frame = grafana_frame
