# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
import datetime
import logging
from odoo import models, api, exceptions, fields, _


class WuaWaterconnectionIrrigationSchedule(models.Model):
    _inherit = 'wua.waterconnection.irrigation.schedule'

    # Añadido irrigation_shift_id. Usado para el cambio en el
    # _compute_name del campo, lo queremos para algo más? Cómo lo relleno?
    irrigation_shift_id = fields.Many2one(
        string='Irrigation Shift',
        comodel_name='wua.waterconnection.irrigation.shift',
        )

    @api.depends('waterconnection_id', 'irrigation_start_day',
                 'irrigation_shift_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.irrigation_start_day and \
                    record.irrigation_shift_id:
                value = record.waterconnection_id.name + u'-' + \
                    record.irrigation_start_day + u'-' + \
                    str(record.shift_number) + record.irrigation_shift_id.name
            record.name = value

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

    # Aux method to transform week_day number format to selection format
    def _get_irr_day_from_letter(self, week_day):
        return {
            'l': '00_monday',
            'm': '01_tuesday',
            'x': '02_wednesday',
            'j': '03_thursday',
            'v': '04_friday',
            's': '05_saturday',
            'd': '06_sunday',
        }.get(week_day)

    # Aux method to get datetime from a %Y-%m-%dT%H:%M:%S
    def _get_datetime_from_date_str(self, date_str):
        date_format = "%Y-%m-%dT%H:%M:%S.%f" if '.' in \
            date_str else "%Y-%m-%dT%H:%M:%S"
        date = datetime.datetime.strptime(date_str, date_format)
        return date

    # Aux method to get the float hours from a string HH:MM
    def _get_float_hour_from_str(self, hour):
        time_split = hour.split(':')
        hours = float(time_split[0])
        minutes = float(time_split[1]) / 60
        return hours + minutes

    @api.model
    def do_import_waterconnection_irrigation_schedule(
            self, save_data=True, show_message=True, list_of_wc=False):
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if (enable_remotecontrol):
            wc_irr_schedule, error_message = \
                self.do_import_waterconnection_irrigation_schedule_all(
                    list_of_wc)
            wc_irr_schedule = self.refine_waterconnection_irrigation_schedule(
                wc_irr_schedule)
            if save_data:
                self.save_waterconnection_irrigation_schedule(wc_irr_schedule)
            if error_message:
                prefix_message = _('Remote Control: Error getting '
                                   'waterconnection irrigation schedule')
                suffix_message = error_message
                company_name = self.env.user.company_id.name
                website_url = self.env['ir.config_parameter'].get_param(
                    "web.base.url")
                domain = self.env['ir.config_parameter'].get_param(
                    "mail.catchall.domain")
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message + '... ' + suffix_message)
                telecontrol_failed_template_id = self.env.ref(
                    'base_wua_remotecontrol_rest.'
                    'telecontrol_failed_email_template').id
                mail_template = self.env['mail.template'].browse(
                    telecontrol_failed_template_id)
                mail_template.subject = '''
                    Waterconnection irrigation_schedule in %s
                    has experienced some problem
                ''' % (domain or self.pool.db_name)
                mail_template.body_html = '''
                    <p style="margin: 0px; padding: 0px; font-size: 13px;">
                        <b><a href="%s">%s</a></p></b>
                        <br/>
                        <span>%s</span>
                    </p>
                ''' % (website_url, company_name, error_message.replace('\n',
                                                                        '<br/>'
                                                                        ))
                mail_template.send_mail(self.id, force_send=True)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def refine_waterconnection_irrigation_schedule(self, wc_irr_schedule):
        resp = []
        for info in wc_irr_schedule:
            refined_wc_irr_schedule = {
                'waterconnection_id': info['waterconnection_id'],
                'irrigation_shift_id': info['irrigation_shift_id'],
                'state': info['state'],
                'shift_number': info['shift_number'],
                'irrigation_start_day': info['irrigation_start_day'],
                'irrigation_start_hour': info['irrigation_start_hour'],
                'irrigation_end_hour': info['irrigation_end_hour'],
                'irrigation_duration': info['irrigation_duration'],
                'max_irrigation_volume': info['max_irrigation_volume'],
                }
            resp.append(refined_wc_irr_schedule)
        return resp

    # Hook Implemented
    def do_import_waterconnection_irrigation_schedule_all(self, list_of_wc):
        # Get waterconnection irrigation schedule of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionIrrigationSchedule, self).
                 do_import_waterconnection_irrigation_schedule_all(list_of_wc))
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_batchline')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_batchline')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_batchline')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_irrigation_schedule_batchline(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, list_of_wc)
            # Update already existing wc irrigation schedule data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message + '\n\n'
        return others_wc_info

    def obtain_schedule_info(self, shifts, groups, list_of_wc, list_of_shifts):
        wc_ids = [wc.id for wc in list_of_wc]
        if wc_ids:
            self.env.cr.execute("""
            DELETE FROM wua_waterconnection_irrigation_shift_relation
            WHERE waterconnection_id IN %s""", (tuple(wc_ids),))
        schedule_info = []
        for wc in list_of_wc:
            for group in groups:
                if wc.watermeter_id.name in group["Hidrantes"]:
                    for shift in shifts:
                        if shift["Id"] in group["Turnos"]:
                            irr_shifts = list_of_shifts.search(
                                [('batchline_id', '=', shift["Id"])])
                            for irr_shift in irr_shifts:
                                if irr_shift.batchline_name == (
                                    group["Descripcion"]
                                ):
                                    wc.write({
                                        'irrigation_shift_ids':
                                        [(0, 0, {
                                            'waterconnection_id': wc.id,
                                            'irrigation_shift_id': irr_shift.id
                                        })]
                                    })
                            days = shift["Dias"]
                            days_scheduled = [
                                self._get_irr_day_from_letter(char)
                                for char in days]
                            intervals = shift["Intervalos"]
                            for interval in range(1, intervals + 1):
                                start_hour = self.\
                                    _get_float_hour_from_str(
                                        shift["Intervalo" + str(interval) +
                                              "Inicio"])
                                duration = \
                                    shift["Intervalo" + str(interval) +
                                          "Duracion"]
                                end_hour = \
                                    start_hour + (duration/60)
                                shift_number = interval
                                for day in days_scheduled:
                                    for irr_shift in irr_shifts:
                                        if irr_shift.batchline_name == (
                                            group["Descripcion"]
                                        ):
                                            schedule_info.append({
                                                'waterconnection_id':
                                                    wc.id,
                                                'irrigation_shift_id':
                                                    irr_shift.id,
                                                'state': '01_active',
                                                'shift_number':
                                                    shift_number,
                                                'irrigation_start_day':
                                                    day,
                                                'irrigation_start_hour':
                                                    start_hour,
                                                'irrigation_end_hour':
                                                    end_hour,
                                                'irrigation_duration':
                                                    duration,
                                                'max_irrigation_volume':
                                                    0.0,
                                            })
        return schedule_info

    def import_waterconnection_irrigation_schedule_batchline(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_wc):
        schedule_info = []
        error_message = ''
        try:
            # If not list of wc, search all watermeters
            # Must be watermeters
            if (not list_of_wc):
                list_of_wc = self.env['wua.waterconnection'].search([
                    ('watermeter_id', '!=', None),
                    ('watermeter_id.state', '=', 'active')])
            list_of_shifts = self.env[
                'wua.waterconnection.irrigation.shift'].search([])
            token, error_message = self.get_token(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if token:
                url_shifts = url_remotecontrol_rest +\
                    '/api/turnosriegos/turnos'
                headers_data = {
                    'authorization': 'bearer ' + token,
                    'content-type': 'application/json',
                }
                response_shifts = requests.get(url_shifts,
                                               headers=headers_data)
                url_groups = url_remotecontrol_rest + \
                    '/api/turnosriegos/grupos'
                response_groups = requests.get(url_groups,
                                               headers=headers_data)
                if response_groups.status_code == 200 and \
                   response_shifts.status_code == 200:
                    shifts = response_shifts.json()
                    groups = response_groups.json()
                    # Method to import shift info from the API
                    self.env['wua.waterconnection.irrigation.shift'].\
                        obtain_shift_info(shifts, groups)
                    schedule_info = self.obtain_schedule_info(shifts,
                                                              groups,
                                                              list_of_wc,
                                                              list_of_shifts)
                else:
                    error_message = _('Unable to get responses information.')
        except Exception as e:
            error_message = 'Error occurred: ' + str(e)
        return [schedule_info, error_message]

    def save_waterconnection_irrigation_schedule(self, wc_irr_schedule,
                                                 update_log=True):
        number_of_wc_irr_schedule = len(wc_irr_schedule)
        # Aux variable to check which waterconnection related schedules
        # have been removed (Removed before add new ones)
        wc_already_cleaned = []
        if number_of_wc_irr_schedule > 0:
            for info in wc_irr_schedule:
                wc = self.env['wua.waterconnection'].browse(
                    info['waterconnection_id'])
                waterconnection_irrigation_schedule_params = {
                    'state': info['state'],
                    'shift_number': info['shift_number'],
                    'irrigation_start_day': info['irrigation_start_day'],
                    'irrigation_start_hour': info['irrigation_start_hour'],
                    'irrigation_end_hour': info['irrigation_end_hour'],
                    'irrigation_duration': info['irrigation_duration'],
                    'max_irrigation_volume': info['max_irrigation_volume'],
                    'waterconnection_id': info['waterconnection_id'],
                    'irrigation_shift_id': info['irrigation_shift_id'],
                    'from_remotecontrol': True,
                }
                if (wc.irrigation_schedule_ids and
                    len(wc.irrigation_schedule_ids) > 0 and wc.id not in
                        wc_already_cleaned):
                    wc.irrigation_schedule_ids.unlink()
                    wc_already_cleaned.append(wc.id)
                    self.create(waterconnection_irrigation_schedule_params)
                else:
                    if wc.id not in wc_already_cleaned:
                        wc_already_cleaned.append(wc.id)
                    self.create(waterconnection_irrigation_schedule_params)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Irrigation Schedules') +
                             '... ' +
                             str(number_of_wc_irr_schedule))
