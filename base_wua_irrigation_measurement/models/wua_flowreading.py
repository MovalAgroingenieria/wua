# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaFlowreading(models.Model):
    _name = 'wua.flowreading'
    _description = 'Entity (flowreading)'

    name = fields.Char(
        string='Flow-Meter Reading',
        index=True,
        store=True,
        compute="_compute_name",
        size=52)

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
        required=True,
        ondelete='restrict')

    reading_time = fields.Datetime(
        string='Time',
        required=True,
        default=lambda self: fields.datetime.now())

    volume = fields.Float(
        string='Value (m3)',
        digits=(32, 4),
        default=0)

    instant_flow = fields.Float(
        string='Flow (m3/h)',
        digits=(32, 4),
        default=0)

    initialization_reading = fields.Boolean(
        string='Initialization Reading',
        required=True,
        default=False)

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        ondelete='restrict',
        readonly=True)

    intakeconsumption_id = fields.Many2one(
        string='Intake Consumption',
        comodel_name='wua.intakeconsumption',
        ondelete='restrict',
        readonly=True)

    reading_of_intake = fields.Boolean(
        string='Reading of intake',
        store=True,
        compute='_compute_reading_of_intake')

    notes = fields.Html(
        string="Notes",
        help="Notes about flow-reading")

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing flow-reading identifier.'),
        ('volume',
         'CHECK (volume >= 0)',
         'Volume of water can\'t be negative.'),
        ]

    @api.depends('flowmeter_id', 'reading_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.flowmeter_id and record.reading_time:
                name = record.flowmeter_id.name + '-' + record.reading_time
            record.name = name

    @api.depends('intake_id')
    def _compute_reading_of_intake(self):
        for record in self:
            reading_of_intake = False
            if record.intake_id:
                reading_of_intake = True
            record.reading_of_intake = reading_of_intake
