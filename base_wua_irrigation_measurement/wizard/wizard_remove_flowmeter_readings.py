# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardRemoveFlowmeterReadings(models.TransientModel):
    _name = 'wizard.remove.flowmeter.readings'
    _description = 'Dialog box to delete flow-meter readings'

    initial_date = fields.Datetime(
        string='Initial Date',
        required=True,
        default=lambda self: self._get_default_initial_date())

    end_date = fields.Datetime(
        string='End Date',
        required=True,
        default=lambda self: self._get_default_end_date())

    num_readings_to_delete = fields.Integer(
        readonly=True,
        string='Readings to delete',
        help="Number of reading to be deleted")

    @api.model
    def _get_default_initial_date(self):
        current_reading = self.env['wua.flowreading'].browse(
            self.env.context['active_id'])
        return current_reading.reading_time

    @api.model
    def _get_default_end_date(self):
        current_reading = self.env['wua.flowreading'].browse(
            self.env.context['active_id'])
        return current_reading.reading_time

    @api.onchange('initial_date', 'end_date')
    def _calculate_readings_to_delete(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        self.num_readings_to_delete = len(self.env['wua.flowreading'].search([
            ('reading_time', '>=', self.initial_date),
            ('reading_time', '<=', self.end_date),
            ('initialization_reading', '=', False)]))

    def get_delete_period(self):
        if len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        self.delete_readings(self.initial_date, self.end_date)

    def delete_readings(self, initial_date, end_date):
        # Get readings between date range
        readings_to_delete = self.env['wua.flowreading'].search([
            ('reading_time', '>=', initial_date),
            ('reading_time', '<=', end_date)],
            order='reading_time desc')
        # Get flow-meter list
        flowmeter_list = []
        for reading_to_delete in readings_to_delete:
            flowmeter_list.append(
                self.env['wua.flowmeter'].browse(
                    reading_to_delete.flowmeter_id.id))
        flowmeter_list = list(set(flowmeter_list))  # Delete repeated

        # Get readings for flow-meter in date range
        for flowmeter in flowmeter_list:
            flowmeter_readings_to_delete = self.env['wua.flowreading'].search([
                ('flowmeter_id', '=', flowmeter.id),
                ('reading_time', '>=', initial_date),
                ('reading_time', '<=', end_date),
                ('initialization_reading', '=', False)],
                order='reading_time desc')
            for read_to_del in flowmeter_readings_to_delete:
                if read_to_del.is_last_reading:
                    read_to_del.unlink()
