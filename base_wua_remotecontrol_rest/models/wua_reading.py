# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
import math
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _order = 'reading_time desc, name'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    remotecontrol_origin = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
        ],
        string='Remote Control Origin',
        default='unknown',
        required=False,
    )

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
        remotecontrol = self.env.ref(
            'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
        if (enable_remotecontrol):
            # GET READINGS OF ALL POSSIBLE TELECONTROLS AND THEN
            # UPDATE IT
            try:
                readings, error_message, error_watermeters = \
                    self.do_import_reading_of_telecontrol()
                readings = self.refine_readings(readings)
                resp[2] = error_message
                resp[3] = error_watermeters
                if readings:
                    resp[0] = readings
                    resp[1] = len(readings)
                    if save_data:
                        number_of_negative_readings = \
                            self.save_readings(readings)
                        resp[4] = number_of_negative_readings
                    _logger.info(
                        _('Remote Control: Getting readings') + '... %s',
                        resp[1])
                if error_message:
                    _logger.info(
                        _('Remote Control: Error getting readings') +
                        '... %s', error_message)
                    company_name = self.env.user.company_id.name
                    website_url = self.env['ir.config_parameter'].get_param(
                        "web.base.url")
                    domain = self.env['ir.config_parameter'].get_param(
                        "mail.catchall.domain")
                    error_subject = _('Remote Control: Error getting readings')
                    remotecontrol.sudo().message_post(
                        subject=error_subject,
                        body="Error: %s" % error_message,
                        message_type='email',
                        subtype='mail.mt_comment',
                    )
                    try:
                        outgoing_server = self.env[
                            'ir.mail_server'].sudo().search(
                            [('active', '=', True)], limit=1)
                        if not outgoing_server:
                            _logger.warning(
                                'No active outgoing mail server found, '
                                'skipping telecontrol error email.')
                        else:
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
                                <p style="margin: 0px; padding: 0px;
                                          font-size: 13px;">
                                    <b><a href="%s">%s</a></p></b>
                                    <br/>
                                    <span>%s</span>
                                </p>
                            ''' % (website_url, company_name,
                                   error_message.replace('\n', '<br/>'))
                            # force_send=False: queued instead of synchronous
                            # SMTP (avoids blocking up to 60s per server)
                            mail_template.send_mail(
                                remotecontrol.id, force_send=False)
                    except Exception as mail_exc:
                        _logger.warning(
                            'Could not send telecontrol error email: %s',
                            str(mail_exc))
            except Exception as e:
                _logger.error("Error getting readings: %s", str(e))
                with self.pool.cursor() as new_cr:
                    new_env = api.Environment(
                        new_cr, self.env.uid, self.env.context)
                    new_remotecontrol = self.with_env(new_env).env.ref(
                        'base_wua_remotecontrol_rest.wua_remotecontrol_logger',
                    )
                    new_remotecontrol.sudo().message_post(
                        subject=_('Remote Control: Exception Error'),
                        body="Error: %s" % str(e),
                        message_type='email',
                        subtype='mail.mt_comment',
                    )
                    new_cr.commit()
                raise e
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
        _logger = logging.getLogger(self.__class__.__name__)
        watermeters = self.env['wua.watermeter']
        for reading in readings:
            filtered_watermeter = watermeters.search(
                [('name', '=', reading['watermeter'])])
            if not filtered_watermeter:
                _logger.warning(
                    'Remote Control: water meter code %r not found in DB,'
                    ' reading discarded.', reading['watermeter'])
                continue
            reading_volume = self.round_reading_volume(reading['volume'])
            watermeter = filtered_watermeter[0]
            if watermeter.state != 'active':
                _logger.warning(
                    'Remote Control: water meter %r is not active,'
                    ' reading discarded.', watermeter.name)
            elif not watermeter.waterconnection_id:
                _logger.warning(
                    'Remote Control: water meter %r has no water connection,'
                    ' reading discarded.', watermeter.name)
            else:
                refined_reading = {
                    'watermeter_id': watermeter.id,
                    'watermeter_name': watermeter.name,
                    'waterconnection_id': watermeter.waterconnection_id.id,
                    'irrigationshed_id': watermeter.irrigationshed_id.id,
                    'hydraulicsector_id': watermeter.hydraulicsector_id.id,
                    'volume': reading_volume,
                    'remotecontrol_origin':
                        reading.get('remotecontrol_origin', 'unknown'),
                    }
                resp.append(refined_reading)
        if readings and not resp:
            _logger.warning(
                'Remote Control: %d raw readings received from telecontrol'
                ' but all were discarded during refinement.', len(readings))
        return resp

    def _get_reading_time_from_remotecontrol(self, reading, now):
        return now

    def save_readings(self, readings, update_log=True):
        _logger = logging.getLogger(self.__class__.__name__)
        number_of_readings = len(readings)
        number_of_negative_readings = 0
        number_of_skipped_readings = 0
        number_of_failed_readings = 0
        failed_watermeter_names = []
        processed_keys = set()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if number_of_readings > 0:
            for reading in readings:
                reading_time = self._get_reading_time_from_remotecontrol(
                    reading, now)
                key = (reading['watermeter_id'], reading_time)
                if key in processed_keys:
                    number_of_skipped_readings += 1
                    continue
                processed_keys.add(key)
                try:
                    with self.env.cr.savepoint():
                        is_negative, negative_volume = \
                            self.is_negative_reading(reading, reading_time)
                        if is_negative:
                            self.env['wua.negative.reading'].create({
                                'watermeter_id': reading['watermeter_id'],
                                'reading_time': reading_time,
                                'volume': reading['volume'],
                                'presconsumption_volume': negative_volume,
                                'from_remotecontrol': True,
                                'remotecontrol_origin':
                                    reading['remotecontrol_origin'],
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
                                'remotecontrol_origin':
                                    reading['remotecontrol_origin'],
                            })
                except Exception as e:
                    number_of_failed_readings += 1
                    wm_name = reading.get(
                        'watermeter_name', str(reading['watermeter_id']))
                    failed_watermeter_names.append(wm_name)
                    _logger.warning(
                        'Remote Control: Could not save reading for water'
                        ' meter %r (time=%s, vol=%s): %s',
                        wm_name, reading_time, reading.get('volume'), e)
            if update_log:
                _logger.info(
                    _('Remote Control: Saved readings') + '... ' +
                    str(number_of_readings))
                if number_of_skipped_readings:
                    _logger.warning(
                        _('Remote Control: Skipped %s duplicated readings '
                          '(same water meter and reading time received more '
                          'than once in the same batch).') %
                        number_of_skipped_readings)
                if number_of_failed_readings:
                    _logger.warning(
                        'Remote Control: Failed to save %s readings: %s',
                        number_of_failed_readings,
                        ', '.join(failed_watermeter_names))
            remotecontrol = self.env.ref(
                'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
            body = (
                "Readings from remote control: %s<br/>"
                "Negative readings: %s<br/>"
                "Skipped duplicated readings: %s" % (
                    number_of_readings,
                    number_of_negative_readings,
                    number_of_skipped_readings))
            if number_of_failed_readings:
                body += "<br/>Failed readings (chronological error): "\
                    "%s (%s)" % (
                        number_of_failed_readings,
                        ', '.join(failed_watermeter_names))
            remotecontrol.message_post(
                subject=_('Remote Control: Readings Saved'),
                body=body,
                message_type='email',
                subtype='mail.mt_comment',
            )
        return number_of_negative_readings
