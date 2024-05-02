# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaOctroi(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.octroi'
    _description = 'Entity (Octroi)'
    _order = 'name'

    _size_name = 100
    _size_description = 255
    _numeric_name = False

    name = fields.Char(
        string='Octroi',
    )

    intake_ids = fields.One2many(
        string='Intakes',
        comodel_name='wua.intake',
        inverse_name='octroi_id',
    )

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='octroi_id',
    )
