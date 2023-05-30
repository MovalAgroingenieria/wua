# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResFile(models.Model):
    _inherit = 'res.file'

    notificationset_ids = fields.One2many(
        string='Notification Sets',
        comodel_name='res.notificationset',
        inverse_name='file_id')

    number_of_notificationsets = fields.Integer(
        string='Number of notification sets',
        compute='_compute_number_of_notificationsets',)

    notification_ids = fields.One2many(
        string='Notifications',
        comodel_name='res.notification',
        inverse_name='file_id')

    number_of_notifications = fields.Integer(
        string='Number of notifications',
        compute='_compute_number_of_notifications',)

    @api.multi
    def _compute_number_of_notificationsets(self):
        for record in self:
            number_of_notificationsets = 0
            if record.notificationset_ids:
                number_of_notificationsets = len(record.notificationset_ids)
            record.number_of_notificationsets = number_of_notificationsets

    @api.multi
    def _compute_number_of_notifications(self):
        for record in self:
            number_of_notifications = 0
            if record.notification_ids:
                number_of_notifications = len(record.notification_ids)
            record.number_of_notifications = number_of_notifications

    @api.multi
    def action_get_notificationsets(self):
        self.ensure_one()
        current_file = self
        id_tree_view = self.env.ref(
            'wua_ncm_notification.res_notificationset_view_tree').id
        id_form_view = self.env.ref(
            'wua_ncm_notification.res_notificationset_view_form').id
        search_view = self.env.ref(
            'wua_ncm_notification.res_notificationset_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Notification Sets'),
            'res_model': 'res.notificationset',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('file_id', '=', current_file.id)],
            'context': {'from_files': True, 'default_file_id': current_file.id,},
            }
        return act_window
