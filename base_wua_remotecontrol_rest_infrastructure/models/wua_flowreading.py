# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, exceptions, _


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    # Hook that will be implemeneted on every telecontrol, appending the info
    def do_import_flowreading_of_telecontrol(self):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        return flowreadings, error_message, error_flowmeters

    @api.model
    def do_import_flowreadings(self, save_data=True, show_message=True):
        # for resp: item 1: list of flow-readings, item 2: number of
        # flow-readings, item 3: possible error message, item 4: list of
        # problematic flow meters, item 5: number of negative flow-readings.
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            flowreadings, error_message, error_flowmeters = \
                self.do_import_flowreading_of_telecontrol()
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
                                      'Getting flow-readings')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' +
                             suffix_message_01)
                if error_message:
                    prefix_message_02 = _('Remote Control: Error '
                                          'getting flow-readings')
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

    def refine_flowreadings(self, flowreadings):
        resp = []
        flowmeters = self.env['wua.flowmeter']
        for flowreading in flowreadings:
            filtered_flowmeter = flowmeters.search(
                [('name', '=', flowreading['flowmeter']),
                 ('intake_id', '!=', False)])
            if filtered_flowmeter:
                flowmeter = filtered_flowmeter[0]
                if flowmeter.state == 'active':
                    refined_flowreading = {
                        'flowmeter_id': flowmeter.id,
                        'volume': flowreading['volume'],
                        'instant_flow': flowreading['instant_flow'],
                        }
                    resp.append(refined_flowreading)
        return resp

    def save_flowreadings(self, flowreadings, update_log=True):
        number_of_flowreadings = len(flowreadings)
        number_of_negative_flowreadings = 0
        if number_of_flowreadings > 0:
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            for flowreading in flowreadings:
                is_negative, negative_volume = \
                    self.is_negative_flowreading(flowreading)
                if is_negative:
                    self.env['wua.negative.flowreading'].create({
                        'flowmeter_id': flowreading['flowmeter_id'],
                        'reading_time': reading_time,
                        'volume': flowreading['volume'],
                        'instant_flow': flowreading['instant_flow'],
                        'consumption_volume': negative_volume,
                        'from_remotecontrol': True,
                        })
                    number_of_negative_flowreadings = \
                        number_of_negative_flowreadings + 1
                else:
                    self.create({
                        'flowmeter_id': flowreading['flowmeter_id'],
                        'reading_time': reading_time,
                        'volume': flowreading['volume'],
                        'instant_flow': flowreading['instant_flow'],
                        'initialization_reading': False,
                        'from_import': False,
                        'validated': False,
                        })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved flow-readings') +
                             '... ' + str(number_of_flowreadings))
        return number_of_negative_flowreadings
