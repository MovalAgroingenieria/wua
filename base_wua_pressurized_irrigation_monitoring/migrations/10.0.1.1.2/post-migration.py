# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    subparcels = env['wua.parcel.subparcel'].search([])
    subparcel_pres = env['wua.comparative.subparcel.presconsumption'].search(
        [])
    soiltype_loamy = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_01')
    soiltype_clayey = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_02')
    soiltype_silty = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_03')
    soiltype_sandy = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_04')
    soiltype_loamclayey = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_05')
    soiltype_loamsilty = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_06')
    soiltype_loamsandy = env.ref(
        'base_wua_pressurized_irrigation_monitoring.soiltype_07')
    soiltypes = {
        'loamy': soiltype_loamy,
        'clayey': soiltype_clayey,
        'silty': soiltype_silty,
        'sandy': soiltype_sandy,
        'loam_clayey': soiltype_loamclayey,
        'loam_silty': soiltype_loamsilty,
        'loam_sandy': soiltype_loamsandy,
    }
    for subparcel in (subparcels or []):
        if not subparcel.soil_type:
            continue
        subparcel.soiltype_id = soiltypes.get(subparcel.soil_type)
    for subparcel_pre in (subparcel_pres or []):
        if not subparcel_pre.soil_type:
            continue
        subparcel_pre.soiltype_id = soiltypes.get(subparcel_pre.soil_type)
