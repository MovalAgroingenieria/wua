# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if not version:
        return
    xml_ids = [
        'equipment_category_waterpipe_waterpipe_id',
    ]
    for xml_id in xml_ids:
        field_record = env.ref(
            'wua_infrastructure_inventory.' + xml_id, raise_if_not_found=False)
        if field_record:
            field_record.write({
                'required': False,
            })
