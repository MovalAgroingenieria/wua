# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from operator import itemgetter
import datetime
import pytz
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Methods for Irrigation settlement report
    def _get_partner_presconsumptions(self, partner_id):
        hydricmovs = False
        hydricmovs = self.env['wua.hydricmovement'].search([
            ('partner_id', '=', partner_id),
            ('of_active_agriculturalseason', '=', True),
            ('type', '=', 'pres_consumption')])
        # Get prescomsuption associated to hydric mov
        presconsumption_ids = []
        if hydricmovs:
            for hydricmov in hydricmovs:
                presconsumption_ids.append(hydricmov.presconsumption_id.id)
        presconsumptions = []
        if presconsumption_ids:
            presconsumption_ids = list(set(presconsumption_ids))
            pres_consumptions = \
                self.env['wua.presconsumption'].browse(presconsumption_ids)
            for consumption in pres_consumptions:
                item = {
                    'hydraulicsector': consumption.hydraulicsector_id.name,
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
                presconsumptions.append(item)
            presconsumptions_sorted = sorted(presconsumptions, key=itemgetter(
                'hydraulicsector', 'waterconnection', 'reading_initial_time'))
            # Change dates format
            tz = pytz.timezone(self.env.user.tz) or pytz.utc
            for consumption_item in presconsumptions_sorted:
                consumption_item['reading_initial_time'] = \
                    pytz.utc.localize(datetime.datetime.strptime(
                        consumption_item['reading_initial_time'],
                        '%Y-%m-%d %H:%M:%S')
                    ).astimezone(tz).strftime('%d/%m/%y')
                consumption_item['reading_end_time'] = \
                    pytz.utc.localize(datetime.datetime.strptime(
                        consumption_item['reading_end_time'],
                        '%Y-%m-%d %H:%M:%S')
                    ).astimezone(tz).strftime('%d/%m/%y')
        return presconsumptions_sorted

    def _get_partner_other_hydricmovements(self, partner_id):
        hydricmovs_raw = False
        hydricmovs_raw = self.env['wua.hydricmovement'].search([
            ('partner_id', '=', partner_id),
            ('of_active_agriculturalseason', '=', True),
            ('type', '!=', 'pres_consumption')], order='event_time')
        hydricmovs = []
        if hydricmovs_raw:
            for hydricmov in hydricmovs_raw:
                item = {
                    'superproduct': hydricmov.superproduct_id.name,
                    'description': hydricmov.description,
                    'accounting_volume': hydricmov.accounting_volume,
                    }
                hydricmovs.append(item)
        return hydricmovs
