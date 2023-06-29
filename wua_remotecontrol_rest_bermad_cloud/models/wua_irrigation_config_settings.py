# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_bermad = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_bermad = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_bermad = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_bermad = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_bermad = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_bermad = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_bermad = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_bermad = fields.Boolean(
        string='Import from readings')

    import_from_pressuresensormeasurement_bermad = fields.Boolean(
        string='Import from pressure measurements')

    import_from_waterconnection_bermad = fields.Boolean(
        string='Import from waterconnection')

    import_from_pressuresensor_bermad = fields.Boolean(
        string='Import from pressuresensor')

    import_from_irrigationshed_bermad = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_bermad = fields.Boolean(
        string='Import from hydraulic sector')

    import_from_intake_readings_bermad = fields.Boolean(
        string='Import from intake readings')

    import_from_waterpipe_readings_bermad = fields.Boolean(
        string='Import from water pipe readings')

    import_from_flowmeter_bermad = fields.Boolean(
        string='Import from flow meter')

    import_from_reservoir_readings_bermad = fields.Boolean(
        string='Import from reservoir readings')

    import_from_reservoir_bermad = fields.Boolean(
        string='Import from reservoir')

    last_api_response_hidrantes = fields.Char(
        string='API Raw Response for endpoint /hidrantes/medidas')

    last_api_response_cabezales = fields.Char(
        string='API Raw Response for endpoint /cabezales/medidas')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_bermad',
                           self.url_remotecontrol_rest_bermad)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_bermad',
                           self.url_remotecontrol_rest_username_bermad)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_bermad',
                           self.url_remotecontrol_rest_password_bermad)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_bermad',
                           self.url_remotecontrol_application_bermad)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_bermad',
                           self.automatic_census_synchronization_bermad)
        values.set_default('wua.irrigation.configuration',
                           'last_api_response_hidrantes',
                           self.last_api_response_hidrantes)
        values.set_default('wua.irrigation.configuration',
                           'last_api_response_cabezales',
                           self.last_api_response_cabezales)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET bermad config
        bermad_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_bermad')
        return other_can_send or bermad_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET bermad config
        bermad_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_bermad')
        return other_can_send or bermad_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_bermad')
        return other_can_import or bermad_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_bermad')
        return other_can_import or bermad_can_impport

    def import_from_pressuresensor_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_pressuresensor_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_pressuresensor_bermad')
        return other_can_import or bermad_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_bermad')
        return other_can_import or bermad_can_impport

    def import_from_flowmeter_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_flowmeter_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_flowmeter_bermad')
        return other_can_import or bermad_can_impport

    def import_from_reservoir_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_reservoir_any()
        # GET bermad config
        bermad_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_reservoir_bermad')
        return other_can_import or bermad_can_impport
