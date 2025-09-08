# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http, fields
from odoo.http import request
from odoo.addons.wua_maintenance.controllers.maintenance_gis_controller \
    import MaintenanceGisController
from bs4 import BeautifulSoup
from datetime import timedelta
import ast
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
                domain = []
                if field.field_domain:
                    try:
                        domain = ast.literal_eval(field.field_domain)
                    except Exception:
                        domain = []
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
                    fixed_options = current_model.search(domain)
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
                elif field.field_type == 'selection':
                    # Get the selection options from the related field
                    # selection, check if category has a model associated
                    # and get the selection options from the model
                    # other case use the maintenance.equipment
                    model = 'maintenance.equipment'
                    if (equipment.category_id.model_id):
                        model = equipment.category_id.model_id.model
                    field_data['fixed_options'] = self.\
                        _get_selection_options(model, field.field_path)
                elif field.field_type == 'many2one':
                    value = field_data['value']
                    field_data['label'] = value.name if value else ''
                    field_data['fixed_options'] = [
                        {'label': rec.name, 'value': rec.id}
                        for rec in request.env[value._name].search([])
                    ]
                    # Only send the selected id, not all the data
                    field_data['value'] = field_data['value'].id
                elif field.field_type == 'binary' and field_data['value']:
                    field_data['value'] = 1
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
        default_gis_refresh_interval = request.env['ir.values'].get_default(
            'maintenance.config.settings',
            'default_gis_inventory_refresh_interval') or \
            60
        config = {
            'default_interval': default_gis_refresh_interval * 1000,
        }
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
            # Count equipments for this category to show in the UI
            equipment_count = request.env[
                'maintenance.equipment'].search_count([
                    ('category_id', '=', category.id),
                    ('available_for_inventory', '=', True),
                ])
            # Get latest update date for this category
            latest_write = request.env['maintenance.equipment'].search([
                ('category_id', '=', category.id),
                ('available_for_inventory', '=', True),
            ], limit=1, order='write_date desc')
            latest_create = request.env['maintenance.equipment'].search([
                ('category_id', '=', category.id),
                ('available_for_inventory', '=', True),
            ], limit=1, order='create_date desc')
            latest_update = False
            if latest_write and latest_create:
                # Compare dates to get the most recent one
                latest_update = latest_write.write_date
                if latest_create.create_date > latest_write.write_date:
                    latest_update = latest_create.create_date
            elif latest_write:
                latest_update = latest_write.write_date
            elif latest_create:
                latest_update = latest_create.create_date
            categories_output[self.to_valid_variable_name(category.name)] = {
                'id': category.id,
                'name': category.name,
                'geometry_type': category.geometry_type,
                'geojson_style': category.geojson_style.replace(
                    '\n', '').strip(),
                'legend_symbology': category.legend_symbology.replace(
                    '\n', '').strip(),
                'equipment_count': equipment_count,
                'latest_update': latest_update,
                'load_by_default': category.load_geometries_by_default,
                'dynamic_fields': self._get_dynamic_fields(
                    category),
            }
        output = {
            'config': self._get_config_for_inventory_workmode(),
            'categories': categories_output,
        }
        return json.dumps(output, ensure_ascii=False)

    @http.route("/inventory_category_equipments", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_inventory_category_equipments(self, *args, **kwargs):
        jsonrequest = request.jsonrequest
        category_id = jsonrequest.get('category_id', False)
        last_update = jsonrequest.get('last_update', False)
        limit = jsonrequest.get('limit', 100)
        offset = jsonrequest.get('offset', 0)
        if not category_id:
            return json.dumps(
                {'error': 'No category_id provided'}, ensure_ascii=False)
        domain = [
            ('category_id', '=', category_id),
            ('available_for_inventory', '=', True),
        ]
        # Add date filter if last_update is provided
        if last_update:
            last_update_obj = fields.Datetime.from_string(last_update)
            # Add one second to avoid errors on boundary conditions
            last_update_obj += timedelta(seconds=1)
            last_update = fields.Datetime.to_string(last_update_obj)
            # Use OR condition to include both created and modified records
            domain = ['&'] + domain + [
                '|',
                ('write_date', '>', last_update),
                ('create_date', '>', last_update),
            ]
        # Get total count for pagination
        total_count = request.env['maintenance.equipment'].search_count(domain)
        query = request.env['maintenance.equipment']._where_calc(domain)
        tables, where_clause, where_params = query.get_sql()
        order_by = "ORDER BY GREATEST(maintenance_equipment.write_date, "\
            "maintenance_equipment.create_date) DESC"
        sql = """
            SELECT maintenance_equipment.id
            FROM {}
            WHERE {}
            {}
            LIMIT %s OFFSET %s
        """.format(tables, where_clause, order_by)
        params = where_params + [limit, offset]
        request.env.cr.execute(sql, params)
        equipment_ids = [r[0] for r in request.env.cr.fetchall()]
        equipments = request.env['maintenance.equipment'].browse(equipment_ids)
        equipments_output = []
        for equipment in equipments:
            equipments_output.append(
                self._get_equipment_formatted_value(equipment))
        output = {
            'equipments': equipments_output,
            'total_count': total_count,
            'has_more': total_count > (offset + limit),
            'category_id': category_id,
        }
        return json.dumps(output, ensure_ascii=False)

    @http.route("/inventory_init_config", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_inventory_init_config(self, *args, **kwargs):
        # Get only categories info without equipment data
        categories_output = {}
        categories = request.env['maintenance.equipment.category'].search([
            ('available_for_inventory', '=', True)],
            order='name asc')
        for category in categories:
            # Count equipments for this category
            equipment_count = request.env[
                'maintenance.equipment'].search_count([
                    ('category_id', '=', category.id),
                    ('available_for_inventory', '=', True),
                ])
            # Get latest update date for this category
            latest_write = request.env['maintenance.equipment'].search([
                ('category_id', '=', category.id),
                ('available_for_inventory', '=', True),
            ], limit=1, order='write_date desc')
            latest_create = request.env['maintenance.equipment'].search([
                ('category_id', '=', category.id),
                ('available_for_inventory', '=', True),
            ], limit=1, order='create_date desc')
            latest_update = False
            if latest_write and latest_create:
                # Compare dates to get the most recent one
                latest_update = latest_write.write_date
                if latest_create.create_date > latest_write.write_date:
                    latest_update = latest_create.create_date
            elif latest_write:
                latest_update = latest_write.write_date
            elif latest_create:
                latest_update = latest_create.create_date
            categories_output[self.to_valid_variable_name(category.name)] = {
                'id': category.id,
                'name': category.name,
                'geometry_type': category.geometry_type,
                'geojson_style': category.geojson_style.replace(
                    '\n', '').strip(),
                'legend_symbology': category.legend_symbology.replace(
                    '\n', '').strip(),
                'equipment_count': equipment_count,
                'latest_update': latest_update,
                'load_by_default': category.load_geometries_by_default,
                'dynamic_fields': self._get_dynamic_fields(category),
            }
        output = {
            'config': self._get_config_for_inventory_workmode(),
            'categories': categories_output,
        }
        return json.dumps(output, ensure_ascii=False)
