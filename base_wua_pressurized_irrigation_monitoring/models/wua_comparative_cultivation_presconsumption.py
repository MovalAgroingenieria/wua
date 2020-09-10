# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, tools


class WuaComparativeCultivationPresconsumption(models.Model):
    _name = 'wua.comparative.cultivation.presconsumption'
    _description = 'Comparative Cultivation Presconsumption'
    _auto = False
    _order = 'controlperiod_id, cultivation_id'

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
        index=True,
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation'
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

    consumption_category = fields.Selection([
        ('a', 'Correct irrigation'),
        ('b', 'Acceptable irrigation'),
        ('c', 'Unacceptable irrigation'),
        ],
        string='Consumption Category'
    )

    def init(self):
        tools.drop_view_if_exists(
            self.env.cr, 'wua_comparative_cultivation_presconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_comparative_cultivation_presconsumption
            AS (SELECT row_number() OVER () AS id, wcsp1.controlperiod_id,
            wcsp1.cultivation_id, SUM(wcsp1.estimated_consumption) AS
            estimated_consumption, SUM(wcsp1.real_consumption) AS
            real_consumption, SUM(wcsp1.deviation) AS deviation,
            CASE
             WHEN (
                    (SUM(wcsp1.real_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.real_consumption) >
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_02'
                     )
                    )
                ) THEN 'c'
             WHEN (
                    (SUM(wcsp1.real_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.real_consumption) >
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_01'
                     )
                    )
                ) THEN 'b'
             ELSE  'a'
            END AS consumption_category,
            wcsp1.agriculturalseason_id FROM
            wua_comparative_subparcel_presconsumption wcsp1 GROUP BY
            wcsp1.cultivation_id, wcsp1.controlperiod_id,
            wcsp1.agriculturalseason_id)
            """)
