# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from jinja2 import Template, TemplateError, Markup
from odoo import models, fields, api, _, exceptions
from datetime import datetime
import json
import random


class WuaMaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
    )

    is_wua = fields.Boolean(
        string='Part of WUA infrastructure?',
        default=False,
        readonly=True,
        copy=False,
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
        copy=False,
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

    geojson_style_preview = fields.Html(
        string="Style Preview",
        compute="_compute_geojson_style_preview",
        sanitize=False,
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
        copy=False,
    )

    parent_id = fields.Many2one(
        string='Parent Category',
        comodel_name='maintenance.equipment.category',
        ondelete='restrict',
    )

    geometry_type = fields.Selection(
        [('01_point', 'Point'),
         ('02_line', 'Line'),
         ('03_polygon', 'Polygon')],
        string='Geometry Type',
        default='01_point',
        required=True,
    )

    active = fields.Boolean(default=True)

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

    def _generate_random_color(self):
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def _generate_random_style(self):
        self.ensure_one()
        try:
            style = json.loads(self.geojson_style or '{}')
        except Exception:
            style = {}
        new_fill_color = self._generate_random_color()
        new_border_color = self._generate_random_color()
        style['fillColor'] = new_fill_color
        style['color'] = new_border_color
        legend_symbology = [
            {
                "fontAwesomeSymbol": "far fa-check-circle",
                "color": new_fill_color,
            },
        ]
        return json.dumps(style, indent=2), json.dumps(
            legend_symbology, indent=2)

    @api.depends('geojson_style')
    def _compute_geojson_style_preview(self):
        for record in self:
            try:
                style = json.loads(record.geojson_style or '{}')
                fill = style.get('fillColor', '#ccc')
                stroke = style.get('color', '#000')
            except Exception:
                fill = '#ccc'
                stroke = '#000'
            svg = '''
            <svg width="60" height="60" xmlns="http://www.w3.org/2000/svg">
            <circle cx="30" cy="30" r="20"
                    fill="{fill}" stroke="{stroke}" stroke-width="3"/>
            </svg>
            '''.format(fill=fill, stroke=stroke)
            record.geojson_style_preview = Markup(svg)

    def copy(self, default=None):
        self.ensure_one()
        self = self.with_context(lang=None)
        if default is None:
            default = {}
        base_name = self.name
        names = self.search([]).mapped('name')
        suffix = 1
        copy_name = _("%s (copy)") % base_name
        while copy_name in names:
            suffix += 1
            copy_name = _("%s (copy %d)") % (base_name, suffix)
        default['name'] = copy_name
        return super(WuaMaintenanceEquipmentCategory, self).copy(default)

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
    def action_randomize_style(self):
        self.ensure_one()
        geojson_style, legend_symbology = self._generate_random_style()
        self.geojson_style = geojson_style
        self.legend_symbology = legend_symbology

    @api.multi
    def unlink(self):
        for record in self:
            if record and record.is_wua:
                raise exceptions.ValidationError(_(
                    'Cannot delete a WUA infrastructure category.'))
        res = super(WuaMaintenanceEquipmentCategory, self).unlink()
        return res
