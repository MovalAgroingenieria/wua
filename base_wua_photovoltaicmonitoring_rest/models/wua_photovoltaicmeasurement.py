# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from odoo import models, api, _


class WuaPhotovoltaicmeasurement(models.Model):
    _inherit = 'wua.photovoltaicmeasurement'

    @api.model
    def do_import_measurements(self, photovoltaicplant_code, delay=True):
        # if resp is equal to -1, then there is an error
        resp = 0
        if photovoltaicplant_code:
            photovoltaicplant = self.env['wua.photovoltaicplant'].search(
                [('photovoltaicplant_code', '=', photovoltaicplant_code)])
            if photovoltaicplant:
                photovoltaicplant = photovoltaicplant[0]
                if (photovoltaicplant.photovoltaicmonitoring_enabled and
                   photovoltaicplant.connected_to_api):
                    measurements, flag_error = \
                        self._import_measurements(photovoltaicplant)
                    if (not flag_error):
                        if measurements and len(measurements) > 0:
                            model_photovoltaicmeasurement = \
                                self.env['wua.photovoltaicmeasurement']
                            for key, value in measurements.items():
                                if (not photovoltaicplant.
                                    last_measurement_time or key >
                                   photovoltaicplant.last_measurement_time):
                                    model_photovoltaicmeasurement.create({
                                        'photovoltaicplant_id':
                                            photovoltaicplant.id,
                                        'measurement_time': key,
                                        'generated_power':
                                        value['generated_power']
                                        })
                                    resp = resp + 1
                    else:
                        resp = -1
                    self._post_import_measurements(
                        photovoltaicplant, measurements, resp, delay)
        return resp

    @api.model
    def do_import_measurements_global(self, show_photovoltaicplants=False):
        resp = 0
        model_photovoltaicplant = self.env['wua.photovoltaicplant']
        model_photovoltaicmeasurement = self.env['wua.photovoltaicmeasurement']
        photovoltaicplants = model_photovoltaicplant.search([])
        for photovoltaicplant in (photovoltaicplants or []):
            number_of_measurements = \
                model_photovoltaicmeasurement.do_import_measurements(
                    photovoltaicplant.photovoltaicplant_code)
            if number_of_measurements != -1:
                resp = resp + number_of_measurements
        if show_photovoltaicplants:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Photovoltaicplants'),
                'res_model': 'wua.photovoltaicplant',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current'
                }
        else:
            return resp

    # Hook
    def _import_measurements(self, photovoltaicplant):
        # Dictionary with measurements and flag of error
        return None, False

    # Hook
    def _post_import_measurements(self, photovoltaicplant,
                                  measurements, number_of_measurements,
                                  delay=True):
        # Actions after "_do_import_measurements"
        if delay:
            model_values = self.env['ir.values'].sudo()
            delay_between_requests = model_values.get_default(
                'wua.infrastructure.configuration',
                'delay_between_requests')
            if (delay_between_requests and delay_between_requests > 0):
                time.sleep(delay_between_requests)
