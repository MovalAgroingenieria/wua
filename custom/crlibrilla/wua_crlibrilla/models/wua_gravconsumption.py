# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'

    watering_duration_dechours = fields.Float(
        string='Time (Hour)',
        required=True,
        digits=(32, 1),
        default=0)

    @api.constrains('watering_duration_dechours')
    def check_watering_duration_dechours(self):
        entire_value = str(self.watering_duration_dechours).split('.')
        if (len(entire_value) > 1 and (entire_value[1] != '5' and
                                       entire_value[1] != '0')):
            error_msg = _('Decimal Time Value must be ,5 or ,0.')
            raise exceptions.ValidationError(error_msg)

    @api.onchange('watering_duration_dechours')
    def _onchange_watering_duration(self):
        for record in self:
            watering_duration = 0
            if (record.watering_duration_dechours):
                entire_value = str(self.watering_duration_dechours).split('.')
                watering_duration = watering_duration + \
                    int(entire_value[0]) * 60
                if (len(entire_value) > 1 and entire_value[1] == '5'):
                    watering_duration = watering_duration + 30
            record.watering_duration = watering_duration

    @api.model_cr
    def init(self):
        gravconsumptions = self.env['wua.gravconsumption'].search([])
        for gravcons in gravconsumptions:
            watering_duration_dechours = 0
            watering_duration_dechours = gravcons.watering_duration / 60
            remainder = gravcons.watering_duration % 60
            if (remainder != 0):
                if (remainder >= 15 and remainder < 45):
                    watering_duration_dechours = watering_duration_dechours + \
                        0.5
                elif (remainder >= 45):
                    watering_duration_dechours = watering_duration_dechours + \
                        1
            gravcons.watering_duration_dechours = watering_duration_dechours
