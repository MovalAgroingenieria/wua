# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        UPDATE wua_parcel_class SET parcel_class = 'RH' WHERE
            parcel_class = 'SAR';
        """)
    env.cr.commit()
    env.invalidate_all()
    classes = env['wua.parcel.class'].search([])
    classes._compute_name()
