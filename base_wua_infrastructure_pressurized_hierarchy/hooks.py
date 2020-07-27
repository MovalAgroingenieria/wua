# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    hydraulicsectors = env['wua.hydraulicsector'].search([])
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
        irrigationsheds = env['wua.irrigationshed'].search([
            ('hydraulicsector_id', '=', hydraulicsector.id)])
        irrigationsheds.write({
            'waterpipe_id': sector_waterpipe.id})
