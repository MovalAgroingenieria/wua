# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, exceptions, _


class WuaWaterpipeflowreading(models.Model):
    _inherit = 'wua.waterpipeflowreading'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    # Hook that will be implemeneted on every telecontrol, appending the info
    def do_import_waterpipeflowreading_of_telecontrol(self):
        waterpipeflowreadings = []
        error_message = ''
        error_flowmeters = []
        return waterpipeflowreadings, error_message, error_flowmeters

    @api.model
    def do_import_waterpipeflowreadings(self, save_data=True,
                                        show_message=True):
        # for resp: item 1: list of flow-readings, item 2: number of
        # flow-readings, item 3: possible error message, item 4: list of
        # problematic flow meters, item 5: number of negative flow-readings.
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            waterpipeflowreadings, error_message, error_flowmeters = \
                self.do_import_waterpipeflowreading_of_telecontrol()
            waterpipeflowreadings = self.refine_waterpipeflowreadings(
                waterpipeflowreadings)
            if waterpipeflowreadings:
                resp[0] = waterpipeflowreadings
                resp[1] = len(waterpipeflowreadings)
                resp[2] = error_message
                resp[3] = error_flowmeters
                if save_data:
                    number_of_negative_waterpipeflowreadings = \
                        self.save_waterpipeflowreadings(
                            waterpipeflowreadings)
                    resp[4] = number_of_negative_waterpipeflowreadings
                prefix_message_01 = _('Remote Control: '
                                      'Getting water-pipe readings')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' + suffix_message_01)
            if error_message:
                prefix_message_02 = _('Remote Control: Error '
                                      'getting water-pipe readings')
                suffix_message_02 = error_message
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
                mail_template.subject = 'Waterpipe Flow Reading remote' +\
                    ' control in %s has experienced some problem' %\
                    (domain or self.pool.db_name)
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

    def refine_waterpipeflowreadings(self, waterpipeflowreadings):
        resp = []
        flowmeters = self.env['wua.flowmeter']
        for waterpipeflowreading in waterpipeflowreadings:
            filtered_flowmeter = flowmeters.search(
                [('name', '=', waterpipeflowreading['flowmeter']),
                 ('waterpipe_id', '!=', False)])
            if filtered_flowmeter:
                flowmeter = filtered_flowmeter[0]
                if flowmeter.state == 'active':
                    refined_waterpipeflowreading = {
                        'flowmeter_id': flowmeter.id,
                        'volume': waterpipeflowreading['volume'],
                        'instant_flow': waterpipeflowreading['instant_flow'],
                        }
                    resp.append(refined_waterpipeflowreading)
        return resp

    def save_waterpipeflowreadings(self, waterpipeflowreadings,
                                   update_log=True):
        number_of_waterpipeflowreadings = len(waterpipeflowreadings)
        number_of_negative_waterpipeflowreadings = 0
        if number_of_waterpipeflowreadings > 0:
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            for waterpipeflowreading in waterpipeflowreadings:
                is_negative, negative_volume = \
                    self.is_negative_waterpipeflowreading(waterpipeflowreading)
                if is_negative:
                    self.env['wua.negative.flowreading'].create({
                        'flowmeter_id': waterpipeflowreading['flowmeter_id'],
                        'reading_time': reading_time,
                        'volume': waterpipeflowreading['volume'],
                        'instant_flow': waterpipeflowreading['instant_flow'],
                        'consumption_volume': negative_volume,
                        'from_remotecontrol': True,
                        })
                    number_of_negative_waterpipeflowreadings = \
                        number_of_negative_waterpipeflowreadings + 1
                else:
                    self.create({
                        'flowmeter_id': waterpipeflowreading['flowmeter_id'],
                        'reading_time': reading_time,
                        'volume': waterpipeflowreading['volume'],
                        'instant_flow': waterpipeflowreading['instant_flow'],
                        'initialization_reading': False,
                        'from_import': False,
                        'validated': False,
                        })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved water-pipe readings') +
                             '... ' + str(number_of_waterpipeflowreadings))
        return number_of_negative_waterpipeflowreadings
