# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_product = env['wua.gravconsumption']._default_product_id()
    if default_product:
        waterings_no_watertype = \
            env['wua.watering'].search(
                [('product_id', '=', False)])
        if waterings_no_watertype:
            vals = {
                'product_id': default_product,
                }
            waterings_no_watertype.write(vals)
        gravconsumptions_no_watertype = \
            env['wua.gravconsumption'].search(
                [('product_id', '=', False), '|',
                 ('state', '=', 'planned'),
                 ('state', '=', 'executed')])
        if gravconsumptions_no_watertype:
            vals = {
                'product_id': default_product,
                }
            gravconsumptions_no_watertype.write(vals)
