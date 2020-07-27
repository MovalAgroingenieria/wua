# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    hydraulicsectors = env['wua.hydraulicsector'].search([])
    if hydraulicsectors:
        waterpipes = []
        for hydraulicsector in hydraulicsectors:
            waterpipes.append(
                {'name': hydraulicsector.name,
                 'waterpipe_code': hydraulicsector.hydraulicsector_code,
                 'hydraulicsector_id': hydraulicsector.id})
        for waterpipe in waterpipes:
            env['wua.waterpipe'].create(waterpipe)
        for hydraulicsector in hydraulicsectors:
            sector_waterpipe = env['wua.waterpipe'].search([
                ('hydraulicsector_id', '=', hydraulicsector.id)])
            if sector_waterpipe:
                sector_waterpipe = sector_waterpipe[0]
                irrigationsheds = env['wua.irrigationshed'].search([
                    ('hydraulicsector_id', '=', hydraulicsector.id)])
                if irrigationsheds:
                    irrigationsheds.write({
                        'waterpipe_id': sector_waterpipe.id})


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        DELETE from ir_values WHERE name = 'max_levels_pressurized_irrigation'
        """)
