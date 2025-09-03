# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class WuaMaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    available_for_inventory = fields.Boolean(
        string='Available for inventory',
        help='If checked, this category is available for inventory on GIS '
             'viewer.',
        default=False,
    )

    load_geometries_by_default = fields.Boolean(
        string='Load geometries by default',
        help='If checked, geometries will be loaded by default when the '
             'category is selected in GIS viewer.',
        default=True,
    )

    dynamic_field_ids = fields.One2many(
        comodel_name='maintenance.equipment.category.dynamic.field',
        inverse_name='maintenance_category_id',
        string='Dynamic Fields',
    )

    def copy(self, default=None):
        self.ensure_one()
        self = self.with_context(lang=None)
        if default is None:
            default = {}
        new_category = super(WuaMaintenanceEquipmentCategory, self).copy(
            default)
        for dynamic_field in self.dynamic_field_ids:
            dynamic_field.copy({
                'maintenance_category_id': new_category.id,
                'fixed_option_ids':
                [(6, 0, dynamic_field.fixed_option_ids.ids)],
            })
        return new_category

    @api.multi
    def action_validate_dynamic_fields(self):
        self.ensure_one()
        model_name = 'maintenance.equipment'
        if self.model_id and self.model_id.model:
            model_name = self.model_id.model
        test_record = self.env[model_name].search([], limit=1)
        if not test_record:
            raise exceptions.UserError(
                "No test record found for model '%s'. Please create a record "
                "to validate dynamic fields." % model_name)
        mapping = self.env['maintenance.equipment'].\
            _get_category_table_mapping().get(self.id)
        gis_table_fields = []
        if mapping and mapping.get('gis_table'):
            gis_table = mapping['gis_table']
            try:
                self.env.cr.execute("SELECT * FROM %s LIMIT 0" % gis_table)
                gis_table_fields = [
                    desc[0] for desc in self.env.cr.description]
            except Exception:
                gis_table_fields = []
        for field in self.dynamic_field_ids:
            path_valid = False
            gis_valid = False
            if field.field_path:
                try:
                    _, _, _ = self.env['maintenance.equipment'].\
                        _resolve_field_path(test_record, field.field_path)
                    path_valid = True
                except Exception:
                    pass
            else:
                path_valid = True
            if field.gis_path:
                if gis_table_fields and field.gis_path in gis_table_fields:
                    gis_valid = True
            else:
                gis_valid = True
            field.validation_status = 'valid' if path_valid and \
                gis_valid else 'invalid'
        return True


class MaintenanceEquipmentCategoryDynamicField(models.Model):
    _name = 'maintenance.equipment.category.dynamic.field'
    _rec_name = 'name'

    name = fields.Char(
        string='Field Name',
        required=True,
        translate=True,
    )

    field_type = fields.Selection(
        [
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

    field_domain = fields.Char(
        string='Field Domain',
        default='[]',
    )

    field_path = fields.Char(
        string='Field Path',
        default='',
        help='Example: \'partner_id.name\'',
    )

    required = fields.Boolean(
        string='Required',
        default=False,
    )

    gis_path = fields.Char(
        string='GIS Path',
        default='',
    )

    maintenance_category_id = fields.Many2one(
        comodel_name='maintenance.equipment.category',
        string='Category',
    )

    fixed_option_ids = fields.Many2many(
        comodel_name='maintenance.category.dynamic.field.selection',
        relation='maintenance_category_dynamic_field_selection_rel',
        column1='dynamic_field_id',
        column2='selection_id',
        string='Selection Options',
    )

    readonly = fields.Boolean(
        string='Readonly',
        default=False,
    )

    related_category_id = fields.Many2one(
        comodel_name='maintenance.equipment.category',
        string='Related Category',
        help='On a many2one field, if it has a related category, you could '
             'create the record directly on viewer.',
    )

    validation_status = fields.Selection([
        ('unchecked', 'Unchecked'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ],
        string='Validation Status',
        default='unchecked',
    )

    def unlink(self):
        for record in self:
            if record.readonly:
                raise models.UserError(
                    "Cannot delete field '%s' because it is marked as readonly"
                    % record.name)
        return super(MaintenanceEquipmentCategoryDynamicField, self).unlink()


class MaintenanceCategoryDynamicFieldSelection(models.Model):
    _name = 'maintenance.category.dynamic.field.selection'

    name = fields.Char(
        string="Label",
        required=True,
    )

    value = fields.Char(
        string="Value",
        required=True,
    )
