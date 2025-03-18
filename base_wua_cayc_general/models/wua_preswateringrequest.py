# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from datetime import timedelta, datetime


class WuaPresreswateringrequest(models.Model):
    _inherit = 'wua.preswateringrequest'

    parent_partner_id = fields.Many2one(
        string='Parent Partner',
        comodel_name='res.partner',
        compute='_compute_parent_partner_id',
        store=True,
    )

    partner_parcel_owner_area = fields.Float(
        string='Partner Parcel Owner Area (ha)',
        store=True,
        compute='_compute_partner_parcel_owner_area',
    )

    is_recurrence = fields.Boolean(
        default=True,
    )

    @api.onchange('initial_date')
    def _onchange_initial_date(self):
        if self.initial_date:
            period = self.env['wua.preswateringperiod'].search(
                [('initial_date', '<=', self.initial_date),
                 ('end_date', '>=', self.initial_date)], limit=1)
            self.preswateringperiod_id = period
            self.recurrence_end_date = fields.Datetime.to_string(
                fields.Datetime.from_string(self.initial_date) +
                timedelta(days=1),
            )

    @api.constrains('recurrence_end_date', 'preswateringperiod_id',
                    'is_recurrence')
    def _check_recurrence_end_date_within_period(self):
        pass

    @api.depends('partner_id', 'partner_id.parent_partner_id')
    def _compute_parent_partner_id(self):
        for record in self:
            parent_partner_id = None
            if record.partner_id and record.partner_id.parent_partner_id:
                parent_partner_id = record.partner_id.parent_partner_id
            record.parent_partner_id = parent_partner_id

    @api.depends('partner_id', 'partner_id.parcel_owner_area')
    def _compute_partner_parcel_owner_area(self):
        for record in self:
            partner_parcel_owner_area = 0.0
            if record.partner_id and record.partner_id.parcel_owner_area:
                partner_parcel_owner_area = record.partner_id.parcel_owner_area
            record.partner_parcel_owner_area = partner_parcel_owner_area

    @api.depends('presresconsumption_ids')
    def _compute_track_presresconsumption_ids(self):
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second',
        )
        for record in self:
            track_presresconsumption_ids = []
            for presresconsumption in record.presresconsumption_ids:
                wc_name = presresconsumption.waterconnection_id.name
                nominal_flow = presresconsumption.nominal_flow_ls if \
                    use_flow_ls else presresconsumption.nominal_flow
                nominal_flow_unit = "l/s" if use_flow_ls else "m³/h"
                description = _(
                    'Waterconnection: %s, Flow: %s %s',
                ) % (wc_name, nominal_flow, nominal_flow_unit)
                track_presresconsumption_ids.append(description)
            record.track_presresconsumption_ids = "\n".join(
                track_presresconsumption_ids)

    @api.multi
    def set_preswateringrequests_as_validated(self):
        now = fields.Datetime.now()
        preswateringrequests = self.env['wua.preswateringrequest'].search(
            [('state', '=', '01_draft')]).filtered(
                lambda x: now >= x.modification_deadline)
        for preswateringrequest in preswateringrequests:
            preswateringrequest.change_state_validated()

    def _copy_single_request(self, request, copy_date):
        copy_date_str = copy_date.strftime('%Y-%m-%d')
        preswateringperiod = self.env['wua.preswateringperiod'].search([
            ('initial_date', '<=', copy_date_str),
            ('end_date', '>=', copy_date_str),
        ], limit=1)
        new_request_vals = {
            'preswateringperiod_id': preswateringperiod.id,
            'initial_date': copy_date_str,
            'partner_id': request.partner_id.id,
            'user_id': request.user_id.id,
            'is_recurrence': True,
            'recurrence_end_date': fields.Datetime.to_string(
                fields.Datetime.from_string(copy_date_str) + timedelta(days=1),
            ),
        }
        if request.presresconsumption_ids:
            presresconsumption_vals = []
            for presresconsumption in request.presresconsumption_ids:
                presresconsumption_vals.append((0, 0, {
                    'waterconnection_id':
                        presresconsumption.waterconnection_id.id,
                    'watering_duration':
                        presresconsumption.watering_duration,
                    'nominal_flow':
                        presresconsumption.nominal_flow,
                    'nominal_flow_ls':
                        presresconsumption.nominal_flow_ls,
                    'initial_hour':
                        presresconsumption.initial_hour,
                }))
            new_request_vals['presresconsumption_ids'] = \
                presresconsumption_vals
        self.env['wua.preswateringrequest'].create(new_request_vals)

    @api.multi
    def generate_recurrences_preswateringrequests(self):
        preswaternigrequests = self.env['wua.preswateringrequest'].search([
            ('initial_date', '=', fields.Date.today()),
        ])
        next_day = datetime.strptime(fields.Date.today(), '%Y-%m-%d')
        next_day += timedelta(days=1)
        for record in preswaternigrequests:
            next_day_request = self.env['wua.preswateringrequest'].search([
                ('initial_date', '=', next_day),
                ('partner_id', '=', record.partner_id.id),
            ], limit=1)
            if not next_day_request:
                record_to_copy = None
                if (record.is_recurrence):
                    record_to_copy = record
                # Not recurrence, search for the last recurrence data
                else:
                    last_recurrence = self.env['wua.preswateringrequest'].\
                        search([
                            ('is_recurrence', '=', True),
                            ('partner_id', '=', record.partner_id.id),
                            ('initial_date', '<', record.initial_date),
                        ], order='initial_date desc', limit=1)
                    record_to_copy = last_recurrence
                if record_to_copy:
                    self._copy_single_request(record_to_copy, next_day)

    @api.model
    def create(self, vals):
        lang = 'es_ES'
        if (self.env and self.env.user and self.env.user.lang):
            lang = self.env.user.lang
        record = super(WuaPresreswateringrequest, self).create(vals)
        if record.parent_partner_id:
            record.message_subscribe(partner_ids=[record.parent_partner_id.id])
            subject = self.env['ir.translation']._get_source(
                False, 'code', lang, u'New Preswatering Request') or \
                _('New Preswatering Request')
            body_str = _(u'A new preswatering request has been created by '
                         u'user: %s on %s.')
            body = (self.env['ir.translation']._get_source(
                False, 'code', lang, body_str) or body_str) % (
                    record.create_uid.name, record.create_date)
            message = self.env['mail.message'].sudo().create({
                'body': body,
                'subject': subject,
                'model': record._name,
                'res_id': record.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'partner_ids': [(4, record.parent_partner_id.id)],
            })
            if record.parent_partner_id.email:
                mail_values = {
                    'subject': subject,
                    'body_html': message.body,
                    'email_to': record.parent_partner_id.email,
                    'email_from':
                        self.env.user.email or 'no-reply@yourdomain.com',
                    'auto_delete': False,
                    'notification': True,
                }
                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.send()
        return record
