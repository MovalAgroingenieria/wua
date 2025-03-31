
# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from datetime import timedelta


class MaintenancePlan(models.Model):

    _inherit = 'maintenance.plan'

    days_to_create_new_maintenance = fields.Integer(
        string='Days to create new maintenance',
        default=1,
    )

    next_creation_date = fields.Date(
        string='Next creation date',
        compute='_compute_next_creation_date',
        store=True,
    )

    @api.depends('days_to_create_new_maintenance', 'next_maintenance_date')
    def _compute_next_creation_date(self):
        for record in self:
            next_creation_date = None
            if (record.next_maintenance_date and
                    record.days_to_create_new_maintenance):
                next_creation_date = fields.Date.from_string(
                    record.next_maintenance_date) - \
                    timedelta(days=record.days_to_create_new_maintenance)
            record.next_creation_date = next_creation_date
