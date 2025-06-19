# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    equipment_definitions = [
        {
            'category_ref':
                'wua_maintenance.equipment_category_processingcentre',
            'table_name': 'wua_processing_centre',
            'infrastructure_type': '01_general',
            'is_primary': False,
        },
        {
            'category_ref': 'wua_maintenance.equipment_category_powerline',
            'table_name': 'wua_power_line',
            'infrastructure_type': '01_general',
            'is_primary': False,
        },
        {
            'category_ref':
                'wua_maintenance.equipment_category_powerlinesupport',
            'table_name': 'wua_power_line_support',
            'infrastructure_type': '01_general',
            'is_primary': False,
        },
    ]

    insert_query = f"""
        INSERT INTO maintenance_equipment
        (active, equipment_assign_to, name, category_id, infrastructure_type, is_primary, is_wua)
        SELECT TRUE, 'employee', name, %s, %s, %s, TRUE
        FROM {table}
        WHERE NOT EXISTS (
            SELECT 1 FROM maintenance_equipment me
            WHERE me.name = {table}.name AND me.category_id = %s
        );
    """
    cr.execute(insert_query, (
        category_id, item['infrastructure_type'],
        item['is_primary'], category_id))

    update_query = f"""
        UPDATE {table} t
        SET equipment_id = me.id
        FROM maintenance_equipment me
        WHERE me.name = t.name
        AND me.category_id = %s
        AND t.equipment_id IS NULL;
    """
    cr.execute(update_query, (category_id,))

