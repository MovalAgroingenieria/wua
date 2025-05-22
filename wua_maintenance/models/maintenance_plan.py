
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

    first_execution_date = fields.Date(
        string='First execution date',
        store=True,
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

    @api.depends('first_execution_date', 'period', 'equipment_id',
                 'maintenance_kind_id')
    def _compute_next_maintenance(self):
        date_now = fields.Date.context_today(self)
        today_date = fields.Date.from_string(date_now)

        for plan in self:
            period_days = plan.period
            if period_days <= 0:
                plan.next_maintenance_date = False
                continue

            period_timedelta = timedelta(days=period_days)

            if plan.first_execution_date:
                first_date = fields.Date.from_string(plan.first_execution_date)
                if first_date > today_date:
                    plan.next_maintenance_date = plan.first_execution_date
                    continue
                elif first_date < today_date:
                    plan.next_maintenance_date = fields.Date.to_string(
                        first_date + period_timedelta)
                    continue
            next_maintenance_todo = self.env['maintenance.request'].search([
                ('equipment_id', '=', plan.equipment_id.id),
                ('maintenance_type', '=', 'preventive'),
                ('maintenance_kind_id', '=', plan.maintenance_kind_id.id),
                ('stage_id.done', '!=', True),
                ('close_date', '=', False)], order="request_date asc", limit=1)
            last_maintenance_done = self.env['maintenance.request'].search([
                ('equipment_id', '=', plan.equipment_id.id),
                ('maintenance_type', '=', 'preventive'),
                ('maintenance_kind_id', '=', plan.maintenance_kind_id.id),
                ('stage_id.done', '=', True),
                ('close_date', '!=', False)], order="close_date desc", limit=1)

            if next_maintenance_todo and last_maintenance_done:
                next_date = next_maintenance_todo.request_date
                date_gap = fields.Date.from_string(
                    next_date) - fields.Date.from_string(
                        last_maintenance_done.close_date)
                if date_gap > max(timedelta(0), period_timedelta * 2) and \
                        fields.Date.from_string(next_date) > today_date:
                    if fields.Date.from_string(
                        last_maintenance_done.close_date) + \
                            period_timedelta < today_date:
                        next_date = date_now
                    else:
                        next_date = fields.Date.to_string(
                            fields.Date.from_string(
                                last_maintenance_done.close_date) +
                            period_timedelta)
            elif next_maintenance_todo:
                next_date = next_maintenance_todo.request_date
                date_gap = fields.Date.from_string(next_date) - today_date
                if date_gap > timedelta(0) and date_gap > period_timedelta * 2:
                    next_date = fields.Date.to_string(
                        today_date + period_timedelta)
            elif last_maintenance_done:
                next_date = fields.Date.from_string(
                    last_maintenance_done.close_date) + period_timedelta
                if next_date < today_date:
                    next_date = date_now
            else:
                next_date = fields.Date.to_string(
                    today_date + period_timedelta)

            plan.next_maintenance_date = next_date
