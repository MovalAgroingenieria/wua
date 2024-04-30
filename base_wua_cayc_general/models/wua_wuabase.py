# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWuabase(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.wuabase'
    _description = 'Entity (Base Water User Association)'
    _order = 'name'

    _size_name = 3
    _size_description = 255
    _numeric_name = True

    name = fields.Char(
        string='Base Water User Association',
        readonly=True,
    )

    partner_ids = fields.One2many(
        string='Partners',
        comodel_name='res.partner',
        inverse_name='wuabase_id',
    )

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='wuabase_id',
    )

    parcel_class_ids = fields.One2many(
        string='Parcel Classes',
        comodel_name='wua.parcel.class',
        inverse_name='wuabase_id',
    )

    def name_get(self):
        result = []
        for record in self:
            display_name = u'[' + record.name + u'] ' + record.description
            result.append((record.id, display_name))
        return result
