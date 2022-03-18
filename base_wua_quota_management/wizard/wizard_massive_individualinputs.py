# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WizardMassiveIndividualinputs(models.TransientModel):
    _name = 'wizard.massive.individualinputs'
    _description = 'Dialog box to assign multiple individual inputs'

    MAX_SIZE_REASON = 75

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
        required=True)

    event_time = fields.Datetime(
        string='Date and Time',
        required=True)

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        required=True)

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON)

    @api.model
    def default_get(self, var_fields):
        current_quotaperiod_data = \
            self._get_current_quotaperiod_data()
        return current_quotaperiod_data

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WizardMassiveIndividualinputs, self).fields_view_get(
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
            suffix_provision = ' (m3/' + area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='provision']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.provision.string)
                node.set('string', original_label + suffix_provision)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def assign_individualinputs(self):
        self.ensure_one()
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        data_ok, error_message = self._check_data(quotaperiod)
        if not data_ok:
            raise exceptions.ValidationError(error_message)
        quotaperiodline = self.env['wua.quotaperiod.line'].search(
            [('quotaperiod_id', '=', quotaperiod.id),
             ('superproduct_id', '=', self.superproduct_id.id)])
        if quotaperiodline:
            quotaperiodline = quotaperiodline[0]
            selected_parcels = filter(
                lambda x: x['selected'] is True,
                quotaperiodline.quotaperiodlineparcel_ids)
            partnerlinks = self.env['wua.parcel.partnerlink'].search([])
            # Notify user
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
                suffix = 'm3/' + area_measurement_name.lower()
            if self.reason:
                reason = self.reason
            else:
                reason = ""
            message_body = _('Superproduct: ') + self.superproduct_id.name + \
                '<br/>' + _('Category: ') + self.category_id.name + '<br/>' + \
                _('Event time: ') + self.event_time + '<br/>' + \
                _('Provision: ') + str(self.provision) + ' ' + suffix + \
                '<br/>' + _('Reason: ') + reason
            quotaperiod.message_post(body=message_body)
            if selected_parcels and partnerlinks:
                partners_with_quota = []
                partnerlinks_with_quota = []
                # First: get water payers.
                selected_parcels_ids = []
                for selected_parcel in selected_parcels:
                    partnerlinks_of_parcel = partnerlinks.filtered(
                        lambda x: x.parcel_id.id ==
                        selected_parcel.parcel_id.id and
                        x.water_costs_percentage > 0)
                    for partnerlink in partnerlinks_of_parcel:
                        partners_with_quota.append(partnerlink.partner_id.id)
                        partnerlinks_with_quota.append(partnerlink.id)
                    selected_parcels_ids.append(selected_parcel.parcel_id.id)
                if partners_with_quota:
                    # Second: loop on partners
                    partners_with_quota = list(set(partners_with_quota))
                    selected_partnerlinks = \
                        self.env['wua.parcel.partnerlink'].browse(
                            partnerlinks_with_quota)
                    for partner_id in partners_with_quota:
                        selected_partnerlinks_of_partner = \
                            selected_partnerlinks.search(
                                [('partner_id', '=', partner_id),
                                 ('parcel_id', 'in', selected_parcels_ids)])
                        area = sum(x.area_official_water_costs_net
                                   for x in selected_partnerlinks_of_partner)
                        volume = area * self.provision
                        if abs(volume) > 0.01:
                            agriculturalseason = \
                                quotaperiod.agriculturalseason_id
                            self.env['wua.individualinput'].create({
                                'agriculturalseason_id': agriculturalseason.id,
                                'quotaperiod_id': quotaperiod.id,
                                'superproduct_id': self.superproduct_id.id,
                                'partner_id': partner_id,
                                'category_id': self.category_id.id,
                                'event_time': self.event_time,
                                'volume': volume,
                                'reason': reason,
                                })

    def _get_current_quotaperiod_data(self):
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        initial_date_str = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d').strftime('%x')
        end_date_str = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d').strftime('%x')
        if quotaperiod.description:
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str + ' ' + \
                '[' + quotaperiod.description + ']'
        else:
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str
        category_id = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            category_id = proposed_category.id
        resp = {
            'quotaperiod_name': quotaperiod_name,
            'category_id': category_id,
            'event_time': str(fields.datetime.now()),
            'provision': 0,
            'reason': '',
            }
        return resp

    def _check_data(self, quotaperiod):
        data_ok = True
        error_message = ''
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        event_time = datetime.datetime.strptime(
            self.event_time, '%Y-%m-%d %H:%M:%S')
        if self.env.user.tz:
            local_timezone = pytz.timezone(self.env.user.tz)
            offset = local_timezone.utcoffset(event_time)
            event_time = event_time + offset
        if event_time < min_date or event_time >= max_date:
            data_ok = False
            error_message = _('The chosen date/time is outside the '
                              'quota period.')
        if self.provision == 0 and data_ok:
            data_ok = False
            error_message = _('The provision cannot be zero.')
        return data_ok, error_message

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp
