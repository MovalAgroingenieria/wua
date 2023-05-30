# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResNotification(models.Model):
    _inherit = 'res.notification'

    is_wua_partner = fields.Boolean(
        string='Is a WUA partner',
        store=True,
        index=True,
        compute='_compute_is_wua_partner',)

    file_id = fields.Many2one(
        string='Associated File',
        comodel_name='res.file',
        store=True,
        compute='_compute_file_id',
        index=True,
        ondelete='restrict',)

    letter_ids = fields.One2many(
        string='Associated Letters',
        comodel_name='res.letter',
        inverse_name='notification_id')

    letter_id = fields.Many2one(
        string='Associated Letter',
        comodel_name='res.letter',
        compute='_compute_letter_id',)

    @api.depends('partner_id')
    def _compute_is_wua_partner(self):
        for record in self:
            is_wua_partner = False
            if record.partner_id and record.partner_id.is_wua_partner:
                is_wua_partner = True
            record.is_wua_partner = is_wua_partner

    @api.depends('notificationset_id', 'notificationset_id.file_id')
    def _compute_file_id(self):
        for record in self:
            file_id = None
            if record.notificationset_id and record.notificationset_id.file_id:
                file_id = record.notificationset_id.file_id
            record.file_id = file_id

    @api.multi
    def _compute_letter_id(self):
        for record in self:
            letter_id = None
            if record.letter_ids and len(record.letter_ids) == 1:
                letter_id = record.letter_ids[0]
            record.letter_id = letter_id

    @api.multi
    def write(self, vals):
        super(ResNotification, self).write(vals)
        if ('state' in vals and ((vals['state'] == '01_draft') or
                                 (vals['state'] == '02_generated') or
                                 (vals['state'] == '03_sent'))):
            if vals['state'] == '01_draft':
                self._delete_letters()
            if vals['state'] == '02_generated':
                self._create_letters()
            if vals['state'] == '03_sent':
                self._set_state_of_letters(state='rec')
        return True

    @api.multi
    def _create_letters(self):
        model_res_letter = self.env['res.letter']
        for record in self:
            if record.notificationset_id.create_letter:
                values = {
                    'name': record.issue,
                    'move': 'out',
                    'state': 'draft',
                    'recipient_partner_id': record.partner_id.id,
                    'sender_partner_id': record.partner_id.company_id.id,
                    'notification_id': record.id,
                    }
                if record.file_id:
                    values.update({'file_id': record.file_id.id})
                model_res_letter.create(values)

    @api.multi
    def _delete_letters(self):
        for record in self:
            if record.letter_ids:
                record.letter_ids.unlink()

    @api.multi
    def _set_state_of_letters(self, state='rec'):
        for record in self:
            if record.letter_ids:
                record.letter_ids.state = state
