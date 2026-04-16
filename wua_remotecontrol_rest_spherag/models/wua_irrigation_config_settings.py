# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_application_spherag = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_spherag = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_spherag = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_spherag = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_spherag = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_spherag = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_spherag = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_spherag = fields.Boolean(
        string='Import from hydraulic sector')

    spherag_default_hydraulicsector_id = fields.Many2one(
        string='Default Hydraulic Sector (Spherag imports)',
        comodel_name='wua.hydraulicsector',
        help='Hydraulic sector used to create irrigation sheds when importing '
             'water connections from Spherag discovery JSON.')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_spherag',
            self.url_remotecontrol_application_spherag)
        values.set_default(
            'wua.irrigation.configuration',
            'automatic_census_synchronization_spherag',
            self.automatic_census_synchronization_spherag)
        values.set_default(
            'wua.irrigation.configuration',
            'spherag_default_hydraulicsector_id',
            self.spherag_default_hydraulicsector_id.id)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET spherag config
        spherag_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_spherag')
        return other_can_send or spherag_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET spherag config
        spherag_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_spherag')
        return other_can_send or spherag_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET spherag config
        spherag_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_spherag')
        return other_can_import or spherag_can_import

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET spherag config
        spherag_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_spherag')
        return other_can_import or spherag_can_import

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET spherag config
        spherag_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_spherag')
        return other_can_import or spherag_can_import
