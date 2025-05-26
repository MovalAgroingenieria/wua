# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.ref('wua_maintenance.equipment_category_intake').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_reservoir').geometry_type = \
        '03_polygon'
    env.ref('wua_maintenance.equipment_category_pumpgroup').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_pump').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_photovoltaicplant').\
        geometry_type = '03_polygon'
    env.ref('wua_maintenance.equipment_category_flowmeter').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_waterpipe').geometry_type = \
        '02_line'
    env.ref('wua_maintenance.equipment_category_irrigationshed').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_waterconnection').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_watermeter').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_pressuresensor').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_irrigationditch').\
        geometry_type = '02_line'
    env.ref('wua_maintenance.equipment_category_drainageditch').\
        geometry_type = '02_line'
    env.ref('wua_maintenance.equipment_category_flowdivider').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_irrigationgate').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_airvalve').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_drainagevalve').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_valve').geometry_type = \
        '01_point'
    env.ref('wua_maintenance.equipment_category_filteringstation').\
        geometry_type = '01_point'
    env.ref('wua_maintenance.equipment_category_field').geometry_type = \
        '01_point'
