# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardCopyRequests(models.TransientModel):
    _name = 'wizard.copy.requests'
    _description = 'Dialog box to copy watering requests'

    source_wateringperiod_id = fields.Many2one(
        string='Source Period',
        comodel_name='wua.wateringperiod')

    source_wateringperiod_name = fields.Char(
        string='Source Period')

    number_of_requests = fields.Integer(
        string='Number of requests')

    wateringperiods_ok = fields.Boolean(
        string='Correct Watering Periods')

    destination_wateringperiod_id = fields.Many2one(
        string='Destination Period',
        comodel_name='wua.wateringperiod')

    destination_type = fields.Selection([
        (1, 'Single Copy'),
        (2, 'Multiple Copy')],
        'Destination',
        required=True)

    initial_date = fields.Date(
        string='Initial Date')

    end_date = fields.Date(
        string='End Date')

    @api.model
    def default_get(self, var_fields):
        wateringperiods_ok = True
        wateringrequest_ids = self.env.context['active_ids']
        wateringrequests = self.env['wua.wateringrequest'].browse(
            wateringrequest_ids)
        is_first = True
        source_wateringperiod_name = ''
        source_wateringperiod_id = None
        i = 1
        for wateringrequest in wateringrequests:
            if is_first:
                is_first = False
                source_wateringperiod_id = wateringrequest.wateringperiod_id
            else:
                i = i + 1
                if (wateringrequest.wateringperiod_id !=
                   source_wateringperiod_id):
                    wateringperiods_ok = False
                    break
        if wateringperiods_ok:
            source_wateringperiod_name = self.get_name_from_wateringperiod(
                source_wateringperiod_id)
        return {
            'source_wateringperiod_id': source_wateringperiod_id.id,
            'source_wateringperiod_name': source_wateringperiod_name,
            'number_of_requests': i,
            'wateringperiods_ok': wateringperiods_ok,
            'destination_type': 1
            }

    @api.multi
    def copy_requests(self):
        self.ensure_one()
        if self.destination_type == 2:
            dates_ok = self.test_initial_end_date(
                self.source_wateringperiod_id,
                self.initial_date, self.end_date)
            if not dates_ok:
                raise exceptions.UserError(_('The dates are incorrect, or '
                                             'the source watering period is '
                                             'within destination dates.'))
            destination_wateringperiods = \
                self.env['wua.wateringperiod'].search(
                    [('initial_date', '>=', self.initial_date),
                     ('end_date', '<=', self.end_date),
                     ('state', '=', 'open')],
                    order='initial_date')
            if destination_wateringperiods:
                for destination_wateringperiod in destination_wateringperiods:
                    self.do_copy(destination_wateringperiod,
                                 self.env.context['active_ids'])
        else:
            self.do_copy(self.destination_wateringperiod_id,
                         self.env.context['active_ids'])

    def get_name_from_wateringperiod(self, wateringperiod):
        initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
            wateringperiod.initial_date)
        end_date_str = self.env['wua.parcel'].transform_date_to_locale(
            wateringperiod.end_date)
        if wateringperiod.agriculturalseason_id.description != '':
            name = initial_date_str + ' - ' + end_date_str + ' ' + \
                '(' + wateringperiod.agriculturalseason_id.description + ')'
        else:
            name = name = initial_date_str + ' - ' + end_date_str
        return name

    def test_initial_end_date(self, source_wateringperiod_id,
                              initial_date, end_date, ):
        is_ok = initial_date < end_date
        if is_ok:
            colission = (source_wateringperiod_id.initial_date >=
                         initial_date and
                         source_wateringperiod_id.initial_date <=
                         end_date) or \
                        (source_wateringperiod_id.end_date >=
                         initial_date and
                         source_wateringperiod_id.end_date <=
                         end_date)
            is_ok = not colission
        return is_ok

    def do_copy(self, destination_wateringperiod_id, active_ids):
        source_wateringrequests = self.env['wua.wateringrequest'].browse(
            active_ids)
        for request in source_wateringrequests:
            if request.number_of_subparcels > 0:
                gravconsumption_ids = []
                for gravconsumption in request.gravconsumption_ids:
                    gravconsumption_vals = {
                        'subparcel_id': gravconsumption.subparcel_id.id,
                        'wateringperiod_id': destination_wateringperiod_id.id,
                        'watering_duration': gravconsumption.watering_duration,
                        }
                    gravconsumption_ids.append((0, 0, gravconsumption_vals))
                wateringrequest_vals = {
                    'wateringperiod_id': destination_wateringperiod_id.id,
                    'partner_id': request.partner_id.id,
                    'gravconsumption_ids': gravconsumption_ids,
                    }
            else:
                wateringrequest_vals = {
                    'wateringperiod_id': destination_wateringperiod_id.id,
                    'partner_id': request.partner_id.id,
                    }
            self.env['wua.wateringrequest'].create(wateringrequest_vals)
