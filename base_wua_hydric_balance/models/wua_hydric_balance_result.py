# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaHydricBalanceResult(models.Model):
    _name = 'wua.hydric.balance.result'
    _description = 'Hydric Balance Result'
    _order = 'element_name'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
    ]

    TYPES_DICT = {
        '01_input': 'Input',
        '02_output': 'Output',
        '03_variation': 'Variation',
    }

    name = fields.Char(
        string='Code',
        unique=True,
        index=True,
        compute='_compute_name',
        store=True,
    )
    hydric_balance_id = fields.Many2one(
        comodel_name='wua.hydric.balance',
        string='Balance',
        required=True,
        index=True,
        ondelete='cascade',
    )
    element_name = fields.Char(
        string='Associated Element',
        index=True,
    )
    result_type = fields.Selection(
        [
            ('01_input', 'Input'),
            ('02_output', 'Output'),
            ('03_variation', 'Variation'),
        ],
        string='Element Type',
        index=True,
    )
    output_type = fields.Selection(
        [
            ('01_presconsumption', 'Pressure Consumption'),
            ('02_gravsconsumption', 'Gravity Consumption'),
            ('03_irrigationreport', 'Irrigation Report'),
            ('04_flowmeter_consumption', 'Flowmeter'),
        ],
        string='Output Type',
        index=True,
    )
    input_type = fields.Selection(
        [('01_flowmeter_consumption', 'Flowmeter Consumption')],
        string='Input Type',
        index=True,
    )
    variation_type = fields.Selection(
        [('01_reservoir_reading', 'Reservoir Reading')],
        string='Variation Type',
        index=True,
    )
    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
    )
    initial_volume = fields.Float(
        string='Initial Volume (m³)',
        digits=(32, 4),
    )
    end_volume = fields.Float(
        string='Final Volume (m³)',
        digits=(32, 4),
    )
    reservoir_id = fields.Many2one(
        comodel_name='wua.reservoir',
        string='Reservoir',
        index=True,
        ondelete='restrict',
    )
    waterconnection_id = fields.Many2one(
        comodel_name='wua.waterconnection',
        string='Waterconnection',
        index=True,
        ondelete='restrict',
    )
    intake_id = fields.Many2one(
        comodel_name='wua.intake',
        string='Intake',
        index=True,
        ondelete='restrict',
    )
    flowmeter_id = fields.Many2one(
        comodel_name='wua.flowmeter',
        string='Flowmeter',
        index=True,
        ondelete='restrict',
    )
    irrigationditch_id = fields.Many2one(
        comodel_name='wua.irrigationditch',
        string='Irrigation Ditch',
        index=True,
        ondelete='restrict',
    )

    @api.depends('hydric_balance_id.name', 'result_type')
    def _compute_name(self):
        for record in self:
            result_element = self.TYPES_DICT.get(record.result_type)
            if result_element:
                if record.input_type:
                    record.name = u"{}-{}-{}-{}".format(
                        record.hydric_balance_id.name,
                        record.result_type,
                        record.input_type,
                        record.element_name,
                    ).encode('utf-8')
                if record.output_type:
                    record.name = u"{}-{}-{}-{}".format(
                        record.hydric_balance_id.name,
                        record.result_type,
                        record.output_type,
                        record.element_name,
                    ).encode('utf-8')
                if record.variation_type:
                    record.name = u"{}-{}-{}-{}".format(
                        record.hydric_balance_id.name,
                        record.result_type,
                        record.variation_type,
                        record.element_name,
                    ).encode('utf-8')
