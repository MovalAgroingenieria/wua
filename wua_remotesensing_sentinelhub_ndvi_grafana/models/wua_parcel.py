# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    ndvi_grafana_frame = fields.Text(
        string='NDVI grafana',
        compute='_compute_ndvi_grafana_frame')

    @api.multi
    def _compute_ndvi_grafana_frame(self):
        # Get configured dashboard
        ndvi_dashboard_id = self.env["ir.values"].get_default(
            "wua.vegetationindex.configuration", "ndvi_dashboard_id")
        ndvi_dashboard = self.env["board.grafana.dashboard.storage"].browse(
            ndvi_dashboard_id)
        # Get ndvi dashboard
        ndvi_dashboard_path = ndvi_dashboard.dashboard_path
        if not ndvi_dashboard_path:
            raise exceptions.ValidationError(
                _("The Grafana NDVI dashboard not found."))
        # Get datasource
        grafana_default_datasource = self.env["ir.values"].get_default(
            "board.grafana.configuration", "grafana_default_datasource")
        if grafana_default_datasource:
            db_name = grafana_default_datasource
        else:
            db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        # Get parcel
        parcel = "var-parcel=" + self.name
        # Get NDVI data
        ndvi_values = self.env['wua.parcel.vegetationindex.ndvi'].search(
            [('parcel_id', '=', self.id),
             ('of_active_agriculturalseason', '=', True)], order='data_date')
        if ndvi_values:
            epoch_from = "from=" + str(int(datetime.datetime.strptime(
                ndvi_values[0].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
            epoch_to = "to=" + str(int(datetime.datetime.strptime(
                ndvi_values[-1].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
            # Construct frame src
            frame_src = ndvi_dashboard_path + '&' + datasource + '&' + \
                parcel + '&' + epoch_from + '&' + epoch_to + '&'
            if ndvi_dashboard.frame_width:
                frame_width = \
                    " width=" + '"' + ndvi_dashboard.frame_width + '"'
            else:
                frame_width = " width=100%"
            if ndvi_dashboard.frame_height:
                frame_height = \
                    " height=" + '"' + ndvi_dashboard.frame_height + '"'
            else:
                frame_height = " height=400px"
            frame_params = frame_width + frame_height
            frame_id = 'ndvi_grafana'
            # Get frame
            grafana_frame = self.env['board.grafana'].create_grafana_frame(
                frame_src, frame_id, frame_params)
        else:
            grafana_frame = _("Data not found")
        for record in self:
            record.ndvi_grafana_frame = grafana_frame
