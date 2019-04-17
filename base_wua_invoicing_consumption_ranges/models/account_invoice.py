# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _get_presconsumptions_from_lines(self, invoice_lines):
        lines = []
        waterconnections_ids = []
        for invoice_line in invoice_lines:
            if (invoice_line.categ_id.productcategory_code == 7 and
               invoice_line.waterconnection_ids_str and
               len(invoice_line.waterconnection_ids_str) > 0):
                waterconnections_ids = \
                    invoice_line.waterconnection_ids_str.split(',')
        if waterconnections_ids:
            waterconnections_ids = list(set(map(int, waterconnections_ids)))
            invoiceset_id = invoice_lines[0].invoiceset_id.id
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

    def _get_daily_quota_data(self, invoice_lines):
        resp = {
            'quota_day': 0,
            'total_area': 0,
            'days': 0,
            'thresold': 0,
            'total_consumption': 0,
            'extra_consumption': 0}
        for invoice_line in invoice_lines:
            if invoice_line.quota_day > 0:
                resp['quota_day'] = invoice_line.quota_day
                resp['total_area'] = invoice_line.total_area
                resp['days'] = invoice_line.days
                resp['threshold'] = invoice_line.threshold
                resp['total_consumption'] = invoice_line.total_consumption
                resp['extra_consumption'] = invoice_line.extra_consumption
                break
        return resp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    waterconnection_ids_str = fields.Text(string='List of waterconnections')

    quota_day = fields.Float(
        string='Daily Quota (m3/area unit)',
        digits=(32, 4),
        default=0)

    total_area = fields.Float(
        string='Area Total',
        digits=(32, 4),
        default=0)

    days = fields.Integer(
        string='Invoicing Days',
        default=0)

    threshold = fields.Float(
        string='Assigned Quota (m3)',
        digits=(32, 4),
        default=0)

    total_consumption = fields.Float(
        string='Total Consumption (m3)',
        digits=(32, 4),
        default=0)

    extra_consumption = fields.Float(
        string='Extra Consumption (m3)',
        digits=(32, 4),
        default=0)
