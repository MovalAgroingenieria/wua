# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WauSMSTracking(models.Model):
    _inherit = "wausms.tracking"

    quota_id = fields.Many2one(
        string='Quota',
        store=True,
        index=True,
        comodel_name='wua.quota',
        ondelete='restrict')
