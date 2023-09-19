# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaAirvalveType(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.airvalve.type'
    _description = 'Entity (Airvalve Type)'
    _order = 'name'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Airvalve Type',
    )

    notes = fields.Html(
        string='Notes',
    )

    airvalve_ids = fields.One2many(
        string='Airvalves',
        comodel_name='wua.airvalve',
        inverse_name='type_id',
    )
