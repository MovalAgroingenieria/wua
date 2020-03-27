# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_fertilizer_product = \
        env['wua.fertconsumption']._default_product_id()
    if default_fertilizer_product:
        fertconsumptions_no_type = \
            env['wua.fertconsumption'].search(
                [('product_id', '=', False)])
        if fertconsumptions_no_type:
            vals = {
                'product_id': default_fertilizer_product,
                }
            fertconsumptions_no_type.write(vals)
