# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    intakeconsumption_ids = fields.One2many(
        string='Intake Consumptions',
        comodel_name='wua.intakeconsumption',
        inverse_name='agriculturalseason_id')

    number_of_intakeconsumptions = fields.Integer(
        string='Number of intake cons.',
        store=True,
        compute='_compute_number_of_intakeconsumptions')

    total_volume = fields.Float(
        string='Total volume',
        digits=(32, 4),
        store=True,
        compute='_compute_total_volume')

    @api.depends('intakeconsumption_ids')
    def _compute_number_of_intakeconsumptions(self):
        for record in self:
            number_of_intakeconsumptions = 0
            if record.intakeconsumption_ids:
                number_of_intakeconsumptions = \
                    len(record.intakeconsumption_ids)
            record.number_of_intakeconsumptions = number_of_intakeconsumptions

    @api.depends('intakeconsumption_ids')
    def _compute_total_volume(self):
        for record in self:
            total_volume = 0.0
            if record.intakeconsumption_ids:
                for intake_consumption_id in record.intakeconsumption_ids:
                    if intake_consumption_id.volume_real:
                        total_volume += intake_consumption_id.volume_real
            record.total_volume = total_volume
