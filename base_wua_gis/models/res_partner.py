# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame'
        )

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            if record.parcel_number > 0 and record.gis_viewer_link != '':
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:20px;' + \
                    'margin-bottom:20px;margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_parcels" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="1" height="400" width="55%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''
