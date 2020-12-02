# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'

    watering_duration_dechours = fields.Float(
        string='Time (Hour)',
        required=True,
        digits=(32, 1),
        default=0)

    watering_duration_dechours_str = fields.Char(
        string='Duration (provisional)',
        compute='_compute_watering_duration_dechours_str')

    confirmed_request = fields.Boolean(
        string="Confirmed request",
        default=False)

    reported_time = fields.Boolean(
        string="Reported time",
        default=False)

    with_notes = fields.Boolean(
        string="With notes",
        compute="_compute_with_notes")

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

    @api.depends('watering_duration_dechours')
    def _compute_watering_duration_dechours_str(self):
        for record in self:
            watering_duration_dechours_str = ''
            if record.watering_duration_dechours > 0:
                watering_duration_dechours_str = \
                    str(record.watering_duration_dechours)
            record.watering_duration_dechours_str = \
                watering_duration_dechours_str

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

    @api.multi
    def change_to_confirmed(self):
        self.ensure_one()
        self.confirmed_request = True

    @api.multi
    def set_as_confirmed(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if not gravconsumption.confirmed_request:
                gravconsumption.change_to_confirmed()

    @api.multi
    def change_to_unconfirmed(self):
        self.ensure_one()
        self.confirmed_request = False

    @api.multi
    def set_as_unconfirmed(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if gravconsumption.confirmed_request:
                gravconsumption.change_to_unconfirmed()

    @api.multi
    def change_reported_time_to_confirmed(self):
        self.ensure_one()
        self.reported_time = True

    @api.multi
    def set_reported_time_as_confirmed(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if not gravconsumption.reported_time:
                gravconsumption.change_reported_time_to_confirmed()

    @api.multi
    def change_reported_time_to_unconfirmed(self):
        self.ensure_one()
        self.reported_time = False

    @api.multi
    def set_reported_time_as_unconfirmed(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if gravconsumption.reported_time:
                gravconsumption.change_reported_time_to_unconfirmed()

    @api.multi
    def _compute_with_notes(self):
        for record in self:
            if record.notes:
                record.with_notes = True
