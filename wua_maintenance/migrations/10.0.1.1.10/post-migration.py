# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    categ_processingcentre = env.ref(
        'wua_maintenance.equipment_category_processingcentre')
    categ_processingcentre.write({
        'geometry_type': '01_point',
    })
