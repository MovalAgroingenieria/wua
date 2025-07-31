# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json

from lxml import etree
from odoo import models, fields, api, tools, _, exceptions


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

    tertiarypipe_id = fields.One2many(
        comodel_name='wua.tertiarypipe',
        string='Tertiary Pipe',
        readonly=True,
        inverse_name='waterconnection_id',
    )

    irrigation_shift_ids = fields.One2many(
        string='Irrigation Shifts',
        comodel_name='wua.waterconnection.irrigation.shift.relation',
        inverse_name='waterconnection_id')

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
        index=True,
    )

    number_of_irrigation_events = fields.Integer(
        string='N. Irrigtion Events',
        compute='_compute_number_of_irrigation_events',
        store=True,
    )

    partner_id = fields.Many2one(
        string='WUA Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_partner_id',
    )

    last_reading_consumption = fields.Float(
        string='Last Consumption Value',
        digits=(32, 4),
        store=True,
        compute='_compute_last_reading_consumption_value',
        group_operator=False,
    )

    zone_id = fields.Many2one(
        string='Zone',
        comodel_name='wua.zone',
        index=True,
        store=True,
        compute='_compute_zone_id',
    )

    estimated_monthly_consumption = fields.Integer(
        string='Estimated monthly consumption (m³)',
        default=0,
    )

    last_reading_type = fields.Selection(
        [
            ('01_estimated', 'Estimated Reading'),
            ('02_real_worker', 'Real Worker Reading'),
            ('03_real_partner', 'Real Partner Reading'),
        ],
        string='Last Reading (type)',
        store=True,
        compute='_compute_last_reading_type',
    )

    waterconnection_state_id = fields.Many2one(
        string='Waterconnection State',
        comodel_name='wua.waterconnection.state',
        index=True,
        default=lambda self: self.get_default_state(),
        ondelete='restrict',
    )

    is_state_close = fields.Boolean(
        string='Is State Closed',
        related='waterconnection_state_id.is_close',
        store=True,
        help='Indicates whether the water connection is closed '
             'and cannot be modified further.',
    )

    _sql_constraints = [
        ('estimated_monthly_consumption_positive',
         'CHECK(estimated_monthly_consumption >= 0)',
         'The estimated monthly consumption must be positive.'),
    ]

    @api.depends('irrigationshed_id', 'irrigationshed_id.zone_id')
    def _compute_zone_id(self):
        for record in self:
            zone_id = None
            if record.irrigationshed_id:
                zone_id = record.irrigationshed_id.zone_id
            record.zone_id = zone_id

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

    @api.depends('irrigationpoint_ids', 'irrigationpoint_ids.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if (record.irrigationpoint_ids and
                    len(record.irrigationpoint_ids) > 0):
                partner_id = record.irrigationpoint_ids[0].partner_id
            record.partner_id = partner_id

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

    @api.depends('watermeter_id', 'watermeter_id.last_reading_consumption')
    def _compute_last_reading_consumption_value(self):
        for record in self:
            last_reading_consumption = 0
            if record.watermeter_id:
                last_reading_consumption = \
                    record.watermeter_id.last_reading_consumption
            record.last_reading_consumption = last_reading_consumption

    @api.depends('watermeter_id', 'watermeter_id.last_reading_type')
    def _compute_last_reading_type(self):
        for record in self:
            last_reading_type = False
            if record.watermeter_id.last_reading_type:
                last_reading_type = record.watermeter_id.last_reading_type
            record.last_reading_type = last_reading_type

    @api.model
    def create(self, vals):
        waterconnection = super(WuaWaterconnection, self).create(vals)
        if vals['watermeter_id']:
            self.update_wua_wc_wm(waterconnection.id, vals['watermeter_id'])
        return waterconnection

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaWaterconnection, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        management_of_reading_type = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'management_of_reading_type')
        if not management_of_reading_type and view_type in [
                'form', 'tree', 'search']:
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='last_reading_type']"):
                node.set('invisible', '1')
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['tree_invisible'] = True
                modifiers['column_invisible'] = True
                modifiers['invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
            if view_type == 'search':
                for filter_node in doc.xpath(
                        "//filter[@domain][contains(@domain, "
                        "'last_reading_type')]"):
                    parent = filter_node.getparent()
                    parent.remove(filter_node)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    @api.multi
    def write(self, vals):
        previous_watermeter_id = None
        new_watermeter_id = None
        if len(self) == 1 and 'watermeter_id' in vals:
            previous_watermeter_id = self.watermeter_id
            new_watermeter_id = vals['watermeter_id']
        resp = super(WuaWaterconnection, self).write(vals)
        if len(self) == 1 and 'watermeter_id' in vals:
            # Convert to IDs for comparison
            if previous_watermeter_id:
                previous_watermeter_id = previous_watermeter_id.id
            else:
                previous_watermeter_id = 0
            if not new_watermeter_id:
                new_watermeter_id = 0
            # Only proceed if there's actually a change
            if previous_watermeter_id != new_watermeter_id:
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
                'assign_end': current_date,
            }
            last_wc_wm_registers_for_current_watermeter.write(
                vals_last_wc_wm_registers_for_current_watermeter)
        # For the new water connection...
        if waterconnection_id:
            vals_new_wc_wm_register = {
                'waterconnection_id': waterconnection_id,
                'watermeter_id': watermeter_id,
                'assign_start': current_date,
            }
            wc_wm_registers.create(vals_new_wc_wm_register)
            # It's necessary to create a initialization reading.
            last_reading_time = current_date
            last_reading_value = 0
            last_reading_consumption = 0
            watermeter = self.env['wua.watermeter'].browse(watermeter_id)
            if watermeter.last_reading_time:
                last_reading_time = str(
                    fields.Datetime.from_string(watermeter.last_reading_time) +
                    datetime.timedelta(seconds=1))
            if watermeter.last_reading_value:
                last_reading_value = watermeter.last_reading_value
            if watermeter.last_reading_consumption:
                last_reading_consumption = watermeter.last_reading_consumption
            vals_new_initialization_reading = {
                'watermeter_id': watermeter_id,
                'reading_time': last_reading_time,
                'volume': last_reading_value,
                'volume_real': last_reading_consumption,
                'initialization_reading': True,
            }
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

    def action_see_tertiary_pipe(self):
        self.ensure_one()
        if not self.tertiarypipe_id:
            raise exceptions.UserError(_('No tertiary pipe associated.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tertiary Pipe'),
            'res_model': 'wua.tertiarypipe',
            'view_mode': 'form',
            'res_id': self.tertiarypipe_id.id,
            'target': 'current',
            'context': {'create': False},
        }

    def get_default_state(self):
        return self.env['wua.waterconnection.state'].search(
            [('default_state', '=', True)], limit=1)


class WuaWaterconnectionIrrigationShiftlink(models.Model):
    _name = 'wua.waterconnection.irrigation.shiftlink'
    _auto = False
    _description = 'Irrigationshift link of a waterconnection'

    waterconnection_id = fields.Many2one(
        string='Waterconnection Code',
        comodel_name='wua.waterconnection',
        required=True,
        index=True,
        ondelete='cascade')

    irrigation_shift_id = fields.Many2one(
        string='Irrigation Shift',
        comodel_name='wua.waterconnection.irrigation.shift',
        required=True,
        index=True,
        ondelete='cascade')

    description = fields.Char(
        string='Description',
        related='irrigation_shift_id.description')

    notes = fields.Html(
        string='Notes',
        related='irrigation_shift_id.notes')

    @api.model_cr
    def init(self):
        self.env.cr.execute("""SELECT EXISTS(
            SELECT * FROM information_schema.tables
            WHERE table_name='wua_waterconnection_irrigation_shiftlink')""")
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(
                self.env.cr, 'wua_waterconnection_irrigation_shiftlink')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
            CREATE OR REPLACE VIEW
            wua_waterconnection_irrigation_shiftlink AS (
                SELECT
                    row_number() OVER() AS id,
                    row.waterconnection_id,
                    row.irrigation_shift_id,
                    row.notes,
                    row.name,
                    row.description
                FROM (
                    SELECT
                        waterconnection.id AS waterconnection_id,
                        irrigation_shift.id AS irrigation_shift_id,
                        irrigation_shift.notes, irrigation_shift.name,
                        irrigation_shift.description
                    FROM wua_waterconnection_irrigation_shift_relation rel
                    INNER JOIN wua_waterconnection waterconnection
                        ON rel.waterconnection_id = waterconnection.id
                    INNER JOIN wua_waterconnection_irrigation_shift
                    irrigation_shift
                        ON rel.irrigation_shift_id = irrigation_shift.id
                ) row
            )
        """)
        except Exception:
            self.env.cr.rollback()


class WuaWaterconnectionIrrigationShiftRelation(models.Model):
    _name = 'wua.waterconnection.irrigation.shift.relation'
    _description = 'Water Connection - Irrigation Shift Relation'
    _order = 'waterconnection_id'

    waterconnection_id = fields.Many2one(
        string='Waterconnection Code',
        comodel_name='wua.waterconnection',
        required=True,
        index=True,
        ondelete='cascade')

    irrigation_shift_id = fields.Many2one(
        string='Irrigation Shift',
        comodel_name='wua.waterconnection.irrigation.shift',
        required=True,
        index=True,
        ondelete='cascade')

    name = fields.Char(
        string='Name',
        related='irrigation_shift_id.name')

    description = fields.Char(
        string='Description',
        related='irrigation_shift_id.description')

    notes = fields.Html(
        string='Notes',
        related='irrigation_shift_id.notes')
