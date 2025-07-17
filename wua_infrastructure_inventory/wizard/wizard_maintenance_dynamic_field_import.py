# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WizardMaintenanceDynamicFieldImport(models.TransientModel):
    _name = 'wizard.maintenance.dynamic.field.import'
    _description = 'Import Dynamic Fields from Model'

    category_id = fields.Many2one(
        string='Maintenance Category',
        comodel_name='maintenance.equipment.category',
        required=True,
    )

    field_ids = fields.One2many(
        string='Fields to Import',
        comodel_name='wizard.maintenance.dynamic.field.import.line',
        inverse_name='wizard_id',
    )

    def _get_translated_field_string(self, model_name, field_name):
        original_label = self.sudo().env['wua.parcel'].\
            get_value_from_translation(
            'base_wua', getattr(self.__class__, field_name).
            string)
        return original_label

    @api.multi
    def action_fetch_fields(self):
        self.ensure_one()
        category = self.category_id
        model_name = category.model_id.model if category.model_id else \
            'maintenance.equipment'
        existing_paths = set(category.dynamic_field_ids.mapped('field_path'))
        excluded_names = {
            'create_date', 'write_date', 'create_uid', 'write_uid'}
        model = self.env[model_name]
        field_lines = []
        for field_name, field in model._fields.items():
            if (
                field_name in existing_paths or
                field_name in excluded_names or
                field_name.startswith('x_') or
                getattr(field, 'compute', False) or
                getattr(field, 'readonly', False) or
                field.type in ('many2many', 'one2many')
            ):
                continue
            translated_label = self.sudo().env['wua.parcel'].\
                get_value_from_translation(
                field._module, field.string)
            field_lines.append((0, 0, {
                'name': translated_label,
                'field_path': field_name,
                'field_type': self._map_field_type(field),
            }))
        self.field_ids = [(5, 0, 0)] + field_lines
        return {
            'type': 'ir.actions.do_nothing',
        }

    def _map_field_type(self, field):
        if field.type == 'char':
            return 'text'
        if field.type in ('float', 'integer'):
            return 'number'
        if field.type == 'boolean':
            return 'checkbox'
        if field.type in ('date', 'datetime'):
            return 'date'
        if field.type == 'binary':
            return 'binary'
        if field.type == 'selection':
            return 'selection'
        if field.type == 'many2one':
            return 'many2one'
        return 'text'

    @api.multi
    def action_import_selected(self):
        for line in self.field_ids.filtered('to_import'):
            self.env['maintenance.equipment.category.dynamic.field'].create({
                'name': line.name,
                'field_path': line.field_path,
                'field_type': line.field_type,
                'maintenance_category_id': self.category_id.id,
            })


class WizardMaintenanceDynamicFieldImportLine(models.TransientModel):
    _name = 'wizard.maintenance.dynamic.field.import.line'
    _description = 'Field Line for Dynamic Field Import'

    wizard_id = fields.Many2one(
        comodel_name='wizard.maintenance.dynamic.field.import',
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Field Name',
        required=True,
    )

    field_path = fields.Char(
        string='Field Path',
        required=True,
    )

    field_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('selection', 'Selection'),
        ('date', 'Date'),
        ('fixed', 'Fixed'),
        ('checkbox', 'Checkbox'),
        ('binary', 'Binary'),
        ('many2one', 'Many2one'),
        ],
        string='Field Type',
        required=True,
    )

    to_import = fields.Boolean(
        string='Import?',
        default=True,
    )
