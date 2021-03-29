# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardSchedulingTank(models.TransientModel):
    _name = 'wizard.scheduling.tank'
    _description = 'Dialog box to schedule a tank'

    html_scheduling_frame = fields.Text(
        string='IrriWEB Scheduling',
        readonly=True)

    @api.model
    def default_get(self, var_fields):
        current_partner_data = \
            self._get_current_partner_data()
        return current_partner_data

    def _get_current_partner_data(self):
        partner = self.env['res.partner'].browse(
            self.env.context['active_id'])
        resp = {
            'html_scheduling_frame': partner.html_scheduling_frame,
            }
        return resp
