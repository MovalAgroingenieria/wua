# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResFile(models.Model):
    _inherit = 'res.file'

    available_on_portal = fields.Boolean(
        string='Available on Portal',
        help='If checked, this file will be available'
             ' for download on the portal.',
        default=False,
        store=True,
    )
