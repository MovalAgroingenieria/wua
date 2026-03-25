# -*- coding: utf-8 -*-
# 2019 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _name = 'wua.agriculturalseason'
    _description = 'Entity (agricultural season)'
    _order = 'name'

    # Size of fields "name" and "description".
    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 75

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    end_date = fields.Date(
        string='End Date',
        default=lambda self: fields.datetime.now() + timedelta(days=364),
        required=True,
        index=True)

    name = fields.Char(
        string='Agricultural Season',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    description = fields.Char(
        string='Description',
        required=True,
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    active_agriculturalseason = fields.Boolean(
        string="Active",
        required=True,
        default=False,
        index=True,
        help="Indicate if this agricultural season is active")

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Agricultural Season.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date

    @api.constrains('description')
    def _check_name(self):
        description_no_blanks = self.description.strip()
        if description_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value (description).'))

    @api.model
    def create(self, vals):
        # Check if there is already an active agricultural season
        if ('active_agriculturalseason' in vals and
           vals['active_agriculturalseason']):
            active_agriculturalseasons = \
                self.env['wua.agriculturalseason'].search(
                    [('active_agriculturalseason', '=', True)])
            if active_agriculturalseasons:
                raise exceptions.ValidationError(
                    _('An active agricultural season already exists.'))
        self.refine_description(vals)
        non_duration_greather_than_one_year = \
            self.test_non_duration_greather_than_one_year(
                vals['initial_date'], vals['end_date'])
        if not non_duration_greather_than_one_year:
            raise exceptions.UserError(_('The duration of an agricultural '
                                         'season can not be longer than one '
                                         'year.'))
        non_overlapping_agriculturalseason = \
            self.test_non_overlapping_agriculturalseason(
                vals['initial_date'], vals['end_date'])
        if not non_overlapping_agriculturalseason:
            raise exceptions.UserError(_('The agricultural season is '
                                         'overlapped on another season.'))
        return super(WuaAgriculturalseason, self).create(vals)

    @api.multi
    def write(self, vals):
        # Check if there is already an active agricultural season
        if ('active_agriculturalseason' in vals and
           vals['active_agriculturalseason']):
            active_agriculturalseasons = \
                self.env['wua.agriculturalseason'].search(
                    [('active_agriculturalseason', '=', True),
                     ('id', '!=', self.id)])
            if active_agriculturalseasons:
                raise exceptions.ValidationError(
                    _('An active agricultural season already exists.'))
        if 'description' in vals:
            self.refine_description(vals)
        if 'initial_date' in vals or 'end_date' in vals:
            if 'initial_date' in vals:
                initial_date = vals['initial_date']
            else:
                initial_date = self.initial_date
            if 'end_date' in vals:
                end_date = vals['end_date']
            else:
                end_date = self.end_date
            non_duration_greather_than_one_year = \
                self.test_non_duration_greather_than_one_year(
                    initial_date, end_date)
            if not non_duration_greather_than_one_year:
                raise exceptions.UserError(_('The duration of an agricultural '
                                             'season can not be longer than '
                                             'one year.'))
            non_overlapping_agriculturalseason = \
                self.test_non_overlapping_agriculturalseason(
                    initial_date, end_date, self.id)
            if not non_overlapping_agriculturalseason:
                raise exceptions.UserError(_('The agricultural season is '
                                             'overlapped on another season.'))
        return super(WuaAgriculturalseason, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.end_date)
            if record.description != '':
                name = initial_date_str + ' - ' + end_date_str + ' ' + \
                    '(' + record.description + ')'
            else:
                name = name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    def refine_description(self, vals):
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})

    def test_non_duration_greather_than_one_year(
            self, initial_date, end_date):
        is_ok = True
        if initial_date and end_date:
            initial_date = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            is_ok = (end_date - initial_date).days + 1 <= 366
        return is_ok

    def test_non_overlapping_agriculturalseason(
            self,
            initial_date, end_date,
            agriculturalseason_id_to_exclude=0):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [('id', '!=', agriculturalseason_id_to_exclude)])
        is_ok = True
        for agriculturalseason in agriculturalseasons:
            not_overlapped = \
                ((agriculturalseason.initial_date < initial_date and
                  agriculturalseason.end_date < initial_date) or
                 (agriculturalseason.initial_date > end_date and
                  agriculturalseason.end_date > end_date))
            if not not_overlapped:
                is_ok = False
                break
        return is_ok
