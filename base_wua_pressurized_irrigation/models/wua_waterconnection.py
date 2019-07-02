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
        compute='_compute_last_reading_value')

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

    # Update the "wua.wc.wm" model.
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
            last_reading_value = 0
            watermeter = self.env['wua.watermeter'].browse(watermeter_id)
            if watermeter.last_reading_value:
                last_reading_value = watermeter.last_reading_value
            vals_new_initialization_reading = {
                'watermeter_id': watermeter_id,
                'reading_time': current_date,
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
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_one_waterconnection_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation.'
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
