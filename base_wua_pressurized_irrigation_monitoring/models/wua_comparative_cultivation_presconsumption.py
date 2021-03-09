# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, tools, api


class WuaComparativeCultivationPresconsumption(models.Model):
    _name = 'wua.comparative.cultivation.presconsumption'
    _description = 'Comparative Cultivation Presconsumption'
    _auto = False
    _order = 'controlperiod_id, cultivation_id'

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation'
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
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

    deviation_percentage = fields.Char(
        string='Deviation Percentage',
        compute='_compute_deviation_percentage',
    )

    deviation_percentage_num = fields.Float(
        string='% Deviation',
        digits=(32, 2),
        compute='_compute_deviation_percentage_num',
    )

    consumption_category = fields.Selection([
        ('A', 'A (correct irrigation)'),
        ('B', 'B (acceptable irrigation)'),
        ('C', 'C (unsatisfactory irrigation)'),
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
                     SUM(wcsp1.real_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_01'
                     )
                    )
                ) THEN 'A'
             WHEN (
                    (SUM(wcsp1.real_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.real_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_02'
                     )
                    )
                ) THEN 'B'
             ELSE  'C'
            END AS consumption_category,
            wcsp1.agriculturalseason_id FROM
            wua_comparative_subparcel_presconsumption wcsp1 GROUP BY
            wcsp1.agriculturalseason_id, wcsp1.controlperiod_id,
            wcsp1.cultivation_id)
            """)

    @api.multi
    def _compute_deviation_percentage(self):
        for record in self:
            if (record.estimated_consumption == 0 and
               record.real_consumption == 0):
                record.deviation_percentage = '0%'
            else:
                deviation_percentage = 100
                is_negative = False
                deviation = record.deviation
                if deviation < 0:
                    deviation = abs(deviation)
                    is_negative = True
                if deviation > 0 and record.real_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.real_consumption
                if is_negative:
                    deviation_percentage = deviation_percentage * -1
                record.deviation_percentage = \
                    '{:.2f}'.format(deviation_percentage) + '%'

    @api.multi
    def _compute_deviation_percentage_num(self):
        for record in self:
            deviation_percentage_num = 0
            if (record.estimated_consumption > 0 or
               record.real_consumption > 0):
                deviation_percentage_num = 100
                deviation = abs(record.deviation)
                if deviation > 0 and record.real_consumption > 0:
                    deviation_percentage_num = \
                        (deviation * 100) / record.real_consumption
                    if deviation_percentage_num > 100:
                        deviation_percentage_num = 100
            record.deviation_percentage_num = deviation_percentage_num
