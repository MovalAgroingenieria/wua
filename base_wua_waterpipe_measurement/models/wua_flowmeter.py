# -*- coding: utf-8 -*-).
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    last_waterpipeflowreading_time = fields.Datetime(
        string='Last Reading Time',)

    last_waterpipeflowreading_value = fields.Float(
        string='Last Reading Value (m³)',
        digits=(32, 4))

    last_waterpipeflowreading_instantflow = fields.Float(
        string='Last Instant Flow (m³/h)',
        digits=(32, 4))

    last_reading_time_show = fields.Datetime(
        string='Last Reading Time',
        compute='_compute_last_reading_time_show',
        store=True,)

    last_reading_value_show = fields.Float(
        string='Last Reading Value (m³)',
        digits=(32, 4),
        compute='_compute_last_reading_value_show',
        store=True,)

    last_reading_instantflow_show = fields.Float(
        string='Last Instant Flow (m³/h)',
        digits=(32, 4),
        compute='_compute_last_reading_instantflow_show',
        store=True,)

    last_reading_time_original = fields.Datetime(
        string='Last Reading Time',)

    last_reading_value_original = fields.Float(
        string='Last Reading Value (m³)',
        digits=(32, 4),)

    last_reading_instantflow_original = fields.Float(
        string='Last Instant Flow (m³/h)',
        digits=(32, 4),)

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

    num_waterpipeflowreading_ids = fields.Integer(
        string='Num. Waterpipe flowreadings',
        compute='_compute_num_waterpipeflowreading_ids')

    num_waterpipeconsumption_ids = fields.Integer(
        string='Num. Waterpipe consumption',
        compute='_compute_num_waterpipeconsumption_ids')

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
            else:
                last_reading_time_show = record.last_reading_time_original
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
            else:
                last_reading_value_show = record.last_reading_value_original
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
            else:
                last_reading_instantflow_show = \
                    record.last_reading_instantflow_original
            record.last_reading_instantflow_show = \
                last_reading_instantflow_show

    @api.depends('waterpipeflowreading_ids')
    def _compute_num_waterpipeflowreading_ids(self):
        for record in self:
            record.num_waterpipeflowreading_ids = \
                len(record.waterpipeflowreading_ids)

    @api.depends('waterpipeconsumption_ids')
    def _compute_num_waterpipeconsumption_ids(self):
        for record in self:
            record.num_waterpipeconsumption_ids = \
                len(record.waterpipeconsumption_ids)

    @api.model
    def create(self, vals):
        if ('last_reading_time_original' in vals):
            vals['last_reading_time'] = \
                vals['last_reading_time_original']
            vals['last_waterpipeflowreading_time'] = \
                vals['last_reading_time_original']
        if ('last_reading_value_original' in vals):
            vals['last_reading_value'] = \
                vals['last_reading_value_original']
            vals['last_waterpipeflowreading_value'] = \
                vals['last_reading_value_original']
        if ('last_reading_instantflow_original' in vals):
            vals['last_reading_instantflow'] = \
                vals['last_reading_instantflow_original']
            vals['last_waterpipeflowreading_instantflow'] = \
                vals['last_reading_instantflow_original']
        return super(WuaFlowmeter, self).create(vals)

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

    @api.multi
    def action_see_waterpipeflowreading(self):
        self.ensure_one()
        condition = [('flowmeter_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_waterpipe_measurement.'
                                    'wua_waterpipeflowreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeflowreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeflowreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterpipe Readings'),
            'res_model': 'wua.waterpipeflowreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
