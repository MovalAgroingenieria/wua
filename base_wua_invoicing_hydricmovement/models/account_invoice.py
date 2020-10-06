# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ14 = fields.Monetary(
        string='C14: Hydricmovements',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ14 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 14))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ14

    # Report method
    def get_hydricmov_presconsumptions_from_lines(self, invoice_lines):
        lines = []
        pres_consumption_ids = []
        for invoice_line in invoice_lines:
            if invoice_line.categ_id.productcategory_code == 14 and \
                    invoice_line.presconsumption_id and \
                    invoice_line.hydricmovement_id.type == 'pres_consumption':
                pres_consumption_ids.append(invoice_line.presconsumption_id.id)

        if pres_consumption_ids:
            pres_consumption_ids = list(set(pres_consumption_ids))
            pres_consumptions = \
                self.env['wua.presconsumption'].browse(pres_consumption_ids)
            for consumption in pres_consumptions:
                item = {
                    'waterconnection': consumption.waterconnection_id.name,
                    'watermeter': consumption.watermeter_id.name,
                    'reading_initial_time': consumption.reading_initial_time,
                    'initial_volume': consumption.initial_volume,
                    'reading_end_time': consumption.reading_end_time,
                    'end_volume': consumption.end_volume,
                    'volume': consumption.volume,
                    'adjustement_volume': consumption.adjustement_volume,
                    'volume_real': consumption.volume_real,
                    }
                lines.append(item)
        return lines

#         lines = []
#         waterconnections_ids = []
#         for invoice_line in invoice_lines:
#             if (invoice_line.categ_id.productcategory_code == 14 and
#                invoice_line.waterconnection_id):
#                 waterconnections_ids.append(invoice_line.waterconnection_id.id)
#         if waterconnections_ids:
#             invoiceset_id = invoice_lines[0].invoiceset_id.id
#             waterconnections_ids = list(set(waterconnections_ids))
#             consumptions = []
#             for waterconnection_id in waterconnections_ids:
#                 consumptions_of_current_wc = \
#                     self.env['wua.presconsumption'].search(
#                         [('waterconnection_id', '=', waterconnection_id),
#                          ('invoiceset_id', '=', invoiceset_id)],
#                         order='reading_end_time')
#                 if consumptions_of_current_wc:
#                     consumptions.extend(consumptions_of_current_wc)
#             for consumption in consumptions:
#                 item = {
#                     'waterconnection': consumption.waterconnection_id.name,
#                     'watermeter': consumption.watermeter_id.name,
#                     'reading_initial_time': consumption.reading_initial_time,
#                     'initial_volume': consumption.initial_volume,
#                     'reading_end_time': consumption.reading_end_time,
#                     'end_volume': consumption.end_volume,
#                     'volume': consumption.volume,
#                     'adjustement_volume': consumption.adjustement_volume,
#                     'volume_real': consumption.volume_real,
#                     }
#                 lines.append(item)
#         return lines



class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    hydricmovement_id = fields.Many2one(
        string='Hydric movement',
        comodel_name='wua.hydricmovement',
        index=True,
        ondelete='restrict')

    presconsumption_id = fields.Many2one(
        string='Pres. Consumption',
        comodel_name='wua.presconsumption',
        index=True,
        ondelete='restrict')
