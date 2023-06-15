# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    irrigationreport_group = env.ref(
        'base_wua_irrigation_report.group_wua_irrigationreport_writer')
    new_category = env.ref('base.module_category_water_users_associations')
    irrigationreport_group.category_id = new_category
