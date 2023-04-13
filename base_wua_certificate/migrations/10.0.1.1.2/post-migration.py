# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    certificates_parcel = env['wua.certificate.parcel'].search([])
    for cp in certificates_parcel:
        cp.area_gis = cp.parcel_id.area_gis
