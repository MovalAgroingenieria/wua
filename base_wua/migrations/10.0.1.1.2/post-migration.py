# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    polling_system_type = env['ir.values'].get_default('wua.configuration',
                                                       'polling_system_type')
    if (polling_system_type == 2 or polling_system_type == 3):
        partners = env['res.partner'].search([])
        recalculate = True
        if (polling_system_type == 3):
            polling_system_intervals = env['ir.values'].get_default(
                'wua.configuration', 'polling_system_intervals')
            if (polling_system_intervals.find('*') < 0):
                recalculate = False
        if (recalculate):
            partners._compute_number_of_votes()
