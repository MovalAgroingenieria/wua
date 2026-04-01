# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import base64
import json
import time
import traceback
from odoo import models, fields, api, _, exceptions


class WuaPresreswatering(models.Model):
    _inherit = 'wua.preswatering'

    consumptions_sended = fields.Boolean(
        string='Remotecontrol sended',
        default=False,
    )

    waterconnections_without_remotecontrol_msg = fields.Char(
        string='Waterconnections without remotecontrol',
        compute='_compute_waterconnections_without_remotecontrol_msg',
        store=False,
    )

    def _send_sinema_remote_data(self, payload, method='put'):
        url = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'sinema_endpoint')
        username = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'sinema_username')
        password = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'sinema_password')
        if (not url or not username or not password):
            raise exceptions.UserError(_(
                'You must configure the SINEMA remotecontrol settings'))
        if method.lower() == 'get':
            variable_name = '*'
            if (payload and 'variableName' in payload):
                variable_name = payload['variableName']
            url = '%s/tagManagement/variables?variableName=%s' % (
                url, variable_name)
        else:
            url = '%s/tagManagement/Values' % (url)
        auth_string = '{}:{}'.format(username, password)
        auth_base64 = base64.b64encode(
            auth_string.encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': 'Basic {}'.format(auth_base64),
            'Content-Type': 'application/json',
        }
        request_function = requests.put
        # Method get is not really a get method, just
        # uses another endpoint
        if method in ['post', 'get']:
            request_function = requests.post
        # Inestable connection, retry X times
        # TODO: Transform this to a parameter
        max_retries = 10
        base_sleep = 10
        for attempt in range(1, max_retries + 1):
            try:
                response = request_function(
                    url,
                    json=payload,
                    headers=headers,
                    verify=False,
                    timeout=300,
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    self.message_post(body=_(
                        'Failed to send data to remote control. Status: %s, '
                        'Response: %s',
                    ) % (response.status_code, response.text))
                    return None
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:
                self.message_post(body=_(
                    'Network error during communication (attempt %s of %s):'
                    ' %s',
                ) % (attempt, max_retries, str(e)))
            except Exception:
                tb = traceback.format_exc()
                self.message_post(body=_(
                    'Unexpected error during communication '
                    '(attempt %s of %s):\n%s',
                ) % (attempt, max_retries, tb))
            if attempt == max_retries:
                self.message_post(body=_('Max retry attempts reached. '
                                         'Giving up.'))
                return None
            sleep_time = base_sleep * attempt
            time.sleep(sleep_time)
        return None

    def _handle_sinema_response(self, response_data):
        errors = []
        for item in response_data:
            if 'error' in item:
                errors.append(
                    '{}: {}'.format(
                        item.get('variableName', 'Unknown variable'),
                        item['error'],
                    ),
                )
        response_data[:] = [
            item for item in response_data if 'error' not in item]
        if errors:
            self.message_post(body=_(
                'The following variables encountered errors:\n%s',
            ) % '\n'.join(errors))
        return True

    @api.multi
    def _compute_waterconnections_without_remotecontrol_msg(self):
        for record in self:
            waterconnections_without_remotecontrol_msg = ''
            if record.presresconsumption_ids:
                wcs = record.presresconsumption_ids.filtered(
                    lambda x: x.selected).mapped(
                        'waterconnection_id').filtered(
                        lambda wc: not wc.siemens_id)
                if len(wcs) > 0:
                    waterconnections_without_remotecontrol_msg = _(
                        'Waterconnections without SIEMENS ID: ')
                    waterconnections_without_remotecontrol_msg += \
                        ', '.join(wcs.mapped('name'))
            record.waterconnections_without_remotecontrol_msg = \
                waterconnections_without_remotecontrol_msg

    @api.multi
    def cancel_preswatering(self):
        if self.consumptions_sended:
            # Check if some consumptions has been issued, in that case
            # we cannot reset the values in the remote control, because
            # this will cause a mismatch between the data used on SINEMA
            # AND the data stored in the database.
            if len(self.presresconsumption_ids.filtered(
                    lambda x: x.state == '03_issued')) > 0:
                raise exceptions.UserError(_(
                    'You cannot cancel a preswatering with issued '
                    'consumptions'))
            siemens_to_reset = self.presresconsumption_ids.filtered(
                lambda x: x.selected).mapped('waterconnection_id.siemens_id')
            siemens_to_reset = list(set(siemens_to_reset))
            payload = []
            for sid in siemens_to_reset:
                payload.append({
                    'variableName': '{}_Solicitado'.format(sid),
                    'value': 0,
                })
                payload.append({
                    'variableName': '{}_Concedido'.format(sid),
                    'value': 0,
                })
            response_data = self._send_sinema_remote_data(
                payload, method='put')
            if response_data and self._handle_sinema_response(response_data):
                self.consumptions_sended = False
                super(WuaPresreswatering, self).cancel_preswatering()
        else:
            super(WuaPresreswatering, self).cancel_preswatering()

    @api.multi
    def validate_presresconsumptions(self):
        self.ensure_one()
        selected_consumptions = self.presresconsumption_ids.filtered(
            lambda x: x.selected)
        if not selected_consumptions:
            self.message_post(body=_(
                'No selected consumptions found. '
                'Skipping SINEMA communication.'))
            return super(WuaPresreswatering, self,
                         ).validate_presresconsumptions()
        siemens_data = {}
        for consumption in selected_consumptions.filtered(
                lambda x: x.waterconnection_id.siemens_id):
            siemens_id = consumption.waterconnection_id.siemens_id
            if siemens_id not in siemens_data:
                siemens_data[siemens_id] = {
                    'nominal_flow_ls': 0,
                    'nominal_flow_ls_granted': 0,
                }
            siemens_data[siemens_id]['nominal_flow_ls'] += \
                consumption.nominal_flow_ls
            siemens_data[siemens_id]['nominal_flow_ls_granted'] += \
                consumption.nominal_flow_ls_granted
        payload = []
        for sid, data in siemens_data.items():
            payload.append({
                'variableName': '{}_Solicitado'.format(sid),
                'value': data['nominal_flow_ls'],
            })
            payload.append({
                'variableName': '{}_Concedido'.format(sid),
                'value': data['nominal_flow_ls_granted'],
            })
        response_data = self._send_sinema_remote_data(
            payload, method='put')
        if response_data and self._handle_sinema_response(response_data):
            self.consumptions_sended = True
            super(WuaPresreswatering, self).validate_presresconsumptions()

    def _process_issued_nominal_flows(self, presresconsumptions, preswatering):
        selected_consumptions = self.presresconsumption_ids.filtered(
            lambda x: x.selected)
        if not selected_consumptions:
            self.message_post(body=_(
                'No selected consumptions found. '
                'Skipping SINEMA communication.'))
            return super(WuaPresreswatering, self,
                         )._process_issued_nominal_flows(
                presresconsumptions, preswatering)
        for presresconsumption in presresconsumptions:
            siemens_data = {}
            for consumption in selected_consumptions.filtered(
                    lambda x: x.waterconnection_id.siemens_id):
                siemens_id = consumption.waterconnection_id.siemens_id
                if siemens_id not in siemens_data:
                    siemens_data[siemens_id] = []
                siemens_data[siemens_id].append(consumption)
            payload = {'variableNames': []}
            for sid, data in siemens_data.items():
                payload['variableNames'].append(
                    '{}_QMedio_24h'.format(sid))
            response_data = self._send_sinema_remote_data(
                payload, method='post')
            if response_data and self._handle_sinema_response(response_data):
                # Save json response for future reference
                json_content = json.dumps(response_data, indent=4)
                current_time_str = fields.Datetime.now()
                filename = 'sinema_response_{}.json'.format(
                    current_time_str)
                self.env['ir.attachment'].create({
                    'name': filename,
                    'res_model': preswatering._name,
                    'res_id': preswatering.id,
                    'type': 'binary',
                    'datas': base64.b64encode(json_content.encode('utf-8')),
                    'datas_fname': filename,
                    'mimetype': 'application/json',
                })
                # Process issued consumptions
                for response_item in response_data:
                    siemens_id = response_item[
                        'variableName'].split('_QMedio_24h')[0]
                    issued_consumption = float(response_item['value'])
                    if siemens_id in siemens_data:
                        consumptions = siemens_data[siemens_id]
                        # More than one consumption you must distribute
                        if (len(consumptions) > 0):
                            total_granted = sum(
                                c.nominal_flow_ls_granted for c in consumptions
                            )
                            if total_granted > 0:
                                for consumption in consumptions:
                                    proportion = (
                                        consumption.nominal_flow_ls_granted /
                                        total_granted
                                    )
                                    consumption.nominal_flow_ls_issued = \
                                        issued_consumption * proportion
                        # Only one consumption
                        else:
                            consumptions[0].nominal_flow_ls_issued = \
                                issued_consumption
                return True
            else:
                return False
