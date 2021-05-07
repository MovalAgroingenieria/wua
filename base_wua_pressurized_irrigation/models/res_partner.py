# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions, _, tools


class ResPartnerWaterconnection(models.Model):
    _inherit = 'res.partner.waterconnection'

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='res_partner_waterconnection')
            """)
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(self.env.cr,
                                      'res_partner_waterconnection')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                CREATE OR REPLACE VIEW res_partner_waterconnection AS (
                SELECT row_number() OVER() AS id, a.* FROM (
                    SELECT wpp1.partner_id, wpi1.waterconnection_id
                    FROM
                    wua_parcel_irrigationpoint wpi1 INNER JOIN
                    wua_waterconnection ww1 ON ww1.id = wpi1.waterconnection_id
                    INNER JOIN wua_parcel_partnerlink wpp1 ON wpp1.parcel_id =
                    wpi1.parcel_id WHERE wpi1.type='WC' AND ww1.watermeter_id
                    IS NOT NULL
                    GROUP BY  wpp1.partner_id, wpi1.waterconnection_id
                ) a )
                """)
        except Exception:
            self.env.cr.rollback()
