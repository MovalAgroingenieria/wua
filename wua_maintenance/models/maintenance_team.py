# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.team"

    category_id = fields.Many2one(
        string='Maintenance category',
        comodel_name='maintenance.equipment.category',
        store=True,
    )

    partner_ids = fields.Many2many(
        string='Partners',
        comodel_name='res.partner',
    )

    name = fields.Char(
        translate=True,
    )

    active = fields.Boolean(default=True)
