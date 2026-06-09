# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class NRSTracking(models.Model):
    _inherit = "nrs.tracking"

    waterconnection_id = fields.Many2one(
        string='Waterconnection',
        store=True,
        index=True,
        comodel_name='wua.waterconnection',
        ondelete='restrict')
