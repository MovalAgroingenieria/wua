# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntakeconsumption(models.Model):
    _inherit = 'wua.intakeconsumption'

    name = fields.Char(
        size=30)

    validated = fields.Boolean(
        string='Validated',
        store=True,
        compute='_compute_validated')

    is_toll = fields.Boolean(
        string='Toll Reading',
        index=True,
        store=True,
        compute='_compute_is_toll')

    @api.depends('flowreading_id', 'flowreading_id.validated')
    def _compute_validated(self):
        for record in self:
            validated = False
            if record.flowreading_id.validated:
                validated = True
            record.validated = validated

    @api.depends('flowreading_id', 'flowreading_id.is_toll')
    def _compute_is_toll(self):
        for record in self:
            is_toll = False
            if record.flowreading_id:
                is_toll = record.flowreading_id.is_toll
            record.is_toll = is_toll

    @api.depends('flowmeter_id', 'flowreading_id', 'flowreading_id.intake_id')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if (record.flowreading_id and record.flowreading_id.intake_id):
                intake_id = record.flowreading_id.intake_id
            elif (record.flowmeter_id and record.flowmeter_id.intake_id):
                intake_id = record.flowmeter_id.intake_id
            record.intake_id = intake_id

    def _compute_name(self):
        for record in self:
            name = ''
            if (record.intake_id and record.intake_id.intake_code and
                    record.reading_end_time):
                name_first_part = '0' * \
                    (6-len(str(record.intake_id.intake_code))) \
                    + str(record.intake_id.intake_code)
                name = name_first_part + ' - ' + record.reading_end_time
                if record.flowreading_id.is_toll:
                    name = name + ' -'
            record.name = name
