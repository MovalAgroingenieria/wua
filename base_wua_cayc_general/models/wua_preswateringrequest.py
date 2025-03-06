# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


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

    @api.model
    def create(self, vals):
        record = super(WuaPresreswateringrequest, self).create(vals)
        if record.parent_partner_id:
            record.message_subscribe(partner_ids=[record.parent_partner_id.id])
            message = self.env['mail.message'].sudo().create({
                'body': _(
                    'A new preswatering request has been created by user: '
                    '%s on %s.' %
                    (record.create_uid.name, record.create_date),
                ),
                'subject': _('New Preswatering Request'),
                'model': record._name,
                'res_id': record.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'partner_ids': [(4, record.parent_partner_id.id)],
            })
            if record.parent_partner_id.email:
                mail_values = {
                    'subject': _('New Preswatering Request'),
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
