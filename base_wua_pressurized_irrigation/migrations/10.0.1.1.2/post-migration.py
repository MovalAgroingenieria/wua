# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, tools


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tools.drop_view_if_exists(env.cr, 'res_partner_waterconnection')
    env.cr.execute("""
        CREATE OR REPLACE VIEW res_partner_waterconnection AS (
        SELECT row_number() OVER() AS id, a.* FROM (
            SELECT wpp1.partner_id, wpi1.waterconnection_id,
            wpi1.active,
            ww1.last_reading_time, ww1.last_reading_value,
            wpc1.volume_real
            FROM
            wua_parcel_irrigationpoint wpi1
            INNER JOIN  wua_waterconnection ww1
            ON ww1.id = wpi1.waterconnection_id
            INNER JOIN wua_parcel_partnerlink wpp1
            ON wpp1.parcel_id = wpi1.parcel_id
            LEFT JOIN wua_presconsumption wpc1
            ON wpc1.waterconnection_id = ww1.id
            AND wpc1.reading_end_time = ww1.last_reading_time
            WHERE wpi1.type='WC' AND ww1.watermeter_id IS NOT NULL
            GROUP BY  wpp1.partner_id, wpi1.waterconnection_id,
            wpi1.active,
            ww1.last_reading_time, ww1.last_reading_value,
            wpc1.volume_real
        ) a )
        """)
