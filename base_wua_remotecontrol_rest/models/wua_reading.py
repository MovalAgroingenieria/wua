# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'
    _order = 'reading_time desc, name'

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
    def do_import_readings(self, save_data=True, show_message=False):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings')
        if (enable_remotecontrol and import_from_readings):
            # Provisional
            resp = [None, 0, '']
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
                data = self.populate_data_for_import_readings()
                if data:
                    # Provisional
                    print data
                    readings, error_message = \
                        self.import_readings(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password,
                            data)
                    if readings:
                        resp[0] = readings
                        resp[1] = len(readings)
                        # Provisional
                        print readings
                        if save_data:
                            pass
                    readings_ok = error_message == ''
                    prefix_message = _('Getting readings')
                    suffix_message = 'OK'
                    if not readings_ok:
                        suffix_message = 'Error ( ' + error_message + ')'
                        resp[2] = error_message
                    # Provisional
                    else:
                        print 'do_import_readings...'
                        self.create({
                            'watermeter_id': 20,
                            'reading_time': datetime.datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'),
                            'volume': 1000,
                            'initialization_reading': False,
                            })
                    _logger = logging.getLogger(self.__class__.__name__)
                    _logger.info(prefix_message + '... ' +
                                 suffix_message)
            return resp
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
            else:
                return False

    # Hook
    def populate_data_for_import_readings(self):
        return None

    # Hook
    def import_readings(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, list_of_data):
        return None, ''
