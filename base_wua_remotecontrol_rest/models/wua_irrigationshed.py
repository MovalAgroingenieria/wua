# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from Crypto.Cipher import AES
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_irrigationshed = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_irrigationshed')
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if import_from_irrigationshed is None:
            import_from_irrigationshed = False
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_irrigationshed

    @api.multi
    def do_import_readings_from_irrigationshed(self):
        self.ensure_one()
        prefix_message = _('Remote Control: Starting reading in '
                           'irrigation sheds')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' +
                     str(self.name))
        data_readings = self.env['wua.reading'].do_import_readings(
            save_data=False)
        readings = data_readings[0]
        if readings:
            readings = [x for x in readings if x['irrigationshed_id']
                        in [self.id]]
            self.env['wua.reading'].save_readings(readings)

    @api.model
    def run_gisviewer_remotecontrol(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        if url and username and password:
            credentials = username + "-" + password
            credentials = credentials.ljust(32)
            current_datetime = pytz.utc.localize(datetime.datetime.now())
            current_datetime = current_datetime.astimezone(
                pytz.timezone('Europe/Madrid'))
            current_datetime = str(current_datetime)[:16].replace(' ', 'T')
            minimum = int(current_datetime[14:])
            if minimum < 30:
                minimum = '00'
            else:
                minimum = '30'
            iv = current_datetime[:14] + minimum
            aes_encryptor = AES.new('hZj<?*aS9w.Rg)3"', AES.MODE_CBC, iv)
            cipher_text = aes_encryptor.encrypt(credentials)
            cipher_text = cipher_text.encode('base64')
            url = url + '?' + 'arg=' + cipher_text + '&mode=min&modo_opera' +\
                'tivo=8&infoCr=1'
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new', }

    def do_import_readings_from_irrigationsheds(self,
                                                active_irrigationsheds):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        irrigationsheds = self.env['wua.irrigationshed'].browse(
            active_irrigationsheds)
        if irrigationsheds:
            prefix_message = _('Remote Control: Starting reading in '
                               'irrigationsheds')
            suffix_message = ''
            for irrigationshed in irrigationsheds:
                suffix_message = suffix_message + ', ' + irrigationshed.name
            suffix_message = suffix_message[2:]
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' + suffix_message)
            data_readings = self.env['wua.reading'].do_import_readings(
                save_data=False)
            readings = data_readings[0]
            if readings:
                readings = [x for x in readings if x['irrigationshed_id']
                            in active_irrigationsheds]
                self.env['wua.reading'].save_readings(readings)
