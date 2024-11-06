# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WuaHydricBalanceVariationLine(models.Model):
    _name = 'wua.hydric.balance.variation.line'
    _description = 'Hydric Balance Variation Line'
    _order = 'variation_time'
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
    variation_id = fields.Many2one(
        comodel_name='wua.hydric.balance.variation',
        string='Variation Element',
        required=True,
        index=True,
        ondelete='cascade',
    )
    variation_time = fields.Datetime(
        string='Time',
        index=True,
    )
    variation_volume = fields.Float(
        string='Variation (m³)',
        digits=(32, 4),
    )
    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
    )
    variation_line_selected = fields.Boolean(
        string='Selected Line',
    )
    reservoirreading_id = fields.Many2one(
        comodel_name='wua.reservoirreading',
        string='Reservoir Reading',
        index=True,
        ondelete='restrict',
    )

    reservoir_id = fields.Many2one(
        comodel_name='wua.reservoir',
        string='Reservoir',
        index=True,
        ondelete='restrict',
    )

    @api.multi
    def add_to_variation(self):
        if (len(self) > 0):
            if (self[0].hydric_balance_id.balance_state == '02_computed'):
                raise UserError(_("You cannot add to variation because "
                                  "the hydric balance state is 'computed'."))
            vals = {
                'variation_line_selected': True,
            }
            self.write(vals)

    @api.multi
    def remove_from_variation(self):
        if (len(self) > 0):
            if (self[0].hydric_balance_id.balance_state == '02_computed'):
                raise UserError(_("You cannot remove from variation because"
                                  "the hydric balance state is 'computed'."))
            vals = {
                'variation_line_selected': False,
            }
            self.write(vals)
