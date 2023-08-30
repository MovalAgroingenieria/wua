# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, api, _, exceptions, fields


class WuaWaterconnectionIrrigationSchedule(models.Model):
    _inherit = 'wua.waterconnection.irrigation.schedule'

    from_remotecontrol = fields.Boolean(
        string='From Remote Control',
        default=False,
        required=True,
    )

    # Hook that will be implemented on all telecontrols, appending info
    def do_import_waterconnection_irrigation_schedule_all(self, list_of_wc):
        wc_irr_schedule = []
        error_message = ''
        return [wc_irr_schedule, error_message]

    @api.model
    def do_import_waterconnection_irrigation_schedule(
            self, save_data=True, show_message=True, list_of_wc=False):
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if (enable_remotecontrol):
            wc_irr_schedule, error_message = \
                self.do_import_waterconnection_irrigation_schedule_all(
                    list_of_wc)
            wc_irr_schedule = self.refine_waterconnection_irrigation_schedule(
                wc_irr_schedule)
            if save_data:
                self.save_waterconnection_irrigation_schedule(wc_irr_schedule)
            if error_message:
                prefix_message = _('Remote Control: Error getting '
                                   'waterconnection irrigation schedule')
                suffix_message = error_message
                company_name = self.env.user.company_id.name
                website_url = self.env['ir.config_parameter'].get_param(
                    "web.base.url")
                domain = self.env['ir.config_parameter'].get_param(
                    "mail.catchall.domain")
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message + '... ' + suffix_message)
                telecontrol_failed_template_id = self.env.ref(
                    'base_wua_remotecontrol_rest.'
                    'telecontrol_failed_email_template').id
                mail_template = self.env['mail.template'].browse(
                    telecontrol_failed_template_id)
                mail_template.subject = '''
                    Waterconnection irrigation_schedule in %s
                    has experienced some problem
                ''' % (domain or self.pool.db_name)
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

    def refine_waterconnection_irrigation_schedule(self, wc_irr_schedule):
        resp = []
        for info in wc_irr_schedule:
            refined_wc_irr_schedule = {
                'waterconnection_id': info['waterconnection_id'],
                'state': info['state'],
                'shift_number': info['shift_number'],
                'irrigation_start_day': info['irrigation_start_day'],
                'irrigation_start_hour': info['irrigation_start_hour'],
                'irrigation_end_hour': info['irrigation_end_hour'],
                'irrigation_duration': info['irrigation_duration'],
                'max_irrigation_volume': info['max_irrigation_volume'],
                }
            resp.append(refined_wc_irr_schedule)
        return resp

    def save_waterconnection_irrigation_schedule(self, wc_irr_schedule,
                                                 update_log=True):
        number_of_wc_irr_schedule = len(wc_irr_schedule)
        # Aux variable to check which waterconnection related schedules
        # have been removed (Removed before add new ones)
        wc_already_cleaned = []
        if number_of_wc_irr_schedule > 0:
            for info in wc_irr_schedule:
                wc = self.env['wua.waterconnection'].browse(
                    info['waterconnection_id'])
                waterconnection_irrigation_schedule_params = {
                    'state': info['state'],
                    'shift_number': info['shift_number'],
                    'irrigation_start_day': info['irrigation_start_day'],
                    'irrigation_start_hour': info['irrigation_start_hour'],
                    'irrigation_end_hour': info['irrigation_end_hour'],
                    'irrigation_duration': info['irrigation_duration'],
                    'max_irrigation_volume': info['max_irrigation_volume'],
                    'waterconnection_id': info['waterconnection_id'],
                    'from_remotecontrol': True,
                }
                if (wc.irrigation_schedule_ids and
                    len(wc.irrigation_schedule_ids) > 0 and wc.id not in
                        wc_already_cleaned):
                    wc.irrigation_schedule_ids.unlink()
                    wc_already_cleaned.append(wc.id)
                else:
                    self.create(waterconnection_irrigation_schedule_params)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Irrigation Schedules') +
                             '... ' +
                             str(number_of_wc_irr_schedule))
