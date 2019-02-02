# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFarmproperty(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.farmproperty'
    _description = 'Farm Properties'

    _size_name = 40
    _size_description = 75
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(string='Farm Property')

    notes = fields.Html(string="Notes")
