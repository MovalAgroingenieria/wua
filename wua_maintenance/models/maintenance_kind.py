# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class MaintenanceKind(models.Model):
    _inherit = 'maintenance.kind'

    category_id = fields.Many2one(comodel_name='maintenance.'
                                               'equipment.category',
                                  string='Maintenance category',
                                  store=True)
