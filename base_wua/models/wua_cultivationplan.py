# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaCultivationplan(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.cultivationplan'
    _description = 'Cultivation plans'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(string='Cultivation Plan')

    notes = fields.Html(string='Notes')
