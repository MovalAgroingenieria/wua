# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        ondelete='restrict')

    with_watermeter = fields.Boolean(
        string='With water meter',
        store=True,
        compute='_compute_with_watermeter')

    wcwm_ids = fields.One2many(
        string='Assigned Water Meters',
        comodel_name='wua.wc.wm',
        inverse_name='waterconnection_id')

    last_reading_time = fields.Datetime(
        string='Last Reading Time',
        store=True,
        compute='_compute_last_reading_time')

    last_reading_value = fields.Float(
        string='Last Reading Value',
        digits=(32, 4),
        store=True,
        compute='_compute_last_reading_value',
        group_operator=False)

    average_consumption = fields.Float(
        string='Average Consumption (m³)',
        digits=(32, 2),
        store=True,
        compute='_compute_average_consumption')

    irrigation_shift_id = fields.Many2one(
        string='Irrigation Shift',
        comodel_name='wua.waterconnection.irrigation.shift',
        index=True,)

    irrigation_schedule_ids = fields.One2many(
        string='Irrigation Schedules',
        comodel_name='wua.waterconnection.irrigation.schedule',
        inverse_name='waterconnection_id')

    number_of_irrigation_schedules = fields.Integer(
        string='N. Irrigtion Schedules',
        compute='_compute_number_of_irrigation_schedules',
        store=True,
    )

    irrigation_event_ids = fields.One2many(
        string='Irrigation Events',
        comodel_name='wua.waterconnection.irrigation.event',
        inverse_name='waterconnection_id')

    last_irrigation_event_id = fields.Many2one(
        string='Last Irrigation Event',
        comodel_name='wua.waterconnection.irrigation.event',
        compute='_compute_last_irrigation_event_id',
        store=True,
        index=True,)

    number_of_irrigation_events = fields.Integer(
        string='N. Irrigtion Events',
        compute='_compute_number_of_irrigation_events',
        store=True,
    )

    @api.depends('watermeter_id')
    def _compute_with_watermeter(self):
        for record in self:
            with_watermeter = False
            if record.watermeter_id:
                with_watermeter = True
            record.with_watermeter = with_watermeter

    @api.depends('watermeter_id', 'watermeter_id.last_reading_time')
    def _compute_last_reading_time(self):
        for record in self:
            last_reading_time = None
            if record.watermeter_id:
                last_reading_time = record.watermeter_id.last_reading_time
            record.last_reading_time = last_reading_time

    @api.depends('watermeter_id', 'watermeter_id.last_reading_value')
    def _compute_last_reading_value(self):
        for record in self:
            last_reading_value = 0
            if record.watermeter_id:
                last_reading_value = record.watermeter_id.last_reading_value
            record.last_reading_value = last_reading_value

    @api.depends('watermeter_id', 'watermeter_id.average_consumption')
    def _compute_average_consumption(self):
        for record in self:
            average_consumption = 0
            if record.watermeter_id:
                average_consumption = record.watermeter_id.average_consumption
            record.average_consumption = average_consumption

    @api.depends('irrigation_schedule_ids')
    def _compute_number_of_irrigation_schedules(self):
        for record in self:
            number_of_irrigation_schedules = 0
            if (record.irrigation_schedule_ids):
                number_of_irrigation_schedules = len(
                    record.irrigation_schedule_ids)
            record.number_of_irrigation_schedules = \
                number_of_irrigation_schedules

    @api.depends('irrigation_event_ids')
    def _compute_last_irrigation_event_id(self):
        for record in self:
            last_irrigation_event_id = None
            if (record.irrigation_event_ids):
                last_irrigation_event_id = record.irrigation_event_ids[0]
            record.last_irrigation_event_id = last_irrigation_event_id

    @api.depends('irrigation_event_ids')
    def _compute_number_of_irrigation_events(self):
        for record in self:
            number_of_irrigation_events = 0
            if (record.irrigation_event_ids):
                number_of_irrigation_events = len(
                    record.irrigation_event_ids)
            record.number_of_irrigation_events = \
                number_of_irrigation_events

    @api.model
    def create(self, vals):
        waterconnection = super(WuaWaterconnection, self).create(vals)
        if vals['watermeter_id']:
            self.update_wua_wc_wm(waterconnection.id, vals['watermeter_id'])
        return waterconnection

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'watermeter_id' in vals:
            previous_watermeter_id = self.watermeter_id
            new_watermeter_id = vals['watermeter_id']
        resp = super(WuaWaterconnection, self).write(vals)
        if len(self) == 1 and 'watermeter_id' in vals:
            if previous_watermeter_id != new_watermeter_id:
                if previous_watermeter_id:
                    previous_watermeter_id = previous_watermeter_id.id
                else:
                    previous_watermeter_id = 0
                if not new_watermeter_id:
                    new_watermeter_id = 0
                # Case 1: from a watermeter to none.
                if previous_watermeter_id > 0 and new_watermeter_id == 0:
                    self.update_wua_wc_wm(0, previous_watermeter_id)
                # Case 2: from no watermeter to a watermeter.
                if previous_watermeter_id == 0 and new_watermeter_id > 0:
                    self.update_wua_wc_wm(self.id, new_watermeter_id)
                # Case 3: from a watermeter to a another.
                if previous_watermeter_id > 0 and new_watermeter_id > 0:
                    self.update_wua_wc_wm(0, previous_watermeter_id)
                    self.update_wua_wc_wm(self.id, new_watermeter_id)
        return resp

    # Update the 'wua.wc.wm' model.
    def update_wua_wc_wm(self, waterconnection_id, watermeter_id):
        current_date = datetime.datetime.now()
        wc_wm_registers = self.env['wua.wc.wm']
        # For the old water connection...
        last_wc_wm_registers_for_current_watermeter = \
            wc_wm_registers.search(
                [('watermeter_id', '=', watermeter_id),
                 ('assign_end', '=', False)],
                limit=1, order='assign_start desc')
        if last_wc_wm_registers_for_current_watermeter:
            vals_last_wc_wm_registers_for_current_watermeter = {
                'assign_end': current_date, }
            last_wc_wm_registers_for_current_watermeter.write(
                vals_last_wc_wm_registers_for_current_watermeter)
        # For the new water connection...
        if waterconnection_id:
            vals_new_wc_wm_register = {
                'waterconnection_id': waterconnection_id,
                'watermeter_id': watermeter_id,
                'assign_start': current_date, }
            wc_wm_registers.create(vals_new_wc_wm_register)
            # It's necessary to create a initialization reading.
            last_reading_time = current_date
            last_reading_value = 0
            watermeter = self.env['wua.watermeter'].browse(watermeter_id)
            if watermeter.last_reading_time:
                last_reading_time = watermeter.last_reading_time
            if watermeter.last_reading_value:
                last_reading_value = watermeter.last_reading_value
            vals_new_initialization_reading = {
                'watermeter_id': watermeter_id,
                'reading_time': last_reading_time,
                'volume': last_reading_value,
                'initialization_reading': True, }
            self.env['wua.reading'].create(
                vals_new_initialization_reading)

    @api.multi
    def action_see_presconsumptions(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_presconsumption_one_waterconnection_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_presconsumption_one_waterconnection_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def action_see_readings(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_reading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_reading_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_reading_view_search')
        reading_label = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
            'base_wua_pressurized_irrigation',
            'Readings')
        if (not reading_label):
            reading_label = _('Readings')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': reading_label,
            'res_model': 'wua.reading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'from_shortcut': 1},
            }
        return act_window

    @api.multi
    def action_see_irrigation_schedules(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_schedule_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_schedule_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_schedule_view_search')
        irrigation_schedules_label = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
            'base_wua_pressurized_irrigation',
            'Irrigation Schedules')
        if (not irrigation_schedules_label):
            irrigation_schedules_label = _('Irrigation Schedules')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': irrigation_schedules_label,
            'res_model': 'wua.waterconnection.irrigation.schedule',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'from_shortcut': 1},
            }
        return act_window

    @api.multi
    def action_see_irrigation_events(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_event_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_event_view_tree').id
        id_pivot_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_event_view_pivot').id
        id_graph_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_event_view_graph').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation.'
            'wua_waterconnection_irrigation_event_view_search')
        irrigation_events_label = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
            'base_wua_pressurized_irrigation',
            'Irrigation Events')
        if (not irrigation_events_label):
            irrigation_events_label = _('Irrigation Events')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': irrigation_events_label,
            'res_model': 'wua.waterconnection.irrigation.event',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_pivot_view, 'pivot'), (id_graph_view, 'graph')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'from_shortcut': 1},
            }
        return act_window
