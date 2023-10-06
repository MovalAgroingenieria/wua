# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaTankconsumption(models.Model):
    _name = 'wua.tankconsumption'
    _description = 'Tank Consumptions'
    _order = 'end_time desc, name'

    tank_id = fields.Many2one(
        string='Tank',
        comodel_name='wua.tank',
        required=True,
        index=True)

    initial_time = fields.Datetime(
        string='Start filling',
        required=True,
        index=True)

    end_time = fields.Datetime(
        string='End filling',
        required=True,
        index=True)

    name = fields.Char(
        string='Tank Consumption',
        store=True,
        index=True,
        compute='_compute_name')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True)

    volume_request = fields.Float(
        string='Vol. requested (m³)',
        digits=(32, 4),
        required=True)

    volume_real = fields.Float(
        string='Vol. consumed (m³)',
        digits=(32, 4),
        required=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        store=True,
        ondelete='restrict',
        compute='_compute_hydraulicsector_id')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    validated = fields.Boolean(
        string='Validated',
        default=True)

    notes = fields.Html(
        string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Tank Consumption.'),
        ('valid_time_limits', 'CHECK (end_time >= initial_time)',
         'The end time must be greater than or equal to initial time.'),
        ('valid_volume_real', 'CHECK (volume_real >= 0)',
         'The consumed volume can not be a negative value.'), ]

    @api.depends('end_time', 'tank_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.tank_id and record.end_time:
                value = record.tank_id.name + ' - ' + record.end_time
            record.name = value

    @api.depends('tank_id', 'tank_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.tank_id.hydraulicsector_id

    @api.depends('end_time')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason = None
            if record.end_time and record.initial_time:
                agriculturalseason = self.env['wua.agriculturalseason'].search(
                    [('end_date', '>=', record.end_time),
                     ('initial_date', '<=', record.initial_time)],)[0]
            record.agriculturalseason_id = agriculturalseason

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            tank_name = record.tank_id.name
            end_time = \
                fields.Datetime.from_string(record.end_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(end_time)
                end_time = end_time + offset
            end_time_str = str(end_time)
            date_str = end_time_str[:10]
            hour_str = end_time_str[-8:]
            name = tank_name + ' - ' + datetime.datetime.strptime(
                date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result

    @api.multi
    def validate_tankconsumption(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_tankconsumption(self):
        # @TODO: control invoiced tankconsumption
        self.ensure_one()
        self.validated = False

    def validate_tankconsumptions(self, active_tankconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        tankconsumptions = \
            self.env['wua.tankconsumption'].browse(active_tankconsumptions)
        for tankconsumption in tankconsumptions:
            if not tankconsumption.validated:
                tankconsumption.validate_tankconsumption()

    def cancel_tankconsumptions(self, active_tankconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        tankconsumptions = \
            self.env['wua.tankconsumption'].browse(active_tankconsumptions)
        for tankconsumption in tankconsumptions:
            if tankconsumption.validated:
                tankconsumption.cancel_tankconsumption()

    def action_assign_agriculturalseason_to_tankconsumptions(self):
        self.env['wua.tankconsumption'].search(
            [])._compute_agriculturalseason_id()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tank consumptions'),
            'res_model': 'wua.tankconsumption',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
