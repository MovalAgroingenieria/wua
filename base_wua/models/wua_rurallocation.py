# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaRurallocation(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.rurallocation'
    _description = 'Rural locations'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(string='Rural Location')

    notes = fields.Html(string="Notes")
