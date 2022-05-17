# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='partner_id')
