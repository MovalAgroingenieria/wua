# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, _


class WuaWaterpipeconsumption(models.Model):
    _name = 'wua.waterpipeconsumption'
    _description = 'Entity (waterpipe consumption)'
    _order = 'reading_end_time desc, name'

    name = fields.Char(
        string='Waterpipe Flow-Meter Consumption',
        index=True,
        store=True,
        compute="_compute_name",
        size=28)

    reading_initial_time = fields.Datetime(
        string='Reading Start Time',
        required=True,
        index=True,
        readonly=True,
        default=lambda self: fields.datetime.now())

    initial_volume = fields.Float(
        string='Initial Value (m3)',
        required=True,
        readonly=True,
        default=0,
        digits=(32, 4))

    reading_end_time = fields.Datetime(
        string='Reading End Time',
        required=True,
        index=True,
        readonly=True,
        default=lambda self: fields.datetime.now())

    end_volume = fields.Float(
        string='Final Value (m3)',
        required=True,
        readonly=True,
        default=0,
        digits=(32, 4))

    volume = fields.Float(
        string='Gross Value (m3)',
        store=True,
        digits=(32, 4),
        compute='_compute_volume')

    waterpipeflowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.waterpipeflowreading',
        inverse_name='waterpipeconsumption_id')

    waterpipeflowreading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.waterpipeflowreading',
        ondelete='cascade',
        store=True,
        compute='_compute_waterpipeflowreading_id')

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
        ondelete='restrict',
        store=True,
        compute='_compute_flowmeter_id')

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        index=True,
        comodel_name='wua.waterpipe',
        ondelete='restrict',
        store=True,
        compute='_compute_waterpipe_id')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        index=True,
        comodel_name='wua.agriculturalseason',
        ondelete='restrict')

    adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        required=True,
        digits=(32, 4),
        default=0)

    volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume_real')

    notes = fields.Html(
        string="Notes",
        help="Notes about waterpipe consumption")

    validated = fields.Boolean(
        string='Validated Consumption',
        store=True,
        compute='_compute_validated')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing waterpipe consumption identifier.'),
        ('volume',
         'CHECK (volume >= 0)',
         'Volume of water can\'t be negative.'),
        ('reading_time',
         'CHECK (reading_end_time >= reading_initial_time)',
         'The reading end time can\'t be lower than the reading start time.'),
    ]

    @api.depends('initial_volume', 'end_volume')
    def _compute_volume(self):
        for record in self:
            record.volume = record.end_volume - record.initial_volume

    @api.depends('waterpipeflowreading_ids')
    def _compute_waterpipeflowreading_id(self):
        for record in self:
            waterpipeflowreading_id = None
            if record.waterpipeflowreading_ids:
                waterpipeflowreading_id = record.waterpipeflowreading_ids[0]
            record.waterpipeflowreading_id = waterpipeflowreading_id

    @api.depends('waterpipeflowreading_id')
    def _compute_flowmeter_id(self):
        for record in self:
            flowmeter_id = None
            if (record.waterpipeflowreading_id and
                    record.waterpipeflowreading_id.flowmeter_id):
                flowmeter_id = record.waterpipeflowreading_id.flowmeter_id
            record.flowmeter_id = flowmeter_id

    @api.depends('flowmeter_id')
    def _compute_waterpipe_id(self):
        for record in self:
            waterpipe_id = None
            if record.flowmeter_id and record.flowmeter_id.waterpipe_id:
                waterpipe_id = record.flowmeter_id.waterpipe_id
            record.waterpipe_id = waterpipe_id

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('waterpipe_id', 'reading_end_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.waterpipe_id and record.waterpipe_id.waterpipe_code and
                    record.reading_end_time):
                name_first_part = '0' * \
                    (6-len(str(record.waterpipe_id.waterpipe_code))) \
                    + str(record.waterpipe_id.waterpipe_code)
                name = name_first_part + ' - ' + record.reading_end_time
            record.name = name

    @api.depends('waterpipeflowreading_id', 'waterpipeflowreading_id.validated')
    def _compute_validated(self):
        for record in self:
            validated = False
            if (record.waterpipeflowreading_id and
               record.waterpipeflowreading_id.validated):
                validated = True
            record.validated = validated

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            waterpipe_name = record.waterpipe_id.name
            reading_end_time = \
                fields.Datetime.from_string(record.reading_end_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_end_time)
                reading_end_time = reading_end_time + offset
            reading_end_time_str = str(reading_end_time)
            date_str = reading_end_time_str[:10]
            hour_str = reading_end_time_str[-8:]
            name = waterpipe_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [('initial_date', '<=', vals['reading_end_time']),
             ('end_date', '>=', vals['reading_end_time'])])
        if (len(agriculturalseasons) == 1):
            vals['agriculturalseason_id'] = agriculturalseasons[0].id
        return super(WuaWaterpipeconsumption, self).create(vals)

    def action_assign_agriculturalseason_to_waterpipeconsumptions(self):
        waterpipeconsumptions = self.env['wua.waterpipeconsumption']
        all_waterpipeconsumptions = waterpipeconsumptions.search([])
        all_waterpipeconsumptions.write({
            'agriculturalseason_id': None,
            })
        agriculturalseasons = self.env['wua.agriculturalseason'].search([])
        for agriculturalseason in agriculturalseasons:
            waterpipeconsumptions_of_current_season = \
                waterpipeconsumptions.search(
                    [('reading_end_time', '>=',
                      agriculturalseason.initial_date),
                     ('reading_end_time', '<=', agriculturalseason.end_date)])
            if len(waterpipeconsumptions_of_current_season) > 0:
                waterpipeconsumptions_of_current_season.write({
                    'agriculturalseason_id': agriculturalseason.id,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Waterpipe Consumptions'),
            'res_model': 'wua.waterpipeconsumption',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
