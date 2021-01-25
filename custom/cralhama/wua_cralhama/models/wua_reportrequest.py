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

    reportrequest_number = fields.Char(
        string='Request Number',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'wua.cralhama.reportrequest.seq'))

    extra_amount = fields.Monetary(
        string='Extra amount',
        default=0,
        help="Positive or negative extra amount for irrigation report "
            "request.")

    final_expected_amount = fields.Monetary(
        string='Final amount',
        store=True,
        compute='_compute_final_expected_amount',
        help="Final expected amount of irrigation report request.")

    _sql_constraints = [
        ('unique_reportrequest_number', 'UNIQUE (reportrequest_number)',
         'Existing request number.')]

    @api.depends('product_id', 'currency_id', 'hours')
    def _compute_expected_amount(self):
        for record in self:
            expected_amount = 0
            if record.product_id and record.currency_id and record.hours:
                if record.product_id.taxes_id and \
                        record.product_id.taxes_id.amount > 0:
                    total_amount = record.hours * record.product_id.lst_price
                    taxes = total_amount * \
                        (record.product_id.taxes_id.amount / 100)
                    expected_amount = total_amount + taxes
                else:
                    expected_amount = \
                        record.hours * record.product_id.lst_price
            record.expected_amount = expected_amount

    @api.depends('expected_amount', 'extra_amount')
    def _compute_final_expected_amount(self):
        for record in self:
            record.final_expected_amount = \
                record.expected_amount + record.extra_amount
