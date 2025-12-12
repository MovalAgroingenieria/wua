# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
import datetime
import pytz
from odoo import models, _, fields


class WuaWaterconnectionIrrigationEvent(models.Model):
    _inherit = 'wua.waterconnection.irrigation.event'

    # Hook Implemented
    def do_import_waterconnection_irrigation_event_all(self, list_of_wc):
        # Get waterconnection irrigation event of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionIrrigationEvent, self).
                 do_import_waterconnection_irrigation_event_all(list_of_wc))
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_irrigation_event_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, list_of_wc)
            # Update already existing wc irrigation event data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message + '\n\n'
        return others_wc_info

    def import_waterconnection_irrigation_event_inelcom(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_wc):
        wc_irr_event_all_info = []
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
        }
        spain_tz = pytz.timezone('Europe/Madrid')
        try:
            # If not list of wc, search all watermeters
            # Must be watermeters because of the code searched
            if (not list_of_wc):
                list_of_wc = self.env['wua.waterconnection'].search([
                    ('watermeter_id', '!=', None),
                    ('watermeter_id.state', '=', 'active'),
                    ('hydraulicsector_id.inelcom_id', '!=', False)])
            for wc in list_of_wc:
                # Should we open a session every time ?
                resprest = requests.post(url_open_session,
                                         data=json.dumps(auth_data),
                                         headers=headers_data)
                if resprest.status_code == 200 and resprest.text:
                    id_session = resprest.text
                    # Start Date of the events to be created on config
                    start_date = self.env['ir.values'].\
                        get_default('wua.irrigation.configuration',
                                    'irrigation_events_start_date')
                    start_date = fields.Date.from_string(start_date)
                    # If WC already have some event, we importt only newers
                    if (wc.last_irrigation_event_id):
                        start_date = fields.Datetime.from_string(
                            wc.last_irrigation_event_id.irrigation_end_date)
                    start_date = start_date.strftime('%d-%m-%y')
                    end_date = fields.Datetime.from_string(
                        fields.Datetime.now()).strftime('%d-%m-%y')
                    url_get_wc_irr_event_info = url_remotecontrol_rest +\
                        '/hidrantes/informesriego' + '?sesion=' + id_session +\
                        '&cabezal=' + wc.hydraulicsector_id.inelcom_id +\
                        '&contador=' + wc.watermeter_id.name + '&inicio=' +\
                        start_date + '&fin=' + end_date
                    resprest = requests.get(
                        url_get_wc_irr_event_info, headers=headers_data)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (outputrest['codError'] == 0):
                            for irrig_event in outputrest['listaInformes']:
                                # Transform to just one var
                                start_irr_date = irrig_event['fechaRiego'] + \
                                    ' ' + irrig_event['horaInicio']
                                end_irr_date = irrig_event['fechaRiego'] + \
                                    ' ' + irrig_event['horaFin']
                                # Set as datetime
                                start_irr_date = datetime.datetime.strptime(
                                    start_irr_date, '%d-%m-%y %H:%M')
                                end_irr_date = datetime.datetime.strptime(
                                    end_irr_date, '%d-%m-%y %H:%M')
                                # If end time is before start time, event
                                # crosses midnight - add 1 day to end date
                                if end_irr_date < start_irr_date:
                                    end_irr_date = end_irr_date + \
                                        datetime.timedelta(days=1)
                                # Localize to UTC from ES
                                start_irr_date = spain_tz.localize(
                                    start_irr_date).astimezone(pytz.utc).\
                                    strftime('%Y-%m-%d %H:%M:%S')
                                end_irr_date = spain_tz.localize(
                                    end_irr_date).astimezone(pytz.utc).\
                                    strftime('%Y-%m-%d %H:%M:%S')
                                wc_irr_event_all_info.append({
                                    'waterconnection_id': wc.id,
                                    'irrigation_volume': irrig_event[
                                        'volumen'],
                                    'irrigation_start_date':
                                        start_irr_date,
                                    'irrigation_end_date':
                                        end_irr_date,
                                    'irrigation_area_static': irrig_event[
                                        'superficie'],
                                })
                        else:
                            error_message += outputrest['textoError']
                    else:
                        error_message += _(' Represt code was not 200. ') + \
                            resprest.text + ' \n'
                else:
                    error_message += _(' Represt code was not 200.') + \
                        resprest.text + ' \n'
        except Exception as e:
            error_message = u'Inelcom error:\n\n' + str(e)
        return [wc_irr_event_all_info, error_message]
