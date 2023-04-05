# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardPrintReadings(models.TransientModel):
    _name = 'wizard.print.readings'
    _description = 'Dialog box to print readings'

    def _default_waterconnection_id(self):
        waterconnection_id = self.env.context['active_id']
        return waterconnection_id

    def _default_initial_date(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        initial_date = active_agriculturalseason.initial_date
        return initial_date

    waterconnection_id = fields.Many2one(
        string="Waterconnection",
        comodel_name='wua.waterconnection',
        default=_default_waterconnection_id)

    initial_date = fields.Datetime(
        string='Initial Date',
        default=_default_initial_date,
        required=True)

    end_date = fields.Datetime(
        string='End Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    num_readings_to_print = fields.Integer(
        readonly=True,
        string='Readings to print',
        compute="_compute_num_readings_to_print",
        help="Number of reading to be printed.")

    reading_ids = fields.One2many(
        string="Readings",
        comodel_name='wua.reading',
        compute="_compute_reading_ids")

    @api.multi
    def _compute_num_readings_to_print(self):
        if self.initial_date and self.end_date:
            if self.initial_date > self.end_date:
                raise exceptions.UserError(
                    _('Incorrect dates, the initial date is before the end '
                      'date.'))
            waterconnection_id = self.env.context['active_id']
            num_readings_to_print = len(self.env['wua.reading'].search([
                ('reading_time', '>=', self.initial_date),
                ('reading_time', '<=', self.end_date),
                ('waterconnection_id', '=', waterconnection_id)]))
            for record in self:
                record.num_readings_to_print = num_readings_to_print

    @api.multi
    def _compute_reading_ids(self):
        if self.initial_date and self.end_date and self.waterconnection_id:
            reading_ids = self.env['wua.reading'].search([
                ('reading_time', '>=', self.initial_date),
                ('reading_time', '<=', self.end_date),
                ('waterconnection_id', '=', self.waterconnection_id.id)]).ids
            for record in self:
                record.reading_ids = reading_ids

    @api.onchange('initial_date', 'end_date')
    def _calculate_readings_to_print(self):
        if self.initial_date and self.end_date:
            if self.initial_date > self.end_date:
                raise exceptions.UserError(
                    _('Incorrect dates, the initial date is before the end '
                      'date.'))
            waterconnection_id = self.env.context['active_id']
            self.num_readings_to_print = len(self.env['wua.reading'].search([
                ('reading_time', '>=', self.initial_date),
                ('reading_time', '<=', self.end_date),
                ('waterconnection_id', '=', waterconnection_id)]))

    @api.multi
    def print_selected_period(self):
        self.ensure_one()
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        report_name = 'base_wua_pressurized_irrigation.wua_waterconnection_' \
            'reading_report_document'
        return self.env['report'].get_action(self, report_name)
