# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    templates = env['product.template'].search([])
    for template in templates:
        if template.categ_id.productcategory_code == 7:
            template.superproduct_id = env.ref(
               'base_wua_quota_management.superproduct_pressurized_irrigation')
        if template.categ_id.productcategory_code == 8:
            template.superproduct_id = env.ref(
               'base_wua_quota_management.superproduct_gravity_irrigation')
        if template.categ_id.productcategory_code == 11:
            template.superproduct_id = env.ref(
               'base_wua_quota_management.superproduct_irrigation_reports')


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    templates = env['product.template'].search([])
    for template in templates:
        if template.superproduct_id:
            template.with_context(uninstall=True).write(
                {'superproduct_id': None})
    superproducts = env['wua.superproduct'].search([])
    for superproduct in superproducts:
        superproduct.with_context(uninstall=True).unlink()
    param_wua_quotas_configuration = env.ref(
        'base_wua_quota_management.param_wua_quotas_configuration')
    if param_wua_quotas_configuration:
        param_wua_quotas_configuration.unlink()
    product_template_action = env.ref(
        'product.product_template_action')
    if product_template_action:
        product_template_action.domain = None
    product_normal_action_puchased = env.ref(
        'purchase.product_normal_action_puchased')
    if product_normal_action_puchased:
        product_normal_action_puchased.domain = None
