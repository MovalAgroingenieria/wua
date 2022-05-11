# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    has_default_field_irrigationreport_intake_id = fields.Boolean(
        string='Has default intake for fields irrigationreport',
        help='If active you can choose a default intake.')

    default_field_irrigationreport_intake_id = fields.Many2one(
        comodel_name='wua.intake',
        string='Default intake for fields irrigationreport',
        help='Value that will be setted in all the fields irrigationreport.')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'has_default_field_irrigationreport_intake_id',
                           self.has_default_field_irrigationreport_intake_id)
        values.set_default('wua.irrigation.configuration',
                           'default_field_irrigationreport_intake_id',
                           self.default_field_irrigationreport_intake_id.id)
        super(WuaIrrigationConfiguration, self).set_default_values()
