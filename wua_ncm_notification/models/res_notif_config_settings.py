# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResNotifConfigSettings(models.TransientModel):
    _inherit = 'res.notif.config.settings'

    with_letter = fields.Boolean(
        string='Create a output letter automatically',
        default=False,)

    hide_address = fields.Boolean(
        string='Hide the address of partner in envelope',
        default=False,)

    @api.multi
    def set_default_values(self):
        super(ResNotifConfigSettings, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('res.notif.config.settings',
                           'with_letter', self.with_letter)
        values.set_default('res.notif.config.settings',
                           'hide_address', self.hide_address)
