# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_rest_inelcom = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_rest_username_inelcom = fields.Char(
        string='User Name',
        size=255,
        help='User name for authentication in remote control')

    url_remotecontrol_rest_password_inelcom = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote control')

    url_remotecontrol_application_inelcom = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_inelcom = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_inelcom = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_inelcom = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_inelcom = fields.Boolean(
        string='Import from readings')

    import_from_pressuresensormeasurement_inelcom = fields.Boolean(
        string='Import from pressure measurements')

    import_from_waterconnection_inelcom = fields.Boolean(
        string='Import from waterconnection')

    import_from_pressuresensor_inelcom = fields.Boolean(
        string='Import from pressuresensor')

    import_from_irrigationshed_inelcom = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_inelcom = fields.Boolean(
        string='Import from hydraulic sector')

    import_from_intake_readings_inelcom = fields.Boolean(
        string='Import from intake readings')

    import_from_waterpipe_readings_inelcom = fields.Boolean(
        string='Import from water pipe readings')

    import_from_flowmeter_inelcom = fields.Boolean(
        string='Import from flow meter')

    import_from_reservoir_readings_inelcom = fields.Boolean(
        string='Import from reservoir readings')

    import_from_reservoir_inelcom = fields.Boolean(
        string='Import from reservoir')

    import_irrigation_event_from_waterconnections_inelcom = fields.Boolean(
        string='Import Irrigation Event from waterconnection')

    import_irrigation_schedule_from_waterconnections_inelcom = fields.Boolean(
        string='Import Irrigation Schedule from waterconnection')

    irrigation_events_start_date = fields.Date(
        string='Irrigation Events Start Date',)

    last_api_response_hidrantes = fields.Char(
        string='API Raw Response for endpoint /hidrantes/medidas')

    last_api_response_cabezales = fields.Char(
        string='API Raw Response for endpoint /cabezales/medidas')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_inelcom',
                           self.url_remotecontrol_rest_inelcom)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_username_inelcom',
                           self.url_remotecontrol_rest_username_inelcom)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest_password_inelcom',
                           self.url_remotecontrol_rest_password_inelcom)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_inelcom',
                           self.url_remotecontrol_application_inelcom)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_inelcom',
                           self.automatic_census_synchronization_inelcom)
        values.set_default('wua.irrigation.configuration',
                           'irrigation_events_start_date',
                           self.irrigation_events_start_date)
        values.set_default('wua.irrigation.configuration',
                           'last_api_response_hidrantes',
                           self.last_api_response_hidrantes)
        values.set_default('wua.irrigation.configuration',
                           'last_api_response_cabezales',
                           self.last_api_response_cabezales)
        values.set_default(
            'wua.irrigation.configuration',
            'import_irrigation_schedule_from_waterconnections_inelcom',
            self.import_irrigation_schedule_from_waterconnections_inelcom)
        values.set_default(
            'wua.irrigation.configuration',
            'import_irrigation_event_from_waterconnections_inelcom',
            self.import_irrigation_event_from_waterconnections_inelcom)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET Inelcom config
        inelcom_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_inelcom')
        return other_can_send or inelcom_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET Inelcom config
        inelcom_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_inelcom')
        return other_can_send or inelcom_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET Inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_inelcom')
        return other_can_import or inelcom_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET Inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_inelcom')
        return other_can_import or inelcom_can_impport

    def import_from_pressuresensor_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_pressuresensor_any()
        # GET Inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_pressuresensor_inelcom')
        return other_can_import or inelcom_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET Inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_inelcom')
        return other_can_import or inelcom_can_impport

    def import_from_flowmeter_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_flowmeter_any()
        # GET inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_flowmeter_inelcom')
        return other_can_import or inelcom_can_impport

    def import_from_reservoir_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_reservoir_any()
        # GET inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_reservoir_inelcom')
        return other_can_import or inelcom_can_impport

    def import_irrigation_schedule_from_wc_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_irrigation_schedule_from_wc_any()
        # GET inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_irrigation_schedule_from_waterconnections_inelcom')
        return other_can_import or inelcom_can_impport

    def import_irrigation_event_from_wc_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_irrigation_event_from_wc_any()
        # GET inelcom config
        inelcom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_irrigation_event_from_waterconnections_inelcom')
        return other_can_import or inelcom_can_impport
