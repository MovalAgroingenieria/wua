# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ12 = fields.Monetary(
        string='C12: Fert. Cons.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ12 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 12))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ12

    # For report.
    def _get_fertconsumptions_from_lines(self, invoice_lines):
        lines = []
        waterconnections_ids = []
        for invoice_line in invoice_lines:
            if (invoice_line.categ_id.productcategory_code == 12 and
               invoice_line.waterconnection_id):
                waterconnections_ids.append(invoice_line.waterconnection_id.id)
        if waterconnections_ids:
            invoiceset_id = invoice_lines[0].invoiceset_id.id
            waterconnections_ids = list(set(waterconnections_ids))
            consumptions = []
            for waterconnection_id in waterconnections_ids:
                consumptions_of_current_wc = \
                    self.env['wua.fertconsumption'].search(
                        [('waterconnection_id', '=', waterconnection_id),
                         ('invoiceset_id', '=', invoiceset_id)],
                        order='reading_end_time')
                if consumptions_of_current_wc:
                    consumptions.extend(consumptions_of_current_wc)
            for consumption in consumptions:
                item = {
                    'waterconnection': consumption.waterconnection_id.name,
                    'reading_initial_time': consumption.reading_initial_time,
                    'reading_end_time': consumption.reading_end_time,
                    'amount': consumption.volume,
                    }
                lines.append(item)
        return lines

    def _is_invoicing_based_on_wc(self):
        return (self.env['ir.values'].get_default(
           'wua.invoicing.configuration', 'invoicing_based_on_wc'))
