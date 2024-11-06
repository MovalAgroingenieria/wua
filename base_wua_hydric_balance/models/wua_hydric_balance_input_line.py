# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WuaHydricBalanceInputLine(models.Model):
    _name = 'wua.hydric.balance.input.line'
    _description = 'Hydric Balance Input Line'
    _order = 'end_time'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'The name must be unique.'),
    ]

    name = fields.Char(
        string='Code',
        unique=True,
        index=True,
    )
    hydric_balance_id = fields.Many2one(
        comodel_name='wua.hydric.balance',
        string='Balance',
        required=True,
        index=True,
        ondelete='cascade',
    )
    input_id = fields.Many2one(
        comodel_name='wua.hydric.balance.input',
        string='Input Element',
        required=True,
        index=True,
        ondelete='cascade',
    )
    initial_time = fields.Datetime(
        string='Start Time',
        index=True,
    )
    end_time = fields.Datetime(
        string='End Time',
        index=True,
    )
    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
    )
    input_line_selected = fields.Boolean(
        string='Selected Line',
    )
    intakeconsumption_id = fields.Many2one(
        comodel_name='wua.intakeconsumption',
        string='Intake Consumption',
        index=True,
        ondelete='restrict',
    )
    waterpipeconsumption_id = fields.Many2one(
        comodel_name='wua.waterpipeconsumption',
        string='Waterpipe Consumption',
        index=True,
        ondelete='restrict',
    )
    intake_id = fields.Many2one(
        comodel_name='wua.intake',
        string='Intake',
        index=True,
        ondelete='restrict',
    )
    waterpipe_id = fields.Many2one(
        comodel_name='wua.waterpipe',
        string='Waterpipe',
        index=True,
        ondelete='restrict',
    )

    flowmeter_id = fields.Many2one(
        comodel_name='wua.flowmeter',
        string='Flowmeter',
        ondelete='restrict',
    )

    @api.multi
    def add_to_input(self):
        if (len(self) > 0):
            if (self[0].hydric_balance_id.balance_state == '02_computed'):
                raise UserError(_("You cannot add to input because "
                                  " the hydric balance state is 'computed'."))
            vals = {
                'input_line_selected': True,
            }
            self.write(vals)

    @api.multi
    def remove_from_input(self):
        if (len(self) > 0):
            if (self[0].hydric_balance_id.balance_state == '02_computed'):
                raise UserError(_("You cannot remove from input because "
                                  "the hydric balance state is 'computed'."))
            vals = {
                'input_line_selected': False,
            }
            self.write(vals)
