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
        ondelete='restrict',)

    create_letter = fields.Boolean(
        string='Create a output letter automatically',
        default=_default_create_letter,)

    def _get_conditions_for_new_notifications(self):
        self.ensure_one()
        resp = super(ResNotificationset,
                     self)._get_conditions_for_new_notifications()
        if (self.notificationset_type_id and
           self.notificationset_type_id.include_partner_if_wua):
            resp.append(('is_wua_partner', '=', True))
        return resp
