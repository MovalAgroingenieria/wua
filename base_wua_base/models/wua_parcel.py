# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    mapped = fields.Boolean(
        string="Mapped",
        default=False,
        readonly=True,
        help="Indicates if this parcel has been mapped with general instance.",
    )

    last_update = fields.Datetime(
        default=False,
        readonly=True,
        help="Date of the last update from with general instance.",
    )
