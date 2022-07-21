# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_hidroconta = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_hidroconta = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_hidroconta = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_hidroconta = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_hidroconta = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_hidroconta = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_hidroconta = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_hidroconta = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_hidroconta = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_hidroconta = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_hidroconta = fields.Boolean(
        string='Import from hydraulic sector')

    import_from_intake_readings_hidroconta = fields.Boolean(
        string='Import from intake readings')

    import_from_waterpipe_readings_hidroconta = fields.Boolean(
        string='Import from water pipe readings')

    import_from_flowmeter_hidroconta = fields.Boolean(
        string='Import from flow meter')

    installation_identifier = fields.Integer(
        string='Installation Id.',
        default=0,
        required=True,
        help='Installation Identifier')

    flow_in_liters = fields.Boolean(
        string='API Flow on l/s.',
        default=False,
        required=True,
        help='Flow value from API demeter in l/s')

    _sql_constraints = [
        ('valid_installation_identifier',
         'CHECK (installation_identifier >= 0)',
         'The installation identifier must be a value zero or positive.'),
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_hidroconta',
                           self.url_remotecontrol_rest_hidroconta)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_hidroconta',
                           self.url_remotecontrol_rest_username_hidroconta)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_hidroconta',
                           self.url_remotecontrol_rest_password_hidroconta)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_hidroconta',
                           self.url_remotecontrol_application_hidroconta)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_hidroconta',
                           self.automatic_census_synchronization_hidroconta)
        values.set_default('wua.irrigation.configuration',
                           'installation_identifier',
                           self.installation_identifier)
        values.set_default('wua.irrigation.configuration',
                           'flow_in_liters',
                           self.flow_in_liters)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET hidroconta config
        hidroconta_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_hidroconta')
        return other_can_send or hidroconta_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET hidroconta config
        hidroconta_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_hidroconta')
        return other_can_send or hidroconta_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET hidroconta config
        hidroconta_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_hidroconta')
        return other_can_import or hidroconta_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET hidroconta config
        hidroconta_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_hidroconta')
        return other_can_import or hidroconta_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET hidroconta config
        hidroconta_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_hidroconta')
        return other_can_import or hidroconta_can_impport

    def import_from_flowmeter_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_flowmeter_any()
        # GET hidroconta config
        hidroconta_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_flowmeter_hidroconta')
        return other_can_import or hidroconta_can_impport
