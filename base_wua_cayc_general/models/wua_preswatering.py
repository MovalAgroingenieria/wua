# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pytz
import logging
import json
import base64
from datetime import datetime, timedelta, time
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class WuaPresreswatering(models.Model):
    _inherit = 'wua.preswatering'

    proration = fields.Float(
        string='Proration',
        required=True,
        digits=(32, 2),
    )

    zones_united = fields.Boolean(
        string='Zones United',
        default=False,
    )

    rebombed_flow_ls = fields.Float(
        string='Rebombed Flow (l/s)',
        digits=(32, 0),
        default=0.0,
    )

    by_gravity_outlet = fields.Boolean(
        string='By Gravity Outlet',
        default=False,
    )

    by_pumping = fields.Boolean(
        string='By Pumping',
        default=False,
    )

    by_surplus = fields.Boolean(
        string='By Surplus',
        default=False,
    )

    nominal_flow_requested = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_requested = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_granted = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_issued = fields.Float(
        digits=(32, 0),
    )

    nominal_flow_ls_issued = fields.Float(
        digits=(32, 0),
    )

    _sql_constraints = [
        ('check_proration_positive',
         'CHECK(proration > 0)',
         'The value of \'Proration\' must be greater than 0.'),
    ]

    @api.onchange('preswateringperiod_id')
    def _onchange_preswateringperiod_id(self):
        if self.preswateringperiod_id:
            self.proration = self.preswateringperiod_id.proration
            self.zones_united = self.preswateringperiod_id.zones_united
            self.rebombed_flow_ls = self.preswateringperiod_id.rebombed_flow_ls
            self.by_gravity_outlet = \
                self.preswateringperiod_id.by_gravity_outlet
            self.by_pumping = self.preswateringperiod_id.by_pumping
            self.by_surplus = self.preswateringperiod_id.by_surplus
            # Now check all the number of presatering_ids of the
            # preswateringperiod_id and set the biggest number + 1
            number_to_set = 1
            id_to_exclude = self.id or self._origin.id
            for preswatering in self.preswateringperiod_id.preswatering_ids.\
                    filtered(lambda x: x.id and x.id not in [id_to_exclude]):
                if preswatering.number >= number_to_set:
                    number_to_set = preswatering.number + 1
            self.number = number_to_set
            condition_lines = []
            for condition in self.preswateringperiod_id.condition_ids:
                condition_lines.append((0, 0, {
                    'condition_id': condition.id,
                    'specific_proration': self.proration,
                    'state': '01_not_checked',
                }))
            self.condition_line_ids = condition_lines

    @api.multi
    def write(self, vals):
        if 'proration' in vals:
            self.mapped('condition_line_ids').write({
                'specific_proration': vals['proration'],
            })
        return super(WuaPresreswatering, self).write(vals)

    def _process_granted_nominal_flows(
            self, presresconsumptions, preswatering):
        presres_grouped = {}
        for presresconsumption in presresconsumptions:
            key = presresconsumption.preswateringrequest_id
            if key not in presres_grouped:
                presres_grouped[key] = []
            presres_grouped[key].append(presresconsumption)
        for preswateringrequest_id, consumptions in presres_grouped.items():
            partner_area = preswateringrequest_id.partner_parcel_owner_area
            is_wua_type = preswateringrequest_id.partner_id.partner_type == \
                '01_WUA'
            condition_lines = self.env[
                'wua.preswatering.condition.line'].search([
                    ('preswatering_id', '=', preswatering.id),
                ])
            specific_prorations = {}
            for line in condition_lines:
                for wc in line.condition_id.waterconnection_ids:
                    specific_prorations[wc.id] = line.specific_proration
            consumptions_by_proration = {}
            for consumption in consumptions:
                wc_id = consumption.waterconnection_id.id
                if is_wua_type and wc_id in specific_prorations:
                    proration = specific_prorations[wc_id]
                else:
                    proration = preswatering.proration
                if proration not in consumptions_by_proration:
                    consumptions_by_proration[proration] = []
                consumptions_by_proration[proration].append(consumption)
            for proration, grouped_consumptions in \
                    consumptions_by_proration.items():
                max_nominal_flow = partner_area * proration
                total_nominal_flow_ls = sum(
                    c.nominal_flow_ls for c in grouped_consumptions)
                if total_nominal_flow_ls > max_nominal_flow and is_wua_type:
                    for consumption in grouped_consumptions:
                        requested_flow = consumption.nominal_flow_ls
                        prorated_flow = (requested_flow * max_nominal_flow) / \
                            total_nominal_flow_ls
                        prorated_flow_rounded = 5 * (
                            (prorated_flow + 2.5) // 5)
                        consumption.write({
                            'nominal_flow_granted':
                                prorated_flow_rounded * 3.6,
                            'nominal_flow_ls_granted': prorated_flow_rounded,
                        })
                else:
                    for consumption in grouped_consumptions:
                        consumption.write({
                            'nominal_flow_granted': consumption.nominal_flow,
                            'nominal_flow_ls_granted':
                                consumption.nominal_flow_ls,
                        })

    # Hook: Ensure only the same day is setted for the initial_time
    def _update_condition(self, condition):
        condition = super(WuaPresreswatering, self)._update_condition(
            condition)
        initial_time = fields.Datetime.from_string(self.initial_time)
        end_of_day = datetime.combine(initial_time.date(), time(23, 59, 59))
        condition.append(
            ('request_time', '<', end_of_day.strftime('%Y-%m-%d %H:%M:%S')))
        return condition

    @api.multi
    def validate_presresconsumptions(self):
        self.ensure_one()
        initial_time_utc = fields.Datetime.from_string(self.initial_time)
        spain_tz = pytz.timezone('Europe/Madrid')
        initial_time_sp = pytz.utc.localize(
            initial_time_utc).astimezone(spain_tz)
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        current_time_sp = pytz.utc.localize(
            current_time_utc_dt).astimezone(spain_tz)
        request_day = initial_time_sp.date()
        # Day before at 12:00
        start_range = datetime.combine(
            request_day - timedelta(days=1), datetime.min.time()).replace(
                hour=12)
        start_range = spain_tz.localize(start_range)
        # Day of the request at 08:00
        end_range = datetime.combine(
            request_day, datetime.min.time()).replace(hour=8)
        end_range = spain_tz.localize(end_range)
        if start_range <= current_time_sp <= end_range:
            return super(WuaPresreswatering, self).\
                validate_presresconsumptions()
        else:
            raise exceptions.UserError(_(
                'You can only validate the consumptions starting from '
                '12:00 on the previous day until 08:00 of the request date.',
            ))

    @api.multi
    def issue_presresconsumptions(self):
        self.ensure_one()
        initial_time_utc = fields.Datetime.from_string(self.initial_time)
        spain_tz = pytz.timezone('Europe/Madrid')
        initial_time_sp = pytz.utc.localize(initial_time_utc).astimezone(
            spain_tz)
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        current_time_sp = pytz.utc.localize(current_time_utc_dt).astimezone(
            spain_tz)
        today_0800_sp = current_time_sp.replace(
            hour=8, minute=0, second=0, microsecond=0)
        valid_start = (today_0800_sp - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        valid_end = today_0800_sp
        if valid_start <= initial_time_sp < valid_end:
            return super(WuaPresreswatering, self).issue_presresconsumptions()
        else:
            raise exceptions.UserError(_(
                'You can only issue the consumptions from the previous day '
                'until 08:00 of the current day'))

    def _get_sinema_consumptions(self):
        consumption_data = {}
        response_data = self._send_sinema_remote_data(
            {"variableName": "*_QMedio_24h*"}, method='get')
        if response_data and 'variables' in response_data:
            variable_names = [
                var['variableName'] for var in response_data['variables']]
            if variable_names:
                payload = {'variableNames': variable_names}
                values_response = self._send_sinema_remote_data(
                    payload, method='post')
                if values_response and self._handle_sinema_response(
                        values_response):
                    json_content = json.dumps(values_response, indent=4)
                    current_time_str = fields.Datetime.now()
                    filename = 'sinema_response_all_data_{}.json'.format(
                        current_time_str)
                    self.env['ir.attachment'].create({
                        'name': filename,
                        'res_model': self._name,
                        'res_id': self.id,
                        'type': 'binary',
                        'datas': base64.b64encode(
                            json_content.encode('utf-8')),
                        'datas_fname': filename,
                        'mimetype': 'application/json',
                    })
                    consumption_data = {
                        var['variableName']: float(var['value'])
                        for var in values_response
                        if float(var['value']) > 0
                    }
        if not consumption_data:
            self.message_post(body=_(
                'No valid consumption data received from SINEMA.'))
        return consumption_data

    def get_sinema_issued_consumptions(self):
        current_time_utc = datetime.utcnow()
        spain_tz = pytz.timezone('Europe/Madrid')
        current_time_sp = pytz.utc.localize(current_time_utc).astimezone(
            spain_tz)
        today_date_sp = current_time_sp.date()
        yesterday_date_sp = today_date_sp - timedelta(days=1)
        valid_start_sp = spain_tz.localize(
            datetime(yesterday_date_sp.year, yesterday_date_sp.month,
                     yesterday_date_sp.day, 0, 0, 0))
        valid_end_sp = spain_tz.localize(
            datetime(yesterday_date_sp.year, yesterday_date_sp.month,
                     yesterday_date_sp.day, 23, 59, 59))
        valid_start_utc = valid_start_sp.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        valid_end_utc = valid_end_sp.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        preswaterings = self.search([
            ('initial_time', '>=', valid_start_utc),
            ('initial_time', '<=', valid_end_utc),
            ('state', '=', '03_validated'),
        ])
        for preswatering in preswaterings:
            try:
                preswatering.issue_presresconsumptions()
            except Exception as e:
                _logger.error(
                    'Error issuing preswatering %s: %s', preswatering, e)

    def simulate_adjusted_total(self, grouped, field, dynamic_proration):
        total = 0.0
        for request, consumptions in grouped.items():
            is_wua = request.partner_id.partner_type == '01_WUA'
            partner_area = request.partner_parcel_owner_area
            if not is_wua or partner_area <= 0:
                total += sum(c[field] for c in consumptions)
                continue
            max_flow = partner_area * dynamic_proration
            sum_flow = sum(c[field] for c in consumptions)
            if sum_flow > max_flow:
                for c in consumptions:
                    prorated = (c[field] * max_flow) / sum_flow
                    rounded = 5 * ((prorated + 2.5) // 5)
                    total += max(0, rounded)
            else:
                total += sum(c[field] for c in consumptions)
        return total

    def _apply_dynamic_proration(self, condition_line, attempt=0):
        field = 'nominal_flow_ls'
        preswatering = self
        target_value = float(condition_line.check_value)
        waterconnections = condition_line.condition_id.waterconnection_ids
        all_consumptions = self.env['wua.presresconsumption'].search([
            ('preswatering_id', '=', preswatering.id),
            ('selected', '=', True),
            ('waterconnection_id', 'in', waterconnections.ids),
        ])
        grouped = {}
        for c in all_consumptions:
            grouped.setdefault(c.preswateringrequest_id, []).append(c)
        wua_requests = [
            r for r in grouped
            if r.partner_id.partner_type == '01_WUA'
        ]
        total_area = sum(
            r.partner_parcel_owner_area
            for r in wua_requests
            if r.partner_parcel_owner_area > 0
        )
        if total_area <= 0 or target_value <= 0:
            return
        dynamic_proration = target_value / total_area
        max_iterations = condition_line.condition_id.max_iterations
        tolerance = condition_line.condition_id.tolerance
        iteration_step = condition_line.condition_id.iteration_step
        iteration = 0
        while (iteration < max_iterations):
            simulated_total = self.simulate_adjusted_total(
                grouped, field, dynamic_proration)
            if (target_value - simulated_total <= tolerance and
                    simulated_total <= target_value):
                break
            elif simulated_total < target_value:
                dynamic_proration *= iteration_step
            else:
                dynamic_proration *= 0.98
            iteration += 1
        total_adjusted = 0.0
        for request, consumptions in grouped.items():
            is_wua_type = request.partner_id.partner_type == '01_WUA'
            partner_area = request.partner_parcel_owner_area
            if is_wua_type and partner_area > 0:
                max_nominal_flow = partner_area * dynamic_proration
                total_nominal_flow = sum(c[field] for c in consumptions)
                if total_nominal_flow > max_nominal_flow:
                    for c in consumptions:
                        requested_flow = c[field]
                        prorated = (requested_flow * max_nominal_flow) / \
                            total_nominal_flow
                        rounded = 5 * ((prorated + 2.5) // 5)
                        rounded = max(0, rounded)
                        c.write({
                            'nominal_flow_granted': rounded * 3.6,
                            'nominal_flow_ls_granted': rounded,
                        })
                        total_adjusted += rounded
                else:
                    for c in consumptions:
                        c.write({
                            'nominal_flow_granted': c.nominal_flow,
                            'nominal_flow_ls_granted': c.nominal_flow_ls,
                        })
                        total_adjusted += c.nominal_flow_ls
            else:
                for c in consumptions:
                    c.write({
                        'nominal_flow_granted': c.nominal_flow,
                        'nominal_flow_ls_granted': c.nominal_flow_ls,
                    })
                    total_adjusted += c.nominal_flow_ls
        condition_line.write({
            'proration_factor_used': dynamic_proration,
        })

    def _update_preswatering_times(self, presresconsumptions):
        request_times = presresconsumptions.mapped('request_time')
        durations = presresconsumptions.mapped('watering_duration')
        if request_times:
            watering_initial_time = min(
                fields.Datetime.from_string(rt) for rt in request_times)
            latest_request_time = max(
                fields.Datetime.from_string(rt) for rt in request_times)
            max_duration = max(durations or [0])
            watering_end_time = latest_request_time + timedelta(
                hours=max_duration)
            preswatering_duration = int(
                (watering_end_time - watering_initial_time).total_seconds() /
                60)
            self.write({
                'preswatering_initial_time': watering_initial_time,
                'preswatering_duration': preswatering_duration,
                'state': '02_calculated',
            })

    @api.multi
    def calculate_presresconsumptions(self):
        self.ensure_one()
        presresconsumptions = self.env['wua.presresconsumption'].search([
            ('preswatering_id', '=', self.id),
            ('selected', '=', True),
        ])
        if presresconsumptions:
            max_attempts = 5
            attempt = 0
            all_conditions_ok = False
            self._process_granted_nominal_flows(presresconsumptions, self)
            while attempt < max_attempts and not all_conditions_ok:
                self.update_conditions()
                # ONly for the first attempt and if first prorration is not 0
                # we set the result_value_first_proration to the
                # result_value of the condition line
                if (attempt == 0):
                    for condition in self.condition_line_ids:
                        if condition.result_value_first_proration == 0.0:
                            condition.result_value_first_proration = \
                                condition.result_value
                not_ok_lines = self.condition_line_ids.filtered(
                    lambda l: l.state == '03_not_ok' and
                    l.condition_id.apply_second_proration)
                all_conditions_ok = not not_ok_lines
                if not all_conditions_ok:
                    for line in not_ok_lines:
                        self._apply_dynamic_proration(line, attempt=attempt)
                attempt += 1
            self._update_preswatering_times(presresconsumptions)

    def generate_daily_preswatering(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        yesterday = today - timedelta(days=1)
        last_preswatering = self.search([
            ('initial_time', '>=', yesterday.strftime('%Y-%m-%d 00:00:00')),
            ('initial_time', '<=', yesterday.strftime('%Y-%m-%d 23:59:59')),
        ], order='initial_time desc', limit=1)
        if last_preswatering:
            initial_time = fields.Datetime.from_string(
                last_preswatering.initial_time) + timedelta(days=1)
            preswatering_period = self.env['wua.preswateringperiod'].search([
                ('initial_date', '<=', str(today)),
                ('end_date', '>=', str(today)),
            ], limit=1)
            number = 1
            if (preswatering_period and
                    preswatering_period.preswatering_ids):
                number = sorted(
                    preswatering_period.preswatering_ids,
                    key=lambda x: x.number)[-1].number + 1
            condition_lines = []
            for condition in last_preswatering.condition_line_ids:
                condition_lines.append((0, 0, {
                    'condition_id': condition.condition_id.id,
                    'specific_proration': preswatering_period.proration,
                    'state': '01_not_checked',
                }))
            new_preswatering = self.create({
                'preswateringperiod_id': preswatering_period.id,
                'number': number,
                'state': '01_draft',
                'initial_time': initial_time,
                'proration': preswatering_period.proration,
                'condition_line_ids': condition_lines,
            })
            new_preswatering._onchange_preswateringperiod_id()
            new_preswatering.select_presresconsumptions()
            new_preswatering.calculate_presresconsumptions()
            new_preswatering.validate_presresconsumptions()

    def _process_issued_nominal_flows(self, presresconsumptions, preswatering):
        response = super(WuaPresreswatering, self).\
            _process_issued_nominal_flows(presresconsumptions, preswatering)
        consumption_data = self._get_sinema_consumptions()
        global_initial_hour = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'default_presresconsumption_initial_hour')
        if consumption_data:
            siemens_ids = [
                name.split('_QMedio_24h')[0] for name in
                consumption_data.keys()]
            waterconnections = self.env['wua.waterconnection'].search(
                [('siemens_id', 'in', siemens_ids)])
            for wc in waterconnections:
                variable_name = '%s_QMedio_24h' % wc.siemens_id
                if variable_name in consumption_data:
                    consumption = consumption_data[variable_name]
                    partner_id = wc.partner_id.id
                    if not partner_id:
                        continue
                    preswatering_date = fields.Datetime.from_string(
                        preswatering.initial_time).date().strftime('%Y-%m-%d')
                    request = self.env['wua.preswateringrequest'].search([
                        ('partner_id', '=', partner_id),
                        ('initial_date', '=', preswatering_date),
                    ], limit=1)
                    if request:
                        existing_consumption = self.env[
                            'wua.presresconsumption'].search([
                                ('preswateringrequest_id', '=', request.id),
                                ('waterconnection_id', '=', wc.id),
                            ], limit=1)
                        if existing_consumption:
                            existing_consumption.nominal_flow_ls_issued = \
                                consumption
                        else:
                            self.env['wua.presresconsumption'].create({
                                'preswateringrequest_id': request.id,
                                'waterconnection_id': wc.id,
                                'nominal_flow': 0.0,
                                'nominal_flow_ls': 0.0,
                                'nominal_flow_ls_issued': consumption,
                                'preswatering_id': preswatering.id,
                                'initial_hour': global_initial_hour,
                                'state': '03_issued',
                                'from_remotecontrol': True,
                            })
                    else:
                        new_request = self.env[
                            'wua.preswateringrequest'].create({
                                'partner_id': partner_id,
                                'initial_date': preswatering_date,
                                'preswateringperiod_id':
                                    preswatering.preswateringperiod_id.id,
                                'user_id': self.env.user.id,
                                'state': '02_validated',
                                'preswateringperiod_id':
                                    preswatering.preswateringperiod_id.id,
                                'from_remotecontrol': True,
                            })
                        self.env['wua.presresconsumption'].create({
                            'preswateringrequest_id': new_request.id,
                            'waterconnection_id': wc.id,
                            'nominal_flow': 0.0,
                            'nominal_flow_ls': 0.0,
                            'nominal_flow_ls_issued': consumption,
                            'preswatering_id': preswatering.id,
                            'initial_hour': global_initial_hour,
                            'state': '03_issued',
                            'from_remotecontrol': True,
                        })
        return response


class WuaPreswateringCondition(models.Model):

    _inherit = 'wua.preswatering.condition'

    apply_second_proration = fields.Boolean(
        string='Apply Second Proration',
        default=True,
    )

    max_iterations = fields.Integer(
        string='Max Iterations',
        default=20,
    )

    tolerance = fields.Float(
        string='Tolerance (l/s)',
        default=50,
    )

    iteration_step = fields.Float(
        string='Iteration Step',
        default=1.03,
    )


class WuaPreswateringConditionLine(models.Model):

    _inherit = 'wua.preswatering.condition.line'

    specific_proration = fields.Float(
        string='Specific Proration',
        required=True,
        digits=(32, 2),
        default=1.0,
    )

    proration_factor_used = fields.Float(
        string='Proration Factor Dynamic',
        digits=(32, 2),
    )

    result_value_first_proration = fields.Float(
        string='Value First Proration',
        digits=(32, 4),
    )

    @api.model
    def create(self, vals):
        if 'preswatering_id' in vals:
            preswatering = self.env['wua.preswatering'].browse(
                vals['preswatering_id'])
            vals['specific_proration'] = preswatering.proration
        return super(WuaPreswateringConditionLine, self).create(vals)
