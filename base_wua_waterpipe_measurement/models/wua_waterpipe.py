# -*- coding: utf-8 -*-).
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _, exceptions, api


class WuaWaterpipe(models.Model):
    _inherit = 'wua.waterpipe'

    flowmeter_id = fields.Many2one(
        string='Flowmeter',
        comodel_name='wua.flowmeter',
        index=True)

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

    waterpipeflowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.waterpipeflowreading',
        inverse_name='flowmeter_id')

    waterpipeconsumption_ids = fields.One2many(
        string='Waterpipe Consumptions',
        comodel_name='wua.waterpipeconsumption',
        inverse_name='waterpipe_id')

    wpfm_ids = fields.One2many(
        string='Assigned Waterpipes',
        comodel_name='wua.wp.fm',
        inverse_name='waterpipe_id')

    @api.constrains('flowmeter_id')
    def _check_flowmeter_id(self):
        if len(self) == 1:
            current_waterpipe = self
            if current_waterpipe.flowmeter_id:
                current_flowmeter = current_waterpipe.flowmeter_id
                # The flow-meter for this waterpipe ("current_flowmeter")
                # cannot be assigned to another waterpipe.
                other_waterpipes_of_flowmeter = self.env['wua.waterpipe'].\
                    search(
                    [('id', '!=', current_waterpipe.id),
                     ('flowmeter_id', '=', current_flowmeter.id)])
                if other_waterpipes_of_flowmeter:
                    raise exceptions.ValidationError(
                        _('Flowmeter already on waterpipe.'))
                other_intakes_of_flowmeter = self.env['wua.intake'].search(
                    [('flowmeter_id', '=', current_flowmeter.id)])
                if other_intakes_of_flowmeter:
                    raise exceptions.ValidationError(
                        _('Flowmeter already on intake.'))

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
    def action_see_waterpipeconsumptions(self):
        self.ensure_one()
        condition = [('waterpipe_id', '=', self.id)]
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

    @api.model
    def create(self, vals):
        waterpipe = super(WuaWaterpipe, self).create(vals)
        if vals['flowmeter_id']:
            self.update_wua_wp_fm(waterpipe.id, vals['flowmeter_id'])
        return waterpipe

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'flowmeter_id' in vals:
            previous_flowmeter_id = self.flowmeter_id
            new_flowmeter_id = vals['flowmeter_id']
        resp = super(WuaWaterpipe, self).write(vals)
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
                    self.update_wua_wp_fm(0, previous_flowmeter_id)
                # Case 2: from no flowmeter to a flowmeter.
                if previous_flowmeter_id == 0 and new_flowmeter_id > 0:
                    self.update_wua_wp_fm(self.id, new_flowmeter_id)
                # Case 3: from a flowmeter to a another.
                if previous_flowmeter_id > 0 and new_flowmeter_id > 0:
                    self.update_wua_wp_fm(0, previous_flowmeter_id)
                    self.update_wua_wp_fm(self.id, new_flowmeter_id)
        return resp

    # Update the "wua.wp.fm" model.
    def update_wua_wp_fm(self, waterpipe_id, flowmeter_id):
        current_date = fields.Datetime.now()
        wp_fm_registers = self.env['wua.wp.fm']
        # For the old water connection...
        last_wp_fm_registers_for_current_flowmeter = \
            wp_fm_registers.search(
                [('flowmeter_id', '=', flowmeter_id),
                 ('assign_end', '=', False)],
                limit=1, order='assign_start desc')
        if last_wp_fm_registers_for_current_flowmeter:
            vals_last_wp_fm_registers_for_current_flowmeter = {
                'assign_end': current_date, }
            last_wp_fm_registers_for_current_flowmeter.write(
                vals_last_wp_fm_registers_for_current_flowmeter)
        # For the new Waterpipe...
        if waterpipe_id:
            vals_new_wp_fm_register = {
                'waterpipe_id': waterpipe_id,
                'flowmeter_id': flowmeter_id,
                'assign_start': current_date, }
            wp_fm_registers.create(vals_new_wp_fm_register)
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
            self.env['wua.waterpipeflowreading'].create(
                vals_new_initialization_reading)
