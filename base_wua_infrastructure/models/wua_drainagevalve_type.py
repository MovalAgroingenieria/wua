# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaDrainagevalveType(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.drainagevalve.type'
    _description = 'Entity (Drainagevalve Type)'
    _order = 'name'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Drainagevalve Type',
    )

    notes = fields.Html(
        string='Notes',
    )

    drainagevalve_ids = fields.One2many(
        string='Drainagevalves',
        comodel_name='wua.drainagevalve',
        inverse_name='type_id',
    )
