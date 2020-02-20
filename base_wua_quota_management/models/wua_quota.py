# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from odoo import models, fields, api, exceptions, _


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

    # For client classes (individual inputs, cessions, etc), when
    # it is necesary to test the preexisting consumptions, after
    # creating one or several quotas.
    def update_hydricmovements_from_consumptions(self, quotaperiod):
        self._create_hydricmovements_of_preexisting_presconsumptions(
            quotaperiod)
        self._create_hydricmovements_of_preexisting_gravconsumptions(
            quotaperiod)
        self._create_hydricmovements_of_preexisting_irrigationreports(
            quotaperiod)
        self._create_hydricmovements_of_preexisting_other_consumptions(
            quotaperiod)

    # For client classes (individual inputs, cessions, etc), when the
    # computed methods are not fired.
    def refresh_quota(self, quota):
        quota.sudo()._compute_accumulated_input()
        quota.sudo()._compute_accumulated_consumption()
        quota.sudo()._compute_balance()

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
            if (waterconnection.product_id and
               waterconnection.product_id.superproduct_id):
                superproduct_id = \
                    waterconnection.product_id.superproduct_id.id
            if (total_area_official > 0 and superproduct_id > 0):
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
                    hydric_consumptions = self._group_hydricmovements(
                        hydric_consumptions)
                    if (quotaperiod.sorted_quotas and
                       (not waterconnection.fixed_water)):
                        hydric_consumptions = \
                            self._adapt_hydricmovements_to_sorted_quotas(
                                hydric_consumptions)
                    for hydric_consumption in hydric_consumptions:
                        quota = self.env['wua.quota'].search(
                            [('quotaperiod_id', '=',
                              hydric_consumption['quotaperiod_id']),
                             ('superproduct_id', '=',
                              hydric_consumption['superproduct_id']),
                             ('partner_id', '=',
                              hydric_consumption['partner_id'])])
                        if quota and hydric_consumption['volume'] > 0:
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
        if presconsumption.hydricmovement_ids:
            presconsumption.hydricmovement_ids.with_context(
                force_unlink=True).sudo().unlink()

    # For client classes (gravity consumptions...)
    def create_hydricmovements_gravconsumption_of_request(
            self, quotaperiod, wateringperiod, superproduct, parcel,
            watering_duration, gravconsumption):
        volume_perunittime = 0
        if parcel.irrigationditch_id:
            volume_perunittime = parcel.irrigationditch_id.water_flow
        if volume_perunittime == 0:
            default_volume_perunitime = \
                self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'default_volume_perunitime')
            if default_volume_perunitime:
                volume_perunittime = default_volume_perunitime
        if volume_perunittime > 0 and parcel.area_official > 0:
            watering_duration = watering_duration * 60
            volume = watering_duration * volume_perunittime / 1000
            for partnerlink in (parcel.partnerlink_ids or []):
                partner = partnerlink.partner_id
                volume_of_hydric_consumption = \
                    (volume * partnerlink.water_costs_percentage / 100)
                quota = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', quotaperiod.id),
                     ('superproduct_id', '=', superproduct.id),
                     ('partner_id', '=', partner.id)])
                if quota:
                    quota = quota[0]
                    available_quota = quota.balance
                    event_time = datetime.datetime.strptime(
                        wateringperiod.initial_date, '%Y-%m-%d')
                    event_time = \
                        event_time.strftime('%Y-%m-%d %H:%M:%S')
                    self.env['wua.hydricmovement'].sudo().create({
                        'quota_id': quota.id,
                        'event_time': event_time,
                        'type': 'grav_consumption',
                        'volume': volume_of_hydric_consumption,
                        'gravconsumption_id': gravconsumption.id,
                        })
                    if volume_of_hydric_consumption > available_quota:
                        prefix_message = \
                            _('Exceeded quota. It is not possible '
                              'to create this watering request. '
                              'AVAILABLE QUOTA:')
                        suffix_message = _('m3')
                        error_message = prefix_message + ' ' + \
                            '{0:.2f}'.format(round(available_quota, 2)) + \
                            ' ' + suffix_message
                        raise exceptions.UserError(error_message)

    # For client classes (gravity consumptions...)
    def create_hydricmovements_gravconsumption(self, gravconsumption):
        parcel = gravconsumption.subparcel_id.parcel_id
        product = gravconsumption.product_id
        superproduct = None
        if product.product_tmpl_id.superproduct_id:
            superproduct = product.product_tmpl_id.superproduct_id
        if superproduct and gravconsumption.watering_end_time:
            quotaperiod = self._get_quotaperiod(
                gravconsumption.watering_end_time)
            volume_perunittime = 0
            if parcel.irrigationditch_id:
                volume_perunittime = parcel.irrigationditch_id.water_flow
            if volume_perunittime == 0:
                default_volume_perunitime = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'default_volume_perunitime')
                if default_volume_perunitime:
                    volume_perunittime = default_volume_perunitime
            if volume_perunittime > 0 and parcel.area_official > 0:
                watering_duration = gravconsumption.watering_duration * 60
                volume = watering_duration * volume_perunittime / 1000
                for partnerlink in (parcel.partnerlink_ids or []):
                    partner = partnerlink.partner_id
                    volume_of_hydric_consumption = \
                        (volume * partnerlink.water_costs_percentage / 100)
                    quota = self.env['wua.quota'].search(
                        [('quotaperiod_id', '=', quotaperiod.id),
                         ('superproduct_id', '=', superproduct.id),
                         ('partner_id', '=', partner.id)])
                    if quota:
                        quota = quota[0]
                        event_time = gravconsumption.watering_end_time
                        self.env['wua.hydricmovement'].sudo().create({
                            'quota_id': quota.id,
                            'event_time': event_time,
                            'type': 'grav_consumption',
                            'volume': volume_of_hydric_consumption,
                            'gravconsumption_id': gravconsumption.id,
                            })

    # For client classes (gravity consumptions...)
    def delete_hydricmovements_gravconsumption(self, gravconsumption):
        if gravconsumption.hydricmovement_ids:
            gravconsumption.hydricmovement_ids.with_context(
                force_unlink=True).sudo().unlink()

    def _get_quotaperiod(self, event_time):
        resp = None
        event_time = datetime.datetime.strptime(
            event_time, '%Y-%m-%d %H:%M:%S')
        quotaperiods = self.env['wua.quotaperiod'].search(
            [('state', '=', 'generated')])
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

    def _get_quotaperiod_for_timeframe(self, initial_date, end_date):
        resp = None
        quotaperiods = self.env['wua.quotaperiod'].search(
            [('initial_date', '<=', initial_date),
             ('end_date', '>=', end_date),
             ('state', '=', 'generated')])
        if (quotaperiods and len(quotaperiods) == 1):
            resp = quotaperiods[0]
        return resp

    def _adapt_hydricmovements_to_sorted_quotas(self, hydric_consumptions):
        resp = []
        if hydric_consumptions:
            quotaperiod_id = hydric_consumptions[0]['quotaperiod_id']
            quotaperiodlines = self.env['wua.quotaperiod.line'].search(
                [('quotaperiod_id', '=', quotaperiod_id)], order='pos')
            if quotaperiodlines:
                max_for = len(quotaperiodlines)
                for hydric_consumption in hydric_consumptions:
                    abort_loop_superproducts = False
                    remaining_volume = hydric_consumption['volume']
                    new_hydric_consumptions = []
                    current_pos = 1
                    partner_id = hydric_consumption['partner_id']
                    for quotaperiodline in quotaperiodlines:
                        superproduct_id = quotaperiodline.superproduct_id.id
                        current_quota = self.env['wua.quota'].search(
                            [('quotaperiod_id', '=', quotaperiod_id),
                             ('superproduct_id', '=', superproduct_id),
                             ('partner_id', '=', partner_id)])
                        if current_quota:
                            current_quota = current_quota[0]
                            if (current_quota.balance >= remaining_volume or
                               current_pos == max_for):
                                new_hydric_consumptions.append({
                                    'quotaperiod_id': quotaperiod_id,
                                    'superproduct_id': superproduct_id,
                                    'partner_id': partner_id,
                                    'volume': remaining_volume,
                                    })
                                remaining_volume = 0
                            else:
                                new_hydric_consumptions.append({
                                    'quotaperiod_id': quotaperiod_id,
                                    'superproduct_id': superproduct_id,
                                    'partner_id': partner_id,
                                    'volume': current_quota.balance,
                                    })
                                remaining_volume = \
                                    remaining_volume - current_quota.balance
                            if remaining_volume == 0:
                                break
                            current_pos = current_pos + 1
                        else:
                            # This should not happen.
                            abort_loop_superproducts = True
                            break
                    if abort_loop_superproducts:
                        resp.append(hydric_consumption)
                        continue
                    else:
                        # Add new hydric consumptions.
                        resp.extend(new_hydric_consumptions)
            else:
                resp = hydric_consumptions
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

    def _create_hydricmovements_of_preexisting_presconsumptions(self,
                                                                quotaperiod):
        presconsumptions = self._get_presconsumptions_without_hydricmovements(
            quotaperiod)
        for presconsumption in (presconsumptions or []):
            self.create_hydricmovements_presconsumption(presconsumption)

    def _create_hydricmovements_of_preexisting_gravconsumptions(self,
                                                                quotaperiod):
        executed_gravconsumptions = \
            self._get_gravconsumptions_without_hydricmovements_executed_state(
                quotaperiod)
        for gravconsumption in (executed_gravconsumptions or []):
            self.create_hydricmovements_gravconsumption(gravconsumption)
        requested_gravconsumptions = \
            self._get_gravconsumptions_without_hydricmovements_type_request(
                quotaperiod)
        for gravconsumption in (requested_gravconsumptions or []):
            wateringrequest = self.env['wua.wateringrequest'].browse(
                gravconsumption.wateringrequest_id.id)
            wateringperiod = wateringrequest.wateringperiod_id
            product = wateringrequest.product_id
            superproduct = None
            if product.product_tmpl_id.superproduct_id:
                superproduct = product.product_tmpl_id.superproduct_id
            if superproduct:
                subparcel = self.env['wua.parcel.subparcel'].browse(
                    gravconsumption.subparcel_id.id)
                parcel = subparcel.parcel_id
                model_quota = self.env['wua.quota']
                model_quota.create_hydricmovements_gravconsumption_of_request(
                    quotaperiod, wateringperiod, superproduct, parcel,
                    gravconsumption.watering_duration, gravconsumption)

    def _create_hydricmovements_of_preexisting_irrigationreports(self,
                                                                 quotaperiod):
        # Provisional
        pass

    # Hook (for future types of hydric consumptions)
    def _create_hydricmovements_of_preexisting_other_consumptions(self,
                                                                  quotaperiod):
        pass

    def _get_presconsumptions_without_hydricmovements(self, quotaperiod):
        resp = []
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        min_date = min_date.strftime('%Y-%m-%d %H:%M:%S')
        max_date = max_date.strftime('%Y-%m-%d %H:%M:%S')
        possible_presconsumptions = self.env['wua.presconsumption'].search(
            [('reading_end_time', '>=', min_date),
             ('reading_end_time', '<', max_date)],
            order='reading_end_time')
        for possible_presconsumption in (possible_presconsumptions or []):
            if not possible_presconsumption.hydricmovement_ids:
                is_valid_presconsumption = \
                    self.env['wua.presconsumption'].is_valid_presconsumption(
                        possible_presconsumption)
                if is_valid_presconsumption:
                    resp.append(possible_presconsumption)
        return resp

    def _get_gravconsumptions_without_hydricmovements_executed_state(
            self, quotaperiod):
        resp = []
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        min_date = min_date.strftime('%Y-%m-%d %H:%M:%S')
        max_date = max_date.strftime('%Y-%m-%d %H:%M:%S')
        possible_gravconsumptions = self.env['wua.gravconsumption'].search(
            [('watering_end_time', '>=', min_date),
             ('watering_end_time', '<', max_date),
             ('state', '=', 'executed')],
            order='watering_end_time')
        for possible_gravconsumption in (possible_gravconsumptions or []):
            if not possible_gravconsumption.hydricmovement_ids:
                is_valid_gravconsumption = \
                    self.env['wua.gravconsumption'].is_valid_gravconsumption(
                        possible_gravconsumption)
                if is_valid_gravconsumption:
                    resp.append(possible_gravconsumption)
        return resp

    def _get_gravconsumptions_without_hydricmovements_type_request(
            self, quotaperiod):
        resp = []
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        min_date = min_date.strftime('%Y-%m-%d %H:%M:%S')
        max_date = max_date.strftime('%Y-%m-%d %H:%M:%S')
        wateringperiods = self.env['wua.wateringperiod'].search(
            [('initial_date', '>=', quotaperiod.initial_date),
             ('end_date', '<=', quotaperiod.end_date)])
        possible_gravconsumptions = []
        for wateringperiod in (wateringperiods or []):
            possible_gravconsumptions_of_wateringperiod = \
                self.env['wua.gravconsumption'].search(
                    [('gravconsumption_type', '=', 'request'),
                     ('state', '!=', 'executed'),
                     ('wateringperiod_id', '=', wateringperiod.id)])
            if possible_gravconsumptions_of_wateringperiod:
                possible_gravconsumptions.extend(
                    possible_gravconsumptions_of_wateringperiod)
        for possible_gravconsumption in (possible_gravconsumptions or []):
            if not possible_gravconsumption.hydricmovement_ids:
                resp.append(possible_gravconsumption)
        return resp
