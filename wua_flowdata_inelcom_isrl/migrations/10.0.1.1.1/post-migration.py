# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    flowmeters = env['wua.flowmeter'].search([])
    for fm in flowmeters:
        fm.inelcom_flow_id = fm.inelcom_id