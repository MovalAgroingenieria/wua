# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


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

    device_parcellink_ids = fields.One2many(
        string='Parcel Links',
        comodel_name='mdm.device.parcellink',
        inverse_name='device_id')

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

    @api.multi
    def action_view_parcels(self):
        self.ensure_one()
        current_device = self
        id_tree_view = self.env.ref(
            'wua_mdm_sensor_management.wua_parcel_from_device_view_tree').id
        search_view = self.env.ref(
            'wua_mdm_sensor_management.wua_parcel_from_device_view_search')
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

    @api.constrains('linked_all_parcels', 'sensor_ids')
    def _check_linked_all_parcels_exclusivity(self):
        for record in self:
            if not record.linked_all_parcels:
                continue
            # Get exclusive sensors of the current device
            exclusive_sensors = record.sensor_ids.filtered(
                lambda s: s.requires_exclusivity)
            if not exclusive_sensors:
                continue
            # Get exclusive types of the current device
            exclusive_types = exclusive_sensors.mapped('type_id.id')
            # Search for all links from other devices
            conflicting_links = self.env['mdm.device.parcellink'].search([
                ('device_id', '!=', record.id)
            ])
            if not conflicting_links:
                continue
            # Gather all sensors from other devices
            other_devices = conflicting_links.mapped('device_id')
            for other_device in other_devices:
                conflicting_sensors = other_device.sensor_ids.filtered(
                    lambda s: s.requires_exclusivity and
                    s.type_id.id in exclusive_types
                )
                if conflicting_sensors:
                    # Get affected parcels
                    affected_parcels = conflicting_links.filtered(
                        lambda l: l.device_id == other_device
                    ).mapped('parcel_id')
                    raise exceptions.ValidationError(_(
                        'Cannot link device "%s" to all parcels because '
                        'sensor "%s" (type: %s) requires exclusivity and '
                        'device "%s" with the same sensor type is already '
                        'linked to %d parcel(s): %s.'
                    ) % (
                        record.name,
                        conflicting_sensors[0].name,
                        conflicting_sensors[0].type_id.name,
                        other_device.name,
                        len(affected_parcels),
                        ', '.join(affected_parcels.mapped('name')[:5]) +
                        ('...' if len(affected_parcels) > 5 else '')
                    ))

    @api.model
    def create(self, vals):
        new_device = super(MeasurementDevice, self).create(vals)
        # a) If linked_all_parcels is True, link all parcels via SQL
        if new_device.linked_all_parcels:
            new_device._link_all_parcels_sql()

        return new_device

    def write(self, vals):
        res = super(MeasurementDevice, self).write(vals)
        # Only process if linked_all_parcels field is being modified
        if 'linked_all_parcels' in vals:
            for record in self:
                if vals['linked_all_parcels']:
                    # c) If setting to True: DELETE + INSERT-SELECT (refresh)
                    record._unlink_all_parcels_sql()
                    record._link_all_parcels_sql()
                else:
                    # b) If setting to False: DELETE all parcel links
                    record._unlink_all_parcels_sql()

        return res

    def _link_all_parcels_sql(self):
        self.ensure_one()
        # Use direct SQL INSERT-SELECT for performance with thousands of parcels
        query = """
            INSERT INTO mdm_device_parcellink
                (device_id, parcel_id, create_uid, create_date, write_uid, write_date)
            SELECT
                %s as device_id,
                wp.id as parcel_id,
                %s as create_uid,
                NOW() as create_date,
                %s as write_uid,
                NOW() as write_date
            FROM wua_parcel wp
            WHERE NOT EXISTS (
                SELECT 1
                FROM mdm_device_parcellink dpl
                WHERE dpl.device_id = %s
                AND dpl.parcel_id = wp.id
            )
        """
        self.env.cr.execute(query, (
            self.id,
            self.env.uid,
            self.env.uid,
            self.id,
        ))
        # Invalidate cache to ensure ORM sees the new records
        self.invalidate_cache(['device_parcellink_ids'])

    def _unlink_all_parcels_sql(self):
        self.ensure_one()
        # Use direct SQL DELETE for performance
        query = """
            DELETE FROM mdm_device_parcellink
            WHERE device_id = %s
        """
        self.env.cr.execute(query, (self.id,))
        # Invalidate cache to ensure ORM sees the changes
        self.invalidate_cache(['device_parcellink_ids'])


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

    @api.constrains('device_id', 'parcel_id')
    def _check_sensor_exclusivity(self):
        for record in self:
            device = record.device_id
            if not device:
                continue
            exclusive_sensors = device.sensor_ids.filtered(lambda s: s.requires_exclusivity)
            if not exclusive_sensors:
                continue
            exclusive_types = exclusive_sensors.mapped('type_id.id')
            if device.linked_all_parcels:
                conflicting_links = self.search([
                    ('device_id', '!=', device.id)
                ])
            else:
                if not record.parcel_id:
                    continue
                conflicting_links = self.search([
                    ('parcel_id', '=', record.parcel_id.id),
                    ('device_id', '!=', device.id)
                ])
            other_sensors = conflicting_links.mapped('device_id.sensor_ids')
            for sensor in other_sensors:
                if sensor.requires_exclusivity and sensor.type_id.id in exclusive_types:
                    raise exceptions.ValidationError(_(
                        'Cannot link device "%s" (%s) because sensor "%s" (type: %s) '
                        'requires exclusivity and there is already another device '
                        'with a sensor of the same type linked %s.'
                    ) % (
                        device.name,
                        'linked to all parcels' if device.linked_all_parcels else record.parcel_id.name,
                        sensor.name,
                        sensor.type_id.name,
                        'in the system' if device.linked_all_parcels else 'to this parcel'
                    ))
