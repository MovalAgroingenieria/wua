# -*- coding: utf-8 -*-
# 2021 Moval Agroingniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        index=True,
        store=True,
        compute="_compute_intake_id")

    @api.depends('irrigationditch_id', 'irrigationditch_id.intake_id')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if (record.irrigationditch_id):
                intake_id = record.irrigationditch_id.intake_id
            record.intake_id = intake_id
