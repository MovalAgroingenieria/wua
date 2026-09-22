# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    defaults = env['ir.values'].search([
        ('key', '=', 'default'),
        ('key2', '=', False),
        ('model', '=', 'wua.irrigation.configuration'),
        ('name', '=', 'import_from_pressuresensormeasurement_regaber'),
        ('user_id', '=', False),
        ('company_id', '=', False),
    ], order='id desc')
    if len(defaults) > 1:
        defaults[1:].unlink()
    return