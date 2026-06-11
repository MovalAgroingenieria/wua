# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    waterconnections = env['wua.waterconnection'].sudo().search([
        ('telecontrol_associated', '=', 'spherag'),
        ('spherag_data', '!=', False),
    ])

    for waterconnection in waterconnections:
        if (waterconnection.spherag_system_id and
                waterconnection.spherag_imei and
                waterconnection.spherag_flow_accumulated_chart_type_id):
            continue

        try:
            spherag_data = json.loads(waterconnection.spherag_data or '{}')
        except Exception:
            continue

        vals = {}

        if not waterconnection.spherag_system_id:
            system_id = spherag_data.get('system_id')
            try:
                vals['spherag_system_id'] = int(system_id)
            except (TypeError, ValueError):
                pass

        if not waterconnection.spherag_imei:
            imei = spherag_data.get('imei')
            if imei:
                vals['spherag_imei'] = str(imei)

        if not waterconnection.spherag_flow_accumulated_chart_type_id:
            chart_type_id = spherag_data.get(
                'flow_accumulated_chart_type_id')
            try:
                vals['spherag_flow_accumulated_chart_type_id'] = int(
                    chart_type_id)
            except (TypeError, ValueError):
                pass

        if vals:
            waterconnection.write(vals)
