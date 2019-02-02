# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ07 = fields.Monetary(
        string='C7: Press. Cons.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

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
        # Provisional
        # waterconnections_ids.append(10)
        if waterconnections_ids:
            waterconnections_ids = list(set(waterconnections_ids))
            consumptions = []
            for waterconnection_id in waterconnections_ids:
                consumptions_of_current_wc = \
                    self.env['wua.presconsumption'].search(
                        [('waterconnection_id', '=', waterconnection_id)],
                        order='reading_end_time')
                if consumptions_of_current_wc:
                    consumptions.extend(consumptions_of_current_wc)
            for consumption in consumptions:
                item = {
                    'waterconnection': consumption.waterconnection_id.name,
                    'watermeter': consumption.watermeter_id.name,
                    'reading_initial_time': consumption.reading_initial_time,
                    'initial_volume': '{:.3f}'.format(
                        consumption.initial_volume),
                    'reading_end_time': consumption.reading_end_time,
                    'end_volume': '{:.3f}'.format(
                        consumption.end_volume),
                    'volume': '{:.3f}'.format(
                        consumption.volume),
                    'adjustement_volume': '{:.3f}'.format(
                        consumption.adjustement_volume),
                    'volume_real': '{:.3f}'.format(
                        consumption.volume_real),
                    }
                lines.append(item)
        return lines
