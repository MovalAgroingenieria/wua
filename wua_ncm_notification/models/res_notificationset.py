# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResNotificationset(models.Model):
    _inherit = 'res.notificationset'

    def _default_create_letter(self):
        resp = False
        with_letter = self.env['ir.values'].get_default(
            'res.notif.config.settings', 'with_letter')
        if with_letter:
            resp = True
        return resp

    file_id = fields.Many2one(
        string='Associated File',
        comodel_name='res.file',
        index=True,
        ondelete='restrict',
    )

    create_letter = fields.Boolean(
        string='Create a output letter automatically',
        default=_default_create_letter,
    )

    def _get_conditions_for_new_notifications(self):
        self.ensure_one()
        resp = super(ResNotificationset,
                     self)._get_conditions_for_new_notifications()
        if (self.notificationset_type_id and
           self.notificationset_type_id.include_partner_if_wua):
            resp.append(('is_wua_partner', '=', True))
        return resp

    # (from hook)
    def _gn_get_additional_fields(self):
        resp = super(ResNotificationset, self)._gn_get_additional_fields()
        return resp + 'is_wua_partner, number_of_votes, ' + \
            'parcel_owner_number, parcel_owner_area_hec, ' + \
            'parcel_lessee_number, parcel_lessee_area_hec, '

    # (from hook)
    def _gn_get_additional_values(self):
        resp = super(ResNotificationset, self)._gn_get_additional_values()
        return resp + 'rp.is_wua_partner, rp.number_of_votes, ' + \
            'rp.parcel_owner_number, rp.parcel_owner_area_hec, ' + \
            'rp.parcel_lessee_number, rp.parcel_lessee_area_hec, '

    # (from hook)
    def _gm_get_where_clause_or_condition(self, notificationset_type):
        resp = \
            super(ResNotificationset, self)._gm_get_where_clause_or_condition(
                notificationset_type)
        if notificationset_type.include_partner_if_wua:
            if not resp:
                resp = 'rp.is_wua_partner'
            else:
                resp = resp + ' OR rp.is_wua_partner'
        return resp

    # (from hook)
    def _gn_final_process(self, notificationset):
        if notificationset.file_id:
            self.env.cr.execute(
                'UPDATE res_notification ' +
                'SET file_id = ' + str(notificationset.file_id.id) + ' ' +
                'WHERE notificationset_id = ' + str(notificationset.id))
            self.env.cr.commit()
            self.env.invalidate_all()

    # (from hook)
    def _action_notif_generation(self, notification):
        notification._create_letters()
