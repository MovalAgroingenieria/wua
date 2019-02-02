# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'
    _description = 'Irrigation Sheds (integrated GIS)'

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame'
        )

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            if record.gis_viewer_link != '':
                url_https = record.gis_viewer_link.replace(
                    'http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:0px;">' + \
                    '<iframe id="iframe_sheds" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url_https + '" ' + \
                    'frameborder="0" height="200" width="100%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''
