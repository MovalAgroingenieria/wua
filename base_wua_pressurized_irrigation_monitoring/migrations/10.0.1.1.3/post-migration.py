# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    subparcel_pres = env['wua.comparative.subparcel.presconsumption'].search(
        [])
    for subparcel_pre in (subparcel_pres or []):
        subparcel_pre.irrigation_flow = \
            subparcel_pre.subparcel_id.irrigation_flow
