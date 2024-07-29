# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields


class LawMeasuringDevice(models.Model):
    _inherit = 'law.measuring.device'
    _description = 'Law Measuring Device'

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',)

    with_gis_measuring_device = fields.Boolean(
        string='GIS Measuring Device',)

    html_gisviewer_frame = fields.Text(
        string='GIS Viewer',
        compute='_compute_html_gisviewer_frame',)

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        measuring_device_param = self.env['ir.values'].get_default(
            'wua.law.measuring.configuration',
            'url_gis_viewer_measuring_devices_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if measuring_device_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        measuring_device_param + '=' + str(record.name)
            if url_for_record and username and password:
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
            if (record.with_gis_measuring_device and
                    record.gis_viewer_link != ''):
                url = record.gis_viewer_link + '&mode=min'
                url = url.replace('http://', 'https://')
                record.html_gisviewer_frame = \
                    '<p style="text-align:center;margin-top:0px;' + \
                    'margin-left:6px;margin-right:6px;">' + \
                    '<iframe id="iframe_measuring_device" scrolling="no" ' + \
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

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_law_gis_measuring_device_table()
            parcel_model.create_measuring_device_triggers()
        except Exception:
            pass
