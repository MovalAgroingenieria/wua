# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_product_intake = env['wua.intake']._default_product_id()
    if default_product_intake:
        intakes_no_watertype = \
            env['wua.intake'].search(
                [('product_id', '=', False)])
        if intakes_no_watertype:
            vals = {
                'product_id': default_product_intake,
                }
            intakes_no_watertype.write(vals)

    default_product_irrigationreport = \
        env['wua.irrigationreport']._default_product_id()
    if default_product_irrigationreport:
        irrigationreports_no_watertype = \
            env['wua.irrigationreport'].search(
                [('product_id', '=', False)])
        if irrigationreports_no_watertype:
            vals = {
                'product_id': default_product_irrigationreport,
                }
            irrigationreports_no_watertype.write(vals)
