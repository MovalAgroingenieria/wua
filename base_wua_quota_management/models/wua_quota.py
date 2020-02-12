# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from odoo import models, fields, api, _


class WuaQuota(models.Model):
    _name = 'wua.quota'
    _description = 'Quota'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_NAME = 12 + MAX_SIZE_PARTNER_CODE + MAX_SIZE_SUPERPRODUCT_CODE

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    name = fields.Char(
        string='Quota',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    initial_value = fields.Float(
        string='Initial Value',
        digits=(32, 2),
        required=True,
        default=0,
        readonly=True)

    accumulated_input = fields.Float(
        string='Inputs',
        digits=(32, 2),
        store=True,
        compute='_compute_accumulated_input')

    accumulated_consumption = fields.Float(
        string='Consumptions',
        digits=(32, 2),
        store=True,
        compute='_compute_accumulated_consumption')

    balance = fields.Float(
        string='Balance',
        digits=(32, 2),
        store=True,
        compute='_compute_balance')

    negative_balance = fields.Float(
        string='Balance',
        digits=(32, 2),
        compute='_compute_negative_balance')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='quota_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota.'),
        ]

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date',
                 'partner_id', 'partner_id.partner_code',
                 'superproduct_id', 'superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.quotaperiod_id and record.partner_id and
               record.superproduct_id):
                name = record.quotaperiod_id.initial_date + '-' + \
                    str(record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE) + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = name

    @api.depends('quotaperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.quotaperiod_id:
                agriculturalseason_id = \
                    record.quotaperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('hydricmovement_ids', 'hydricmovement_ids.accounting_volume')
    def _compute_accumulated_input(self):
        for record in self:
            accumulated_input = 0
            positive_hydricmovements = filter(
                lambda x: x['accounting_volume'] > 0,
                record.hydricmovement_ids)
            if positive_hydricmovements:
                accumulated_input = \
                    sum(x.accounting_volume for x in positive_hydricmovements)
            record.accumulated_input = accumulated_input

    @api.depends('hydricmovement_ids', 'hydricmovement_ids.accounting_volume')
    def _compute_accumulated_consumption(self):
        for record in self:
            accumulated_consumption = 0
            negative_hydricmovements = filter(
                lambda x: x['accounting_volume'] < 0,
                record.hydricmovement_ids)
            if negative_hydricmovements:
                accumulated_consumption = \
                    sum(x.accounting_volume for x in negative_hydricmovements)
            accumulated_consumption = -accumulated_consumption
            record.accumulated_consumption = accumulated_consumption

    @api.depends('accumulated_input', 'accumulated_consumption')
    def _compute_balance(self):
        for record in self:
            balance = record.accumulated_input - record.accumulated_consumption
            record.balance = balance

    @api.multi
    def _compute_negative_balance(self):
        # Auxiliary field for negative balances in red (form view).
        for record in self:
            record.negative_balance = record.balance

    @api.model
    def create(self, vals):
        new_quota = super(WuaQuota, self).create(vals)
        self._update_hydricmovements_from_consumptions(
            new_quota.id, vals['quotaperiod_id'])
        return new_quota

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            if self.env.context.get('show_only_partner_data', False):
                name = partner_name + ' (' + _('quota') + ': ' + \
                    '{0:.2f}'.format(round(record.balance, 2)) + ')'
            else:
                try:
                    if is_english:
                        locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                    initial_date_str = datetime.datetime.strptime(
                        record.quotaperiod_id.initial_date,
                        '%Y-%m-%d').strftime('%x')
                    end_date_str = datetime.datetime.strptime(
                        record.quotaperiod_id.end_date,
                        '%Y-%m-%d').strftime('%x')
                finally:
                    locale.setlocale(locale.LC_TIME, default_locale)
                superproduct_name = record.superproduct_id.name
                name = initial_date_str + ' - ' + end_date_str + \
                    ' (' + superproduct_name.lower() + '), ' + partner_name
            result.append((record.id, name))
        return result

    @api.multi
    def action_open_individualinput_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_individualinput_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Individual Input'),
            'res_model': 'wua.individualinput',
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'new',
            'context': {'agriculturalseason_id': self.agriculturalseason_id.id,
                        'quotaperiod_id': self.quotaperiod_id.id,
                        'superproduct_id': self.superproduct_id.id,
                        'partner_id': self.partner_id.id,
                        }
            }
        return act_window

    @api.multi
    def action_open_cession_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_cession_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Cession'),
            'res_model': 'wua.cession',
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'new',
            'context': {'agriculturalseason_id': self.agriculturalseason_id.id,
                        'quotaperiod_id': self.quotaperiod_id.id,
                        'superproduct_id': self.superproduct_id.id,
                        'quota_id': self.id,
                        }
            }
        return act_window

    def _update_hydricmovements_from_consumptions(self, quota_id,
                                                  quotaperiod_id):
        # Provisional (pending: update hydric movements for new quota)
        print '_update_hydricmovements_from_consumptions'

    # For client classes (individual inputs, cessions, etc), when the
    # computed methods are not fired.
    def refresh_quota(self, quota):
        quota._compute_accumulated_input()
        quota._compute_accumulated_consumption()
        quota._compute_balance()

    def _get_quotaperiod(self, event_time):
        resp = None
        event_time = datetime.datetime.strptime(
            event_time, '%Y-%m-%d %H:%M:%S')
        quotaperiods = self.env['wua.quotaperiod'].search([])
        for quotaperiod in (quotaperiods or []):
            min_date = datetime.datetime.strptime(
                quotaperiod.initial_date, '%Y-%m-%d')
            max_date = datetime.datetime.strptime(
                quotaperiod.end_date, '%Y-%m-%d') + \
                datetime.timedelta(days=1)
            if (event_time >= min_date and event_time < max_date):
                resp = quotaperiod
                break
        return resp

    def _adapt_hydricmovements_to_sorted_quotas(self, hydric_consumptions):
        resp = []
        # Provisional
        print '_adapt_hydricmovements_to_sorted_quotas...'
        return resp

    def _group_hydricmovements(self, hydricmovements):
        resp = []
        for item in (hydricmovements or []):
            if not resp:
                resp.append(item)
            else:
                filtered_resp = filter(
                    lambda x: x['quotaperiod_id'] == item['quotaperiod_id'] and
                    x['superproduct_id'] == item['superproduct_id'] and
                    x['partner_id'] == item['partner_id'], resp)
                if not filtered_resp:
                    resp.append(item)
                else:
                    item_to_update = filtered_resp[0]
                    item_to_update.update(
                        {'volume': item_to_update['volume'] + item['volume']})
        return resp

    # For client classes (pressurized consumptions...)
    def create_hydricmovements_presconsumption(self, presconsumption):
        waterconnection = presconsumption.waterconnection_id
        volume = presconsumption.volume_real
        quotaperiod = self._get_quotaperiod(presconsumption.reading_end_time)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('waterconnection_id', '=', waterconnection.id)])
        if irrigationpoints and quotaperiod:
            parcels = [x.parcel_id for x in irrigationpoints]
            total_area_official = sum(x.area_official for x in parcels)
            superproduct_id = 0
            if not quotaperiod.sorted_quotas or waterconnection.fixed_water:
                if (waterconnection.product_id and
                   waterconnection.product_id.superproduct_id):
                    superproduct_id = \
                        waterconnection.product_id.superproduct_id.id
            if (total_area_official > 0 and
               (quotaperiod.sorted_quotas or superproduct_id > 0)):
                data_parcels = []
                hydric_consumptions = []
                for parcel in parcels:
                    if parcel.area_official > 0:
                        volume_of_parcel = \
                            volume * parcel.area_official / total_area_official
                        data_parcels.append({
                            'parcel_id': parcel.id,
                            'volume': volume_of_parcel,
                            })
                for data_parcel in (data_parcels or []):
                    parcel = filter(lambda x: x['id'] ==
                                    data_parcel['parcel_id'], parcels)[0]
                    for partnerlink in (parcel.partnerlink_ids or []):
                        volume_of_hydric_consumption = \
                            (data_parcel['volume'] *
                             partnerlink.water_costs_percentage / 100)
                        hydric_consumptions.append({
                            'quotaperiod_id': quotaperiod.id,
                            'superproduct_id': superproduct_id,
                            'partner_id': partnerlink.partner_id.id,
                            'volume': volume_of_hydric_consumption,
                            })
                if hydric_consumptions:
                    if quotaperiod.sorted_quotas:
                        hydric_consumptions = \
                            self._adapt_hydricmovements_to_sorted_quotas(
                                hydric_consumptions)
                    hydric_consumptions = self._group_hydricmovements(
                        hydric_consumptions)
                    for hydric_consumption in hydric_consumptions:
                        quota = self.env['wua.quota'].search(
                            [('quotaperiod_id', '=',
                              hydric_consumption['quotaperiod_id']),
                             ('superproduct_id', '=',
                              hydric_consumption['superproduct_id']),
                             ('partner_id', '=',
                              hydric_consumption['partner_id'])])
                        if quota:
                            quota = quota[0]
                            self.env['wua.hydricmovement'].sudo().create({
                                'quota_id': quota.id,
                                'event_time': presconsumption.reading_end_time,
                                'type': 'pres_consumption',
                                'volume': hydric_consumption['volume'],
                                'presconsumption_id': presconsumption.id,
                                })

    # For client classes (pressurized consumptions...)
    def delete_hydricmovements_presconsumption(self, presconsumption):
        # Provisional
        print 'delete_hydricmovements_presconsumption for...'
        print presconsumption.waterconnection_id.name
        print presconsumption.volume_real
