# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    ndvi_grafana_frame = fields.Text(
        string='NDVI grafana',
        compute='_compute_ndvi_grafana_frame')

    def _compute_ndvi_grafana_frame(self):
        grafana_host = "https://grafana.moval.es/d-solo/"
        dashboard_id = "FjMOzPo7k"
        dashboard_url = grafana_host + dashboard_id + "/ndvi?orgId=1"
        theme = "theme=light"
        panel = "panelId=2"
        db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        parcel = "var-parcel=" + self.name
        body = "<iframe src="
        # Get date range
        ndvi_values = self.env['wua.parcel.vegetationindex.ndvi'].search(
                [('parcel_id', '=', self.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
        epoch_from = "from=" + str(int(datetime.datetime.strptime(
            ndvi_values[0].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
        epoch_to = "to=" + str(int(datetime.datetime.strptime(
            ndvi_values[-1].data_date, "%Y-%m-%d").strftime('%s')) * 1000)
        # Contruct URL
        frame = dashboard_url + '&amp;' + datasource + '&amp;' + \
            parcel + '&amp;' + epoch_from + '&amp;' + epoch_to + '&amp;' + \
            theme + '&amp;' + panel + " "
        body += frame
        body += 'width="100%" height="400" frameborder="0"'
        for record in self:
            record.ndvi_grafana_frame = body
