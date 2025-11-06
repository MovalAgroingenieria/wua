# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Use set_default method with sudo, same pattern as in set_default_values
    env['ir.values'].sudo().set_default(
        'wua.invoicing.configuration',
        'print_consumption_section',
        True,
    )
