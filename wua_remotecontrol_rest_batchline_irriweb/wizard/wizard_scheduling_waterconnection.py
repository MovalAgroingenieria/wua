# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WizardSchedulingWaterconnection(models.TransientModel):
    _name = 'wizard.scheduling.waterconnection'
    _description = 'Dialog box to schedule a water connection'

    html_scheduling_frame = fields.Text(
        string='IrriWEB Scheduling',
        readonly=True)

    @api.model
    def default_get(self, var_fields):
        current_waterconnection_data = \
            self._get_current_waterconnection_data()
        return current_waterconnection_data

    def _get_current_waterconnection_data(self):
        waterconnection = self.env['wua.waterconnection'].browse(
            self.env.context['active_id'])
        resp = {
            'html_scheduling_frame': waterconnection.html_scheduling_frame,
            }
        return resp
