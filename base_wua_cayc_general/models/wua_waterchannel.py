# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterchannel(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.waterchannel'
    _description = 'Entity (waterchannel)'
    _order = 'name'

    _size_name = 100
    _size_description = 255
    _numeric_name = False

    name = fields.Char(
        string='Waterchannel',
    )

    intake_ids = fields.One2many(
        string='Intakes',
        comodel_name='wua.intake',
        inverse_name='waterchannel_id',
    )

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='waterchannel_id',
    )
