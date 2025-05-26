# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    xml_ids = ['stage_0', 'stage_1', 'stage_3', 'stage_4']
    old_to_new_stage = {}
    for xml_id in xml_ids:
        try:
            old_stage = env.ref('maintenance.%s' % xml_id)
        except ValueError:
            continue
        new_stage = env['maintenance.stage'].search([
            ('name', '=', old_stage.name),
            ('id', '!=', old_stage.id),
        ], limit=1)
        if not new_stage:
            new_stage = env['maintenance.stage'].create({
                'name': old_stage.name,
                'sequence': old_stage.sequence,
                'fold': old_stage.fold,
                'done': old_stage.done,
                'active': True,
                'requests_visible_on_gis': old_stage.requests_visible_on_gis,
                'default_stage_for_viewer_creation':
                    old_stage.default_stage_for_viewer_creation,
            })
            cr.execute("""
                SELECT lang, value
                FROM ir_translation
                WHERE name = 'maintenance.stage,name'
                  AND res_id = %s
                  AND type = 'model'
            """, (old_stage.id,))
            for lang, value in cr.fetchall():
                cr.execute("""
                    INSERT INTO ir_translation (
                    name, lang, type, res_id, src, value, module, state)
                    VALUES ('maintenance.stage,name', %s, 'model',
                    %s, %s, %s, 'maintenance', 'translated')
                """, (lang, new_stage.id, old_stage.name, value))

        old_to_new_stage[old_stage.id] = new_stage.id
    if old_to_new_stage:
        request_model = env['maintenance.request']
        for old_stage_id, new_stage_id in old_to_new_stage.items():
            requests = request_model.search([('stage_id', '=', old_stage_id)])
            if requests:
                requests.write({'stage_id': new_stage_id})
    for old_stage_id in old_to_new_stage.keys():
        env['maintenance.stage'].browse(old_stage_id).write({'active': False})
