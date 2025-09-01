# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, _, api


class WizardMassiveMaintenancePlans(models.TransientModel):
    _name = 'wizard.massive.maintenance.plans'
    _description = 'Wizard to create massive maintenance plans'

    def _default_maintenance_equipment_ids(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            equipments = self.env['maintenance.equipment'].browse(active_ids)
            categories = equipments.mapped('category_id').filtered(lambda c: c)
            if len(categories) > 1:
                raise models.ValidationError(_(
                    "Error: You have selected equipment from different "
                    "categories. Please select equipment from the same "
                    "category."))
            return [(6, 0, active_ids)]
        return []

    maintenance_equipment_ids = fields.Many2many(
        string="Maintenance equipments",
        comodel_name='maintenance.equipment',
        default=lambda self: self._default_maintenance_equipment_ids(),
    )

    maintenance_category_id = fields.Many2one(
        string='Maintenance category',
        comodel_name='maintenance.equipment.category',
        compute='_compute_maintenance_category_id',
        store=True,
        readonly=True,
    )

    maintenance_kind_id = fields.Many2one(
        string='Action type',
        comodel_name='maintenance.kind',
        required=True,
    )

    period = fields.Integer(
        string='Period (days)',
        required=True,
    )

    first_execution_date = fields.Date(
        string='First execution date',
        required=True,
    )

    days_to_create_new_maintenance = fields.Integer(
        string='Days to create new maintenance',
        default=1,
    )

    duration = fields.Float(
        string='Duration',
        digits=(16, 2),
    )

    @api.onchange('maintenance_equipment_ids')
    @api.depends('maintenance_equipment_ids')
    def _compute_maintenance_category_id(self):
        for record in self:
            maintenance_category_id = None
            if record.maintenance_equipment_ids:
                categories = record.maintenance_equipment_ids.mapped(
                    'category_id')
                if categories:
                    maintenance_category_id = categories[0]
            record.maintenance_category_id = maintenance_category_id

    def create_plans(self):
        self.ensure_one()
        plan_ids = []
        for equipment in self.maintenance_equipment_ids:
            vals = {
                'equipment_id': equipment.id,
                'maintenance_kind_id': self.maintenance_kind_id.id,
                'period': self.period,
                'first_execution_date': self.first_execution_date,
                'days_to_create_new_maintenance':
                    self.days_to_create_new_maintenance,
                'active': True,
                'duration': self.duration,
            }
            plan = self.env['maintenance.plan'].create(vals)
            plan_ids.append(plan.id)

        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Plans'),
            'res_model': 'maintenance.plan',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', plan_ids)],
            'context': {'create': False},
        }
        return act_window
