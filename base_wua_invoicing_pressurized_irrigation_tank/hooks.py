# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_tank_product = env['wua.tankconsumption']._default_product_id()
    if default_tank_product:
        tankconsumptions_no_type = env['wua.tankconsumption'].search(
            [('product_id', '=', False)])
        if tankconsumptions_no_type:
            vals = {'product_id': default_tank_product, }
            tankconsumptions_no_type.write(vals)
