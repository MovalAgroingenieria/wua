# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class NRSTracking(models.Model):
    _inherit = "nrs.tracking"
    _description = "Tracking of SMS sent"

    parcel_id = fields.Many2one(
        string='Parcel',
        store=True,
        index=True,
        readoly=True,
        comodel_name='wua.parcel')
