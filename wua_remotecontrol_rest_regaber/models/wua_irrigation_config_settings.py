# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pickle

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    url_remotecontrol_application_regaber = fields.Char(
        string='Application URL',
        size=255,
        help='URL of the Regaber SKYplatform web application.',
    )

    import_from_readings_regaber = fields.Boolean(
        string='Import from readings (Regaber)',
        help='If enabled, counter readings are imported from the Regaber '
             'SKYplatform when running the reading import.',
    )

    import_from_pressuresensormeasurement_regaber = fields.Boolean(
        string='Import pressure measurements (Regaber)',
        help='If enabled, pressure measurements are imported from Regaber '
             'SKYplatform when running the pressure measurement import.',
    )

    import_from_waterconnection_regaber = fields.Boolean(
        string='Import from waterconnection (Regaber)',
    )

    import_from_irrigationshed_regaber = fields.Boolean(
        string='Import from irrigationshed (Regaber)',
    )

    import_from_hydraulicsector_regaber = fields.Boolean(
        string='Import from hydraulic sector (Regaber)',
    )

    regaber_default_hydraulicsector_id = fields.Many2one(
        string='Default Hydraulic Sector (Regaber imports)',
        comodel_name='wua.hydraulicsector',
        help='Hydraulic sector used to create irrigation sheds when importing '
             'water connections from Regaber.',
    )

    def _get_regaber_pressure_import_enabled(self):
        defaults = self.env['ir.values'].search([
            ('key', '=', 'default'),
            ('key2', '=', False),
            ('model', '=', 'wua.irrigation.configuration'),
            ('name', '=', 'import_from_pressuresensormeasurement_regaber'),
            ('user_id', '=', False),
            ('company_id', '=', False),
        ], order='id desc', limit=1)
        enabled = False
        if defaults:
            enabled = pickle.loads(defaults.value.encode('utf-8'))
        return enabled

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_regaber',
            self.url_remotecontrol_application_regaber)
        values.set_default(
            'wua.irrigation.configuration',
            'import_from_pressuresensormeasurement_regaber',
            self.import_from_pressuresensormeasurement_regaber)
        values.set_default(
            'wua.irrigation.configuration',
            'regaber_default_hydraulicsector_id',
            self.regaber_default_hydraulicsector_id.id)

    def import_from_readings_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_readings_any()
        regaber_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_regaber')
        return other_can_import or regaber_can_import

    def import_from_waterconnection_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_waterconnection_any()
        regaber_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_regaber')
        return other_can_import or regaber_can_import

    def import_from_irrigationshed_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_irrigationshed_any()
        regaber_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_regaber')
        return other_can_import or regaber_can_import

    def import_from_hydraulicsector_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration,
            self).import_from_hydraulicsector_any()
        regaber_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_regaber')
        return other_can_import or regaber_can_import

    def import_from_pressuresensor_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration,
            self).import_from_pressuresensor_any()
        regaber_can_import = self._get_regaber_pressure_import_enabled()
        return other_can_import or regaber_can_import
