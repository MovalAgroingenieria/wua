# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields


class WuaPresresconsumption(models.Model):
    _inherit = 'wua.presresconsumption'

    controlreading_id = fields.Many2one(
        string='Control Reading',
        comodel_name='wua.controlreading',
        ondelete='restrict',
        index=True,
    )

    # On creation of presresconsumption, we create a related controlreading
    # and assing it to the controlreading_id field
    def create(self, vals):
        presresconsumption = super(WuaPresresconsumption, self).create(vals)
        # If not in vals we create a controlreading
        if ('controlreading_id' not in vals):
            # Use auxiliary method from wua.controlreading
            self.env['wua.controlreading'].\
                _create_controlreading_for_pr(
                    presresconsumption)
        return presresconsumption

    # On update with write, we check if the watering_volume or request_time
    # fields are updated, if so we update the related controlreading
    def write(self, vals):
        res = super(WuaPresresconsumption, self).write(vals)
        for record in self:
            if record.controlreading_id and record.controlreading_id.active:
                update_controlreading = False
                update_controlpresconsumption = False
                controlreading_vals = {}
                controlpresconsumption_vals = {}
                if 'nominal_flow' in vals or 'watering_duration' in vals:
                    # Let's check if nominal flow or watering duration is
                    # setted if both, we recalculate watering volume with
                    # vals, else, with vals and record values
                    nominal_flow = vals.get('nominal_flow',
                                            record.nominal_flow)
                    watering_duration = vals.get('watering_duration',
                                                 record.watering_duration)
                    if nominal_flow and watering_duration:
                        # Watering duration is alwais hours and nominal flow
                        # is m³/h, even if nominal_flow_ls is also setted
                        watering_volume = (
                            nominal_flow * watering_duration)
                        controlpresconsumption_vals['adjustement_volume'] = (
                            watering_volume)
                        update_controlpresconsumption = True
                    controlpresconsumption_vals['adjustement_volume'] = (
                        record.watering_volume)
                    update_controlpresconsumption = True
                if 'initial_hour' in vals or 'watering_duration' in vals:
                    # add to request time, the watering duration in hours
                    request_dt = fields.Datetime.from_string(
                        record.request_time)
                    controlreading_vals['reading_time'] = (
                        request_dt + datetime.timedelta(
                            hours=record.watering_duration))
                    controlpresconsumption_vals['reading_end_time'] = (
                        request_dt + datetime.timedelta(
                            hours=record.watering_duration))
                    update_controlreading = True
                    update_controlpresconsumption = True
                if update_controlreading:
                    record.controlreading_id.write(controlreading_vals)
                if update_controlpresconsumption:
                    record.controlreading_id.controlpresconsumption_id.write(
                        controlpresconsumption_vals)
        return res
