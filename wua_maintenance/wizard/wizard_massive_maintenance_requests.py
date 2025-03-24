# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _, api


class WizardMassiveMaintenanceReequests(models.TransientModel):
    _name = 'wizard.massive.maintenance.requests'

    def _default_maintenance_equipment_ids(self):
        active_ids = self.env.context.get('active_ids')
        return [(6, 0, active_ids)] if active_ids else []

    maintenance_equipment_ids = fields.Many2many(
        string="Maintenance equipments",
        comodel_name='maintenance.equipment',
        default=_default_maintenance_equipment_ids,
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

    maintenance_kind_id = fields.Many2one(
        string='Action type',
        comodel_name='maintenance.kind',
    )

    maintenance_team_id = fields.Many2one(
        string='Maintenance team',
        comodel_name='maintenance.team',
        required=True,
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

    description = fields.Text(
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
