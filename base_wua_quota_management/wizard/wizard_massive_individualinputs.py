# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WizardMassiveIndividualinputs(models.TransientModel):
    _name = 'wizard.massive.individualinputs'
    _description = 'Dialog box to assign multiple individual inputs'

    def _get_superproduct_domain(self):
        valid_superproduct_ids = []
        if 'active_id' in self.env.context:
            quotaperiod = self.env['wua.quotaperiod'].browse(
                self.env.context['active_id'])
            for quotaperiodline in (quotaperiod.quotaperiodline_ids or []):
                valid_superproduct_ids.append(
                    quotaperiodline.superproduct_id.id)
        return [('id', 'in', valid_superproduct_ids)]

    quotaperiod_name = fields.Char(
        string='Quota Period',
        readonly=True)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        domain=_get_superproduct_domain)

    category_id = fields.Many2one(
        string='Category',
        comodel_name='wua.individualinput.category',
        index=True,
        required=True)

    @api.model
    def default_get(self, var_fields):
        current_quotaperiod_data = \
            self._get_current_quotaperiod_data()
        return current_quotaperiod_data

    @api.multi
    def assign_individualinputs(self):
        self.ensure_one()
        # Provisional
        print 'assign_individualinputs'

    def _get_current_quotaperiod_data(self):
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        initial_date_str = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d').strftime('%x')
        end_date_str = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d').strftime('%x')
        if quotaperiod.description != '':
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str + ' ' + \
                '[' + quotaperiod.description + ']'
        category_id = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            category_id = proposed_category.id
        else:
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str
        resp = {
            'quotaperiod_name': quotaperiod_name,
            'category_id': category_id,
            }
        return resp
