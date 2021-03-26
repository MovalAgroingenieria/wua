# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import requests
import json
import logging
from odoo import models, api, exceptions, _


class WuaTankconsumption(models.Model):
    _inherit = 'wua.tankconsumption'

    def get_token(self, url_remotecontrol_rest,
                  url_remotecontrol_rest_username,
                  url_remotecontrol_rest_password):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/token'
        auth_data = {
            'username': url_remotecontrol_rest_username,
            'password': url_remotecontrol_rest_password,
            'grant_type': 'password',
        }
        headers_data = {
            'content-type': 'application/json',
        }
        resprest = requests.post(url_open_session,
                                 data=auth_data,
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            outputrest = json.loads(resprest.text)
            resp = outputrest['access_token']
        return resp, error_message

    @api.model
    def do_import_tankconsumptions(self, save_data=True, show_message=True):
        # for resp: item 1: list of consumpt, item 2: number of
        # # tankconsumptions,
        # item 3: possible error message, item 4: list of problematic
        # tanks
        resp = [None, 0, '', None]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_tankconsumptions = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_tankconsumptions')
        there_are_tankconsumptions_not_validated = False
        tankconsumptions_not_validated = self.env['wua.tankconsumption'].\
            search([('validated', '=', False)])
        if tankconsumptions_not_validated:
            there_are_tankconsumptions_not_validated = True
        if (enable_remotecontrol and import_from_tankconsumptions and
           not there_are_tankconsumptions_not_validated):
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'url_remotecontrol_rest')
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username')
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password')
            if (url_remotecontrol_rest and url_remotecontrol_rest_username and
               url_remotecontrol_rest_password):
                data = self.populate_data_for_import_tankconsumptions(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    tankconsumptions, error_message, error_tanks = \
                        self.import_tankconsumptions(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
                    tankconsumptions = self.refine_tankconsumptions(
                        tankconsumptions)
                    if tankconsumptions:
                        resp[0] = tankconsumptions
                        resp[1] = len(tankconsumptions)
                        resp[2] = error_message
                        resp[3] = error_tanks
                        if save_data:
                            self.save_tankconsumptions(tankconsumptions)
                        prefix_message_01 = _('Remote Control: '
                                              'Getting tankconsumptions')
                        suffix_message_01 = str(resp[1])
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info(prefix_message_01 + '... ' +
                                     suffix_message_01)
                        if error_message:
                            prefix_message_02 = _('Remote Control: '
                                                  'Error getting '
                                                  'tankconsumptions')
                            suffix_message_02 = error_message
                            _logger = logging.getLogger(
                                self.__class__.__name__)
                            _logger.info(prefix_message_02 + '... ' +
                                         suffix_message_02)
        else:
            if show_message:
                if there_are_tankconsumptions_not_validated:
                    raise exceptions.UserError(_('There are tankconsumptions '
                                                 'not validated. Please, first'
                                                 ' validate or delete them.'))
                else:
                    raise exceptions.UserError(_('The communication with '
                                                 'the remote control is not '
                                                 'enabled.'))
        return resp

    # Hook
    def populate_data_for_import_tankconsumptions(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        return True

    def import_tankconsumptions(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        tankconsumptions = []
        error_message = ''
        error_tanks = []
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            from_date = '1970-01-01'
            to_date = '9999-12-31'
            # Check if all tanks have consumptions and in that case
            # check for the last consumptions to ask for
            if len(self.env['wua.tank'].search(
                    [('with_tankconsumptions', '=', False)])) > 0:
                all_tankconsumptions = self.env['wua.tankconsumption'].search(
                    [], order='end_time desc')
                if (all_tankconsumptions and all_tankconsumptions[0]):
                    from_date = datetime.datetime.strptime(
                        all_tankconsumptions[0].initial_time,
                        '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            url_get_tankconsumptions = url_remotecontrol_rest + \
                '/api/asientosCubas?desde=' + from_date + '&hasta=' + to_date
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.get(url_get_tankconsumptions,
                                    headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                for tank_info in outputrest:
                    tank = tank_info['Cuba']
                    volume_request = tank_info['CantidadSolicitada']
                    volume_real = tank_info['CantidadRegada']
                    partner = tank_info['Pagador']
                    initial_time = tank_info['Inicio']
                    end_time = tank_info['Fin']
                    # Localize dates
                    try:
                        initial_time = datetime.datetime.strptime(
                            initial_time, '%Y-%m-%dT%H:%M:%S.%f')
                    except Exception:
                        initial_time = datetime.datetime.strptime(
                            initial_time, '%Y-%m-%dT%H:%M:%S')
                    initial_time = pytz.timezone('Europe/Madrid').\
                        localize(initial_time)
                    initial_time = initial_time.astimezone(
                        pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
                    try:
                        end_time = datetime.datetime.strptime(
                            end_time, '%Y-%m-%dT%H:%M:%S.%f')
                    except Exception:
                        end_time = datetime.datetime.strptime(
                            end_time, '%Y-%m-%dT%H:%M:%S')
                    end_time = pytz.timezone('Europe/Madrid').\
                        localize(end_time)
                    end_time = end_time.astimezone(
                        pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')
                    tankconsumptions.append({
                        'tank': tank,
                        'volume_request': volume_request,
                        'volume_real': volume_real,
                        "partner_id": partner,
                        "initial_time": initial_time,
                        "end_time": end_time
                    })
            else:
                error_message = _(' It is not possible to get the '
                                  'tankconsumptions. ')
        return [tankconsumptions, error_message, error_tanks]
        return None, '', None

    def refine_tankconsumptions(self, tankconsumptions):
        resp = []
        tanks = self.env['wua.tank']
        partners = self.env['res.partner']
        for tankconsumption in tankconsumptions:
            filtered_tank = tanks.search(
                [('name', '=', tankconsumption['tank'])])
            if filtered_tank:
                tank = filtered_tank[0]
                #  Check if already exists this consumption
                # (PK == NAME - end_time)
                existing_tankconsumption = tank.tankconsumption_ids.search(
                    [('end_time', '=', tankconsumption['end_time'])])
                # Check if partner exists
                partner = partners.search(
                    [('partner_code', '=', tankconsumption['partner_id'])])
                if (partner and partner[0] and not existing_tankconsumption):
                    partner = partner[0]
                    refined_tank = {
                        'tank_id': tank.id,
                        'tank_name': tank.name,
                        'partner_id': partner.id,
                        'volume_request': tankconsumption['volume_request'],
                        'volume_real': tankconsumption['volume_real'],
                        "initial_time": tankconsumption['initial_time'],
                        "end_time": tankconsumption['end_time'],
                    }
                    resp.append(refined_tank)
        return resp

    def save_tankconsumptions(self, tankconsumptions, update_log=True):
        number_of_tankconsumptions = len(tankconsumptions)
        if number_of_tankconsumptions > 0:
            for tankconsumption in tankconsumptions:
                self.create({
                    'tank_id': tankconsumption['tank_id'],
                    'partner_id': tankconsumption['partner_id'],
                    'initial_time': tankconsumption['initial_time'],
                    'end_time': tankconsumption['end_time'],
                    'volume_request': tankconsumption['volume_request'],
                    'volume_real': tankconsumption['volume_real'],
                    'validated': False,
                    })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved tankconsumptions') +
                             '... ' + str(number_of_tankconsumptions))
        return 0
