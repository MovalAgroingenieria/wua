# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaParceltag(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.parceltag'
    _description = 'Tags for parcels'

    _size_name = 25
    _size_description = 75
    _numeric_name = False
    _lowercase_name = True
    _uppercase_name = False

    name = fields.Char(string='Parcel Tag')

    color = fields.Integer(
        string='Color Index',
        help='0:grey, 1:green, 2:yellow, ' +
        '3:orange, 4:red, 5:purple, 6:blue, ' +
        '7:cyan, 8:light-green, 9:magenta')

    notes = fields.Html(string="Notes")
