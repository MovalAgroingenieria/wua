# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, api, _, exceptions


class WuaWaterconnectionIrrigationEvent(models.Model):
    _inherit = 'wua.waterconnection.irrigation.event'

    # Hook that will be implemented on all telecontrols, appending info
    def do_import_waterconnection_irrigation_event_all(self, list_of_wc):
        wc_irr_event = []
        error_message = ''
        return [wc_irr_event, error_message]

    @api.model
    def do_import_waterconnection_irrigation_event(
            self, save_data=True, show_message=True, list_of_wc=False):
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if enable_remotecontrol is None:
            enable_remotecontrol = False
        if (enable_remotecontrol):
            wc_irr_event, error_message = \
                self.do_import_waterconnection_irrigation_event_all(
                    list_of_wc)
            wc_irr_event = self.refine_waterconnection_irrigation_event(
                wc_irr_event)
            if save_data:
                self.save_waterconnection_irrigation_event(wc_irr_event)
            if error_message:
                prefix_message = _('Remote Control: Error getting '
                                   'waterconnection irrigation event')
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
                    Waterconnection irrigation_event in %s
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

    def refine_waterconnection_irrigation_event(self, wc_irr_event):
        resp = []
        for info in wc_irr_event:
            refined_wc_irr_event = {
                'waterconnection_id': info['waterconnection_id'],
                'irrigation_start_date': info['irrigation_start_date'],
                'irrigation_end_date': info['irrigation_end_date'],
                'irrigation_volume': info['irrigation_volume'],
                }
            if ('irrigation_area_static' in info):
                refined_wc_irr_event['irrigation_area_static'] = info[
                    'irrigation_area_static']
            waterconnection = self.env['wua.waterconnection'].browse(
                info['waterconnection_id'])
            # We must check if the start_Date is greater than the latest end
            # date and only append later ones (Only if some event)
            if (not waterconnection.last_irrigation_event_id or (
                waterconnection.last_irrigation_event_id and
                waterconnection.last_irrigation_event_id.irrigation_end_date <=
                    info['irrigation_start_date'])):
                resp.append(refined_wc_irr_event)
        return resp

    def save_waterconnection_irrigation_event(self, wc_irr_event,
                                              update_log=True):
        number_of_wc_irr_event = len(wc_irr_event)
        if number_of_wc_irr_event > 0:
            for info in wc_irr_event:
                waterconnection_irrigation_event_params = {
                    'waterconnection_id': info['waterconnection_id'],
                    'irrigation_start_date': info['irrigation_start_date'],
                    'irrigation_end_date': info['irrigation_end_date'],
                    'irrigation_volume': info['irrigation_volume'],
                }
                if ('irrigation_area_static' in info):
                    waterconnection_irrigation_event_params[
                        'irrigation_area_static'] = info[
                            'irrigation_area_static']
                self.create(waterconnection_irrigation_event_params)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved Irrigation events') +
                             '... ' +
                             str(number_of_wc_irr_event))
