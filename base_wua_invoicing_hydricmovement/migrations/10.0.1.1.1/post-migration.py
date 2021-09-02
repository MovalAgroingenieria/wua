# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        UPDATE wua_hydricmovement SET invoiced_hydricmovement = FALSE WHERE
        invoiced_hydricmovement is NULL
        """)
