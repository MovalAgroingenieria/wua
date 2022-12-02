# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame')

    html_gisviewer_frame_bis = fields.Text(
        string='GIS Viewer (bis)',
        related='html_gisviewer_frame')

    partner_gis_preview_in_form = fields.Boolean(
        string='GIS preview of partners in the form',
        compute='_compute_partner_gis_preview_in_form')

    @api.multi
    def _compute_html_gisviewer_frame(self):
        model_wua_parcel = self.env['wua.parcel']
        model_wua_parcel_partnerlink = self.env['wua.parcel.partnerlink']
        for record in self:
            html_gisviewer_frame = ''
            if record.parcel_number > 0 and record.gis_viewer_link != '':
                parcels_with_gis = False
                partnerlinks = model_wua_parcel_partnerlink.search(
                    [('partner_id', '=', record.id)])
                for partnerlink in (partnerlinks or []):
                    parcel_id = partnerlink.parcel_id.id
                    parcel = model_wua_parcel.browse(parcel_id)
                    if parcel and parcel.with_gis_parcel:
                        parcels_with_gis = True
                        break
                if parcels_with_gis:
                    url = record.gis_viewer_link + '&mode=min'
                    url = url.replace('http://', 'https://')
                    html_gisviewer_frame = \
                        '<p style="text-align:center;' + \
                        'margin-left:6px;margin-right:6px;">' + \
                        '<iframe id="iframe_partner_parcels" ' + \
                        'scrolling="no" marginheight="0" marginwidth="0" ' + \
                        'src="' + url + '" ' + \
                        'frameborder="1" height="400" width="67%" ' + \
                        '></iframe></p>'
            record.html_gisviewer_frame = html_gisviewer_frame

    @api.multi
    def _compute_partner_gis_preview_in_form(self):
        partner_gis_preview_in_form = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'partner_gis_preview_in_form')
        for record in self:
            record.partner_gis_preview_in_form = partner_gis_preview_in_form
