# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
import datetime
import logging
import pytz
from odoo import models, _, fields

_logger = logging.getLogger(__name__)

# Timeout for HTTP requests to the Inelcom REST API (seconds)
HTTP_TIMEOUT = 30


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

    def _get_last_event_dates_for_wcs(self, wc_ids):
        """Pre-fetch last irrigation_end_date per waterconnection
        using a single SQL query.  Returns dict {wc_id: end_date_str}.
        """
        if not wc_ids:
            return {}
        self.env.cr.execute("""
            SELECT waterconnection_id,
                   MAX(irrigation_end_date) AS last_end
            FROM wua_waterconnection_irrigation_event
            WHERE waterconnection_id IN %s
            GROUP BY waterconnection_id
        """, (tuple(wc_ids),))
        return {
            row['waterconnection_id']: row['last_end']
            for row in self.env.cr.dictfetchall()
        }

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

        # If not list of wc, search all watermeters
        if not list_of_wc:
            list_of_wc = self.env['wua.waterconnection'].search([
                ('watermeter_id', '!=', None),
                ('watermeter_id.state', '=', 'active'),
                ('hydraulicsector_id.inelcom_id', '!=', False)])

        if not list_of_wc:
            return [wc_irr_event_all_info, error_message]

        _logger.info(
            'Inelcom irrigation event import: '
            'processing %d waterconnections', len(list_of_wc))

        # Pre-fetch last event dates to avoid N+1 on
        # wc.last_irrigation_event_id (which triggers stored compute
        # and loads all events via One2many)
        wc_ids = list_of_wc.ids if hasattr(list_of_wc, 'ids') else [
            w.id for w in list_of_wc]
        last_event_dates = self._get_last_event_dates_for_wcs(wc_ids)

        # Global config: fallback start date
        config_start_date = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'irrigation_events_start_date')
        config_start_date = fields.Date.from_string(config_start_date)
        end_date = fields.Datetime.from_string(
            fields.Datetime.now()).strftime('%d-%m-%y')

        # Open ONE session for the entire batch (reuse if possible)
        id_session = None
        for idx, wc in enumerate(list_of_wc):
            try:
                # Open session (reuse or refresh)
                if not id_session:
                    resprest = requests.post(
                        url_open_session,
                        data=json.dumps(auth_data),
                        headers=headers_data,
                        timeout=HTTP_TIMEOUT)
                    if resprest.status_code != 200 or not resprest.text:
                        error_message += (
                            _(' Session open failed for WC %s. ')
                            % wc.name) + resprest.text + ' \n'
                        continue
                    id_session = resprest.text

                # Determine start date for this WC
                last_end = last_event_dates.get(wc.id)
                if last_end:
                    start_date = fields.Datetime.from_string(
                        last_end).strftime('%d-%m-%y')
                else:
                    start_date = config_start_date.strftime('%d-%m-%y')

                url_get_wc_irr_event_info = (
                    url_remotecontrol_rest +
                    '/hidrantes/informesriego' +
                    '?sesion=' + id_session +
                    '&cabezal=' + wc.hydraulicsector_id.inelcom_id +
                    '&contador=' + wc.watermeter_id.name +
                    '&inicio=' + start_date +
                    '&fin=' + end_date)
                resprest = requests.get(
                    url_get_wc_irr_event_info,
                    headers=headers_data,
                    timeout=HTTP_TIMEOUT)

                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    if outputrest['codError'] == 0:
                        for irrig_event in outputrest['listaInformes']:
                            start_irr_date = (
                                irrig_event['fechaRiego'] + ' ' +
                                irrig_event['horaInicio'])
                            end_irr_date = (
                                irrig_event['fechaRiego'] + ' ' +
                                irrig_event['horaFin'])
                            start_irr_date = datetime.datetime.strptime(
                                start_irr_date, '%d-%m-%y %H:%M')
                            end_irr_date = datetime.datetime.strptime(
                                end_irr_date, '%d-%m-%y %H:%M')
                            if end_irr_date < start_irr_date:
                                end_irr_date = (
                                    end_irr_date +
                                    datetime.timedelta(days=1))
                            start_irr_date = spain_tz.localize(
                                start_irr_date).astimezone(
                                pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
                            end_irr_date = spain_tz.localize(
                                end_irr_date).astimezone(
                                pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
                            wc_irr_event_all_info.append({
                                'waterconnection_id': wc.id,
                                'irrigation_volume':
                                    irrig_event['volumen'],
                                'irrigation_start_date': start_irr_date,
                                'irrigation_end_date': end_irr_date,
                                'irrigation_area_static':
                                    irrig_event['superficie'],
                            })
                    else:
                        error_message += outputrest['textoError']
                elif resprest.status_code == 401:
                    # Session expired, force re-authentication
                    id_session = None
                    error_message += (
                        _(' Session expired for WC %s, '
                          'will retry. ') % wc.name + '\n')
                else:
                    error_message += (
                        _(' Represt code was not 200 for WC %s. ')
                        % wc.name) + resprest.text + ' \n'
            except requests.exceptions.Timeout:
                _logger.warning(
                    'Inelcom: HTTP timeout for WC %s (id=%d)',
                    wc.name, wc.id)
                error_message += (
                    _(' HTTP timeout for WC %s. ') % wc.name + '\n')
                # Invalidate session on timeout
                id_session = None
            except requests.exceptions.ConnectionError as e:
                _logger.warning(
                    'Inelcom: Connection error for WC %s: %s',
                    wc.name, str(e))
                error_message += (
                    _(' Connection error for WC %s: %s ')
                    % (wc.name, str(e)) + '\n')
                id_session = None
            except Exception as e:
                _logger.exception(
                    'Inelcom: unexpected error for WC %s (id=%d)',
                    wc.name, wc.id)
                error_message += (
                    u'Inelcom error for WC %s:\n%s\n'
                    % (wc.name, str(e)))

            # Log progress every 50 WCs
            if (idx + 1) % 50 == 0:
                _logger.info(
                    'Inelcom irrigation event import: '
                    'processed %d/%d WCs, %d events collected so far',
                    idx + 1, len(list_of_wc),
                    len(wc_irr_event_all_info))

        _logger.info(
            'Inelcom irrigation event import: '
            'finished - %d events from %d WCs',
            len(wc_irr_event_all_info), len(list_of_wc))
        return [wc_irr_event_all_info, error_message]
