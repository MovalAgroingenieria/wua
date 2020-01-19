# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WizardGenerateQuotaperiods(models.TransientModel):
    _name = 'wizard.generate.quotaperiods'
    _description = 'Dialog box to generate quota periods'

    agriculturalseason_name = fields.Char(
        string='Agricultural Season',
        readOnly=True)

    quotaperiod_01 = fields.Date(
        string='1',
        readonly=True)

    quotaperiod_02 = fields.Date(
        string='2')

    quotaperiod_03 = fields.Date(
        string='3')

    quotaperiod_04 = fields.Date(
        string='4')

    @api.model
    def default_get(self, var_fields):
        current_agriculturalseason_data = \
            self.get_current_agriculturalseason_data()
        return current_agriculturalseason_data

    @api.multi
    def generate_quotaperiods(self):
        self.ensure_one()
        if len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        if agriculturalseason:
            # Provisional (test all dates)
            self.create_quotaperiods(agriculturalseason, self.quotaperiod_01)

    def get_current_agriculturalseason_data(self):
        agriculturalseason_name = ''
        quotaperiod_01 = fields.datetime.now()
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            self.env.context['active_id'])
        if agriculturalseason:
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
            quotaperiod_01 = agriculturalseason.initial_date
        resp = {
            'agriculturalseason_name': agriculturalseason_name,
            'quotaperiod_01': quotaperiod_01,
            }
        return resp

    def create_quotaperiods(self, agriculturalseason, quotaperiod_01):
        # Provisional
        print 'create_quotaperiods...'
