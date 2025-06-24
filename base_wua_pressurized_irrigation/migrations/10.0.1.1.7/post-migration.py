# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, SUPERUSER_ID


def migrate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    waterconnection_model = env['wua.waterconnection']
    waterconnection_state_model = env['wua.waterconnection.state']
    waterconnections = waterconnection_model.search([])
    waterconnection_state = waterconnection_state_model.search(
        [('default_state', '=', 'True')])
    waterconnections.write({
        'waterconnection_state_id': waterconnection_state[0].id,
    })
