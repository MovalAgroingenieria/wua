# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    comp_cons = fields.Boolean(
        string='Template for comparative consumptions',
        default=False)

    comp_cons_send_after_calculate = fields.Boolean(
        string='Send after calculating (comparative consumptions)',
        default=False)
