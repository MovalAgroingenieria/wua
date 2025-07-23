# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class MeasurementDevice(models.Model):
    _name = 'mdm.measurement.device'
    _inherit = ['mdm.measurement.device']

    subparcel_id = fields.Many2one(
        string='Subparcel',
        comodel_name='wua.parcel.subparcel',
        index=True,
        ondelete='restrict',
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        compute='_compute_parcel_id',
        store=True,
        index=True,
        ondelete='restrict',
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        compute='_compute_partner_id',
        store=True,
        index=True,
        ondelete='restrict',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
    )

    with_gis_measurement_device = fields.Boolean(
        string='With GIS Measurement Device',
        readonly=True,
    )

    @api.depends('subparcel_id', 'subparcel_id.partner_id')
    def _compute_parcel_id(self):
        for record in self:
            parcel_id = None
            if record.subparcel_id:
                parcel_id = record.subparcel_id.parcel_id.id
            record.parcel_id = parcel_id

    @api.depends('parcel_id', 'parcel_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.parcel_id and record.parcel_id.partner_id:
                partner_id = record.parcel_id.partner_id.id
            record.partner_id = partner_id

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        param = "measurementdeviceid"
        for record in self:
            final_url = url
            if final_url:
                query_params = []
                if param and record.name:
                    query_params.append('%s=%s' % (param, record.name))
                if username and password:
                    cipher_text = self.env[
                        'wua.parcel']._get_viewer_credentials(
                        username, password)
                    if cipher_text:
                        query_params.append('arg=%s' % cipher_text)
                if query_params:
                    sep = '?' if '?' not in final_url else '&'
                    final_url += sep + '&'.join(query_params)
            record.gis_viewer_link = final_url or ''

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
            parcel_model.create_mdm_gis_measurement_device_table()
            parcel_model.create_measurement_device_triggers()
        except Exception:
            pass
