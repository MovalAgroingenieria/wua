# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaPresresconsumption(models.Model):
    _inherit = 'wua.presresconsumption'

    watering_duration = fields.Integer(
        string='Watering Duration (Hours)',
        default=24,
        required=True,
        readonly=True,
    )

    maximum_nominal_flow = fields.Float(
        string='Maximum nominal flow (m³/h)',
        compute='_compute_maximum_nominal_flow',
        digits=(32, 4),
    )

    def is_close(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    @api.constrains('nominal_flow', 'waterconnection_id')
    def _check_nominal_flow_like_some_flow(self):
        # The nominal flow must be a combination of some of the modules
        # setted on the waterconnection
        for record in self:
            if (record.waterconnection_id.watermeter_id and
                record.waterconnection_id.watermeter_id.
                    watermeter_module_ids):
                module_flows = record.waterconnection_id.watermeter_id.\
                    watermeter_module_ids.mapped(lambda x: x.module_flow)
                # All the possible combinations
                # This function create an array with all the possible arrays
                # combinations
                possible_combinations = [[]]
                for flow in module_flows:
                    possible_combinations += [
                        f + [flow] for f in possible_combinations]
                some_combination = False
                # Check if some combination eqquals the nominal_flow
                for combination in possible_combinations:
                    if (self.is_close(
                            record.nominal_flow, sum(combination))):
                        some_combination = True
                        break
                if (not some_combination):
                    raise ValidationError(
                        _('The nominal flow of %s is not a combination of '
                          'the watermeter modules (%s -> %s).') % (
                            record.waterconnection_id.name,
                            str(int(record.nominal_flow)),
                            ', '.join([str(int(x)) for x in module_flows])))

    @api.constrains('maximum_nominal_flow', 'nominal_flow')
    def _check_nominal_flow(self):
        for record in self:
            if (record.nominal_flow and record.maximum_nominal_flow and
                    (record.nominal_flow > record.maximum_nominal_flow)):
                raise ValidationError(
                    _('The nominal flow cannot be greater than the '
                      'maximum_nominal_flow.'))

    @api.onchange('waterconnection_id')
    def _onchange_waterconnection_id(self):
        # Get the default initial hour fo the waterconnection
        # if not initial hour duration on WC, then check global parameter
        initial_hour = 0.0
        global_initial_hour = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'default_presresconsumption_initial_hour')
        if (self.waterconnection_id):
            initial_hour = \
                self.waterconnection_id.default_request_initial_hour
        if (not initial_hour and global_initial_hour):
            initial_hour = global_initial_hour
        nominal_flow = 0
        if (self.waterconnection_id and self.waterconnection_id.watermeter_id):
            nominal_flow = \
                self.waterconnection_id.watermeter_id.nominal_water_flow
        self.nominal_flow = nominal_flow
        self.initial_hour = initial_hour

    @api.multi
    def _compute_maximum_nominal_flow(self):
        for record in self:
            maximum_nominal_flow = 0
            if (record.waterconnection_id and
                    record.waterconnection_id.maximum_nominal_flow):
                maximum_nominal_flow = record.waterconnection_id.\
                    maximum_nominal_flow
            record.maximum_nominal_flow = maximum_nominal_flow
