# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _order = 'reading_time desc, name'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    validated = fields.Boolean(
        string='Validated',
        default=True,
        required=True)

    @api.model
    def run_remotecontrol_application_url(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_application')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    @api.model
    def do_import_readings(self, save_data=True, show_message=True):
        # for resp: item 1: list of readings, item 2: number of readings,
        # item 3: possible error message, item 4: list of problematic
        # water meters, item 5: number of negative readings.
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings')
        if (enable_remotecontrol and import_from_readings):
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
                data = self.populate_data_for_import_readings(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
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
                            suffix_message_02 = error_message
                            _logger = logging.getLogger(
                                self.__class__.__name__)
                            _logger.info(prefix_message_02 + '... ' +
                                         suffix_message_02)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    # Hook
    def populate_data_for_import_readings(self, url_remotecontrol_rest,
                                          url_remotecontrol_rest_username,
                                          url_remotecontrol_rest_password):
        return None

    # Hook
    def import_readings(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, list_of_data):
        return None, '', None

    def refine_readings(self, readings):
        resp = []
        watermeters = self.env['wua.watermeter']
        for reading in readings:
            filtered_watermeter = watermeters.search(
                [('name', '=', reading['watermeter'])])
            if filtered_watermeter:
                watermeter = filtered_watermeter[0]
                if (watermeter.state == 'active' and
                   watermeter.waterconnection_id):
                    refined_reading = {
                        'watermeter_id': watermeter.id,
                        'watermeter_name': watermeter.name,
                        'waterconnection_id': watermeter.waterconnection_id.id,
                        'irrigationshed_id': watermeter.irrigationshed_id.id,
                        'hydraulicsector_id': watermeter.hydraulicsector_id.id,
                        'volume': reading['volume'],
                        }
                    resp.append(refined_reading)
        return resp

    def save_readings(self, readings, update_log=True):
        number_of_readings = len(readings)
        number_of_negative_readings = 0
        if number_of_readings > 0:
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            for reading in readings:
                is_negative, negative_volume = \
                    self.is_negative_reading(reading)
                if is_negative:
                    self.env['wua.negative.reading'].create({
                        'watermeter_id': reading['watermeter_id'],
                        'reading_time': reading_time,
                        'volume': reading['volume'],
                        'presconsumption_volume': negative_volume,
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

    def is_negative_reading(self, reading):
        is_negative = False
        negative_volume = 0
        current_volume = reading['volume']
        current_reading_time = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        previous_reading = self.env['wua.reading'].search(
            [('watermeter_id', '=', reading['watermeter_id']),
             ('reading_time', '<', current_reading_time)],
            limit=1, order='reading_time desc')
        if previous_reading:
            previous_volume = previous_reading[0].volume
        if previous_volume > current_volume:
            is_negative = True
            negative_volume = current_volume - previous_volume
        return is_negative, negative_volume
