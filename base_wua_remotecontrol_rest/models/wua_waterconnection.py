# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import logging
from odoo import models, fields, api, exceptions, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    remotecontrol_enabled = fields.Boolean(
        string='Remote Control enabled',
        compute='_compute_remotecontrol_enabled')

    conversion_factor = fields.Integer(
        string="Conversion Factor",
        required=True,
        default=1)

    telecontrol_ids = fields.One2many(
        string="Waterconnection telecontrols",
        comodel_name="wua.waterconnection.telecontrol",
        inverse_name="waterconnection_id")

    last_waterflow = fields.Float(
        string='Waterconnection Waterflow (l/s)',
        digits=(32, 4),
        compute="_compute_waterconnection_telecontrol_info",
        store=True)

    last_valve_open = fields.Boolean(
        string='Valve Open',
        compute="_compute_waterconnection_telecontrol_info",
        store=True)

    last_valve_scheduled = fields.Boolean(
        string='Valve Scheluded',
        compute="_compute_waterconnection_telecontrol_info",
        store=True)

    last_data_time = fields.Datetime(
        string='Last Capture Date',
        compute="_compute_waterconnection_telecontrol_info",
        store=True)

    html_last_telecontrol_info = fields.Html(
        string='Telecontrol Info',
        compute='_compute_html_last_telecontrol_info')

    _sql_constraints = [
        ('conversion_factor_positive', 'CHECK (conversion_factor > 0)',
         'Conversion factor must be greater than 0.'),
        ]

    @api.multi
    def _compute_remotecontrol_enabled(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        import_from_waterconnection = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_waterconnection')
        for record in self:
            record.remotecontrol_enabled = \
                enable_remotecontrol & import_from_waterconnection

    @api.depends('telecontrol_ids')
    def _compute_waterconnection_telecontrol_info(self):
        for record in self:
            if (record.telecontrol_ids and (len(record.telecontrol_ids) > 0)):
                wc_telecontrol = record.telecontrol_ids[-1]
                record.write({
                    'last_data_time': wc_telecontrol.data_time,
                    'last_waterflow': wc_telecontrol.waterflow,
                    'last_valve_open': wc_telecontrol.valve_open,
                    'last_valve_scheduled': wc_telecontrol.valve_scheduled
                })

    @api.multi
    def do_import_readings_from_waterconnection(self):
        self.ensure_one()
        prefix_message = _('Remote Control: Starting reading in '
                           'water connections')
        _logger = logging.getLogger(self.__class__.__name__)
        _logger.info(prefix_message + '... ' +
                     str(self.name))
        data_readings = self.env['wua.reading'].do_import_readings(
            save_data=False)
        readings = data_readings[0]
        if readings:
            readings = [x for x in readings if x['waterconnection_id']
                        in [self.id]]
            self.env['wua.reading'].save_readings(readings)

    def do_import_readings_from_waterconnections(self,
                                                 active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        if waterconnections:
            prefix_message = _('Remote Control: Starting reading in '
                               'water connections')
            suffix_message = ''
            for waterconnection in waterconnections:
                suffix_message = suffix_message + ', ' + waterconnection.name
            suffix_message = suffix_message[2:]
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + '... ' + suffix_message)
            data_readings = self.env['wua.reading'].do_import_readings(
                save_data=False)
            readings = data_readings[0]
            if readings:
                readings = [x for x in readings if x['waterconnection_id']
                            in active_waterconnections]
                self.env['wua.reading'].save_readings(readings)

    @api.multi
    def _compute_html_last_telecontrol_info(self):
        for record in self:
            html_last_telecontrol_info = ''
            html_last_telecontrol_info = self._get_html_last_telecontrol_info()
            record.html_last_telecontrol_info = html_last_telecontrol_info

    def _get_html_last_telecontrol_info(self):
        resp = ''
        label_date = _('Capture Date')
        label_waterflow = _('Waterflow')
        last_waterflow = self.env['wua.parcel'].transform_float_to_locale(
            self.last_waterflow, 4)
        if (self.last_valve_open):
            label_valve_open = _('Valve Open: Yes')
        else:
            label_valve_open = _('Valve Open: No')
        if (self.last_valve_scheduled):
            label_valve_scheduled = _('Valve Scheduled: Yes')
        else:
            label_valve_scheduled = _('Valve Scheduled: No')
        info_color = 'unset'
        if (self.last_data_time):
            data_time = datetime.datetime.strptime(
                self.last_data_time, '%Y-%m-%d %H:%M:%S')
            data_time = pytz.timezone('UTC').localize(data_time)
            if (self.env.user.tz):
                local_timezone = pytz.timezone(self.env.user.tz)
                data_time = data_time.astimezone(local_timezone)
            last_data_time = data_time.strftime('%d/%m/%Y %H:%M:%S')
        else:
            last_data_time = '-'
        if (self.last_waterflow > 0):
            info_color = 'blue'
        body = '<div style="display: flex; justify-content: space-around;">' +\
            '<span>' + label_date + ': ' + last_data_time + '</span>' + \
            '<span>' + label_waterflow + ': ' + \
            str(last_waterflow) + ' (l/s)' + '</span>' + \
            '<span>' + label_valve_open + \
            '</span><span>' + label_valve_scheduled + \
            '</span>' + '</div>'
        resp = '<div class="panel-body text-left" ' + \
               'style="background:#f4f6f6;border-radius:4px;' + \
               'border-color:#696969;border-width:1px;' + \
               'border-style:solid;padding-top:8px;' + \
               'padding-bottom:8px;' + \
               'margin-left:40px;margin-right:40px;' + \
               'color: ' + info_color + ';">' + \
               body + '</div>'
        return resp
