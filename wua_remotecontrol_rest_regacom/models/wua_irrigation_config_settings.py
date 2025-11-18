# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_application_regacom = fields.Char(
        string='Application URL',
        size=255)

    automatic_census_synchronization_regacom = fields.Boolean(
        string='Automatic Synchcron.',
        help='if it is marked, the changes in parcel/partner census ' +
             'will be automatically sent to the remote control')

    can_be_sent_partners_census_regacom = fields.Boolean(
        string='Can be sent partner census')

    can_be_sent_parcels_census_regacom = fields.Boolean(
        string='Can be sent parcels census')

    import_from_readings_regacom = fields.Boolean(
        string='Import from readings')

    import_from_waterconnection_regacom = fields.Boolean(
        string='Import from waterconnection')

    import_from_irrigationshed_regacom = fields.Boolean(
        string='Import from irrigationshed')

    import_from_hydraulicsector_regacom = fields.Boolean(
        string='Import from hydraulic sector')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application_regacom',
                           self.url_remotecontrol_application_regacom)
        values.set_default('wua.irrigation.configuration',
                           'automatic_census_synchronization_regacom',
                           self.automatic_census_synchronization_regacom)

    def can_be_sent_partners_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_partners_census_any()
        # GET regacom config
        regacom_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_partners_census_regacom')
        return other_can_send or regacom_can_send

    def can_be_sent_parcels_census_any(self):
        other_can_send = super(WuaIrrigationConfiguration, self).\
            can_be_sent_parcels_census_any()
        # GET regacom config
        regacom_can_send = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'can_be_sent_parcels_census_regacom')
        return other_can_send or regacom_can_send

    def import_from_waterconnection_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_waterconnection_any()
        # GET regacom config
        regacom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_regacom')
        return other_can_import or regacom_can_impport

    def import_from_irrigationshed_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_irrigationshed_any()
        # GET regacom config
        regacom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_regacom')
        return other_can_import or regacom_can_impport

    def import_from_hydraulicsector_any(self):
        other_can_import = super(WuaIrrigationConfiguration, self).\
            import_from_hydraulicsector_any()
        # GET regacom config
        regacom_can_impport = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_regacom')
        return other_can_import or regacom_can_impport
