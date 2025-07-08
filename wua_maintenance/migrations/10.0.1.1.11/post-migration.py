# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    category_ref = 'wua_maintenance.equipment_category_tertiarypipe'
    table_name = 'wua_tertiarypipe'
    infrastructure_type = '01_general'
    is_primary = False

    category_id = env.ref(category_ref).id

    # Insert new equipment records from wua_tertiarypipe if not existing
    cr.execute("""
        INSERT INTO maintenance_equipment
        (active, equipment_assign_to, name, category_id, infrastructure_type,
        is_primary, is_wua)
        SELECT TRUE, 'employee', name, %s, %s, %s, TRUE
        FROM """ + table_name + """ t
        WHERE NOT EXISTS (
            SELECT 1 FROM maintenance_equipment me
            WHERE me.name = t.name AND me.category_id = %s
        );
    """, (category_id, infrastructure_type, is_primary, category_id))

    # Update equipment_id in source table if missing
    cr.execute("""
        UPDATE """ + table_name + """ t
        SET equipment_id = me.id
        FROM maintenance_equipment me
        WHERE me.name = t.name
          AND me.category_id = %s
          AND t.equipment_id IS NULL;
    """, (category_id,))

    env.cr.commit()
