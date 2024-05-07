# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    parcels = env['wua.parcel'].search([])
    for parcel in parcels:
        parcel.write({
            'parcel_class_ids': [[
                0,
                False,
                {
                    'area_official': parcel.area_official,
                    'parcel_class': 'SAR',
                },
            ]]
        })
