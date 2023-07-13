# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIndividualinputMassiveAssignment(models.Model):
    _inherit = 'wua.individualinput.massive.assignment'

    total_volume_hours = fields.Char(
        string='Total Volume (hours)',
        compute='_compute_total_volume_hours'
    )

    total_effective_volume_hours = fields.Char(
        string='Total Effective Volume (hours)',
        compute='_compute_total_effective_volume_hours')

    @api.depends('total_effective_volume')
    def _compute_total_effective_volume_hours(self):
        for record in self:
            total_effective_volume_hours = self.env['wua.quota'].\
                transform_to_quota_hours_format(record.total_effective_volume)
            record.total_effective_volume_hours = total_effective_volume_hours

    @api.depends('total_volume')
    def _compute_total_volume_hours(self):
        for record in self:
            total_volume_hours = self.env['wua.quota'].\
                transform_to_quota_hours_format(record.total_volume)
            record.total_volume_hours = total_volume_hours


class WuaIndividualinputMassiveAssignmentLine(models.Model):
    _inherit = 'wua.individualinput.massive.assignment.line'

    volume_hours = fields.Char(
        string='Volume (hours)',
        compute='_compute_volume_hours')

    effective_volume_hours = fields.Char(
        string='Effective Volume (hours)',
        compute='_compute_effective_volume_hours')

    @api.depends('volume')
    def _compute_volume_hours(self):
        for record in self:
            record.volume_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.volume)

    @api.depends('effective_volume')
    def _compute_effective_volume_hours(self):
        for record in self:
            record.effective_volume_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.effective_volume)
