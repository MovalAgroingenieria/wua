# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WizardRemoveReadings(models.TransientModel):
    _name = 'wizard.remove.readings'
    _description = 'Dialog box to delete readings'

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
        current_reading = self.env['wua.reading'].browse(self.env.context['active_id'])
        return current_reading.reading_time

    @api.model
    def _get_default_end_date(self):
        current_reading = self.env['wua.reading'].browse(self.env.context['active_id'])
        return current_reading.reading_time

    @api.onchange('initial_date', 'end_date')
    def _calculate_readings_to_delete(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates, the initial date is before the end date.'))
        self.num_readings_to_delete = len(self.env['wua.reading'].search([('reading_time','>=',self.initial_date),('reading_time','<=',self.end_date)]))

    @api.multi
    def get_delete_period(self):
        self.ensure_one()
        if len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates, the initial date is before the end date.'))
        self.delete_readings(self.initial_date, self.end_date)

    def delete_readings(self, initial_date, end_date):
        # Get readings between date range
        readings_to_delete = self.env['wua.reading'].search([('reading_time','>=',initial_date),('reading_time','<=',end_date)])

        # Get watermeter list
        watermeter_list = []
        for reading_to_delete in readings_to_delete:
            watermeter_list.append(self.env['wua.watermeter'].browse(reading_to_delete.watermeter_id.id))
        watermeter_list = list(set(watermeter_list))  # Delete repeated 

        # Get readings for watermeter in date ranges
        for watermeter in watermeter_list:
            watermeter_readings_to_delete =  self.env['wua.reading'].search([
                ('watermeter_id','=',watermeter.id),
                ('reading_time','>=',initial_date),
                ('reading_time','<=',end_date)])

            for read_to_del in watermeter_readings_to_delete:
                if read_to_del.initialization_reading:
                    raise exceptions.UserError(_(
                        'Initial reading can not be deleted'))
                else:
                    if read_to_del.is_last_reading:
                        read_to_del.unlink()

