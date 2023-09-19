# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFilteringstationType(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.filteringstation.type'
    _description = 'Entity (Filteringstation Type)'
    _order = 'name'

    _size_name = 50
    _size_description = 100
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(
        string='Filteringstation Type',
    )

    notes = fields.Html(
        string='Notes',
    )

    filteringstation_ids = fields.One2many(
        string='Filteringstations',
        comodel_name='wua.filteringstation',
        inverse_name='type_id',
    )
