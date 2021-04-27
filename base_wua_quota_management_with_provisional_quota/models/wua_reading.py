# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def do_import_readings(self, save_data=True, show_message=True):
        if save_data:
            self.env['wua.controlreading'].do_import_controlreadings(
                True, False)
        resp = super(WuaReading, self).do_import_readings(
            save_data, show_message)
        return resp
