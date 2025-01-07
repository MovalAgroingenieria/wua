# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, exceptions, _, api
import logging

_logger = logging.getLogger(__name__)


class WuaRemotecontrol(models.Model):
    _name = 'wua.remotecontrol'
    _description = 'Remote Control for API and Credentials'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Name',
        required=True,
    )

    description = fields.Char(
        string='Description',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    readonly = fields.Boolean(
        string='Readonly',
        default=False,
    )

    notes = fields.Html(
        string='Notes',
    )

    def unlink(self):
        for record in self:
            if record.readonly:
                raise exceptions.UserError(_(
                    'You cannot delete a readonly record.'))
        return super(WuaRemotecontrol, self).unlink()

    @api.model
    def create(self, vals):
        if self.search_count([]) > 0:
            raise exceptions.UserError(_(
                'You can only have one remote control record.'))
        return super(WuaRemotecontrol, self).create(vals)
