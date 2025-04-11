# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ07 = fields.Monetary(
        string='C7: Press. Cons.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount',
    )

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ07 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 7))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ07

    # For report.
    def _get_presconsumptions_from_lines(self, invoice_lines):
        lines = []
        waterconnections_ids = []
        for invoice_line in invoice_lines:
            if (invoice_line.categ_id.productcategory_code == 7 and
               invoice_line.waterconnection_id):
                waterconnections_ids.append(invoice_line.waterconnection_id.id)
        if waterconnections_ids:
            invoiceset_id = invoice_lines[0].invoiceset_id.id
            waterconnections_ids = list(set(waterconnections_ids))
            consumptions = []
            for waterconnection_id in waterconnections_ids:
                consumptions_of_current_wc = \
                    self.env['wua.presconsumption'].search(
                        [('waterconnection_id', '=', waterconnection_id),
                         ('invoiceset_id', '=', invoiceset_id)],
                        order='reading_end_time')
                if consumptions_of_current_wc:
                    consumptions.extend(consumptions_of_current_wc)
            for consumption in consumptions:
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

    def _get_grouped_wc_description_for_report(
            self, waterconnection_id, quantity):
        formatted_qty = self.env['wua.parcel'].transform_float_to_locale(
            quantity, 4,
        )
        return _(u'Water Connection %s; Total Consumption: %s m³') % (
            waterconnection_id.name, formatted_qty)

    def _is_invoicing_based_on_wc(self):
        return (self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'invoicing_based_on_wc'))

    def _must_group_wc_lines_on_report(self):
        return (self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'group_wc_lines_on_report'))
