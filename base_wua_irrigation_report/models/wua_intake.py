# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    irrigationreport_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.irrigationreport",
        inverse_name="intake_id")

    number_of_irrigationreports = fields.Integer(
        string="N. of Irrig. Reports",
        index=True,
        store=True,
        compute="_compute_number_of_irrigationreports")

    @api.depends('irrigationreport_ids')
    def _compute_number_of_irrigationreports(self):
        for record in self:
            record.number_of_irrigationreports = \
                len(record.irrigationreport_ids)
