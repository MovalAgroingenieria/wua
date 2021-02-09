# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
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
                    # Round var hours before calculation (invoiceset behavior)
                    hours = round(record.hours, 2)
                    total_amount = hours * record.product_id.lst_price
                    taxes = total_amount * \
                        (record.product_id.taxes_id.amount / 100)
                    expected_amount = total_amount + taxes
                else:
                    # Round var hours before calculation (invoiceset behavior)
                    hours = round(record.hours, 2)
                    expected_amount = \
                        hours * record.product_id.lst_price
            record.expected_amount = expected_amount

    @api.depends('expected_amount', 'extra_amount')
    def _compute_final_expected_amount(self):
        for record in self:
            record.final_expected_amount = \
                record.expected_amount + record.extra_amount

    @api.multi
    def name_get(self):
        if self.env.context.get('show_reportrequest_number', False):
            result = []
            for record in self:
                name = ''
                if (record.request_date and record.partner_id and
                    record.product_id and record.reportrequest_number):
                    reportrequest_number = str(record.reportrequest_number)
                    request_date_str = datetime.datetime.strptime(
                        record.request_date, '%Y-%m-%d').strftime('%x')
                    language = record.partner_id.lang
                    product = \
                        record.with_context({'lang': language}).product_id.name
                    name = reportrequest_number + ' - ' + request_date_str + \
                        ' - ' + product
                result.append((record.id, name))
        else:
            result = super(WuaReportrequest, self).name_get()
        return result
