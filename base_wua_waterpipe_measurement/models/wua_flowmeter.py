# -*- coding: utf-8 -*-).
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    last_waterpipeflowreading_time = fields.Datetime(
        string='Last Reading Time',)

    last_waterpipeflowreading_value = fields.Float(
        string='Last Reading Value (m3)',
        digits=(32, 4))

    last_waterpipeflowreading_instantflow = fields.Float(
        string='Last Instant Flow (m3/h)',
        digits=(32, 4))

    last_reading_time_show = fields.Datetime(
        string='Last Reading Time',
        compute='_compute_last_reading_time_show',
        store=True,)

    last_reading_value_show = fields.Float(
        string='Last Reading Value (m3)',
        digits=(32, 4),
        compute='_compute_last_reading_value_show',
        store=True,)

    last_reading_instantflow_show = fields.Float(
        string='Last Instant Flow (m3/h)',
        digits=(32, 4),
        compute='_compute_last_reading_instantflow_show',
        store=True,)

    waterpipe_ids = fields.One2many(
        string='Waterpipes',
        comodel_name='wua.waterpipe',
        inverse_name='flowmeter_id',
        help="Waterpipes related to the flow-meter")

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        comodel_name='wua.waterpipe',
        index=True,
        compute="_compute_waterpipe_id",
        store=True)

    connected_to_waterpipe = fields.Boolean(
        string="In waterpipe",
        store=True,
        compute="_compute_connected_to_waterpipe")

    waterpipeflowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.waterpipeflowreading',
        inverse_name='flowmeter_id')

    waterpipeconsumption_ids = fields.One2many(
        string='Waterpipe Consumptions',
        comodel_name='wua.waterpipeconsumption',
        inverse_name='flowmeter_id')

    wpfm_ids = fields.One2many(
        string='Assigned Waterpipes',
        comodel_name='wua.wp.fm',
        inverse_name='flowmeter_id')

    @api.depends('waterpipe_ids')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if record.waterpipe_ids:
                waterpipe_id = record.waterpipe_ids[0]
            record.waterpipe_id = waterpipe_id

    @api.depends('waterpipe_id')
    def _compute_connected_to_waterpipe(self):
        for record in self:
            connected_to_waterpipe = False
            if record.waterpipe_id:
                connected_to_waterpipe = True
            record.connected_to_waterpipe = connected_to_waterpipe

    @api.depends('connected_to_waterpipe', 'last_waterpipeflowreading_time',
                 'connected_to_intake', 'last_reading_time')
    def _compute_last_reading_time_show(self):
        for record in self:
            last_reading_time_show = None
            if (record.connected_to_waterpipe):
                last_reading_time_show = record.last_waterpipeflowreading_time
            elif (record.connected_to_intake):
                last_reading_time_show = record.last_reading_time
            record.last_reading_time_show = last_reading_time_show

    @api.depends('connected_to_waterpipe', 'last_waterpipeflowreading_value',
                 'connected_to_intake', 'last_reading_value')
    def _compute_last_reading_value_show(self):
        for record in self:
            last_reading_value_show = None
            if (record.connected_to_waterpipe):
                last_reading_value_show = \
                    record.last_waterpipeflowreading_value
            elif (record.connected_to_intake):
                last_reading_value_show = record.last_reading_value
            record.last_reading_value_show = last_reading_value_show

    @api.depends('connected_to_waterpipe', 'connected_to_intake',
                 'last_waterpipeflowreading_instantflow',
                 'last_reading_instantflow')
    def _compute_last_reading_instantflow_show(self):
        for record in self:
            last_reading_instantflow_show = None
            if (record.connected_to_waterpipe):
                last_reading_instantflow_show = \
                    record.last_waterpipeflowreading_instantflow
            elif (record.connected_to_intake):
                last_reading_instantflow_show = \
                    record.last_reading_instantflow
            record.last_reading_instantflow_show = \
                last_reading_instantflow_show

    @api.multi
    def action_see_waterpipeconsumptions(self):
        self.ensure_one()
        condition = [('flowmeter_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_waterpipe_measurement.'
                                    'wua_waterpipeconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.waterpipeconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
