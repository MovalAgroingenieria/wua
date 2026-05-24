# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    xmlid = env['ir.model.data'].search([
        ('module', '=', 'base_wua_quota_management_with_provisional_quota'),
        ('name', '=', 'ir_cron_recalculate_extra_hydric_movements'),
        ('model', '=', 'ir.cron'),
    ], limit=1)
    if not xmlid:
        return
    cron = env['ir.cron'].browse(xmlid.res_id).exists()
    if not cron:
        return
    cron.write({
        'model': 'res.partner',
        'function': 'recalculate_extra_hydric_movements',
        'args': '()',
    })
