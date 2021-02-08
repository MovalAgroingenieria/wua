# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    partner_with_separate_billing_id = fields.Many2one(
        string='Partner With Separate Billing',
        comodel_name='res.partner',
        index=True,
        readonly=True,
        ondelete='restrict')
