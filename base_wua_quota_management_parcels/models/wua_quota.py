# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='quota_id')
