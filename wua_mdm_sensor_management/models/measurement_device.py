# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


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

    # Modified EIS
    deviceparcellink_ids = fields.One2many(
        string='Parcel Links',
        comodel_name='mdm.device.parcellink',
        inverse_name='device_id')

    # Modified EIS
    linked_all_parcels = fields.Boolean(
        string='Device linked to all parcels (y/n)',
        default=False,
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

    # Modified EIS
    @api.multi
    def action_view_parcels(self):
        self.ensure_one()
        current_device = self
        id_tree_view = self.env.ref(
            'wua_mdm_sensor_management.wua_parcel_from_device_view_tree').id
        search_view = self.env.ref(
            'base_wua.wua_parcel_view_search')
        mapped_device_id = 0
        if not current_device.linked_all_parcels:
            mapped_device_id = current_device.id
        custom_context = {'mapped_device_id': mapped_device_id, }
        self.env['wua.parcel'].__class__._my_mapped_device_id = mapped_device_id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'context': custom_context,
            }
        return act_window


# Modified EIS
class MeasurementDeviceParcellink(models.Model):
    _name = 'mdm.device.parcellink'
    _description = 'Parcel link of a device'
    _order = 'name'

    device_id = fields.Many2one(
        string='Device',
        comodel_name='mdm.measurement.device',
        required=True,
        index=True,
        ondelete='cascade',
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Code',
        store=True,
        index=True,
        compute='_compute_name',
    )

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing device-parcel line.'),
        ]

    @api.depends('device_id', 'parcel_id', 'device_id.name', 'parcel_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.device_id and record.parcel_id and
               record.device_id.name and record.parcel_id.name):
                name = record.parcel_id.name + ' - ' + record.device_id.name
            record.name = name
