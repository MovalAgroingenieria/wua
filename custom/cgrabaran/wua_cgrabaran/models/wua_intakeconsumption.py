# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntakeconsumption(models.Model):
    _inherit = 'wua.intakeconsumption'

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
