# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pytz
import logging
import json
import base64
from datetime import datetime, timedelta
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

    def _process_granted_nominal_flows(
            self, presresconsumptions, preswatering):
        presres_grouped = {}
        # Group by wateringrequest
        for presresconsumption in presresconsumptions:
            key = presresconsumption.preswateringrequest_id
            if key not in presres_grouped:
                presres_grouped[key] = []
            presres_grouped[key].append(presresconsumption)
        # Calculation
        for preswateringrequest_id, consumptions in presres_grouped.items():
            partner_area = preswateringrequest_id.partner_parcel_owner_area
            is_wua_type = preswateringrequest_id.partner_id.partner_type == \
                '01_WUA'
            max_nominal_flow = partner_area * preswatering.proration
            total_nominal_flow_ls = sum(
                c.nominal_flow_ls for c in consumptions)
            # Proration
            if total_nominal_flow_ls > max_nominal_flow and is_wua_type:
                for consumption in consumptions:
                    requested_flow = consumption.nominal_flow_ls
                    prorated_flow = (requested_flow * max_nominal_flow) / \
                        total_nominal_flow_ls
                    # Floor to the nearest 5
                    prorated_flow_rounded = 5 * (
                        (prorated_flow + 2.5) // 5)
                    consumption.write({
                        'nominal_flow_granted': prorated_flow_rounded * 3.6,
                        'nominal_flow_ls_granted': prorated_flow_rounded,
                    })
            else:
                for consumption in consumptions:
                    consumption.write({
                        'nominal_flow_granted': consumption.nominal_flow,
                        'nominal_flow_ls_granted': consumption.nominal_flow_ls,
                    })

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
                    json_content = json.dumps(response_data, indent=4)
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

    @api.model
    def get_sinema_issued_consumptions(self):
        current_time_utc = fields.Datetime.now()
        current_time_utc_dt = fields.Datetime.from_string(current_time_utc)
        spain_tz = pytz.timezone('Europe/Madrid')
        current_time_sp = pytz.utc.localize(current_time_utc_dt).astimezone(
            spain_tz)
        today_0800_sp = current_time_sp.replace(
            hour=8, minute=0, second=0, microsecond=0)
        valid_start = (today_0800_sp - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        valid_end = today_0800_sp
        valid_start_utc = valid_start.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        valid_end_utc = valid_end.astimezone(pytz.utc).strftime(
            '%Y-%m-%d %H:%M:%S')
        preswaterings = self.search([
            ('initial_time', '>=', valid_start_utc),
            ('initial_time', '<', valid_end_utc),
            ('state', '=', '02_validated'),
        ])
        for preswatering in preswaterings:
            try:
                preswatering.issue_presresconsumptions()
            except Exception as e:
                _logger.error(
                    'Error issuing preswatering %s: %s', preswatering, e)

    def _process_issued_nominal_flows(self, presresconsumptions, preswatering):
        response = super(WuaPresreswatering, self).\
            _process_issued_nominal_flows(presresconsumptions, preswatering)
        consumption_data = self._get_sinema_consumptions()
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
                                'nominal_flow_ls_issued': consumption,
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
                            })
                        self.env['wua.presresconsumption'].create({
                            'preswateringrequest_id': new_request.id,
                            'waterconnection_id': wc.id,
                            'nominal_flow_ls_issued': consumption,
                            'preswatering_id': preswatering.id,
                        })
        return response
