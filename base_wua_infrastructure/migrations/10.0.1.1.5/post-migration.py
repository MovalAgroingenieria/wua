# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        DELETE FROM ir_model_data WHERE model =
            'wua.waterconnection.subparcel.rel';
        DROP TABLE IF EXISTS wua_waterconnection_subparcel_rel ;
        """)
