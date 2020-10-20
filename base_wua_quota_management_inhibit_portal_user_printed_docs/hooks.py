# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    do_unlink = True
    try:
        quota_report = env.ref(
            'base_wua_quota_management.wua_partner_quota_report')
        group_wua_user = env.ref('base_wua.group_wua_user')
    except:
        do_unlink = False
    do_unlink = \
        do_unlink and quota_report and group_wua_user
    if do_unlink:
        quota_report.write({'groups_id': [(3, group_wua_user.id)]})

