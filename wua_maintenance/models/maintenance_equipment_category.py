# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from jinja2 import Template, TemplateError
from odoo import models, fields, api, _, exceptions
from datetime import datetime
import random


class WuaMaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    name = fields.Char('Name', required=True, translate=True)

    is_wua = fields.Boolean(
        string='Part of WUA infrastructure?',
        default=False,
        readonly=True,
    )

    infrastructure_type = fields.Selection(
        [('01_general', 'General Infrastructure'),
         ('02_pressurized', 'Pressurized Irrigation'),
         ('03_gravity', 'Gravity Irrigation')],
        string='Infrastructure Type',
        readonly=True,
    )

    is_primary = fields.Boolean(
        string='Primary infrastructure?',
        default=False,
        readonly=True,
    )

    extradata_template = fields.Text(
        string='Extradata Template',
        help='Template with jinja2 variables.',
    )

    extradata_template_resolved = fields.Text(
        string='Template resolved',
        readonly=True,
        help='The template after resolve variables using random item.',
    )

    geojson_style = fields.Text(
        string='GeoJSON style for viewer data',
        help='GeoJSON style for viewer data.',
        default="""
        {
          "radius": 6,
          "fillColor": "#ff7800",
          "color": "#000",
          "weight": 1,
          "opacity": 1,
          "fillOpacity": 0.5
        }
        """,
    )

    legend_symbology = fields.Text(
        string='Legend symbology viewer data',
        help='Legend symbology for viewer data.',
        default="""
        [
            {
                "fontAwesomeSymbol": "far fa-check-circle",
                "color": "#ff7800"
            }
        ]
        """,
    )

    model_id = fields.Many2one(
        string='Model',
        comodel_name='ir.model',
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         _('Maintenance category already exists.')),
    ]

    def _get_random_equipment(self, category):
        equipment = ''
        equipment_ids = self.env['maintenance.equipment'].search(
            [('category_id', '=', category.id)], limit=1000).ids
        if len(equipment_ids) > 0:
            random_equipment_id = random.choice(equipment_ids)
            equipment = self.env['maintenance.equipment'].browse(
                random_equipment_id)
        else:
            raise exceptions.ValidationError(_('No equipment found'))
        return equipment

    @api.multi
    def action_resolve_template(self):
        self.ensure_one()
        template = equipment = message = ''
        if self.extradata_template:
            template = Template(self.extradata_template)
            equipment = self._get_random_equipment(self)
            try:
                message = template.render(
                    equipment=equipment, datetime=datetime)
            except TemplateError as err:
                raise exceptions.ValidationError(
                    _('Error resolving template: {}'.format(err.message)))
        if message:
            self.extradata_template_resolved = message

    @api.multi
    def unlink(self):
        for record in self:
            if record and record.is_wua:
                raise exceptions.ValidationError(_(
                    'Cannot delete a WUA infrastructure category.'))
        res = super(WuaMaintenanceEquipmentCategory, self).unlink()
        return res
