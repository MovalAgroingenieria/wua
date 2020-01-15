# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    product_template_action = env.ref('product.product_template_action')
    if product_template_action:
        product_template_action.domain = None
    templates_of_superproduct = env['product.template'].search(
        [('is_superproduct', '=', True)])
    if templates_of_superproduct:
        templates_of_superproduct.unlink()
