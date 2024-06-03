# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    values.set_default(
        'wua.irrigation.configuration',
        'remotecontrol_rounding_reading_volume',
        '00_without_rounding',)
