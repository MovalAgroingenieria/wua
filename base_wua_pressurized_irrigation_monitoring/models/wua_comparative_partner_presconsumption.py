# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, tools


class WuaComparativePartnerPresconsumption(models.Model):
    _name = 'wua.comparative.partner.presconsumption'
    _description = 'Comparative Partner Presconsumption'
    _auto = False
    _order = 'controlperiod_id'

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
        index=True,
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4)
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4)
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4)
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4)
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_comparative_partner_presconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_comparative_partner_presconsumption AS (
            SELECT row_number() OVER () AS id, wcsp1.controlperiod_id,
            wcsp1.partner_id, SUM(wcsp1.estimated_consumption) AS
            estimated_consumption, SUM(wcsp1.real_consumption) AS
            real_consumption, SUM(wcsp1.deviation) AS deviation,
            SUM(wcsp1.area_official) AS area_official,
            wcsp1.agriculturalseason_id FROM
            wua_comparative_subparcel_presconsumption wcsp1 INNER JOIN
            res_partner rp1 ON rp1.id = wcsp1.partner_id GROUP BY
            wcsp1.partner_id, wcsp1.controlperiod_id,
            wcsp1.agriculturalseason_id)
            """)
