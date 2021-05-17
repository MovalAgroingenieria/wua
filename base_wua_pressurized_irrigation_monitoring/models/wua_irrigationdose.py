# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationdose(models.Model):
    _name = 'wua.irrigationdose'
    _order = 'name'

    MAX_SIZE_NAME = 85

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        required=True,
        index=True,
        ondelete='restrict',)

    soiltype_id = fields.Many2one(
        comodel_name='wua.soiltype',
        string='Soil Type',
        index=True,
        required=True)

    minimum_irrigation_dose = fields.Float(
        string='Minimun Irrigation Dose (mm)',
        digits=(32, 4),
        required=True,
        default=0)

    age_category = fields.Selection([
        ('l', 'Little'),
        ('m', 'Middle'),
        ('b', 'Full Production'),
        ],
        string='Age Category',
        required=True,
    )

    name = fields.Char(
        string='Identifier of minimun irrigation dose',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Irrigationdose.'),
        ('valid_minimum_irrigation_dose',
         'CHECK (minimum_irrigation_dose >= 0)',
         'The Minimun Irrigation Dose must be '
         'a value zero or positive.'),
        ]

    @api.depends('cultivation_id', 'cultivation_id.name',
                 'soiltype_id', 'soiltype_id.name',
                 'age_category')
    def _compute_name(self):
        for record in self:
            record.name = str(record.cultivation_id.name) + ' - ' + \
                str(record.soiltype_id.name) + ' - ' + record.age_category
