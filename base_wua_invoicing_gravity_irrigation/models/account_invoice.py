# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ08 = fields.Monetary(
        string='C8: Grav. Cons.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ08 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 8))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ08

    # For report
    def _get_gravconsumptions_from_lines(self, invoice_lines):
        resp = []
        consumptions = []
        lines = []
        for invoice_line in invoice_lines:
            if invoice_line.categ_id.productcategory_code == 8:
                resp.append(invoice_line)
        if resp:
            for line in resp:
                irrigationgate_id = line.irrigationgate_id
                parcel_id = line.parcel_id
                invoiceset_id = line.invoiceset_id
                data_current_line = \
                    self.env['wua.gravconsumption'].search(
                        [('parcel_id', '=', parcel_id.id),
                         ('irrigationgate_id', '=', irrigationgate_id.id),
                         ('invoiceset_id', '=', invoiceset_id.id)])
                if data_current_line:
                    consumptions.extend(data_current_line)
        if consumptions:
            # Delete duplicates
            consumptions = set(consumptions)
            for consumption in consumptions:
                watering_initial_time = consumption.watering_initial_time
                watering_end_time = consumption.watering_end_time
                watering_duration_min = consumption.watering_duration
                watering_duration = float(watering_duration_min) / 60
                watering_volume_real = consumption.watering_volume_real
                item = {
                    'irrigationditch': consumption.irrigationditch_id.name,
                    'irrigationgate': consumption.irrigationgate_id.name,
                    'product': consumption.product_id.name,
                    'watering_initial_time': watering_initial_time,
                    'watering_end_time': watering_end_time,
                    'watering_duration': watering_duration,
                    'watering_volume_real': watering_volume_real,
                }
                lines.append(item)
        return lines
