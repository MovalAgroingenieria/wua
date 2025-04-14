# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    try:
        cr.execute("""
            UPDATE maintenance_equipment AS me1
            SET parent_id = me2.id
            FROM wua_waterconnection AS ww1
            INNER JOIN wua_irrigationshed AS wi1 ON ww1.irrigationshed_id =
                wi1.id
            INNER JOIN maintenance_equipment AS me2 ON wi1.equipment_id =
                me2.id
            WHERE ww1.equipment_id = me1.id
            AND wi1.equipment_id IS NOT NULL
        """)
        cr.execute("""
            UPDATE maintenance_equipment AS me1
            SET parent_id = me2.id
            FROM wua_watermeter AS ww1
            INNER JOIN wua_irrigationshed AS wi1 ON ww1.irrigationshed_id =
                wi1.id
            INNER JOIN maintenance_equipment AS me2 ON wi1.equipment_id =
                me2.id
            WHERE ww1.equipment_id = me1.id
            AND wi1.equipment_id IS NOT NULL
        """)
        # On maintenance_equipment equipments that comes from a
        # wua.pumpunit
        # the parent_id of the maintenance_equipment is the equipment_id
        # associated with the pumpgroup_id
        cr.execute("""
            UPDATE maintenance_equipment AS me1
            SET parent_id = me2.id
            FROM wua_pumpunit AS wp2
            INNER JOIN wua_pumpgroup AS wp1 ON wp2.pumpgroup_id =
                wp1.id
            INNER JOIN maintenance_equipment AS me2 ON wp1.equipment_id =
                me2.id
            WHERE wp2.equipment_id = me1.id
            AND wp1.equipment_id IS NOT NULL;
        """)
        # On maintenance_equipment equipments that comes from a
        # wua.flowdivider or a wua.irrigationgate
        # the parent_id of the maintenance_equipment is the equipment_id
        # associated with the irrigationditch_id
        cr.execute("""
            UPDATE maintenance_equipment AS me1
            SET parent_id = me2.id
            FROM wua_flowdivider AS wf1
            INNER JOIN wua_irrigationditch AS wi1 ON wf1.irrigationditch_id =
                wi1.id
            INNER JOIN maintenance_equipment AS me2 ON wi1.equipment_id =
                me2.id
            WHERE wf1.equipment_id = me1.id
            AND wi1.equipment_id IS NOT NULL;
        """)
        cr.execute("""
            UPDATE maintenance_equipment AS me1
            SET parent_id = me2.id
            FROM wua_irrigationgate AS wi2
            INNER JOIN wua_irrigationditch AS wi1 ON wi2.irrigationditch_id =
                wi1.id
            INNER JOIN maintenance_equipment AS me2 ON wi1.equipment_id =
                me2.id
            WHERE wi2.equipment_id = me1.id
            AND wi1.equipment_id IS NOT NULL;
        """)

        env = api.Environment(cr, SUPERUSER_ID, {})
        env.ref('wua_maintenance.equipment_category_irrigationgate').write({
            'parent_id': env.ref(
                'wua_maintenance.equipment_category_irrigationditch').id
        })
        env.ref('wua_maintenance.equipment_category_flowdivider').write({
            'parent_id': env.ref(
                'wua_maintenance.equipment_category_irrigationditch').id
        })
        env.ref('wua_maintenance.equipment_category_watermeter').write({
            'parent_id': env.ref(
                'wua_maintenance.equipment_category_irrigationshed').id
        })
        env.ref('wua_maintenance.equipment_category_waterconnection').write({
            'parent_id': env.ref(
                'wua_maintenance.equipment_category_irrigationshed').id
        })
        env.ref('wua_maintenance.equipment_category_pump').write({
            'parent_id': env.ref(
                'wua_maintenance.equipment_category_pumpgroup').id
        })

    except Exception as e:
        _logger.error(
            'Error updating parents for %s' % (e))
