# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MaintenanceKind(models.Model):
    _inherit = 'maintenance.kind'

    category_id = fields.Many2one(
        string='Maintenance category',
        comodel_name='maintenance.equipment.category',
        store=True,
    )

    dynamic_field_ids = fields.One2many(
        comodel_name='maintenance.kind.dynamic.field',
        inverse_name='maintenance_kind_id',
        string='Dynamic Fields',
    )

    procedure_description = fields.Html(
        string='Procedure description',
    )

    images_required = fields.Boolean(
        string='Images required',
        default=True,
    )

    image_before_required = fields.Boolean(
        string='Before Image Required',
        default=True,
    )

    image_after_required = fields.Boolean(
        string='After Image Required',
        default=True,
    )

    mandatory_comment = fields.Boolean(
        string='Mandatory Comment',
        default=True,
    )

    multiple_before_images = fields.Boolean(
        string='Allow Multiple Before Images',
        default=False,
    )

    multiple_after_images = fields.Boolean(
        string='Allow Multiple After Images',
        default=False,
    )

    def _resolve_field_path_preview(self, model_obj, field_path):
        # If field_path is empty, it's a custom dynamic field stored in HTML
        if not field_path:
            return True
        field_names = field_path.split('.')
        target_model = model_obj
        for field_name in field_names:
            if '[' in field_name and ']' in field_name:
                field_name = field_name.split('[')[0]
            if field_name not in target_model._fields:
                raise ValueError("Field '%s' not found in model '%s'" % (
                    field_name, target_model._name))
            field_obj = target_model._fields[field_name]
            if field_obj.type == 'many2one':
                target_model = self.env[field_obj.comodel_name]
            elif field_obj.type in ['one2many', 'many2many']:
                raise ValueError("Cannot follow field '%s' of type '%s'" % (
                    field_name, field_obj.type))
            else:
                break

    @api.multi
    def action_validate_dynamic_fields(self):
        self.ensure_one()
        self.dynamic_field_ids.write({'validation_status': 'unchecked'})
        if not self.category_id or not self.category_id.model_id:
            return True
        model = self.env[self.category_id.model_id.model]
        for field in self.dynamic_field_ids:
            try:
                # If the field has no path, custom field so it's ok
                if not field.field_path:
                    field.write({'validation_status': 'valid'})
                else:
                    self._resolve_field_path_preview(model, field.field_path)
                    field.write({'validation_status': 'valid'})
            except Exception:
                field.write({'validation_status': 'invalid'})
        return True


class MaintenanceKindDynamicField(models.Model):
    _name = 'maintenance.kind.dynamic.field'
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
        required=False,
        default='',
        help='Example: \'partner_id.name\'. Leave empty for custom fields.',
    )

    field_domain = fields.Char(
        string='Field Domain',
        default='[]',
    )

    maintenance_kind_id = fields.Many2one(
        comodel_name='maintenance.kind',
        string='Maintenance Kind',
    )

    fixed_option_ids = fields.Many2many(
        comodel_name='maintenance.kind.dynamic.field.selection',
        relation='maintenance_kind_dynamic_field_selection_rel',
        column1='dynamic_field_id',
        column2='selection_id',
        string='Selection Options',
    )

    required = fields.Boolean(
        string='Required',
        default=False,
    )

    is_request_field = fields.Boolean(
        string='Is Request Field',
        default=False,
        help='If checked, this field belongs to the request. '
             'If not checked, it belongs to the equipment.',
    )

    validation_status = fields.Selection([
        ('unchecked', 'Unchecked'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ],
        string='Validation Status',
        default='unchecked',
    )


class MaintenanceKindDynamicFieldSelection(models.Model):
    _name = 'maintenance.kind.dynamic.field.selection'

    name = fields.Char(
        string="Label",
        required=True,
    )

    value = fields.Char(
        string="Value",
        required=True,
    )
