# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_hp3 = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_hp3 = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_hp3 = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_hp3 = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_hp3 = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_hp3 = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_hp3 = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_hp3 = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_hp3 = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_hp3 = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_hp3 = fields.Boolean(
        string='Import from hydraulic sector')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_hp3',
                           self.url_remotecontrol_rest_hp3)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_hp3',
                           self.url_remotecontrol_rest_username_hp3)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_hp3',
                           self.url_remotecontrol_rest_password_hp3)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_hp3',
                           self.url_remotecontrol_application_hp3)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_hp3',
                           self.automatic_census_synchronization_hp3)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET hp3 config
        hp3_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_hp3')
        return other_can_send or hp3_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET hp3 config
        hp3_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_hp3')
        return other_can_send or hp3_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET hp3 config
        hp3_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_hp3')
        return other_can_import or hp3_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET hp3 config
        hp3_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_hp3')
        return other_can_import or hp3_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET hp3 config
        hp3_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_hp3')
        return other_can_import or hp3_can_impport
