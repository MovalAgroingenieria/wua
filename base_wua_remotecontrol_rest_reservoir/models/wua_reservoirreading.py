# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, exceptions, _


class WuaReservoirreading(models.Model):
    _inherit = 'wua.reservoirreading'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    # Hook that will be implemeneted on every telecontrol, appending the info
    def do_import_reservoirreading_of_telecontrol(self):
        reservoirreadings = []
        error_message = ''
        error_reservoirs = []
        return reservoirreadings, error_message, error_reservoirs

    @api.model
    def do_import_reservoirreadings(self, save_data=True, show_message=True):
        # for resp: item 1: list of reservoir-readings, item 2: number of
        # reservoir-readings, item 3: possible error message, item 4: list of
        # problematic reservoirs.
        resp = [None, 0, '', None]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            reservoirreadings, error_message, error_reservoirs = \
                self.do_import_reservoirreading_of_telecontrol()
            reservoirreadings = self.refine_reservoirreadings(
                reservoirreadings)
            if reservoirreadings:
                resp[0] = reservoirreadings
                resp[1] = len(reservoirreadings)
                resp[2] = error_message
                resp[3] = error_reservoirs
                if save_data:
                    self.save_reservoirreadings(reservoirreadings)
                prefix_message_01 = _('Remote Control: '
                                      'Getting reservoir-readings')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' +
                             suffix_message_01)
            if error_message:
                prefix_message_02 = _('Remote Control: Error '
                                        'getting reservoir-readings')
                suffix_message_02 = error_message
                company_name = self.env.user.company_id.name
                website_url = self.env['ir.config_parameter'].get_param("web.base.url")
                domain =  self.env['ir.config_parameter'].get_param("mail.catchall.domain")
                _logger = logging.getLogger(
                    self.__class__.__name__)
                _logger.info(prefix_message_02 + '... ' +
                                suffix_message_02)
                telecontrol_failed_template_id = self.env.ref(
                    'base_wua_remotecontrol_rest.'
                    'telecontrol_failed_email_template').id
                mail_template = self.env['mail.template'].browse(
                    telecontrol_failed_template_id)
                mail_template.subject = 'Reservoir reading remote control in %s has experienced some problem' % (domain or self.pool.db_name)
                mail_template.body_html = '''
                    <p style="margin: 0px; padding: 0px; font-size: 13px;">
                        <b><a href="%s">%s</a></p></b>
                        <br/>
                        <span>%s</span>
                    </p>
                ''' % (website_url, company_name, error_message.replace('\n', '<br/>'))
                mail_template.send_mail(self.id, force_send=True)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def refine_reservoirreadings(self, reservoirreadings):
        resp = []
        reservoirs = self.env['wua.reservoir']
        for reservoirreading in reservoirreadings:
            filtered_reservoir = reservoirs.search(
                [('name', '=', reservoirreading['reservoir']), ])
            if filtered_reservoir:
                reservoir = filtered_reservoir[0]
                refined_reservoirreading = {
                    'reservoir_id': reservoir.id,
                    'value': reservoirreading['value'],
                    }
                resp.append(refined_reservoirreading)
        return resp

    def save_reservoirreadings(self, reservoirreadings, update_log=True):
        number_of_reservoirreadings = len(reservoirreadings)
        if number_of_reservoirreadings > 0:
            measurements_in_height = self.env['ir.values'].get_default(
                'wua.infrastructure.configuration', 'measurements_in_height'
            )
            conversion_factor = 1.0
            if (measurements_in_height):
                conversion_factor = self.env['ir.values'].get_default(
                    'wua.infrastructure.configuration',
                    'conversion_factor_bar_to_meters'
                )
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            for reservoirreading in reservoirreadings:
                reservoir_id = reservoirreading['reservoir_id']
                reservoir_data = {
                    'reservoir_id': reservoir_id,
                    'reading_time': reading_time,
                    'from_import': False,
                    }
                if (not measurements_in_height):
                    reservoir_data['volume_entered'] = \
                        reservoirreading['value']
                else:
                    reservoir_obj = self.env['wua.reservoir'].browse(
                        reservoir_id)
                    reservoir_data['height'] = \
                        reservoirreading['value'] * conversion_factor - \
                        reservoir_obj.height_correction
                self.create(reservoir_data)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved reservoir-readings') +
                             '... ' + str(number_of_reservoirreadings))
