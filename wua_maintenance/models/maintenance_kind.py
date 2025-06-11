# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo import models, fields, api, _

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

    @api.model
    def update_dynamic_fields(self, record, values):
        for field in self.dynamic_field_ids:
            path = field.field_path
            value = values.get(path)
            if value is not None:
                try:
                    field_names = path.split('.')
                    target = record
                    for field_name in field_names[:-1]:
                        target = getattr(target, field_name, None)
                        if not target:
                            _logger.warning(_('Invalid field path: %s'), path)
                            break
                    if target:
                        target.write({field_names[-1]: value})
                        _logger.info(
                            _('Updated field %s with value %s'), path, value)
                except Exception as e:
                    _logger.error(_('Error updating field %s: %s'), path, e)


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
        required=True,
        help='Example: \'partner_id.name\'',
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
