# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WuaPressuresensor(models.Model):
    _inherit = 'wua.pressuresensor'

    telecontrol_associated = fields.Selection(
        selection_add=[('regaber', 'Regaber SKYplatform')],
    )

    regaber_tree_node_id = fields.Integer(
        string='Regaber TreeNode ID',
        help='ATLAS Sensor ID from GET /TreeNode in SKYplatform.',
    )