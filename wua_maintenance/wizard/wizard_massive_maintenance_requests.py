# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _, api


class WizardMassiveMaintenanceReequests(models.TransientModel):
    _name = 'wizard.massive.maintenance.requests'

    def _default_maintenance_equipment_ids(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            # Validate categories before opening the wizard
            equipments = self.env['maintenance.equipment'].browse(active_ids)
            categories = equipments.mapped('category_id')
            # Filter out empty categories
            categories = categories.filtered(lambda c: c)
            if len(categories) > 1:
                raise models.ValidationError(_(
                    "Error: You have selected equipment from different "
                    "categories. Please select equipment from the same "
                    "category."))
            return [(6, 0, active_ids)]
        return []

    def _get_default_team_id(self):
        return self.env['maintenance.team'].search(
            [('default_team', '=', True)], limit=1)

    maintenance_equipment_ids = fields.Many2many(
        string="Maintenance equipments",
        comodel_name='maintenance.equipment',
        default=lambda self: self._default_maintenance_equipment_ids(),
    )

    maintenance_subject = fields.Char(
        string='Maintenance subject',
        required=True,
    )

    request_date = fields.Date(
        string='Request date',
        default=lambda self: fields.datetime.now(),
    )

    maintenance_type = fields.Selection(
        string='Maintenance type',
        selection=[
            ('corrective', 'Corrective'),
            ('preventive', 'Preventive')],
        default='corrective',
    )

    maintenance_category_id = fields.Many2one(
        string='Maintenance category',
        comodel_name='maintenance.equipment.category',
        compute='_compute_maintenance_category_id',
        store=True,
    )

    maintenance_kind_id = fields.Many2one(
        string='Action type',
        comodel_name='maintenance.kind',

    )

    maintenance_team_id = fields.Many2one(
        string='Maintenance team',
        comodel_name='maintenance.team',
        required=True,
        default=lambda self: self._get_default_team_id(),
    )

    technician_user_id = fields.Many2one(
        string='Technician',
        comodel_name='res.users',
    )

    scheduled_date = fields.Date(
        string='Scheduled date',
    )

    duration = fields.Float(
        string='Duration',
        digits=(16, 2),
    )

    priority = fields.Selection(
        string='Priority',
        selection=[
            ('0', 'Very Low'),
            ('1', 'Low'),
            ('2', 'Normal'),
            ('3', 'High')],
        default='0',
    )

    project_id = fields.Many2one(
        string='Project',
        comodel_name='project.project',
    )

    description = fields.Html(
        string='Description',
    )

    @api.onchange('maintenance_team_id')
    def onchange_maintenance_team_id(self):
        if (self.maintenance_team_id and
                self.maintenance_team_id.partner_ids and
                len(self.maintenance_team_id.partner_ids) == 1 and
                self.maintenance_team_id.partner_ids[0].user_ids):
            self.technician_user_id = self.maintenance_team_id.\
                partner_ids[0].user_ids[0]

    @api.onchange('maintenance_category_id')
    def onchange_maintenance_category_id(self):
        result = {}
        if self.maintenance_category_id:
            result['domain'] = {
                'maintenance_kind_id': [
                    ('category_id', '=', self.maintenance_category_id.id),
                ],
            }
        else:
            result['domain'] = {'maintenance_kind_id': []}
        return result

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

    def create_requests(self):
        self.ensure_one()
        maintenance_request_ids = []
        for equipment in self.maintenance_equipment_ids:
            vals = {
                'equipment_id': equipment.id,
                'name': self.maintenance_subject,
                'description': self.description,
                'request_date': self.request_date,
                'maintenance_type': self.maintenance_type,
                'maintenance_kind_id': self.maintenance_kind_id.id,
                'maintenance_team_id': self.maintenance_team_id.id,
                'technician_user_id': self.technician_user_id.id,
                'scheduled_date': self.scheduled_date,
                'duration': self.duration,
                'priority': self.priority,
                'project_id': self.project_id.id,
            }
            maintenance_request = self.env['maintenance.request'].create(vals)
            maintenance_request.onchange_category_equipment_id_render_data()
            maintenance_request_ids.append(maintenance_request.id)
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Requests'),
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', maintenance_request_ids)],
            'context': {'create': False},
        }
        return act_window
