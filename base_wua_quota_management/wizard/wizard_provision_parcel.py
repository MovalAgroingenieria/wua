# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api, exceptions, _


class WizardProvisionParcel(models.TransientModel):
    _name = 'wizard.provision.parcel'
    _description = 'Dialog box to assign a initial provision to a parcel'

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

    agriculturalseason_description = fields.Char(
        string='Active agricultural season',
        readonly=True)

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        readonly=True)

    parcel_name = fields.Char(
        string='Parcel Code',
        readonly=True)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        domain=_get_quotaperiod_domain)

    provision_lines = fields.One2many(
        comodel_name='wizard.provision.parcel.line',
        inverse_name='wizard_id',
        string='Provisions')

    @api.onchange('quotaperiod_id')
    def _onchange_quotaperiod(self):
        for line in self.provision_lines:
            line.provision = self.env['wua.quotaperiod'].get_provision(
                self.quotaperiod_id, line.superproduct_id)

    @api.model
    def default_get(self, var_fields):
        current_parcel_data = \
            self._get_current_parcel_data()
        return current_parcel_data

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WizardProvisionParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_provision = ' (' + _('m³') + '/' + \
                area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='provision_lines']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.provision_lines.string)
                node.set('string', original_label + suffix_provision)
            for node in doc.xpath("//field[@name='provision_lines']/tree/"
                                  "field[@name='provision']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.env['wizard.provision.parcel.line'].
                        provision.string)
                node.set('string', original_label + suffix_provision)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def assign_provision(self):
        self.ensure_one()
        quotaperiod = self.quotaperiod_id
        parcel = self.parcel_id
        for line in self.provision_lines:
            superproduct = line.superproduct_id
            provision = line.provision
            data_ok, error_message = self._check_data(
                quotaperiod, superproduct, parcel, provision)
            if not data_ok:
                raise exceptions.ValidationError(error_message)
            quotaperiod_model = self.env['wua.quotaperiod']
            quotaperiodline_model = self.env['wua.quotaperiod.line']
            quotaperiodlineparcel_model = self.env[
                'wua.quotaperiod.line.parcel']
            quota_model = self.env['wua.quota']
            hydricmovement_model = self.env['wua.hydricmovement']
            # 1. Create a new record for the quotaperiod-line
            quotaperiod_line = quotaperiodline_model.search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id)])[0]
            quotaperiodlineparcel_model.create({
                'quotaperiodline_id': quotaperiod_line.id,
                'parcel_id': parcel.id,
                'cadastral_reference': parcel.cadastral_reference,
                'is_billable_water': parcel.is_billable_water,
                'is_billable_expenses': parcel.is_billable_expenses,
                'leased_parcel': parcel.leased_parcel,
                'area_official': parcel.area_official,
                'partner_id': parcel.partner_id.id,
                'hydraulic_infrastructure_type':
                    parcel.hydraulic_infrastructure_type,
                'pressurized_irrigation_right':
                    parcel.pressurized_irrigation_right,
                'gravityfed_irrigation_right': parcel.
                    gravityfed_irrigation_right,
                'hydraulicsector_id': parcel.hydraulicsector_id.id,
                'irrigationditch_id': parcel.irrigationditch_id.id,
                'with_watering_shift': parcel.with_watering_shift,
                'with_irrigation_worker': parcel.with_irrigation_worker,
                'employee_id': parcel.employee_id.id})
            # 2. Add quota/s and hydric movement/s
            for partnerlink in (parcel.partnerlink_ids or []):
                partner = partnerlink.partner_id
                area = partnerlink.area_official_water_costs_net
                volume = area * provision
                # If the partner has a quota for the quota period and the
                # superproduct, then find the initial hydric-movement and add
                # the new volume to the hydric-movement and the quota.
                quota_to_update = quota_model.search(
                    [('partner_id', '=', partner.id),
                     ('quotaperiod_id', '=', quotaperiod.id),
                     ('superproduct_id', '=', superproduct.id)])
                if quota_to_update:
                    quota_to_update = quota_to_update[0]
                    initial_hydricmovement = \
                        quota_to_update.hydricmovement_ids.filtered(
                            lambda x: x.type == 'multiple_assign')
                    if initial_hydricmovement:
                        initial_hydricmovement = initial_hydricmovement[0]
                        initial_hydricmovement.volume = \
                            initial_hydricmovement.volume + volume
                    else:
                        hydricmovement_model.create({
                            'quota_id': quota_to_update.id,
                            'event_time':
                                quota_to_update.quotaperiod_id.initial_date,
                            'type': 'multiple_assign',
                            'volume': volume,
                            })
                else:
                    new_quota = quota_model.create({
                        'quotaperiod_id': quotaperiod.id,
                        'partner_id': partner.id,
                        'superproduct_id': superproduct.id,
                        'initial_value': volume,
                        })
                    hydricmovement_model.create({
                        'quota_id': new_quota.id,
                        'event_time': quotaperiod.initial_date,
                        'type': 'multiple_assign',
                        'volume': volume,
                        })
            # 3. Populate "mapped_to_current_quotaperiod", if necessary.
            if not parcel.mapped_to_current_quotaperiod:
                current_quotaperiod = \
                    quotaperiod_model.get_current_generated_quotaperiod()
                if quotaperiod == current_quotaperiod:
                    parcel.mapped_to_current_quotaperiod = True

    @api.multi
    def add_missing_provisions(self):
        self.ensure_one()
        quotaperiod = self.quotaperiod_id
        parcel = self.parcel_id
        if not quotaperiod:
            raise exceptions.ValidationError(
                _('Quota Period is not selected.'))
        all_superproduct_ids = self.env['wua.quotaperiod.line'].search([
            ('quotaperiod_id', '=', quotaperiod.id)
        ]).mapped('superproduct_id.id')
        existing_superproduct_ids = self.env['wua.quotaperiod.line.parcel'].\
            search([
                ('parcel_id', '=', parcel.id),
                ('quotaperiod_id', '=', quotaperiod.id)
            ]).mapped('superproduct_id.id')
        missing_superproduct_ids = list(
            set(all_superproduct_ids) - set(existing_superproduct_ids))
        for superproduct_id in missing_superproduct_ids:
            self.provision_lines.create({
                'wizard_id': self.id,
                'superproduct_id': superproduct_id,
                'provision': 0.0,
            })
        return {
            'type': 'ir.actions.do_nothing'
        }

    def _get_current_parcel_data(self):
        agriculturalseason_description = ''
        parcel_id = 0
        parcel_name = ''
        quotaperiod_id = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            active_agriculturalseason = active_agriculturalseasons[0]
            agriculturalseason_description = \
                active_agriculturalseason.description
            parcel = self.env['wua.parcel'].browse(
                self.env.context['active_id'])
            if parcel:
                parcel_id = parcel.id
                parcel_name = parcel.name
                quotaperiod = parcel.current_quotaperiod_id
                if quotaperiod:
                    quotaperiod_id = quotaperiod.id
        resp = {
            'agriculturalseason_description': agriculturalseason_description,
            'parcel_id': parcel_id,
            'parcel_name': parcel_name,
            'quotaperiod_id': quotaperiod_id,
            }
        return resp

    def _check_data(self, quotaperiod, superproduct, parcel, provision):
        data_ok = True
        error_message = ''
        if (not self.env['wua.quotaperiod'].exists_superproduct_in_quotaperiod(
           quotaperiod, superproduct)):
            data_ok = False
            error_message = _('The chosen superproduct does not exist '
                              'in that quota period.')
        if (data_ok and
           self.env['wua.quotaperiod'].exists_parcel_in_quotaperiodline(
               quotaperiod, superproduct, parcel)):
            data_ok = False
            error_message = _('The parcel is already included in the '
                              'quota period/superproduct.')
        if (data_ok and provision < 0):
            data_ok = False
            error_message = _('Incorrect Provision Value.')
        return data_ok, error_message

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp


class WizardProvisionParcelLine(models.TransientModel):
    _name = 'wizard.provision.parcel.line'
    _description = 'Provision line associated with a superproduct'

    wizard_id = fields.Many2one(
        string='Wizard',
        comodel_name='wizard.provision.parcel',
        required=True,
    )

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
    )

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        required=True,
    )
