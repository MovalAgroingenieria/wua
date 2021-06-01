# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaPumpgroupmeasurement(models.Model):
    _inherit = 'wua.pumpgroupmeasurement'

    @api.model
    def do_import_measurements(self, pumpgroup_code):
        # if resp is equal to -1, then there is an error
        resp = 0
        if pumpgroup_code:
            pumpgroup = self.env['wua.pumpgroup'].search(
                [('pumpgroup_code', '=', pumpgroup_code)])
            if pumpgroup:
                pumpgroup = pumpgroup[0]
                if (pumpgroup.energymonitoring_enabled and
                   pumpgroup.connected_to_api):
                    measurements, flag_error = \
                        self._import_measurements(pumpgroup)
                    if (not flag_error):
                        if measurements and len(measurements) > 0:
                            model_pumpgroupmeasurement = \
                                self.env['wua.pumpgroupmeasurement']
                            for key, value in measurements.items():
                                if (not pumpgroup.last_measurement_time or
                                   key >
                                   pumpgroup.last_measurement_time):
                                    model_pumpgroupmeasurement.create({
                                        'pumpgroup_id': pumpgroup.id,
                                        'measurement_time': key,
                                        'impulsion_pressure':
                                        value['impulsion_pressure'],
                                        'suction_pressure':
                                        value['suction_pressure'],
                                        'instantaneous_flow':
                                        value['instantaneous_flow'],
                                        'consumed_power':
                                        value['consumed_power']
                                        })
                                    resp = resp + 1
                    else:
                        resp = -1
        return resp

    @api.model
    def do_import_measurements_global(self, show_pumpgroups=False):
        resp = 0
        model_pumpgroup = self.env['wua.pumpgroup']
        model_pumpgroupmeasurement = self.env['wua.pumpgroupmeasurement']
        pumpgroups = model_pumpgroup.search([])
        for pumpgroup in (pumpgroups or []):
            number_of_measurements = \
                model_pumpgroupmeasurement.do_import_measurements(
                    pumpgroup.pumpgroup_code)
            if number_of_measurements != -1:
                resp = resp + number_of_measurements
        if show_pumpgroups:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Pumpgroups'),
                'res_model': 'wua.pumpgroup',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current'
                }
        else:
            return resp

    # Hook
    def _import_measurements(self, pumpgroup):
        # Dictionary with measurements and flag of error
        return None, False
