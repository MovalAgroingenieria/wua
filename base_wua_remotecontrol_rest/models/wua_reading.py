# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
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
    def do_import_readings(self):
        # Provisional
        print 'do_import_readings...'
        self.create({
            'watermeter_id': 20,
            'reading_time': datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            'volume': 1000,
            'initialization_reading': False,
            })
