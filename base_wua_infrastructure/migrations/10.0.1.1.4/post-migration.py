# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID, tools


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    waterconnections = env['wua.waterconnection'].search([])

    for waterconnection in waterconnections:
        for irrigationpointwc in waterconnection.irrigationpointwc_ids:
            subparcels = irrigationpointwc.parcel_id.subparcel_ids
            for subparcel in subparcels:
                existing_record = env['wua.waterconnection.subparcel.rel'].search([
                    ('waterconnection_id', '=', waterconnection.id),
                    ('subparcel_id', '=', subparcel.id)
                ])
                if existing_record:
                    existing_record.write({
                        'waterconnection_id': waterconnection.id,
                        'subparcel_id': subparcel.id
                    })
                else:
                    env['wua.waterconnection.subparcel.rel'].create({
                        'waterconnection_id': waterconnection.id,
                        'subparcel_id': subparcel.id
                    })
