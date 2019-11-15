# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntakeconsumption(models.Model):
    _name = 'wua.intakeconsumption'
    _description = 'Entity (intakeconsumption)'

    name = fields.Char(
        string='Flow-Meter Reading',
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

    flowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.flowreading',
        inverse_name='intakeconsumption_id')

    flowreading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.flowreading',
        ondelete='cascade',
        store=True,
        compute='_compute_flowreading_id')

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
        ondelete='restrict',
        store=True,
        compute='_compute_flowmeter_id')

    intake_id = fields.Many2one(
        string='Intake',
        index=True,
        comodel_name='wua.intake',
        ondelete='restrict',
        store=True,
        compute='_compute_intake_id')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
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
        help="Notes about intakeconsumption")

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing flow-reading identifier.'),
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
            volume = 0
            if record.initial_volume and record.end_volume:
                volume = record.end_volume - record.initial_volume
            record.volume = volume

    @api.depends('flowreading_ids')
    def _compute_flowreading_id(self):
        for record in self:
            flowreading_id = None
            if record.flowreading_ids:
                flowreading_id = record.flowreadings_ids[0]
            record.flowreading_id = flowreading_id

    @api.depends('flowreading_id')
    def _compute_flowmeter_id(self):
        for record in self:
            flowmeter_id = None
            if record.flowreading_id and record.flowreading_id.flowmeter_id:
                flowmeter_id = record.flowreadings_id.flowmeter_id
            record.flowmeter_id = flowmeter_id

    @api.depends('flowmeter_id')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if record.flowmeter_id and record.flowmeter_id.intake_id:
                intake_id = record.flowmeter_id.intake_id
            record.intake_id = intake_id

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            volume_real = None
            if record.volume and record.adjustement_volume:
                volume_real = record.volume + record.adjustement_volume
            record.volume_real = volume_real

    @api.depends('intake_id', 'reading_end_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.intake_id and record.intake_id.intake_code and
                    record.reading_end_time):
                name_first_part = '0' * (6-len(record.intake_id.intake_code)) \
                    + record.intake_id.intake_code
                name = name_first_part + ' - ' + record.reading_end_time
            record.name = name
