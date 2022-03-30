# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
# from odoo import exceptions, _


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    data_in_hours = fields.Boolean(
        string='Water Amount in hours',
        default=False,
        help='Enter the water amount of a irrigation report as a '
             'hour-value (if not, as a m³-value)')

    hours_sexagesimal = fields.Boolean(
        string='Sexagesimal Hours',
        default=False,
        help='Values of hour in the HH:MM format (if not, as decimal format)')

    @api.multi
    def set_default_values(self):
        previous_data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        current_data_in_hours = self.data_in_hours
        # if previous_data_in_hours != current_data_in_hours:
        #     irrigation_reports = self.env['wua.irrigationreport'].search([])
        #     if irrigation_reports:
        #         raise exceptions.UserError(
        #             _('If there are already irrigation reports, you cannot '
        #               'change the \"Water Amount in hours (Yes/No)\" '
        #               'parameter.\n\n'
        #               'Before it is necessary to delete all irrigation '
        #               'reports.'))
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'data_in_hours',
                           self.data_in_hours)
        values.set_default('wua.irrigation.configuration',
                           'hours_sexagesimal',
                           self.hours_sexagesimal)
        if previous_data_in_hours != current_data_in_hours:
            irrigation_reports = self.env['wua.irrigationreport'].search([])
            if irrigation_reports:
                irrigation_reports._compute_volume()
