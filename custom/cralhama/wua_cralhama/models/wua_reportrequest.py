# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaReportrequest(models.Model):
    _inherit = 'wua.reportrequest'

    expected_amount = fields.Monetary(
        string='Amount',
        compute='_compute_expected_amount',
        help="Expected amount of irrigation report request.")

    @api.depends('product_id', 'currency_id', 'hours')
    def _compute_expected_amount(self):
        for record in self:
            expected_amount = 0
            if record.product_id and record.currency_id and record.hours:
                expected_amount = record.hours * record.product_id.lst_price
            record.expected_amount = expected_amount
