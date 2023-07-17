# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    last_reading_time = fields.Datetime(
        string='Last Reading Time',)

    last_reading_value = fields.Float(
        string='Last Reading Value (m³)',
        digits=(32, 4))

    last_reading_instantflow = fields.Float(
        string='Last Instant Flow (m³/h)',
        digits=(32, 4))

    flowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.flowreading',
        inverse_name='flowmeter_id')

    intakeconsumption_ids = fields.One2many(
        string='Intake Consumptions',
        comodel_name='wua.intakeconsumption',
        inverse_name='flowmeter_id')

    infm_ids = fields.One2many(
        string='Assigned Intakes',
        comodel_name='wua.in.fm',
        inverse_name='flowmeter_id')

    num_intakeflowreading_ids = fields.Integer(
        string='Num. Intake flowreadings',
        compute='_compute_num_intakeflowreading_ids')

    num_intakeconsumption_ids = fields.Integer(
        string='Num. Intake consumption',
        compute='_compute_num_intakeconsumption_ids')

    @api.depends('flowreading_ids')
    def _compute_num_intakeflowreading_ids(self):
        for record in self:
            record.num_intakeflowreading_ids = \
                len(record.flowreading_ids)

    @api.depends('intakeconsumption_ids')
    def _compute_num_intakeconsumption_ids(self):
        for record in self:
            record.num_intakeconsumption_ids = \
                len(record.intakeconsumption_ids)

    @api.multi
    def action_see_flowmeterconsumptions(self):
        self.ensure_one()
        condition = [('flowmeter_id', '=', self.id)]
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

    @api.multi
    def action_see_flowreadings(self):
        self.ensure_one()
        condition = [('flowmeter_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_irrigation_measurement.'
                                    'wua_flowreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_irrigation_measurement.wua_flowreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_irrigation_measurement.wua_flowreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Flow readings'),
            'res_model': 'wua.flowreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'context': {'from_shortcut': 1},
            'target': 'current',
            }
        return act_window
