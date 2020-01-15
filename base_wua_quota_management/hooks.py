# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    print "uninstall_hook..."
    env = api.Environment(cr, SUPERUSER_ID, {})
    product_template_action = env.ref('product.product_template_action_all')
    print product_template_action
    print product_template_action.domain
