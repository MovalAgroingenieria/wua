# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResFile(models.Model):
    _inherit = 'res.file'

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame')

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if parcel_param:
                    parcels = ','.join(record.parcellink_ids.mapped(
                        lambda x: str(x.parcel_id.name)))
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + str(parcels)
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if (cipher_text):
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def _compute_html_gisviewer_frame(self):
        for record in self:
            if record.has_parcellinks and record.gis_viewer_link != '':
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:0px;' + \
                    'margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_files" scrolling="no" ' + \
                    'marginheight="0" marginwidth="0" ' + \
                    'src="' + url + '" ' + \
                    'frameborder="0" height="260" width="98%" ' + \
                    '></iframe></p>'
            else:
                record.html_gisviewer_frame = ''

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }
