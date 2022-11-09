# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaReadingperiod(models.Model):
    _inherit = 'wua.readingperiod'

    readingperiodflowmeterline_ids = fields.One2many(
        string='Associated flow-meters',
        comodel_name='wua.readingperiod.flowmeterline',
        inverse_name='readingperiod_id')

    number_of_flowmeters = fields.Integer(
        string='Number of flow-meters',
        store=True,
        index=True,
        compute='_compute_number_of_flowmeters')

    flowmeters = fields.Char(
        string='Flow-Meters',
        store=True,
        compute='_compute_flowmeters')

    flowreading_ids = fields.One2many(
        string='Intake Readings',
        comodel_name='wua.flowreading',
        inverse_name='readingperiod_id')

    number_of_flowreadings = fields.Integer(
        string='Number of intake readings',
        store=True,
        index=True,
        compute='_compute_number_of_flowreadings')

    waterpipeflowreading_ids = fields.One2many(
        string='Water-Pipe Readings',
        comodel_name='wua.waterpipeflowreading',
        inverse_name='readingperiod_id')

    number_of_waterpipeflowreadings = fields.Integer(
        string='Number of water-pipe readings',
        store=True,
        index=True,
        compute='_compute_number_of_waterpipeflowreadings')

    negative_flowreading_ids = fields.One2many(
        string='Negative Flowreadings',
        comodel_name='wua.negative.flowreading',
        inverse_name='readingperiod_id')

    number_of_negative_flowreadings = fields.Integer(
        string='Number of negative flowreadings',
        store=True,
        index=True,
        compute='_compute_number_of_negative_flowreadings')

    @api.depends('readingperiodflowmeterline_ids')
    def _compute_flowmeters(self):
        for record in self:
            flowmeters = []
            if (record.readingperiodflowmeterline_ids):
                flowmeters = record.readingperiodflowmeterline_ids.mapped(
                    lambda x: x.flowmeter_id.name)
            record.flowmeters = ','.join(flowmeters)

    @api.depends('readingperiodflowmeterline_ids')
    def _compute_number_of_flowmeters(self):
        for record in self:
            number_of_flowmeters = 0
            if (record.readingperiodflowmeterline_ids):
                number_of_flowmeters = len(
                    record.readingperiodflowmeterline_ids.mapped(
                        lambda x: x.flowmeter_id))
            record.number_of_flowmeters = number_of_flowmeters

    @api.depends('waterpipeflowreading_ids')
    def _compute_number_of_waterpipeflowreadings(self):
        for record in self:
            number_of_waterpipeflowreadings = 0
            if (record.waterpipeflowreading_ids):
                number_of_waterpipeflowreadings = \
                    len(record.waterpipeflowreading_ids)
            record.number_of_waterpipeflowreadings = \
                number_of_waterpipeflowreadings

    @api.depends('flowreading_ids')
    def _compute_number_of_flowreadings(self):
        for record in self:
            number_of_flowreadings = 0
            if (record.flowreading_ids):
                number_of_flowreadings = len(record.flowreading_ids)
            record.number_of_flowreadings = number_of_flowreadings

    @api.depends('negative_flowreading_ids')
    def _compute_number_of_negative_flowreadings(self):
        for record in self:
            number_of_negative_flowreadings = 0
            if (record.negative_flowreading_ids):
                number_of_negative_flowreadings = len(
                    record.negative_flowreading_ids)
            record.number_of_negative_flowreadings = \
                number_of_negative_flowreadings

    @api.multi
    def action_cancel_readingperiod(self):
        self.ensure_one()
        readingperiod = self
        if (self.reading_ids or self.negative_reading_ids or
            self.flowreading_ids or self.waterpipeflowreading_ids or
                self.negative_flowreading_ids):
            raise exceptions.UserError(_(
                'Operation not allowed: this reading period has some '
                'associated readings. Before canceling, it is mandatory to '
                'remove this readings.'))
        self._delete_irrigationshed_assignments(readingperiod,
                                                only_unselected=False)
        self.state = 'draft'

    @api.multi
    def action_get_flowreading_ids(self):
        self.ensure_one()
        condition = [('readingperiod_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_flowreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_flowreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_flowreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Flow Readings'),
            'res_model': 'wua.flowreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.multi
    def action_get_negative_flowreading_ids(self):
        self.ensure_one()
        condition = [('readingperiod_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_negative_flowreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_negative_flowreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_irrigation_measurement.'
            'wua_negative_flowreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Negative flowreadings'),
            'res_model': 'wua.negative.flowreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.multi
    def action_get_waterpipeflowreading_ids(self):
        self.ensure_one()
        condition = [('readingperiod_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeflowreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeflowreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_waterpipe_measurement.'
            'wua_waterpipeflowreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Water-Pipe Readings'),
            'res_model': 'wua.waterpipeflowreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    @api.multi
    def action_get_flowmeters(self):
        if self.readingperiodflowmeterline_ids:
            raise exceptions.UserError(_(
                'If a period already has flowmeters, this operation is not '
                'possible.'))
        flowmeters = self.env['wua.flowmeter'].search([])
        for flowmeter in flowmeters:
            self.env['wua.readingperiod.flowmeterline'].create({
                'flowmeter_id': flowmeter.id,
                'readingperiod_id': self.id,
                })


class WuaReadingperiodFlowmeterLine(models.Model):
    _name = 'wua.readingperiod.flowmeterline'
    _description = 'Reading-Period Flow-Meter Line'
    _order = 'name'

    MAX_SIZE_NAME = 52

    readingperiod_id = fields.Many2one(
        string='Reading Period',
        required=True,
        index=True,
        comodel_name='wua.readingperiod',
        ondelete='cascade')

    flowmeter_id = fields.Many2one(
        string='Flow-Meter',
        required=True,
        comodel_name='wua.flowmeter',
        domain=[('state', '=', 'active'),
                '|', ('intake_id', '!=', False),
                ('waterpipe_id', '!=', False)],
        ondelete='cascade')

    name = fields.Char(
        string='Reading-Period Flow-Meter Line',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        compute='_compute_intake_id',
        store=True,)

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        compute='_compute_waterpipe_id',
        store=True,)

    flowreading_id = fields.Many2one(
        string='Intake Reading',
        readonly=True,
        comodel_name='wua.flowreading',
        ondelete='set null',)

    negative_flowreading_id = fields.Many2one(
        string='Negative Flowreading',
        readonly=True,
        comodel_name='wua.negative.flowreading',
        ondelete='set null',)

    waterpipeflowreading_id = fields.Many2one(
        string='Water-Pipe Reading',
        readonly=True,
        comodel_name='wua.waterpipeflowreading',
        ondelete='set null',)

    is_visited = fields.Boolean(
        string='Flowmeter Visited?',
        store=True,
        default=False,
        compute='_compute_is_visited')

    @api.depends('readingperiod_id', 'flowmeter_id')
    def _compute_name(self):
        for record in self:
            name = None
            if (record.readingperiod_id and record.flowmeter_id):
                name = record.readingperiod_id.name + '-' + \
                    record.flowmeter_id.name
            record.name = name

    @api.depends('flowmeter_id')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if (record.flowmeter_id):
                intake_id = record.flowmeter_id.intake_id
            record.intake_id = intake_id

    @api.depends('flowmeter_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if (record.flowmeter_id):
                waterpipe_id = record.flowmeter_id.waterpipe_id
            record.waterpipe_id = waterpipe_id

    @api.depends('readingperiod_id.waterpipeflowreading_ids',
                 'readingperiod_id.flowreading_ids',
                 'readingperiod_id.negative_flowreading_ids',
                 'waterpipeflowreading_id',
                 'flowreading_id',
                 'negative_flowreading_id')
    def _compute_is_visited(self):
        for record in self:
            is_visited = record.flowreading_id or \
                record.waterpipeflowreading_id or \
                record.negative_flowreading_id
            record.is_visited = is_visited
