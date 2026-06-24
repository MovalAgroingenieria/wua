# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    def import_from_readings_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_readings_any()
        mula_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_readings_scada_mula',
        )
        return other_can_import or mula_can_import

    def import_from_waterconnection_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_waterconnection_any()
        mula_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterconnection_scada_mula',
        )
        return other_can_import or mula_can_import

    def import_from_irrigationshed_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_irrigationshed_any()
        mula_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_irrigationshed_scada_mula',
        )
        return other_can_import or mula_can_import

    def import_from_hydraulicsector_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration,
            self).import_from_hydraulicsector_any()
        mula_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_hydraulicsector_scada_mula',
        )
        return other_can_import or mula_can_import
