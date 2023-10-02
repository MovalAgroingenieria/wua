# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def handle_equipment(category_ref, table_name,
                         infrastructure_type, is_primary):
        category_id = env.ref(category_ref).id
        env.cr.execute("""
            INSERT INTO maintenance_equipment
                (active, equipment_assign_to, name,
                 category_id, infrastructure_type, is_primary, is_wua)
            SELECT True AS active, 'employee' AS equipment_assign_to, name,
                %s AS category_id, %s AS infrastructure_type,
                %s AS is_primary, True AS is_wua
            FROM """ + table_name + """ ;
        """, (category_id, infrastructure_type, is_primary))
        env.cr.commit()
        env.cr.execute("""
            UPDATE """ + table_name + """ SET equipment_id = me1.id FROM
                   maintenance_equipment me1 WHERE me1.name = """ +
                       table_name + """.name
                   AND me1.category_id = %s;
        """, (category_id,))

    # Handle equipment
    equipment_mappings = [
        ('wua_maintenance.equipment_category_intake',
         'wua_intake', '01_general', True),
        ('wua_maintenance.equipment_category_reservoir',
         'wua_reservoir', '01_general', True),
        ('wua_maintenance.equipment_category_pumpgroup',
         'wua_pumpgroup', '01_general', True),
        ('wua_maintenance.equipment_category_photovoltaicplant',
         'wua_photovoltaicplant', '01_general', True),
        ('wua_maintenance.equipment_category_flowmeter',
         'wua_flowmeter', '01_general', False),
        ('wua_maintenance.equipment_category_pump',
         'wua_pumpunit', '01_general', False),
        ('wua_maintenance.equipment_category_waterpipe',
         'wua_waterpipe', '02_pressurized', True),
        ('wua_maintenance.equipment_category_irrigationshed',
         'wua_irrigationshed', '02_pressurized', False),
        ('wua_maintenance.equipment_category_waterconnection',
         'wua_waterconnection', '02_pressurized', False),
        ('wua_maintenance.equipment_category_watermeter',
         'wua_watermeter', '02_pressurized', False),
        ('wua_maintenance.equipment_category_pressuresensor',
         'wua_pressuresensor', '02_pressurized', False),
        ('wua_maintenance.equipment_category_irrigationditch',
         'wua_irrigationditch', '03_gravity', True),
        ('wua_maintenance.equipment_category_drainageditch',
         'wua_drainageditch', '03_gravity', True),
        ('wua_maintenance.equipment_category_flowdivider',
         'wua_flowdivider', '03_gravity', False),
        ('wua_maintenance.equipment_category_irrigationgate',
         'wua_irrigationgate', '03_gravity', False),
        ('wua_maintenance.equipment_category_airvalve',
         'wua_airvalve', '03_gravity', False),
        ('wua_maintenance.equipment_category_drainagevalve',
         'wua_drainagevalve', '03_gravity', False),
        ('wua_maintenance.equipment_category_valve',
         'wua_valve', '03_gravity', False),
        ('wua_maintenance.equipment_category_filteringstation',
         'wua_filteringstation', '03_gravity', False)
    ]

    for category_ref, table_name, \
            infrastructure_type, is_primary in equipment_mappings:
        handle_equipment(category_ref, table_name,
                         infrastructure_type, is_primary)

    sequence = env.ref('wua_maintenance.sequence_certificate_code')
    values = env['ir.values']
    values.set_default('maintenance.config.settings',
                       'sequence_maintenance_request_code_id',
                       sequence.id)
