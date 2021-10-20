# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardRemoveControlReadings(models.TransientModel):
    _name = 'wizard.remove.controlreadings'
    _description = 'Dialog box to delete control readings'

    initial_date = fields.Datetime(
        string='Initial Date',
        required=True,
        default=lambda self: self._get_default_initial_date())

    end_date = fields.Datetime(
        string='End Date',
        required=True,
        default=lambda self: self._get_default_end_date())

    num_controlreadings_to_delete = fields.Integer(
        readonly=True,
        string='Control readings to delete',
        help="Number of control reading to be deleted")

    @api.model
    def _get_default_initial_date(self):
        current_controlreading = self.env['wua.controlreading'].browse(
            self.env.context['active_id'])
        return current_controlreading.reading_time

    @api.model
    def _get_default_end_date(self):
        current_controlreading = self.env['wua.controlreading'].browse(
            self.env.context['active_id'])
        return current_controlreading.reading_time

    @api.onchange('initial_date', 'end_date')
    def _calculate_controlreadings_to_delete(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        self.num_controlreadings_to_delete = \
            len(self.env['wua.controlreading'].search([
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
        self.delete_controlreadings(self.initial_date, self.end_date)

    def delete_controlreadings(self, initial_date, end_date):
        # Get readings between date range
        controlreadings_to_delete = self.env['wua.controlreading'].search([
            ('reading_time', '>=', initial_date),
            ('reading_time', '<=', end_date)],
            order='reading_time desc')

        # Get watermeter list
        watermeter_list = []
        for controlreading_to_delete in controlreadings_to_delete:
            watermeter_list.append(
                self.env['wua.watermeter'].browse(
                    controlreading_to_delete.watermeter_id.id))
        watermeter_list = list(set(watermeter_list))  # Delete repeated

        # Get control readings for watermeter in date range
        for watermeter in watermeter_list:
            watermeter_controlreadings_to_delete = \
                self.env['wua.controlreading'].search([
                    ('watermeter_id', '=', watermeter.id),
                    ('reading_time', '>=', initial_date),
                    ('reading_time', '<=', end_date),
                    ('initialization_reading', '=', False)],
                    order='reading_time desc')

            for read_to_del in watermeter_controlreadings_to_delete:
                if read_to_del.is_last_reading:
                    read_to_del.unlink()
