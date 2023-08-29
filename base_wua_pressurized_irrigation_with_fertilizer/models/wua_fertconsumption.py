# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _, exceptions


class WuaFertconsumption(models.Model):
    _name = 'wua.fertconsumption'
    _description = 'Entity (fertilizer consumption)'

    MAX_SIZE_NAME = 52

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        required=True,
        index=True,
        store=True,
        comodel_name='wua.waterconnection',
        ondelete='restrict')

    reading_initial_time = fields.Datetime(
        string='Reading Start Time',
        required=True,
        index=True)

    reading_end_time = fields.Datetime(
        string='Reading End Time',
        required=True,
        index=True)

    name = fields.Char(
        string='Fertilized Consumption',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    notes = fields.Html(string='Notes')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    amount = fields.Float(
        string='Amount',
        digits=(32, 4),
        store=True,
        required=True,
        index=True,
        default=0.0)

    presconsumption_id = fields.Many2one(
        string='Associated Consumption',
        comodel_name='wua.presconsumption',
        ondelete='restrict')

    validated = fields.Boolean(
        string='Validated Fertconsumption',
        default=True,
        required=True,
    )

    with_presconsumption = fields.Boolean(
        string='Water Consumption',
        store=True,
        compute='_compute_with_presconsumption')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        store=True,
        index=True,
        comodel_name='wua.irrigationshed',
        compute='_compute_irrigationshed_id',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        store=True,
        index=True,
        comodel_name='wua.hydraulicsector',
        compute='_compute_hydraulicsector_id',
        ondelete='restrict')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Fertconsumption.'),
        ('valid_reading_limits',
         'CHECK (reading_end_time >= reading_initial_time)',
         'The reading end time must be greather than or equal to '
         'reading initial time.'),
        ('valid_amount',
         'CHECK (amount >= 0)',
         'The consumption amount can not be a negative value.'),
        ]

    @api.depends('reading_end_time', 'waterconnection_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.reading_end_time:
                value = record.waterconnection_id.name + ' - ' + \
                    record.reading_end_time
            record.name = value

    @api.depends('reading_end_time')
    def _compute_agriculturalseason_id(self):
        agriculturalseasons = self.env['wua.agriculturalseason'].search([])
        for record in self:
            agr_season = None
            if record.reading_end_time:
                agr_season = agriculturalseasons.filtered(
                    lambda x:
                    record.reading_end_time >= x.initial_date and
                    record.reading_end_time <= x.end_date)
            record.agriculturalseason_id = agr_season

    @api.depends('presconsumption_id')
    def _compute_with_presconsumption(self):
        for record in self:
            with_presconsumption = False
            if record.presconsumption_id:
                with_presconsumption = True
            record.with_presconsumption = with_presconsumption

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            irrigationshed_id = None
            if record.waterconnection_id:
                irrigationshed_id = record.waterconnection_id.irrigationshed_id
            record.irrigationshed_id = irrigationshed_id

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if record.waterconnection_id and \
                    record.waterconnection_id.hydraulicsector_id:
                hydraulicsector_id = \
                    record.waterconnection_id.hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.multi
    def validate_fertconsumption(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_fertconsumption(self):
        self.ensure_one()
        self.validated = False

    def validate_fertconsumptions(self, active_fertconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        fertconsumptions = self.env['wua.fertconsumption'].browse(
            active_fertconsumptions)
        for fertconsumption in fertconsumptions:
            if not fertconsumption.validated:
                fertconsumption.validate_fertconsumption()

    def cancel_fertconsumptions(self, active_fertconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        fertconsumptions = self.env['wua.fertconsumption'].browse(
            active_fertconsumptions)
        for fertconsumption in fertconsumptions:
            if fertconsumption.validated:
                fertconsumption.cancel_fertconsumption()

    @api.model
    def create(self, vals):
        if ('presconsumption_id' in vals and vals['presconsumption_id']):
            presconsumption = self.env['wua.presconsumption'].browse(
                vals['presconsumption_id'])
            vals['reading_initial_time'] = presconsumption.reading_initial_time
            vals['reading_end_time'] = presconsumption.reading_end_time
            vals['waterconnection_id'] = presconsumption.waterconnection_id.id
        waterconnection_id = vals['waterconnection_id']
        reading_end_time = vals['reading_end_time']
        exists_fertconsumption = self.search([
            ('waterconnection_id', '=', waterconnection_id),
            ('reading_end_time', '=', reading_end_time)])
        if exists_fertconsumption:
            while exists_fertconsumption and \
                    not (exists_fertconsumption.id == self.id):
                reading_end_time = datetime.datetime.strptime(
                    reading_end_time, '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(seconds=1)
                reading_end_time = \
                    reading_end_time.strftime('%Y-%m-%d %H:%M:%S')
                exists_fertconsumption = self.search(
                    [('waterconnection_id', '=', waterconnection_id),
                     ('reading_end_time', '=', reading_end_time)])
            vals['reading_end_time'] = reading_end_time
        return super(WuaFertconsumption, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('presconsumption_id' in vals and vals['presconsumption_id']):
            presconsumption = self.env['wua.presconsumption'].browse(
                vals['presconsumption_id'])
            vals['reading_initial_time'] = presconsumption.reading_initial_time
            vals['reading_end_time'] = presconsumption.reading_end_time
            vals['waterconnection_id'] = presconsumption.waterconnection_id.id
        if (
            ('waterconnection_id' in vals and vals['waterconnection_id']) or
                ('reading_end_time' in vals and vals['reading_end_time'])):
            if ('waterconnection_id' in vals and vals['waterconnection_id']):
                waterconnection_id = vals['waterconnection_id']
            else:
                waterconnection_id = self.waterconnection_id.id
            if ('reading_end_time' in vals and vals['reading_end_time']):
                reading_end_time = vals['reading_end_time']
            else:
                reading_end_time = self.reading_end_time
            exists_fertconsumption = self.search([
                ('waterconnection_id', '=', waterconnection_id),
                ('reading_end_time', '=', reading_end_time)])
            if exists_fertconsumption:
                while exists_fertconsumption and exists_fertconsumption:
                    reading_end_time = datetime.datetime.strptime(
                        reading_end_time, '%Y-%m-%d %H:%M:%S') + \
                        datetime.timedelta(seconds=1)
                    reading_end_time = \
                        reading_end_time.strftime('%Y-%m-%d %H:%M:%S')
                    exists_fertconsumption = self.search(
                        [('waterconnection_id', '=', waterconnection_id),
                         ('reading_end_time', '=', reading_end_time)])
                vals['reading_end_time'] = reading_end_time
        resp = super(WuaFertconsumption, self).write(vals)
        return resp

    @api.onchange('presconsumption_id')
    def _onchange_presconsumption_id(self):
        for record in self:
            if record.presconsumption_id:
                record.reading_initial_time = \
                    record.presconsumption_id.reading_initial_time
                record.reading_end_time = \
                    record.presconsumption_id.reading_end_time
                record.waterconnection_id = \
                    record.presconsumption_id.waterconnection_id

    def action_assign_agriculturalseason_to_fertconsumptions(self):
        fertconsumptions = self.env['wua.fertconsumption']
        all_fertconsumptions = fertconsumptions.search([])
        all_fertconsumptions.write({
            'agriculturalseason_id': None,
            })
        agriculturalseasons = self.env['wua.agriculturalseason'].search([])
        for agriculturalseason in agriculturalseasons:
            fertconsumptions_of_current_season = fertconsumptions.search(
                [('reading_end_time', '>=', agriculturalseason.initial_date),
                 ('reading_end_time', '<=', agriculturalseason.end_date)])
            if len(fertconsumptions_of_current_season) > 0:
                fertconsumptions_of_current_season.write({
                    'agriculturalseason_id': agriculturalseason.id,
                    })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fertconsumptions'),
            'res_model': 'wua.fertconsumption',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
