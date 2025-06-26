# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class WuaMaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    available_for_inventory = fields.Boolean(
        string='Available for inventory',
        help='If checked, this category is available for inventory on GIS '
             'viewer.',
        default=True,
    )

    dynamic_field_ids = fields.One2many(
        comodel_name='maintenance.equipment.category.dynamic.field',
        inverse_name='maintenance_category_id',
        string='Dynamic Fields',
    )


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
