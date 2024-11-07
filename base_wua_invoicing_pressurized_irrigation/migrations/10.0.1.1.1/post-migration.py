# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    separate_wc_invoices = env['ir.values'].get_default(
        'wua.invoicing.configuration',
        'separate_wc_invoices')
    if (separate_wc_invoices is None):
        values.set_default(
            'wua.invoicing.configuration',
            'separate_wc_invoices',
            True)
