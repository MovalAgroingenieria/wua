# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    sql_server_scada = fields.Char(
        string='SQL Server',
        size=255,
    )

    sql_port_scada = fields.Char(
        string='SQL Port',
        size=255,
    )

    sql_database_scada = fields.Char(
        string='SQL Database',
        size=255,
    )

    sql_uid_scada = fields.Char(
        string='SQL User ID',
        size=255,
    )

    sql_pwd_scada = fields.Char(
        string='SQL Password',
        size=255,
    )

    import_from_readings_scada = fields.Boolean(
        string='Import readings (SCADA SQL)',
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'sql_server_scada',
            self.sql_server_scada,
        )
        values.set_default(
            'wua.irrigation.configuration',
            'sql_port_scada',
            self.sql_port_scada,
        )
        values.set_default(
            'wua.irrigation.configuration',
            'sql_database_scada',
            self.sql_database_scada,
        )
        values.set_default(
            'wua.irrigation.configuration',
            'sql_uid_scada',
            self.sql_uid_scada,
        )
        values.set_default(
            'wua.irrigation.configuration',
            'sql_pwd_scada',
            self.sql_pwd_scada,
        )
        values.set_default(
            'wua.irrigation.configuration',
            'import_from_readings_scada',
            self.import_from_readings_scada,
        )

    def import_from_readings_any(self):
        other_can_import = super(
            WuaIrrigationConfiguration, self).import_from_readings_any()
        scada_can_import = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_readings_scada',
        )
        return other_can_import or scada_can_import
