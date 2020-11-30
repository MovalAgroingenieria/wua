# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _, exceptions


class WuaWaterconnectionTelecontrol(models.Model):
    _name = 'wua.waterconnection.telecontrol'
    _description = 'Entity (waterconnection telecontrol)'
    _order = 'data_time, name'

    MAX_SIZE_NAME = 52
    MAX_COUNT_HIST = 24

    data_time = fields.Datetime(
        string='Capture Date',
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='cascade')

    waterflow = fields.Float(
        string='Waterconnection Waterflow (l/s)',
        digits=(32, 4))

    valve_open = fields.Boolean(
        string='Valve Open',)

    valve_scheduled = fields.Boolean(
        string='Valve Scheluded',)

    name = fields.Char(
        string='Telecontrol Data',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    @api.depends('data_time', 'waterconnection_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.data_time:
                value = record.waterconnection_id.name + ' - ' + \
                    record.data_time
            record.name = value

    @api.model
    def do_import_waterconnection_telecontrol_info(
            self, save_data=True, show_message=True):
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
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
                data = \
                    self.\
                    populate_data_for_import_waterconnection_telecontrol_info(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password)
                if data:
                    wc_info, error_message = \
                        self.import_waterconnection_telecontrol_info(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
                    wc_info = self.refine_waterconnection_telecontrol_info(
                        wc_info)
                    if save_data:
                        self.save_waterconnection_telecontrol_info(wc_info)
                    if error_message:
                        prefix_message = _('Remote Control: Error getting '
                                           'waterconnection info')
                        suffix_message = error_message
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info(prefix_message + '... ' + suffix_message)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def populate_data_for_import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        return None

    # Hook
    def import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        return None, ''

    def refine_waterconnection_telecontrol_info(self, wc_info):
        resp = []
        waterconnections = self.env['wua.waterconnection']
        for info in wc_info:
            filtered_waterconnection = waterconnections.search(
                [('name', '=', info['waterconnection'])])
            if filtered_waterconnection:
                waterconnection = filtered_waterconnection[0]
                conversion_factor = waterconnection.conversion_factor
                refined_wc_info = {
                    'waterconnection_id': waterconnection.id,
                    'valve_open': info['valve_open'],
                    'valve_scheduled': info['valve_scheduled'],
                    'waterflow': info['waterflow'] / conversion_factor,
                    'data_time': info['data_time'],
                    }
                resp.append(refined_wc_info)
        return resp

    def save_waterconnection_telecontrol_info(self, wc_info,
                                              update_log=True):
        number_of_wc_info = len(wc_info)
        if number_of_wc_info > 0:
            for info in wc_info:
                # Remove? Or Keep history?
                wc = self.env['wua.waterconnection'].browse(
                    info['waterconnection_id'])
                waterconnection_telecontrol_params = {
                    'data_time': info['data_time'],
                    'waterflow': info['waterflow'],
                    'valve_open': info['valve_open'],
                    'valve_scheduled': info['valve_scheduled'],
                    'waterconnection_id': info['waterconnection_id'],
                }
                newest_info = wc.telecontrol_ids[-1]
                if (newest_info.data_time < info['data_time']):
                    # WHILE For the case when MAX_COUNT_HIST get lower than
                    # current data
                    while (wc.telecontrol_ids and
                            len(wc.telecontrol_ids) >=
                            self.MAX_COUNT_HIST):
                        # Unlink the last one
                        wc.telecontrol_ids[0].unlink()
                    self.create(waterconnection_telecontrol_params)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Waterconnection'
                               'Telecontrol Info') + '... ' +
                             str(number_of_wc_info))
