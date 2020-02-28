# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WizardGenerateQuotaperiods(models.TransientModel):
    _name = 'wizard.generate.quotaperiods'
    _description = 'Dialog box to generate quota periods'

    MAX_QUOTA_PERIODS = 12

    agriculturalseason_name = fields.Char(
        string='Agricultural Season',
        readonly=True)

    quotaperiod_01_initial_date = fields.Date(
        string='Quota Period #1, initial_date',
        readonly=True)

    quotaperiod_01_description = fields.Char(
        string='Quota Period #1, description')

    quotaperiod_02_initial_date = fields.Date(
        string='Quota Period #2, initial_date')

    quotaperiod_02_description = fields.Char(
        string='Quota Period #2, description')

    quotaperiod_03_initial_date = fields.Date(
        string='Quota Period #3, initial_date')

    quotaperiod_03_description = fields.Char(
        string='Quota Period #3, description')

    quotaperiod_04_initial_date = fields.Date(
        string='Quota Period #4, initial_date')

    quotaperiod_04_description = fields.Char(
        string='Quota Period #4, description')

    quotaperiod_05_initial_date = fields.Date(
        string='Quota Period #5, initial_date')

    quotaperiod_05_description = fields.Char(
        string='Quota Period #5, description')

    quotaperiod_06_initial_date = fields.Date(
        string='Quota Period #6, initial_date')

    quotaperiod_06_description = fields.Char(
        string='Quota Period #6, description')

    quotaperiod_07_initial_date = fields.Date(
        string='Quota Period #7, initial_date')

    quotaperiod_07_description = fields.Char(
        string='Quota Period #7, description')

    quotaperiod_08_initial_date = fields.Date(
        string='Quota Period #8, initial_date')

    quotaperiod_08_description = fields.Char(
        string='Quota Period #8, description')

    quotaperiod_09_initial_date = fields.Date(
        string='Quota Period #9, initial_date')

    quotaperiod_09_description = fields.Char(
        string='Quota Period #9, description')

    quotaperiod_10_initial_date = fields.Date(
        string='Quota Period #10, initial_date')

    quotaperiod_10_description = fields.Char(
        string='Quota Period #10, description')

    quotaperiod_11_initial_date = fields.Date(
        string='Quota Period #11, initial_date')

    quotaperiod_11_description = fields.Char(
        string='Quota Period #11, description')

    quotaperiod_12_initial_date = fields.Date(
        string='Quota Period #12, initial_date')

    quotaperiod_12_description = fields.Char(
        string='Quota Period #12, description')

    @api.model
    def default_get(self, var_fields):
        current_agriculturalseason_data = \
            self._get_current_agriculturalseason_data()
        return current_agriculturalseason_data

    @api.multi
    def generate_quotaperiods(self):
        self.ensure_one()
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        quotaperiods = self._get_values_of_quotaperiods()
        if (quotaperiods and
           quotaperiods[-1]['initial_date'] < agriculturalseason.end_date):
            self._create_quotaperiods(agriculturalseason, quotaperiods)
        else:
            raise exceptions.ValidationError(_(
                'Incorrect dates: check sort and possible gaps.'))

    def _get_current_agriculturalseason_data(self):
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        initial_date_str = datetime.datetime.strptime(
            agriculturalseason.initial_date, '%Y-%m-%d').strftime('%x')
        end_date_str = datetime.datetime.strptime(
            agriculturalseason.end_date, '%Y-%m-%d').strftime('%x')
        if agriculturalseason.description != '':
            agriculturalseason_name = initial_date_str + ' - ' + \
                end_date_str + ' ' + \
                '[' + agriculturalseason.description + ']'
        else:
            agriculturalseason_name = initial_date_str + ' - ' + \
                end_date_str
        quotaperiod_01_initial_date = agriculturalseason.initial_date
        resp = {
            'agriculturalseason_name': agriculturalseason_name,
            'quotaperiod_01_initial_date': quotaperiod_01_initial_date,
            }
        return resp

    def _get_values_of_quotaperiods(self):
        resp = []
        error = False
        last_filled_field = self.MAX_QUOTA_PERIODS
        for i in range(self.MAX_QUOTA_PERIODS, 0, -1):
            if self._get_value_of_quotaperiod(i):
                last_filled_field = i
                break
        previous_date = ''
        for i in range(1, last_filled_field + 1):
            value_of_quotaperiod = self._get_value_of_quotaperiod(i)
            if not value_of_quotaperiod:
                error = True
                break
            if i > 1 and previous_date >= value_of_quotaperiod['initial_date']:
                error = True
                break
            previous_date = value_of_quotaperiod['initial_date']
            resp.append(value_of_quotaperiod)
        if error:
            resp = []
        return resp

    def _get_value_of_quotaperiod(self, index):
        resp = None
        field_name_for_initial_date = 'quotaperiod_' + str(index).zfill(2) + \
            '_initial_date'
        field_name_for_description = 'quotaperiod_' + str(index).zfill(2) + \
            '_description'
        initial_date = self[field_name_for_initial_date]
        description = self[field_name_for_description]
        if initial_date:
            resp = {'initial_date': initial_date, 'description': description}
        return resp

    def _create_quotaperiods(self, agriculturalseason, quotaperiods):
        size_of_quotaperiods = len(quotaperiods)
        for i in range(0, size_of_quotaperiods):
            initial_date = quotaperiods[i]['initial_date']
            if i == size_of_quotaperiods - 1:
                end_date = agriculturalseason.end_date
            else:
                end_date = datetime.datetime.strptime(
                    quotaperiods[i+1]['initial_date'], '%Y-%m-%d') + \
                    datetime.timedelta(days=-1)
                end_date = end_date.date()
            description = quotaperiods[i]['description']
            self.env['wua.quotaperiod'].create({
                'agriculturalseason_id': agriculturalseason.id,
                'initial_date': initial_date,
                'end_date': end_date,
                'description': description,
                })
