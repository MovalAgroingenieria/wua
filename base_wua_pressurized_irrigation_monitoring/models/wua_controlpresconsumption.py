# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaControlpresconsumption(models.Model):
    _name = 'wua.controlpresconsumption'
    _description = 'Entity (pressurized consumption)'
    _order = 'reading_end_time desc, name'

    MAX_SIZE_NAME = 52

    controlreading_ids = fields.One2many(
        string='Control Readings',
        comodel_name='wua.controlreading',
        inverse_name='controlpresconsumption_id',
        readonly=True)

    controlreading_id = fields.Many2one(
        string='Control Reading',
        comodel_name='wua.controlreading',
        store=True,
        compute='_compute_controlreading_id',
        ondelete='cascade')

    reading_initial_time = fields.Datetime(
        string='Reading Start Time',
        readonly=True,
        index=True)

    initial_volume = fields.Float(
        string='Initial Value (m3)',
        digits=(32, 4),
        readonly=True)

    reading_end_time = fields.Datetime(
        string='Reading End Time',
        readonly=True,
        index=True)

    end_volume = fields.Float(
        string='Final Value (m3)',
        digits=(32, 4),
        readonly=True)

    volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume')

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        store=True,
        compute='_compute_watermeter_id',
        ondelete='restrict')

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        required=True,
        default=0)

    volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_volume_real')

    name = fields.Char(
        string='Pressurized Consumption',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    notes = fields.Html(string='Notes')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='set null')

    validated = fields.Boolean(
        string='Validated Consumption',
        store=True,
        compute='_compute_validated')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Consumption.'),
        ('valid_reading_limits',
         'CHECK (reading_end_time >= reading_initial_time)',
         'The reading end time must be greather than or equal to '
         'reading initial time.'),
        ('valid_volume',
         'CHECK (volume >= 0)',
         'The consumption volume can not be a negative value.'),
        ]

    @api.depends('controlreading_ids')
    def _compute_controlreading_id(self):
        for record in self:
            controlreading_id = None
            filtered_readings = self.env['wua.controlreading'].search([
                ('controlpresconsumption_id', '=', record.id)])
            if len(filtered_readings) == 1:
                controlreading_id = filtered_readings[0].id
                record.controlreading_id = controlreading_id

    @api.depends('initial_volume', 'end_volume')
    def _compute_volume(self):
        for record in self:
            record.volume = record.end_volume - record.initial_volume

    @api.depends('controlreading_id')
    def _compute_watermeter_id(self):
        for record in self:
            if record.controlreading_id.watermeter_id:
                correct_watermeter_id = \
                    record.controlreading_id.watermeter_id.state == 'active' \
                    and record.controlreading_id.watermeter_id.\
                    waterconnection_id
                if correct_watermeter_id:
                    record.watermeter_id = \
                        record.controlreading_id.watermeter_id
                else:
                    raise exceptions.UserError(
                        _('The water meter is mandatory, '
                          'it must be active and it must '
                          'have a water connection.'))

    @api.depends('watermeter_id')
    def _compute_hydraulic_infrastructure_data(self):
        for record in self:
            waterconnection_id_value = None
            irrigationshed_id_value = None
            hydraulicsector_value = None
            if record.watermeter_id:
                waterconnection_id_value = \
                    record.watermeter_id.waterconnection_id
                irrigationshed_id_value = \
                    record.watermeter_id.irrigationshed_id
                hydraulicsector_value = \
                    record.watermeter_id.hydraulicsector_id
            record.waterconnection_id = waterconnection_id_value
            record.irrigationshed_id = irrigationshed_id_value
            record.hydraulicsector_id = hydraulicsector_value

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('reading_end_time', 'waterconnection_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.reading_end_time:
                value = record.waterconnection_id.name + ' - ' + \
                    record.reading_end_time
            record.name = value

    @api.depends('controlreading_id', 'controlreading_id.validated')
    def _compute_validated(self):
        for record in self:
            validated = False
            if record.controlreading_id.validated:
                validated = True
            record.validated = validated

    @api.model
    def create(self, vals):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [('initial_date', '<=', vals['reading_end_time']),
             ('end_date', '>=', vals['reading_end_time'])])
        if len(agriculturalseasons) == 1:
            vals['agriculturalseason_id'] = agriculturalseasons[0].id
        return super(WuaControlpresconsumption, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            waterconnection_name = record.waterconnection_id.name
            reading_end_time = \
                fields.Datetime.from_string(record.reading_end_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_end_time)
                reading_end_time = reading_end_time + offset
            reading_end_time_str = str(reading_end_time)
            date_str = reading_end_time_str[:10]
            hour_str = reading_end_time_str[-8:]
            name = waterconnection_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result

    def action_assign_agriculturalseason_to_consumptions(self):
        controlpresconsumptions = self.env['wua.controlpresconsumption']
        all_controlpresconsumptions = controlpresconsumptions.search([])
        all_controlpresconsumptions.write({
            'agriculturalseason_id': None,
            })
        agriculturalseasons = self.env['wua.agriculturalseason'].search([])
        for agriculturalseason in agriculturalseasons:
            controlpresconsumptions_of_current_season = \
                controlpresconsumptions.search(
                    [('reading_end_time', '>=',
                        agriculturalseason.initial_date),
                     ('reading_end_time', '<=', agriculturalseason.end_date)])
            if len(controlpresconsumptions_of_current_season) > 0:
                controlpresconsumptions_of_current_season.write({
                    'agriculturalseason_id': agriculturalseason.id,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
