# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResLetter(models.Model):
    _inherit = 'res.letter'

    notification_id = fields.Many2one(
        string='Notification',
        comodel_name='res.notification',
        ondelete='cascade',)
