# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class WuaWatermeter(models.Model):
    _inherit = 'wua.watermeter'

    maximum_nominal_flow = fields.Float(
        string='Maximum nominal flow (l/s)',
        compute='_compute_maximum_nominal_flow',
        digits=(32, 4),
    )

    watermeter_module_ids = fields.One2many(
        string='Modules',
        comodel_name='wua.watermeter.module',
        inverse_name='watermeter_id',
    )

    @api.multi
    def _compute_maximum_nominal_flow(self):
        for record in self:
            maximum_nominal_flow = 0.0
            if (record.watermeter_module_ids):
                for module in record.watermeter_module_ids:
                    maximum_nominal_flow += module.module_flow
            record.maximum_nominal_flow = maximum_nominal_flow


class WuaWatermeterModule(models.Model):
    _name = 'wua.watermeter.module'
    _order = 'name'

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Watermeter position already exists.'),
    ]

    watermeter_id = fields.Many2one(
        string='Watermeter',
        comodel_name='wua.watermeter',
        required=True,
        ondelete='cascade',
    )

    position = fields.Integer(
        string='Position',
        default=1,
    )

    module_flow = fields.Float(
        string='Module Flow (l/s)',
        digits=(32, 4),
        required=True,
    )

    name = fields.Char(
        string='Identifier',
        compute='_compute_name',
        store=True,
    )

    @api.constrains('module_flow')
    def _check_module_multiple_of_five(self):
        for record in self:
            if int(round(record.module_flow)) % 5 != 0:
                raise ValidationError(
                    _('The module value must be a multiple of 5.'))

    @api.depends('position', 'watermeter_id', 'watermeter_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.position and record.watermeter_id and \
                    record.watermeter_id.name:
                name = str(record.position).zfill(2) + '-' + \
                    record.watermeter_id.name
            record.name = name
