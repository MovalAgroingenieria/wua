# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from odoo.fields import Many2one


class WuaCultivation(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.cultivation'
    _description = 'Cultivations'

    _size_name = 40
    _size_description = 75
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Cultivation',
        translate=True)

    variety_ids = fields.One2many(
        string='Varieties',
        comodel_name='wua.cultivation.variety',
        inverse_name='cultivation_id')

    number_of_varieties = fields.Integer(
        string='Number of varieties',
        compute='_compute_number_of_varieties')

    notes = fields.Html(string='Notes')

    @api.multi
    def _compute_number_of_varieties(self):
        for record in self:
            record.number_of_varieties = len(record.variety_ids)


class WuaCultivationVariety(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.cultivation.variety'
    _description = 'Cultivation Varieties'

    _size_name = 40
    _size_description = 75
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Variety',
        translate=True)

    cultivation_id = Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        required=True,
        ondelete='restrict')
