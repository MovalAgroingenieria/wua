# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    category_model_ref_map = {
        'equipment_category_intake':
            'base_wua_infrastructure_primary.model_wua_intake',
        'equipment_category_reservoir':
            'base_wua_reservoir.model_wua_reservoir',
        'equipment_category_pumpgroup':
            'base_wua_infrastructure_pump.model_wua_pumpgroup',
        'equipment_category_photovoltaicplant':
            'base_wua_infrastructure_pump.'
            'model_wua_photovoltaicplant',
        'equipment_category_flowmeter':
            'base_wua_infrastructure_primary.model_wua_flowmeter',
        'equipment_category_pump':
            'base_wua_infrastructure_pump.model_wua_pumpunit',
        'equipment_category_waterpipe':
            'base_wua_infrastructure_pressurized_hierarchy.'
            'model_wua_waterpipe',
        'equipment_category_irrigationshed':
            'base_wua_infrastructure.model_wua_irrigationshed',
        'equipment_category_waterconnection':
            'base_wua_infrastructure.'
            'model_wua_waterconnection',
        'equipment_category_watermeter':
            'base_wua_pressurized_irrigation.model_wua_watermeter',
        'equipment_category_pressuresensor':
            'base_wua_pressurized_irrigation.model_wua_pressuresensor',
        'equipment_category_irrigationditch':
            'base_wua_infrastructure.model_wua_irrigationditch',
        'equipment_category_drainageditch':
            'base_wua_infrastructure_gravity_hierarchy.model_wua_drainageditch',
        'equipment_category_flowdivider':
            'base_wua_infrastructure.model_wua_flowdivider',
        'equipment_category_irrigationgate':
            'base_wua_infrastructure.model_wua_irrigationgate',
        'equipment_category_airvalve':
            'base_wua_infrastructure.model_wua_airvalve',
        'equipment_category_drainagevalve':
            'base_wua_infrastructure.model_wua_drainagevalve',
        'equipment_category_valve': 'base_wua_infrastructure.model_wua_valve',
        'equipment_category_filteringstation':
            'base_wua_infrastructure_primary.model_wua_filteringstation',
    }

    for category_xml_id, model_ref in category_model_ref_map.items():
        try:
            category = env.ref('wua_maintenance.%s' % category_xml_id,
                               raise_if_not_found=False)
            model = env.ref(model_ref, raise_if_not_found=False)
            if model and category.model_id != model:
                category.write({'model_id': model.id})
                _logger.info('Updated model_id for %s (%s) -> %s' % (
                    category.name, category_xml_id, model.name))
            else:
                _logger.warning(
                    'Model %s not found for %s. Skipping...' % (
                        model_ref, category_xml_id))
        except Exception as e:
            _logger.error(
                'Error updating model_id for %s: %s' % (category_xml_id, e))
