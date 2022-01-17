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
        dashboard_url = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'dashboard_url')
        panel_id = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'panel_id')
        panel = "panelId=" + str(panel_id)
        if not dashboard_url or not panel_id:
            raise exceptions.ValidationError(
                _('The grafana configuration parameters have not been set.'))
        # Get data
        db_name = self.env.cr.dbname
        datasource = "var-Datasource=" + db_name
        parcel = "var-parcel=" + self.name
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
        grafana_frame = dashboard_url + '&amp;' + datasource + '&amp;' + \
            parcel + '&amp;' + epoch_from + '&amp;' + epoch_to + '&amp;' + \
            'theme=light' + '&amp;' + panel + '&kiosk' + " "
        body = "<iframe src=" + grafana_frame
        body += 'width="100%" height="400" frameborder="0"'
        for record in self:
            record.ndvi_grafana_frame = body
