# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    fertconsumption_ids = fields.One2many(
        string='Fertilizers',
        comodel_name='wua.fertconsumption',
        inverse_name='presconsumption_id')

    number_of_fertconsumptions = fields.Integer(
        string='Uses of fert.',
        store=True,
        compute='_compute_number_of_fertconsumptions')

    with_fertconsumptions = fields.Boolean(
        string='With fertilizers',
        store=True,
        compute='_compute_with_fertconsumptions')

    @api.depends('fertconsumption_ids')
    def _compute_number_of_fertconsumptions(self):
        for record in self:
            number_of_fertconsumptions = 0
            if record.fertconsumption_ids:
                number_of_fertconsumptions = len(record.fertconsumption_ids)
            record.number_of_fertconsumptions = number_of_fertconsumptions

    @api.depends('fertconsumption_ids')
    def _compute_with_fertconsumptions(self):
        for record in self:
            with_fertconsumptions = False
            if record.fertconsumption_ids and len(record.fertconsumption_ids):
                with_fertconsumptions = True
            record.with_fertconsumptions = with_fertconsumptions
