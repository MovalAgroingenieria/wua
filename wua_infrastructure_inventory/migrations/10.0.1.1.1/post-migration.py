# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if not version:
        return
    xml_ids = [
        'equipment_category_intake_image',
        'equipment_category_reservoir_image',
        'equipment_category_pumpgroup_photo_01',
        'equipment_category_pumpgroup_photo_02',
        'equipment_category_photovoltaicplant_photo_01',
        'equipment_category_photovoltaicplant_photo_02',
        'equipment_category_flowmeter_image',
        'equipment_category_pump_photo_01',
        'equipment_category_pump_photo_02',
        'equipment_category_irrigationshed_image',
        'equipment_category_waterconnection_image',
        'equipment_category_flowdivider_image',
        'equipment_category_irrigationgate_image',
        'equipment_category_airvalve_image',
        'equipment_category_drainagevalve_image',
        'equipment_category_valve_image',
        'equipment_category_filteringstation_image',
        'equipment_category_building_photo',
        'equipment_category_processingcentre_photo_01',
        'equipment_category_processingcentre_photo_02',
        'equipment_category_powerline_image',
    ]
    for xml_id in xml_ids:
        binary_field = env.ref(
            'wua_infrastructure_inventory.' + xml_id, raise_if_not_found=False)
        if binary_field:
            binary_field.write({
                'required': False,
                'readonly': False,
            })
