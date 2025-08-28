# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WizardGenerateControlPeriods(models.TransientModel):
    _name = 'wizard.generate.controlperiods'
    _description = 'Dialog box to generate control periods'

    agriculturalseason_name = fields.Char(
        string='Agricultural Season',
        readOnly=True)

    initial_date = fields.Date(
        string='Initial Date',
        required=True)

    end_date = fields.Date(
        string='End Date',
        required=True)

    interval = fields.Integer(
        string='Interval (days)',
        required=True)

    @api.model
    def default_get(self, var_fields):
        current_agriculturalseason_data = \
            self.get_current_agriculturalseason_data()
        return current_agriculturalseason_data

    @api.multi
    def generate_controlperiods(self):
        self.ensure_one()
        if len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        if agriculturalseason:
            if self.initial_date > self.end_date:
                raise exceptions.UserError(_('Incorrect dates.'))
            if self.interval <= 0:
                raise exceptions.UserError(_('Incorrect interval.'))
            if (self.initial_date < agriculturalseason.initial_date or
               self.end_date > agriculturalseason.end_date):
                raise exceptions.UserError(_('The range of dates must be '
                                             'within the agricultural '
                                             'season.'))
            self.create_controlperiods(agriculturalseason, self.initial_date,
                                       self.end_date, self.interval)

    def get_current_agriculturalseason_data(self):
        agriculturalseason_name = ''
        initial_date = fields.datetime.now()
        end_date = initial_date
        interval = 0
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        if agriculturalseason:
            initial_date_str = self.env['wua.parcel'].\
                transform_date_to_locale(agriculturalseason.initial_date)
            end_date_str = self.env['wua.parcel'].\
                transform_date_to_locale(agriculturalseason.end_date)
            if agriculturalseason.description != '':
                agriculturalseason_name = initial_date_str + ' - ' + \
                    end_date_str + ' ' + \
                    '[' + agriculturalseason.description + ']'
            else:
                agriculturalseason_name = initial_date_str + ' - ' + \
                    end_date_str
            initial_date = agriculturalseason.initial_date
            end_date = agriculturalseason.end_date
            interval = 7
        resp = {
            'agriculturalseason_name': agriculturalseason_name,
            'initial_date': initial_date,
            'end_date': end_date,
            'interval': interval,
            }
        return resp

    def create_controlperiods(self, agriculturalseason,
                              initial_date, end_date, interval):
        initial_date = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        period_initial_date = initial_date
        period_end_date = initial_date + timedelta(days=interval-1)
        controlperiods = self.env['wua.controlperiod']
        while period_initial_date <= end_date and period_end_date <= end_date:
            controlperiods.create({
                'initial_date': period_initial_date.strftime('%Y-%m-%d'),
                'end_date': period_end_date.strftime('%Y-%m-%d'),
                'agriculturalseason_id': agriculturalseason.id
                })
            period_initial_date = \
                period_initial_date + timedelta(days=interval)
            period_end_date = \
                period_initial_date + timedelta(days=interval-1)
