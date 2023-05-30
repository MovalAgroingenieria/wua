# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    values = env['ir.values'].sudo()
    # Set to "False" the "include_partner_if_wua" for standard types.
    notificationset_type_customers = \
        env.ref('ncm_notifmgmt.notificationset_type_customers')
    if notificationset_type_customers:
        notificationset_type_customers.include_partner_if_wua = False
    notificationset_type_suppliers = \
        env.ref('ncm_notifmgmt.notificationset_type_suppliers')
    if notificationset_type_suppliers:
        notificationset_type_suppliers.include_partner_if_wua = False
    notificationset_type_all = \
        env.ref('ncm_notifmgmt.notificationset_type_all')
    if notificationset_type_all:
        notificationset_type_all.include_partner_if_wua = False
    # Initialize the "default_notificationset_type_id" param (Many2one)
    default_notificationset_type_id = 0
    try:
        default_notificationset_type_id = env.ref(
            'wua_ncm_notification.notificationset_type_wua').id
    except Exception:
        default_notificationset_type_id = 0
    if default_notificationset_type_id > 0:
        values.set_default('res.notif.config.settings',
                           'default_notificationset_type_id',
                           default_notificationset_type_id)
    # Assignement of "group_ncm_manager" group to all WUA managers.
    group_ncm_manager = env.ref('ncm_notifmgmt.group_ncm_manager')
    users = env['res.users'].search([])
    for user in (users or []):
        if user.has_group('base_wua.group_wua_manager'):
            user.write({'groups_id': [(4, group_ncm_manager.id)]})
