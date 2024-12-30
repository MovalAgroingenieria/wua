# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
import math
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _order = 'reading_time desc, name'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    # Hook that will be implemeneted on every telecontrol, appending the info
    def do_import_reading_of_telecontrol(self):
        readings = []
        error_message = ''
        error_watermeters = []
        return readings, error_message, error_watermeters

    @api.model
    def do_import_readings(self, save_data=True, show_message=True):
        # for resp: item 1: list of readings, item 2: number of readings,
        # item 3: possible error message, item 4: list of problematic
        # water meters, item 5: number of negative readings.
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            # GET READINGS OF ALL POSSIBLE TELECONTROLS AND THEN
            # UPDATE IT
            readings, error_message, error_watermeters = \
                self.do_import_reading_of_telecontrol()
            readings = self.refine_readings(readings)
            if readings:
                resp[0] = readings
                resp[1] = len(readings)
                resp[2] = error_message
                resp[3] = error_watermeters
                if save_data:
                    number_of_negative_readings = \
                        self.save_readings(readings)
                    resp[4] = number_of_negative_readings
                prefix_message_01 = _('Remote Control: '
                                      'Getting readings')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' +
                             suffix_message_01)
            if error_message:
                prefix_message_02 = _('Remote Control: '
                                      'Error getting readings')
                suffix_message_02 = resp[2]
                company_name = self.env.user.company_id.name
                website_url = self.env['ir.config_parameter'].get_param(
                    "web.base.url")
                domain = self.env['ir.config_parameter'].get_param(
                    "mail.catchall.domain")
                _logger = logging.getLogger(
                    self.__class__.__name__)
                _logger.info(prefix_message_02 + '... ' +
                             suffix_message_02)
                telecontrol_failed_template_id = self.env.ref(
                    'base_wua_remotecontrol_rest.'
                    'telecontrol_failed_email_template').id
                mail_template = self.env['mail.template'].browse(
                    telecontrol_failed_template_id)
                mail_template.subject = '''
                    Reading remote control in %s has
                    experienced some problem
                ''' % (domain or self.pool.db_name)
                mail_template.body_html = '''
                    <p style="margin: 0px; padding: 0px; font-size: 13px;">
                        <b><a href="%s">%s</a></p></b>
                        <br/>
                        <span>%s</span>
                    </p>
                ''' % (website_url, company_name, resp[2].replace(
                    '\n', '<br/>'))
                mail_template.send_mail(self.id, force_send=True)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def round_reading_volume(self, reading_volume):
        volume = float(reading_volume)
        rounding_type = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'remotecontrol_rounding_reading_volume')
        if (rounding_type == '01_round'):
            volume = round(volume, 0)
        elif (rounding_type == '02_truncate'):
            volume = int(volume)
        elif (rounding_type == '03_ceiling'):
            volume = math.ceil(volume)
        return volume

    def refine_readings(self, readings):
        resp = []
        watermeters = self.env['wua.watermeter']
        for reading in readings:
            filtered_watermeter = watermeters.search(
                [('name', '=', reading['watermeter'])])
            if filtered_watermeter:
                reading_volume = self.round_reading_volume(reading['volume'])
                watermeter = filtered_watermeter[0]
                if (watermeter.state == 'active' and
                   watermeter.waterconnection_id):
                    refined_reading = {
                        'watermeter_id': watermeter.id,
                        'watermeter_name': watermeter.name,
                        'waterconnection_id': watermeter.waterconnection_id.id,
                        'irrigationshed_id': watermeter.irrigationshed_id.id,
                        'hydraulicsector_id': watermeter.hydraulicsector_id.id,
                        'volume': reading_volume,
                        }
                    resp.append(refined_reading)
        return resp

    def _get_reading_time_from_remotecontrol(self, reading, now):
        return now

    def save_readings(self, readings, update_log=True):
        number_of_readings = len(readings)
        number_of_negative_readings = 0
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if number_of_readings > 0:
            for reading in readings:
                reading_time = self._get_reading_time_from_remotecontrol(
                    reading, now)
                is_negative, negative_volume = \
                    self.is_negative_reading(reading)
                if is_negative:
                    self.env['wua.negative.reading'].create({
                        'watermeter_id': reading['watermeter_id'],
                        'reading_time': reading_time,
                        'volume': reading['volume'],
                        'presconsumption_volume': negative_volume,
                        'from_remotecontrol': True,
                        })
                    number_of_negative_readings = \
                        number_of_negative_readings + 1
                else:
                    self.create({
                        'watermeter_id': reading['watermeter_id'],
                        'reading_time': reading_time,
                        'volume': reading['volume'],
                        'initialization_reading': False,
                        'from_import': False,
                        'validated': False,
                    })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved readings') + '... ' +
                             str(number_of_readings))
        return number_of_negative_readings
