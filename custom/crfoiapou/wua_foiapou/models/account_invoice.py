# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


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
            rural_locations = []
            parcel = self.env['wua.parcel'].search([])
            for waterconnection_id in waterconnections_ids:
                consumptions_of_current_wc = \
                    self.env['wua.presconsumption'].search(
                        [('waterconnection_id', '=', waterconnection_id),
                         ('invoiceset_id', '=', invoiceset_id)],
                        order='reading_end_time')
                rural_location = ""
                for current_parcel in parcel:
                    for wc_parcel_id in current_parcel.irrigationpointwc_ids:
                        if(wc_parcel_id.waterconnection_id.id == waterconnection_id):
                            rural_location = \
                                current_parcel.rurallocation_id.name
                if consumptions_of_current_wc:
                    consumptions.extend(consumptions_of_current_wc)
                    rural_locations.append(rural_location)
            i = 0
            for consumption in consumptions:
                print consumption.waterconnection_id.name
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
                    'rural_location': rural_locations[i],
                    }
                i = i+1
                lines.append(item)
        return lines
