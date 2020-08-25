# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaWateringperiod(models.Model):
    _name = 'wua.wateringperiod'
    _description = 'Entity (watering period)'
    _order = 'name'

    # Size of fields
    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 40

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    end_date = fields.Date(
        string='End Date',
        required=True)

    name = fields.Char(
        string='Watering Period',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ], string='State',
        index=True,
        default='closed')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict')

    year = fields.Integer(
        string='Year',
        store=True,
        compute='_compute_year')

    notes = fields.Html(string='Notes')

    watering_ids = fields.One2many(
        string='Waterings',
        comodel_name='wua.watering',
        inverse_name='wateringperiod_id')

    number_of_waterings = fields.Integer(
        string='Number of waterings',
        store=True,
        compute='_compute_number_of_waterings')

    wateringrequest_ids = fields.One2many(
        string='Watering Requests',
        comodel_name='wua.wateringrequest',
        inverse_name='wateringperiod_id')

    number_of_requests = fields.Integer(
        string='Number of requests',
        store=True,
        compute='_compute_number_of_requests')

    publication_permission = fields.Boolean(
        string='Publication Permis.',
        help='Extra condition: The period will only be publishable if his '
             'state is closed',
        default=False)

    publishable = fields.Boolean(
        string='Publishable',
        store=True,
        compute='_compute_publishable')

    predicted_watering = fields.Boolean(
        string='Predicted Watering',
        default=True,
        required=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Watering Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date

    @api.depends('initial_date')
    def _compute_year(self):
        for record in self:
            if record.initial_date:
                record.year = int(record.initial_date[:4])
            else:
                record.year = 0

    @api.depends('watering_ids')
    def _compute_number_of_waterings(self):
        for record in self:
            record.number_of_waterings = \
                len(record.watering_ids)

    @api.depends('wateringrequest_ids')
    def _compute_number_of_requests(self):
        for record in self:
            record.number_of_requests = \
                len(record.wateringrequest_ids)

    @api.depends('publication_permission', 'state')
    def _compute_publishable(self):
        for record in self:
            record.publishable = record.publication_permission and \
                record.state == 'closed'

    @api.model
    def create(self, vals):
        if not vals['predicted_watering']:
            vals['state'] = 'closed'
        agriculturalseason_id = vals['agriculturalseason_id']
        initial_date = vals['initial_date']
        end_date = vals['end_date']
        range_of_dates_within_agriculturalseason = \
            self.test_range_of_dates_within_agriculturalseason(
                agriculturalseason_id, initial_date, end_date)
        if not range_of_dates_within_agriculturalseason:
            raise exceptions.UserError(_('The watering period is outside '
                                         'his agricultural season.'))
        non_overlapping_wateriorperiod = \
            self.test_non_overlapping_wateriorperiod(
                agriculturalseason_id, initial_date, end_date)
        if not non_overlapping_wateriorperiod:
            raise exceptions.UserError(_('The watering period is overlapped '
                                         'on another period.'))
        return super(WuaWateringperiod, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'predicted_watering' in vals:
            if not vals['predicted_watering']:
                vals['state'] = 'closed'
        if ('agriculturalseason_id' in vals or
           'initial_date' in vals or 'end_date' in vals):
            if 'agriculturalseason_id' in vals:
                agriculturalseason_id = vals['agriculturalseason_id']
            else:
                agriculturalseason_id = self.agriculturalseason_id.id
            if 'initial_date' in vals:
                initial_date = vals['initial_date']
            else:
                initial_date = self.initial_date
            if 'end_date' in vals:
                end_date = vals['end_date']
            else:
                end_date = self.end_date
            range_of_dates_within_agriculturalseason = \
                self.test_range_of_dates_within_agriculturalseason(
                    agriculturalseason_id, initial_date, end_date)
            if not range_of_dates_within_agriculturalseason:
                raise exceptions.UserError(_('The watering period is outside '
                                             'his agricultural season.'))
            non_overlapping_wateriorperiod = \
                self.test_non_overlapping_wateriorperiod(
                    agriculturalseason_id, initial_date, end_date, self.id)
            if not non_overlapping_wateriorperiod:
                raise exceptions.UserError(_('The watering period is '
                                             'overlapped on another period.'))
        return super(WuaWateringperiod, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.end_date, '%Y-%m-%d').strftime('%x')
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def open_period(self):
        self.ensure_one()
        if not self.predicted_watering:
            raise exceptions.UserError(_('It is not possible to '
                                         'reopen the period, because '
                                         'there is no a predicted '
                                         'watering.'))
        if self.number_of_waterings > 0:
            waterings = self.watering_ids
            all_waterings_are_validated = True
            for watering in waterings:
                if watering.state != 'validated':
                    all_waterings_are_validated = False
                    break
            if all_waterings_are_validated:
                raise exceptions.UserError(_('It is not possible to '
                                             'reopen the period, because '
                                             'all the waterings are '
                                             'validated.'))
        self.state = 'open'

    @api.multi
    def close_period(self):
        self.ensure_one()
        self.state = 'closed'

    @api.multi
    def action_see_waterings(self):
        self.ensure_one()
        condition = [('wateringperiod_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_form').id
        id_tree_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_tree').id
        search_view = self.env.ref('base_wua_gravity_irrigation.'
                                   'wua_watering_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterings'),
            'res_model': 'wua.watering',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def set_as_open(self, active_wateringperiods):
        wateringperiods = self.env['wua.wateringperiod'].browse(
            active_wateringperiods)
        for record in wateringperiods:
            if not record.predicted_watering:
                raise exceptions.UserError(_('It is not possible to '
                                             'reopen a period, because '
                                             'there is no a predicted '
                                             'watering.'))
            if record.number_of_waterings > 0:
                waterings = record.watering_ids
                all_waterings_are_validated = True
                for watering in waterings:
                    if watering.state != 'validated':
                        all_waterings_are_validated = False
                        break
                if all_waterings_are_validated:
                    raise exceptions.UserError(_('It is not possible to '
                                                 'reopen the period, because '
                                                 'all the waterings are '
                                                 'validated.'))
            vals = {
                'state': 'open',
                }
            record.write(vals)

    @api.multi
    def set_as_close(self, active_wateringperiods):
        wateringperiods = self.env['wua.wateringperiod'].browse(
            active_wateringperiods)
        for record in wateringperiods:
            vals = {
                'state': 'closed',
                }
            record.write(vals)

    def test_range_of_dates_within_agriculturalseason(self,
                                                      agriculturalseason_id,
                                                      initial_date, end_date):
        is_ok = False
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            agriculturalseason_id)
        if agriculturalseason:
            is_ok = (initial_date >= agriculturalseason.initial_date and
                     end_date <= agriculturalseason.end_date)
        return is_ok

    def test_non_overlapping_wateriorperiod(self,
                                            agriculturalseason_id,
                                            initial_date, end_date,
                                            wateringperiod_id_to_exclude=0):
        is_ok = False
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            agriculturalseason_id)
        if agriculturalseason:
            wateringperiods = self.env['wua.wateringperiod'].search(
                [('agriculturalseason_id', '=', agriculturalseason_id),
                 ('id', '!=', wateringperiod_id_to_exclude)])
            is_ok = True
            for wateringperiod in wateringperiods:
                not_overlapped = \
                    ((wateringperiod.initial_date < initial_date and
                      wateringperiod.end_date < initial_date) or
                     (wateringperiod.initial_date > end_date and
                      wateringperiod.end_date > end_date))
                if not not_overlapped:
                    is_ok = False
                    break
        return is_ok
