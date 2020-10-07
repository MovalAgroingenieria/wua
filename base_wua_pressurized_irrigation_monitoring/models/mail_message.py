# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class Message(models.Model):
    _inherit = 'mail.message'

    incoming_mail_processed = fields.Boolean(
        string='Processed',
        default=False)
