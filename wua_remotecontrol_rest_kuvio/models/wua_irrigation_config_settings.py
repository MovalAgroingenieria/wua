# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    import_from_readings_kuvio = fields.Boolean(
        string='Import from readings (Kuvio)',
        help='If enabled, the Kuvio scheduled procedure will import '
             'readings for configured devices.',
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'import_from_readings_kuvio',
            self.import_from_readings_kuvio,
        )
        procedure = self.env.ref(
            'remotecontrol_kuvio.remotecontrol_kuvio_procedure_daily_sync',
            raise_if_not_found=False,
        )
        if procedure:
            procedure.write({'active': self.import_from_readings_kuvio})
            procedure.action_create_update_cron()

    def import_from_readings_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_readings_any()
        kuvio_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_readings_kuvio',
        )
        return other_can_import or kuvio_can_import
