# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    last_reading_time = fields.Datetime(
        string='Last Reading Time',
        store=True,
        compute='_compute_last_reading_time')

    last_reading_value = fields.Float(
        string='Last Reading Value',
        store=True,
        digits=(32, 4),
        compute='_compute_last_reading_value')

    last_reading_instantflow = fields.Float(
        string='Last Reading Instant Flow',
        store=True,
        digits=(32, 4),
        compute='_compute_last_reading_instantflow')

    flowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.flowreading',
        inverse_name='flowmeter_id')

    intakeconsumption_ids = fields.One2many(
        string='Intake Consumptions',
        comodel_name='wua.intakeconsumption',
        inverse_name='intake_id')

    infm_ids = fields.One2many(
        string='Assigned Intakes',
        comodel_name='wua.in.fm',
        inverse_name='intake_id')

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_time')
    def _compute_last_reading_time(self):
        for record in self:
            last_reading_time = None
            if record.flowmeter_id and record.flowmeter_id.last_reading_time:
                last_reading_time = record.flowmeter_id.last_reading_time
            record.last_reading_time = last_reading_time

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_value')
    def _compute_last_reading_value(self):
        for record in self:
            last_reading_value = 0
            if record.flowmeter_id and record.flowmeter_id.last_reading_value:
                last_reading_value = record.flowmeter_id.last_reading_value
            record.last_reading_value = last_reading_value

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_instantflow')
    def _compute_last_reading_instantflow(self):
        for record in self:
            last_reading_instantflow = 0
            if record.flowmeter_id and \
                    record.flowmeter_id.last_reading_instantflow:
                last_reading_instantflow = \
                    record.flowmeter_id.last_reading_instantflow
            record.last_reading_instantflow = last_reading_instantflow

    @api.multi
    def action_see_intakeconsumptions(self):
        self.ensure_one()
        condition = [('intake_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_irrigation_measurement.'
                                    'wua_intakeconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_intakeconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_intakeconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.intakeconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.model
    def create(self, vals):
        intake = super(WuaIntake, self).create(vals)
        if vals['flowmeter_id']:
            self.update_wua_in_fm(intake.id, vals['flowmeter_id'])
        return intake

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'flowmeter_id' in vals:
            previous_flowmeter_id = self.flowmeter_id
            new_flowmeter_id = vals['flowmeter_id']
        resp = super(WuaIntake, self).write(vals)
        if len(self) == 1 and 'flowmeter_id' in vals:
            if previous_flowmeter_id != new_flowmeter_id:
                if previous_flowmeter_id:
                    previous_flowmeter_id = previous_flowmeter_id.id
                else:
                    previous_flowmeter_id = 0
                if not new_flowmeter_id:
                    new_flowmeter_id = 0
                # Case 1: from a flowmeter to none.
                if previous_flowmeter_id > 0 and new_flowmeter_id == 0:
                    self.update_wua_in_fm(0, previous_flowmeter_id)
                # Case 2: from no flowmeter to a flowmeter.
                if previous_flowmeter_id == 0 and new_flowmeter_id > 0:
                    self.update_wua_in_fm(self.id, new_flowmeter_id)
                # Case 3: from a flowmeter to a another.
                if previous_flowmeter_id > 0 and new_flowmeter_id > 0:
                    self.update_wua_in_fm(0, previous_flowmeter_id)
                    self.update_wua_in_fm(self.id, new_flowmeter_id)
        return resp

    # Update the "wua.in.fm" model.
    def update_wua_in_fm(self, intake_id, flowmeter_id):
        current_date = fields.Datetime.now()
        in_fm_registers = self.env['wua.in.fm']
        # For the old water connection...
        last_in_fm_registers_for_current_flowmeter = \
            in_fm_registers.search(
                [('flowmeter_id', '=', flowmeter_id),
                 ('assign_end', '=', False)],
                limit=1, order='assign_start desc')
        if last_in_fm_registers_for_current_flowmeter:
            vals_last_in_fm_registers_for_current_flowmeter = {
                'assign_end': current_date, }
            last_in_fm_registers_for_current_flowmeter.write(
                vals_last_in_fm_registers_for_current_flowmeter)
        # For the new intake...
        if intake_id:
            vals_new_in_fm_register = {
                'intake_id': intake_id,
                'flowmeter_id': flowmeter_id,
                'assign_start': current_date, }
            in_fm_registers.create(vals_new_in_fm_register)
            # It's necessary to create a initialization reading.
            last_reading_time = current_date
            last_reading_value = 0
            last_reading_instantflow = 0
            flowmeter = self.env['wua.flowmeter'].browse(flowmeter_id)
            if flowmeter.last_reading_time:
                last_reading_time = flowmeter.last_reading_time
            if flowmeter.last_reading_value:
                last_reading_value = flowmeter.last_reading_value
            if flowmeter.last_reading_instantflow:
                last_reading_instantflow = flowmeter.last_reading_instantflow
            vals_new_initialization_reading = {
                'flowmeter_id': flowmeter_id,
                'reading_time': last_reading_time,
                'volume': last_reading_value,
                'instant_flow': last_reading_instantflow,
                'initialization_reading': True, }
            self.env['wua.flowreading'].create(
                vals_new_initialization_reading)
