# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    hydraulicsector_id = fields.Many2one(comodel_name='wua.hydraulicsector',
                                         string='Hydraulic Sector',
                                         store=True,
                                         compute='_compute_hydraulicsector_id')

    sequence = fields.Char(readonly=True)

    @api.depends('equipment_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.equipment_id.hydraulicsector_id

    @api.onchange('maintenance_kind_id')
    def onchange_maintenance_kind_id(self):
        if self.maintenance_kind_id:
            kind_category = self.maintenance_kind_id.category_id
            if kind_category:
                if self.equipment_id and \
                        self.equipment_id.category_id != kind_category:
                    self.equipment_id = None
                self.category_id = kind_category.id
                return {
                    'domain': {
                        'equipment_id': [('category_id',
                                          '=',
                                          kind_category.id)]
                    }
                }
            else:
                self.category_id = None
                self.category_id = kind_category.id
                return {
                    'domain': {
                        'equipment_id': []
                    }
                }
        else:
            if not self.equipment_id:
                self.category_id = None
            return {
                'domain': {
                    'equipment_id': []
                }
            }

    @api.model
    def create(self, vals):
        model_ir_sequence = self.env['ir.sequence'].sudo()
        sequence_maintenance_request_code = None
        sequence_maintenance_request_code_id = \
            self.env['ir.values'].get_default(
                'maintenance.config.settings',
                'sequence_maintenance_request_code_id')
        if sequence_maintenance_request_code_id:
            sequence_maintenance_request_code = \
                model_ir_sequence.browse(sequence_maintenance_request_code_id)
        if sequence_maintenance_request_code:
            vals['sequence'] = model_ir_sequence.next_by_code(
                sequence_maintenance_request_code.code)
        new_request = super(MaintenanceRequest, self).create(vals)
        return new_request
