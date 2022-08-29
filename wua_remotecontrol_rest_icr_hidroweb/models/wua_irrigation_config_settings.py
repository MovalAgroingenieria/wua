# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_icr = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_icr = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_icr = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_icr = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_icr = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_icr = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_icr = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_icr = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_icr = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_icr = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_icr = fields.Boolean(
        string='Import from hydraulic sector')

    import_from_intake_readings_icr = fields.Boolean(
        string='Import from intake readings')

    import_from_waterpipe_readings_icr = fields.Boolean(
        string='Import from water pipe readings')

    import_from_flowmeter_icr = fields.Boolean(
        string='Import from flow meter')

    client_identifier = fields.Integer(
        string='Client Id.',
        default=0,
        required=True,
        help='Client Identifier')

    installation_identifier = fields.Char(
        string='Installation Id.',
        required=True,
        help='Installation Identifier, (If more than 1 installation, '
             'separate them by commas)')

    wc_per_group = fields.Integer(
        string='WC. Per group',
        default=4,
        required=True,
        help='Waterconnections per group')

    _sql_constraints = [
        ('valid_client_identifier',
         'CHECK (client_identifier >= 0)',
         'The client identifier must be a value zero or positive.'),
        ('valid_wc_per_group',
         'CHECK (wc_per_group >= 0)',
         'The waterconnections per group must be a value zero or positive.')
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_icr',
                           self.url_remotecontrol_rest_icr)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_icr',
                           self.url_remotecontrol_rest_username_icr)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_icr',
                           self.url_remotecontrol_rest_password_icr)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_icr',
                           self.url_remotecontrol_application_icr)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_icr',
                           self.automatic_census_synchronization_icr)
        values.set_default('wua.irrigation.configuration',
                           'installation_identifier',
                           self.installation_identifier)
        values.set_default('wua.irrigation.configuration',
                           'client_identifier',
                           self.client_identifier)
        values.set_default('wua.irrigation.configuration',
                           'wc_per_group',
                           self.wc_per_group)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET icr config
        icr_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_icr')
        return other_can_send or icr_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET icr config
        icr_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_icr')
        return other_can_send or icr_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET icr config
        icr_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_icr')
        return other_can_import or icr_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET icr config
        icr_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_icr')
        return other_can_import or icr_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET icr config
        icr_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_icr')
        return other_can_import or icr_can_impport

    def import_from_flowmeter_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_flowmeter_any()
        # GET icr config
        icr_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_flowmeter_icr')
        return other_can_import or icr_can_impport
