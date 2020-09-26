# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCultivationKc(models.Model):
    _name = 'wua.cultivation.kc'
    _description = 'Kc of cultivations'
    _order = 'cultivation_id, period_number'

    MAX_SIZE_NAME = 43

    period_number = fields.Integer(
        string='Period Number',
        required=True,
        index=True,
        default=1
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        required=True,
        index=True,
        ondelete='restrict')

    name = fields.Char(
        string='Kc',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    kc_little = fields.Float(
        string='Kc for little cultivations',
        digits=(32, 3),
        required=True,
        default=0)

    kc_middle = fields.Float(
        string='Kc for middle cultivations',
        digits=(32, 3),
        required=True,
        default=0)

    kc_big = fields.Float(
        string='Kc for big cultivations',
        digits=(32, 3),
        required=True,
        default=0)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_period_number',
         'CHECK (period_number > 0)',
         'The period number must be a value zero or positive.'),
        ('valid_kc_little',
         'CHECK (kc_little >= 0)',
         'The \"kc for little cultivations\" must be '
         'a value zero or positive.'),
        ('valid_kc_middle',
         'CHECK (kc_middle >= 0)',
         'The \"kc for middle cultivations\" must be '
         'a value zero or positive.'),
        ('valid_kc_big',
         'CHECK (kc_big >= 0)',
         'The \"kc for big cultivations\" must be '
         'a value zero or positive.'),
        ]

    @api.depends('period_number', 'cultivation_id', 'cultivation_id.name')
    def _compute_name(self):
        for record in self:
            record.name = str(record.period_number).zfill(2) + '-' + \
                record.cultivation_id.name

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = str(record.period_number) + ' - ' + \
                record.cultivation_id.name
            result.append((record.id, name))
        return result
