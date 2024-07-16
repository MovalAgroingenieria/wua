# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WizardProvisionPartner(models.TransientModel):
    _name = 'wizard.provision.partner'
    _description = 'Dialog box to assign a initial provision to a partner'

    def _get_quotaperiod_domain(self):
        valid_quotaperiod_ids = []
        active_agriculturalseason = None
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            active_agriculturalseason = active_agriculturalseasons[0]
            valid_quotaperiods = self.env['wua.quotaperiod'].search(
                [('agriculturalseason_id', '=', active_agriculturalseason.id),
                 ('state', '=', 'generated')])
            for quotaperiod in (valid_quotaperiods or []):
                valid_quotaperiod_ids.append(quotaperiod.id)
        return [('id', 'in', valid_quotaperiod_ids)]

    partner_id = fields.Many2one(
        string='Partner WUA',
        comodel_name='res.partner',
        readonly=True,)

    partner_name = fields.Char(
        string='WUA Partner',
        readonly=True,)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        domain=_get_quotaperiod_domain)

    superproduct_ids = fields.Many2many(
        string='Superproducts',
        comodel_name='wua.superproduct',
        relation='wizard_provision_partner_superproduct_rel',
        column1='wizard_provision_partner_id',
        column2='superproduct_id',
        required=False,
    )

    agriculturalseason_description = fields.Char(
        string='Active agricultural season',
        readonly=True)

    @api.model
    def default_get(self, var_fields):
        current_partner_data = \
            self._get_current_partner_data()
        return current_partner_data

    def _get_current_partner_data(self):
        agriculturalseason_description = ''
        partner_id = 0
        partner_name = ''
        quotaperiod_id = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            active_agriculturalseason = active_agriculturalseasons[0]
            agriculturalseason_description = \
                active_agriculturalseason.description
            partner = self.env['res.partner'].browse(
                self.env.context['active_id'])
            if partner:
                partner_id = partner.id
                partner_name = partner.name
                quotaperiod = partner._get_current_quotaperiod()
                if quotaperiod:
                    quotaperiod_id = quotaperiod.id
        resp = {
            'agriculturalseason_description': agriculturalseason_description,
            'partner_id': partner_id,
            'partner_name': partner_name,
            'quotaperiod_id': quotaperiod_id,
            }
        return resp

    @api.multi
    def assign_provision(self):
        self.ensure_one()
        quotaperiod = self.quotaperiod_id
        partner = self.partner_id
        for superproduct in self.superproduct_ids:
            data_ok, error_message = self._check_data(
                quotaperiod, superproduct, partner)
            if not data_ok:
                raise exceptions.ValidationError(error_message)
            quota_model = self.env['wua.quota']
            hydricmovement_model = self.env['wua.hydricmovement']
            new_quota = quota_model.create({
                'quotaperiod_id': quotaperiod.id,
                'partner_id': partner.id,
                'superproduct_id': superproduct.id,
                'initial_value': 0,
                })
            hydricmovement_model.create({
                'quota_id': new_quota.id,
                'event_time': quotaperiod.initial_date,
                'type': 'multiple_assign',
                'volume': 0,
                })

    @api.multi
    def add_missing_superproducts(self):
        self.ensure_one()
        partner = self.partner_id
        quotaperiod = self.quotaperiod_id
        if not partner or not quotaperiod:
            raise exceptions.ValidationError(
                _('Partner or Quota Period is not selected.'))
        all_superproduct_ids = self.env['wua.quotaperiod.line'].search([
            ('quotaperiod_id', '=', quotaperiod.id)
        ]).mapped('superproduct_id.id')
        existing_superproduct_ids = self.env['wua.quota'].search([
            ('partner_id', '=', partner.id),
            ('quotaperiod_id', '=', quotaperiod.id)
        ]).mapped('superproduct_id.id')
        missing_superproduct_ids = list(set(all_superproduct_ids) - set(
            existing_superproduct_ids))
        self.superproduct_ids = [(6, 0, missing_superproduct_ids)]
        return {
            'type': 'ir.actions.do_nothing'
        }

    def _check_data(self, quotaperiod, superproduct, partner):
        data_ok = True
        error_message = ''
        if (not self.env['wua.quotaperiod'].exists_superproduct_in_quotaperiod(
           quotaperiod, superproduct)):
            data_ok = False
            error_message = _('The chosen superproduct does not exist '
                              'in that quota period.')
        if (data_ok and
           self.env['wua.quotaperiod'].exists_partner_in_quotaperiod(
               quotaperiod, superproduct, partner)):
            data_ok = False
            error_message = _('The partner is already included in the '
                              'quota period/superproduct.')
        return data_ok, error_message
