# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request
from odoo.addons.wua_maintenance.controllers.maintenance_gis_controller \
    import MaintenanceGisController
from bs4 import BeautifulSoup
import re
import unicodedata
import json


class InventoryGisController(http.Controller):

    def _get_geojson_from_equipment_id(self, equipment):
        return MaintenanceGisController()._get_geojson_from_equipment_id(
            equipment)

    def _get_selection_options(self, model, field_path):
        return MaintenanceGisController()._get_selection_options(
            model, field_path)

    def _get_field_value(self, equipment, field_path, gis_path, name):
        if (not field_path and not gis_path and equipment):
            value = ''
            soup = BeautifulSoup(equipment.inventory_extra_data, 'html.parser')
            span_tag = soup.find('span', attrs={'name-value': name})
            if span_tag:
                value = span_tag.get_text(strip=True)
            return value
        return MaintenanceGisController()._get_field_value(
            equipment, field_path)

    def _get_dynamic_fields(self, category):
        dynamic_fields = []
        model_name = 'maintenance.equipment'
        if (category.model_id):
            model_name = category.model_id.model
        for field in category.dynamic_field_ids:
            field_data = {
                'name': field.name,
                'field_id': field.id,
                'field_type': field.field_type,
                'field_path': field.field_path,
                'gis_path': field.gis_path,
                'required': field.required,
                'related_category_id': field.related_category_id.id,
                'related_category_name': field.related_category_id.name,
            }
            if field.field_type == 'fixed':
                field_data['fixed_options'] = [
                    {'label': option.name, 'value': option.value}
                    for option in field.fixed_option_ids
                ]
            if field.field_type == 'selection':
                model = 'maintenance.equipment'
                if (category.model_id):
                    model = category.model_id.model
                # Get the selection options from the related field selection
                field_data['fixed_options'] = self._get_selection_options(
                    model, field.field_path)
            # We dont have a object to get the field value from, so we need to
            # get the model from the field path
            # and get the field from there
            if field.field_type == 'many2one':
                current_model = request.env[model_name]
                path_parts = field.field_path.split('.')
                for part in path_parts:
                    field_obj = current_model._fields.get(part)
                    if not field_obj:
                        current_model = None
                        break
                    if field_obj.type in ('many2one'):
                        current_model = request.env[field_obj.comodel_name]
                    else:
                        current_model = None
                        break
                if current_model is not None:
                    fixed_options = current_model.search([])
                    field_data['fixed_options'] = [
                        {'label': rec['name'], 'value': rec['id']} for rec in
                        fixed_options
                    ]
                else:
                    field_data['fixed_options'] = []
            dynamic_fields.append(field_data)
        return dynamic_fields

    def to_valid_variable_name(self, s):
        if isinstance(s, str):
            s = s.decode('utf-8')
        s = unicodedata.normalize('NFD', s)
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        s = re.sub(ur'[^a-zA-Z0-9_ ]', u'', s)
        s = re.sub(ur'\s+', u'_', s)
        if re.match(ur'^[0-9]', s):
            s = u'_' + s
        return s.encode('utf-8')

    def _get_equipment_formatted_value(self, equipment):
        dynamic_fields = []
        if equipment.category_id:
            for field in equipment.category_id.dynamic_field_ids:
                field_data = {
                    'name': field.name,
                    'field_id': field.id,
                    'field_type': field.field_type,
                    'field_path': field.field_path or '',
                    'gis_path': field.gis_path or '',
                    'required': field.required,
                    'related_category_id': field.related_category_id.id,
                    'related_category_name':
                    field.related_category_id.name,
                    'value': self._get_field_value(
                        equipment, field.field_path, field.gis_path,
                        field.name),
                }
                if field.field_type == 'fixed':
                    field_data['fixed_options'] = [
                        {'label': option.name, 'value': option.value}
                        for option in field.fixed_option_ids
                    ]
                if field.field_type == 'selection':
                    # Get the selection options from the related field
                    # selection, check if category has a model associated
                    # and get the selection options from the model
                    # other case use the maintenance.equipment
                    model = 'maintenance.equipment'
                    if (equipment.category_id.model_id):
                        model = equipment.category_id.model_id.model
                    field_data['fixed_options'] = self.\
                        _get_selection_options(model, field.field_path)
                if field.field_type == 'many2one':
                    value = field_data['value']
                    field_data['label'] = value.name if value else ''
                    field_data['fixed_options'] = [
                        {'label': rec.name, 'value': rec.id}
                        for rec in request.env[value._name].search([])
                    ]
                    # Only send the selected id, not all the data
                    field_data['value'] = field_data['value'].id
                dynamic_fields.append(field_data)
        return {
            'id': equipment.id,
            'name': equipment.name,
            'category': equipment.category_id.name,
            'geometry_type': equipment.category_id.geometry_type,
            'geom': self._get_geojson_from_equipment_id(equipment),
            'write_date': equipment.write_date,
            'dynamic_fields': dynamic_fields,
        }

    def _get_config_for_inventory_workmode(self):
        # Only use the equipments that have categories that can be inventoried
        equipments = request.env['maintenance.equipment'].search([
            ('category_id.available_for_inventory', '=', True),
            ('category_id.load_geometries_by_default', '=', True),
            ('available_for_inventory', '=', True),
        ])
        default_gis_refresh_interval = request.env['ir.values'].get_default(
            'maintenance.config.settings',
            'default_gis_inventory_refresh_interval') or \
            60
        config = {
            'equipments': [],
            'default_interval': default_gis_refresh_interval * 1000,
        }
        for equipment in equipments:
            config['equipments'].append(self._get_equipment_formatted_value(
                equipment))
        return config

    @http.route("/inventory_equipments", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_inventory_equipments_data(self, *args, **kwargs):
        equipments_output = []
        # Get the equipment_ids from the request data and then search for them
        jsonrequest = request.jsonrequest
        equipment_ids = jsonrequest.get('equipment_ids', [])
        equipments = request.env['maintenance.equipment'].browse(equipment_ids)
        for equipment in equipments:
            equipments_output.append(
                self._get_equipment_formatted_value(equipment))
        output = {
            'equipments': equipments_output,
        }
        return json.dumps(output, ensure_ascii=False)

    @http.route("/inventory_categories", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_inventory_categories_data(self, *args, **kwargs):
        categories_output = {}
        categories = request.env['maintenance.equipment.category'].search([
            ('available_for_inventory', '=', True)],
            order='name asc')
        for category in categories:
            categories_output[self.to_valid_variable_name(category.name)] = {
                'id': category.id,
                'name': category.name,
                'geometry_type': category.geometry_type,
                'geojson_style': category.geojson_style.replace(
                    '\n', '').strip(),
                'legend_symbology': category.legend_symbology.replace(
                    '\n', '').strip(),
                'dynamic_fields': self._get_dynamic_fields(
                    category),
            }
        output = {
            'categories': categories_output,
        }
        return json.dumps(output, ensure_ascii=False)

    @http.route("/inventory_init_config", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_inventory_init_config(self, *args, **kwargs):
        categories_output = {}
        categories = request.env['maintenance.equipment.category'].search([
            ('available_for_inventory', '=', True)],
            order='name asc')
        for category in categories:
            categories_output[self.to_valid_variable_name(category.name)] = {
                'id': category.id,
                'name': category.name,
                'geometry_type': category.geometry_type,
                'geojson_style': category.geojson_style.replace(
                    '\n', '').strip(),
                'legend_symbology': category.legend_symbology.replace(
                    '\n', '').strip(),
                'dynamic_fields': self._get_dynamic_fields(
                    category),
            }
        output = {
            'config': self._get_config_for_inventory_workmode(),
            'categories': categories_output,
        }
        return json.dumps(output, ensure_ascii=False)
