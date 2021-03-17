# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, tools


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tools.drop_view_if_exists(env.cr, 'res_partner_waterconnection')
    env.cr.execute("""
        CREATE OR REPLACE VIEW res_partner_waterconnection AS (
        SELECT row_number() OVER() AS id, a.* FROM (
            SELECT wpi1.partner_id, wpi1.waterconnection_id,
            ww1.last_data_time, ww1.last_total_volume, ww1.last_waterflow,
            ww1.last_valve_open, ww1.last_valve_scheduled FROM
            wua_parcel_irrigationpoint wpi1 INNER JOIN
            wua_waterconnection ww1 ON ww1.id = wpi1.waterconnection_id
            WHERE wpi1.type='WC' GROUP BY  wpi1.partner_id,
            wpi1.waterconnection_id, ww1.last_data_time,
            ww1.last_waterflow, ww1.last_valve_open,
            ww1.last_valve_scheduled, ww1.last_total_volume
        ) a )
        """)
