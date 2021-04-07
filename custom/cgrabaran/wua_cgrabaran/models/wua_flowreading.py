# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import logging
import pyodbc
from odoo import models, fields, api, exceptions, _


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'
    _order = 'reading_time desc, name'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    validated = fields.Boolean(
        string='Validated',
        default=True,
        required=True)

    intake_id = fields.Many2one(
        readonly=False)

    is_toll = fields.Boolean(
        string='Toll Reading',
        index=True,
        store=True,
        compute='_compute_is_toll')

    @api.depends('intake_id', 'flowmeter_id')
    def _compute_is_toll(self):
        for record in self:
            is_toll = False
            if (record.intake_id and record.flowmeter_id):
                is_toll = not (record.intake_id == record.flowmeter_id.
                               intake_id)
            record.is_toll = is_toll

    @api.model
    def do_import_flowreadings(self, save_data=True, show_message=True):
        # for resp: item 1: list of readings, item 2: number of readings,
        # item 3: possible error message, item 4: list of problematic
        # water meters, item 5: number of negative readings.
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            url_scada_server = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'url_scada_server')
            scada_server_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'scada_server_username')
            scada_server_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'scada_server_password')
            scada_server_database = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'scada_server_database')
            if (url_scada_server and scada_server_username and
               scada_server_password and scada_server_database):
                data = self.populate_data_for_import_flowreadings(
                    url_scada_server,
                    scada_server_database,
                    scada_server_username,
                    scada_server_password)
                if data:
                    flowreadings, error_message, error_flowmeters = \
                        self.import_flowreadings(
                            url_scada_server,
                            scada_server_database,
                            scada_server_username,
                            scada_server_password, data)
                    flowreadings = self.refine_flowreadings(flowreadings)
                    if flowreadings:
                        resp[0] = flowreadings
                        resp[1] = len(flowreadings)
                        resp[2] = error_message
                        resp[3] = error_flowmeters
                        if save_data:
                            number_of_negative_flowreadings = \
                                self.save_flowreadings(flowreadings)
                            resp[4] = number_of_negative_flowreadings
                        prefix_message_01 = _('Remote Control: '
                                              'Getting flowreadings')
                        suffix_message_01 = str(resp[1])
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.info(prefix_message_01 + '... ' +
                                     suffix_message_01)
                        if error_message:
                            prefix_message_02 = _('Remote Control: '
                                                  'Error getting flowreadings')
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

    def populate_data_for_import_flowreadings(self, url_scada_server,
                                              scada_server_database,
                                              scada_server_username,
                                              scada_server_password):
        resp = []
        flowmeters = self.env['wua.flowmeter'].search([])
        flowmetersWithRemote = []
        for flowmeter in flowmeters:
            if (flowmeter.scada_remote_code and
                flowmeter.scada_info_type and
                    flowmeter.scada_identifier):
                flowmetersWithRemote.append(flowmeter)
        for flowmeter in flowmetersWithRemote:
            queryToGetInfo = """
                SELECT hc.REMOTA,
                hc.IDENTIFICADOR,
                hc.TIPO_INFORMACION,
                hc.VALOR,
                hc.FECHA FROM HISTORICO_CAUDALIMETROS hc
                WHERE hc.REMOTA = """ + flowmeter.scada_remote_code + """
                AND hc.IDENTIFICADOR = """ + flowmeter.scada_identifier + """
                AND hc.TIPO_INFORMACION = """ + \
                flowmeter.scada_info_type + \
                """ ORDER BY hc.FECHA DESC
            """
            resp.append(queryToGetInfo)
        return resp

    # Implemented hook
    def import_flowreadings(self, url_scada_server,
                            scada_server_database,
                            scada_server_username,
                            scada_server_password,
                            list_of_data):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        try:
            cnxn = pyodbc.connect(driver='{FreeTDS}', host=url_scada_server,
                                  database=scada_server_database,
                                  user=scada_server_username,
                                  password=scada_server_password)
            cursor = cnxn.cursor()
        except Exception as e:
            return [flowreadings, str(e), error_flowmeters]
        spTz = pytz.timezone('Europe/Madrid')
        utc = pytz.timezone('UTC')
        for query in list_of_data:
            try:
                cursor.execute(query)
                flowreading = cursor.fetchone()
                flowreadingDict = {
                    'scada_remote_code': flowreading[0],
                    'scada_identifier': flowreading[1],
                    'scada_info_type': flowreading[2],
                    'volume': flowreading[3],
                    'reading_time': spTz.localize(flowreading[4]).astimezone(
                        utc).strftime(
                        '%Y-%m-%d %H:%M:%S'),
                    'instant_flow': 0}
                flowreadings.append(flowreadingDict)
            except Exception as e:
                error_flowmeters.append(query)
                error_message = str(e)
        return [flowreadings, error_message, error_flowmeters]

    def refine_flowreadings(self, flowreadings):
        resp = []
        flowmeters = self.env['wua.flowmeter']
        for flowreading in flowreadings:
            filtered_flowmeter = flowmeters.search(
                ['&', '&', ('scada_remote_code', '=',
                            flowreading['scada_remote_code']),
                           ('scada_identifier', '=',
                            flowreading['scada_identifier']),
                           ('scada_info_type', '=',
                            flowreading['scada_info_type'])])
            if filtered_flowmeter:
                flowmeter = filtered_flowmeter[0]
                if (flowmeter.state == 'active' and
                   flowmeter.intake_id):
                    refined_flowreading = {
                        'flowmeter_id': flowmeter.id,
                        'flowmeter_name': flowmeter.name,
                        'intake_id': flowmeter.intake_id.id,
                        'volume': flowreading['volume'],
                        'instant_flow': flowreading['instant_flow'],
                        'reading_time': flowreading['reading_time']
                        }
                    resp.append(refined_flowreading)
        return resp

    def save_flowreadings(self, flowreadings, update_log=True):
        number_of_flowreadings = len(flowreadings)
        number_of_negative_flowreadings = 0
        if number_of_flowreadings > 0:
            for flowreading in flowreadings:
                is_negative, negative_volume = \
                    self.is_negative_flowreading(flowreading)
                if is_negative:
                    self.env['wua.negative.flowreading'].create({
                        'flowmeter_id': flowreading['flowmeter_id'],
                        'reading_time': flowreading['reading_time'],
                        'volume': flowreading['volume'],
                        'intakeconsumption_volume': negative_volume,
                        })
                    number_of_negative_flowreadings = \
                        number_of_negative_flowreadings + 1
                else:
                    self.create({
                        'flowmeter_id': flowreading['flowmeter_id'],
                        'reading_time': flowreading['reading_time'],
                        'volume': flowreading['volume'],
                        'instant_flow': flowreading['instant_flow'],
                        'initialization_reading': False,
                        'from_import': False,
                        'validated': False,
                        })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved floweadings') + '... ' +
                             str(number_of_flowreadings))
        return number_of_negative_flowreadings

    def is_negative_flowreading(self, flowreading):
        is_negative = False
        negative_volume = 0
        current_volume = flowreading['volume']
        current_reading_time = flowreading['reading_time']
        previous_flowreading = self.env['wua.flowreading'].search(
            [('flowmeter_id', '=', flowreading['flowmeter_id']),
             ('reading_time', '<', current_reading_time)],
            limit=1, order='reading_time desc')
        if previous_flowreading:
            previous_volume = previous_flowreading[0].volume
        if previous_volume > current_volume:
            is_negative = True
            negative_volume = current_volume - previous_volume
        return is_negative, negative_volume

    @api.multi
    def validate_flowreading(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_flowreading(self):
        self.ensure_one()
        if not self.intakeconsumption_id.invoiced_consumption:
            self.validated = False
        else:
            raise exceptions.UserError(_('The reading is mapped to a '
                                         'invoiced consumption: it is not '
                                         'possible to cancel the reading.'))

    def validate_flowreadings(self, active_flowreadings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        flowreadings = self.env['wua.flowreading'].browse(active_flowreadings)
        for flowreading in flowreadings:
            if not flowreading.validated:
                flowreading.validate_flowreading()

    def cancel_flowreadings(self, active_flowreadings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        flowreadings = self.env['wua.flowreading'].browse(active_flowreadings)
        for flowreading in flowreadings:
            if flowreading.validated:
                flowreading.cancel_flowreading()
