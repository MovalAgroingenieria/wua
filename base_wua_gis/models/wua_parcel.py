# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame')

    html_gisviewer_frame_bis = fields.Text(
        string='GIS Viewer (bis)',
        related='html_gisviewer_frame')

    parcel_gis_preview_in_form = fields.Boolean(
        string='GIS preview of parcels in the form',
        compute='_compute_parcel_gis_preview_in_form')

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            with_gis_parcel = record.with_gis_parcel
            gis_viewer_link = record.gis_viewer_link
            if record.with_gis_parcel and record.gis_viewer_link != '':
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;' + \
                    'margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_parcels" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="1" height="400" width="67%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''

    @api.multi
    def _compute_parcel_gis_preview_in_form(self):
        parcel_gis_preview_in_form = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'parcel_gis_preview_in_form')
        for record in self:
            record.parcel_gis_preview_in_form = parcel_gis_preview_in_form
