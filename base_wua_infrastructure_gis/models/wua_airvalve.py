# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAirvalve(models.Model):
    _inherit = 'wua.airvalve'

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame',
    )

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            if record.with_gis_airvalve and record.gis_viewer_link != '':
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:0px;' + \
                    'margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_airvalves" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="0" height="260" width="98%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''
