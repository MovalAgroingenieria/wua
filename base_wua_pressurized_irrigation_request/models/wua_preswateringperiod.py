# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WuaPreswateringperiod(models.Model):
    _name = 'wua.preswateringperiod'
    _description = 'Preswatering Period'
    _order = 'initial_date'

    name = fields.Char(
        string='Pres Watering Period',
        store=True,
        compute='_compute_name',
        index=True,
    )

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True,
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
    )

    state = fields.Selection(
        string='Status',
        selection=[
            ('01_open', 'Open'),
            ('02_closed', 'Closed'),
        ],
        required=True,
        default='02_closed',
        index=True,
    )

    description = fields.Char(
        string='Description',
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        ondelete='restrict',
        index=True,
    )

    year = fields.Integer(
        string='Year',
        compute='_compute_year',
        store=True,
    )

    notes = fields.Html(
        string='Notes',
    )

    preswateringrequest_ids = fields.One2many(
        string='Watering Requests',
        comodel_name='wua.preswateringrequest',
        inverse_name='preswateringperiod_id',
    )

    preswatering_ids = fields.One2many(
        string='Pres Waterings',
        comodel_name='wua.preswatering',
        inverse_name='preswateringperiod_id',
    )

    number_of_requests = fields.Integer(
        string='Number of Requests',
        compute='_compute_number_of_requests',
        compute_sudo=True,
        store=True,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Preswatering Period.'),
        ('valid_dates', 'CHECK (initial_date <= end_date)',
         'Invalid dates: End date must be after start date.'),
    ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if(record.initial_date):
                name = record.initial_date
            record.name = name

    @api.depends('initial_date')
    def _compute_year(self):
        for record in self:
            year = 0
            if record.initial_date:
                year = int(record.initial_date[:4])
            record.year = year

    @api.multi
    def name_get(self):
        result = []
        parcel_model = self.env['wua.parcel']
        # Context may not exists?
        lang = getattr(self.env, 'context', {}).get('lang', 'es_ES')
        for record in self:
            initial_date_str = parcel_model.transform_date_to_locale(
                record.initial_date, lang,
            )
            end_date_str = parcel_model.transform_date_to_locale(
                record.end_date, lang,
            )
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.depends('preswateringrequest_ids')
    def _compute_number_of_requests(self):
        for record in self:
            record.number_of_requests = len(record.preswateringrequest_ids)

    @api.model
    def create(self, vals):
        agriculturalseason_id = vals['agriculturalseason_id']
        initial_date = vals['initial_date']
        end_date = vals['end_date']
        range_of_dates_within_agriculturalseason = \
            self.test_range_of_dates_within_agriculturalseason(
                agriculturalseason_id, initial_date, end_date)
        if not range_of_dates_within_agriculturalseason:
            raise exceptions.UserError(_('The watering period is outside '
                                         'his agricultural season.'))
        non_overlapping_wateriorperiod = \
            self.test_non_overlapping_wateriorperiod(
                agriculturalseason_id, initial_date, end_date)
        if not non_overlapping_wateriorperiod:
            raise exceptions.UserError(_('The watering period is overlapped '
                                         'on another period.'))
        return super(WuaPreswateringperiod, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('agriculturalseason_id' in vals or
           'initial_date' in vals or 'end_date' in vals):
            if 'agriculturalseason_id' in vals:
                agriculturalseason_id = vals['agriculturalseason_id']
            else:
                agriculturalseason_id = self.agriculturalseason_id.id
            if 'initial_date' in vals:
                initial_date = vals['initial_date']
            else:
                initial_date = self.initial_date
            if 'end_date' in vals:
                end_date = vals['end_date']
            else:
                end_date = self.end_date
            range_of_dates_within_agriculturalseason = \
                self.test_range_of_dates_within_agriculturalseason(
                    agriculturalseason_id, initial_date, end_date)
            if not range_of_dates_within_agriculturalseason:
                raise exceptions.UserError(_('The watering period is outside '
                                             'his agricultural season.'))
            non_overlapping_wateriorperiod = \
                self.test_non_overlapping_wateriorperiod(
                    agriculturalseason_id, initial_date, end_date, self.id)
            if not non_overlapping_wateriorperiod:
                raise exceptions.UserError(_('The watering period is '
                                             'overlapped on another period.'))
        return super(WuaPreswateringperiod, self).write(vals)

    def test_range_of_dates_within_agriculturalseason(self,
                                                      agriculturalseason_id,
                                                      initial_date, end_date):
        is_ok = False
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            agriculturalseason_id)
        if agriculturalseason:
            is_ok = (initial_date >= agriculturalseason.initial_date and
                     end_date <= agriculturalseason.end_date)
        return is_ok

    def test_non_overlapping_wateriorperiod(self,
                                            agriculturalseason_id,
                                            initial_date, end_date,
                                            wateringperiod_id_to_exclude=0):
        is_ok = False
        agriculturalseason = self.env['wua.agriculturalseason'].browse(
            agriculturalseason_id)
        if agriculturalseason:
            preswateringperiods = self.env['wua.preswateringperiod'].search(
                [('agriculturalseason_id', '=', agriculturalseason_id),
                 ('id', '!=', wateringperiod_id_to_exclude)])
            is_ok = True
            for wateringperiod in preswateringperiods:
                not_overlapped = \
                    ((wateringperiod.initial_date < initial_date and
                      wateringperiod.end_date < initial_date) or
                     (wateringperiod.initial_date > end_date and
                      wateringperiod.end_date > end_date))
                if not not_overlapped:
                    is_ok = False
                    break
        return is_ok

    def open_period(self):
        for record in self:
            record.state = '01_open'

    def close_period(self):
        for record in self:
            record.state = '02_closed'

    @api.multi
    def set_as_open(self, active_preswateringperiods):
        preswateringperiods = self.env['wua.preswateringperiod'].browse(
            active_preswateringperiods)
        for record in preswateringperiods:
            vals = {
                'state': '01_open',
                }
            record.write(vals)

    @api.multi
    def set_as_close(self, active_preswateringperiods):
        preswateringperiods = self.env['wua.preswateringperiod'].browse(
            active_preswateringperiods)
        for record in preswateringperiods:
            vals = {
                'state': '02_closed',
                }
            record.write(vals)

    def send_partner_notifications(self, preswateringrequests):
        partner_consumptions = {}
        for request in preswateringrequests:
            for consumption in request.presresconsumption_ids:
                partner_id = request.partner_id.id
                if partner_id not in partner_consumptions:
                    partner_consumptions[partner_id] = []
                timezone = request.partner_id.tz or 'Europe/Madrid'
                request_time = consumption.request_time
                utc_time = fields.Datetime.from_string(request_time)
                user_tz = pytz.timezone(timezone)
                localized_request_time = pytz.utc.localize(utc_time).\
                    astimezone(user_tz)
                formatted_request_time = localized_request_time.strftime(
                    '%d/%m/%Y')
                partner_consumptions[partner_id].append({
                    'date': formatted_request_time,
                    'water_connection': consumption.waterconnection_id.name,
                    'nominal_flow_ls': consumption.nominal_flow_ls,
                    'watering_duration': consumption.watering_duration,
                    'watering_volume': consumption.watering_volume,
                })
        mail_template = self.env.ref(
            'base_wua_pressurized_irrigation_request.'
            'wua_preswatering_weekly_email_template')
        for partner_id, consumptions in partner_consumptions.items():
            partner = self.env['res.partner'].browse(partner_id)
            if partner.email:
                mail_template.with_context({
                    'data': {'consumptions': consumptions},
                }).send_mail(partner.id, force_send=True)

    def action_send_partner_notifications(self):
        self.send_partner_notifications(self.preswateringrequest_ids)

    @api.model
    def send_partner_notifications_cron_action(self, days_advance=7):
        today = fields.Date.today()
        today_date = fields.Date.from_string(fields.Date.today())
        end_date = today_date + timedelta(days=days_advance)
        end_str = fields.Date.to_string(end_date)
        preswateringrequests = self.env['wua.preswateringrequest'].search([
            ('initial_date', '>=', today),
            ('initial_date', '<=', end_str),
        ])
        self.send_partner_notifications(preswateringrequests)

    @api.multi
    def action_see_preswateringrequests(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preswatering Requests'),
            'res_model': 'wua.preswateringrequest',
            'view_mode': 'tree,form',
            'domain': [('preswateringperiod_id', '=', self.id)],
            'target': 'current',
        }
