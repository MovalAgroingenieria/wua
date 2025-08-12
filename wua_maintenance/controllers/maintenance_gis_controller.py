# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import http, _
from odoo.http import request
import json


class MaintenanceGisController(http.Controller):

    def _get_geojson_from_equipment_id(self, equipment):
        env = request.env
        category_mapping = env['maintenance.equipment'].\
            _get_category_table_mapping()
        geojson_geom = None
        category_id = equipment.category_id.id
        # If the category is not in the mapping, try to find the parent
        # category
        while category_id not in category_mapping and equipment.parent_id:
            equipment = equipment.parent_id
            category_id = equipment.category_id.id
        if category_id in category_mapping:
            mapping = category_mapping[category_id]
            base_table = mapping['base_table']
            base_field = mapping['base_field']
            gis_table = mapping['gis_table']
            gis_field = mapping['gis_field']
            intermediate_table = mapping['intermediate_table']
            intermediate_field = mapping['intermediate_field']
            intermediate_gis_field = mapping['intermediate_gis_field']
            sql_query = """
                SELECT ST_AsGeoJSON(gis.geom)
                FROM maintenance_equipment me
                INNER JOIN %(base_table)s bt ON me.id = bt.equipment_id
            """ % {
                'base_table': base_table,
            }
            if (intermediate_table and intermediate_field and
                    intermediate_gis_field):
                sql_query += """
                    INNER JOIN %(intermediate_table)s it ON bt.%(base_field)s =
                        it.%(intermediate_field)s
                    INNER JOIN %(gis_table)s gis ON
                        it.%(intermediate_gis_field)s =
                        gis.%(gis_field)s
                """ % {
                    'intermediate_table': intermediate_table,
                    'base_field': base_field,
                    'intermediate_field': intermediate_field,
                    'gis_table': gis_table,
                    'intermediate_gis_field': intermediate_gis_field,
                    'gis_field': gis_field,
                }
            else:
                sql_query += """
                    INNER JOIN %(gis_table)s gis ON bt.%(base_field)s =
                    gis.%(gis_field)s
                """ % {
                    'gis_table': gis_table,
                    'base_field': base_field,
                    'gis_field': gis_field,
                }
            sql_query += ' WHERE me.id = %s' % equipment.id
            env.cr.execute(sql_query)
            result = env.cr.fetchone()
            geojson_geom = result[0] if result else None
        if not geojson_geom:
            geojson_geom = equipment.geojson_geom
        return geojson_geom

    def _get_selection_options(self, model, field_path):
        field_names = field_path.split('.')
        target = request.env[model]
        for i, field_name in enumerate(field_names):
            if i == len(field_names) - 1:
                if field_name in target._fields and \
                        target._fields[field_name].type == 'selection':
                    return [
                        {'label': target._fields[field_name].convert_to_export(
                            val, target), 'value': val}
                        for val, _ in target._fields[field_name].selection
                    ]
            else:
                if field_name in target._fields and target._fields[
                        field_name].type == 'many2one':
                    target = request.env[
                        target._fields[field_name].comodel_name]
                else:
                    return []
        return []

    def _get_config_for_maintenance_workmode(self, maintenances):
        # Only use the equipments that have maintenance requests
        # equipments = request.env['maintenance.equipment'].search()
        equipments = maintenances.mapped('equipment_id')
        maintenance_stages = request.env['maintenance.stage'].search([(
            'requests_visible_on_gis', '=', True)])
        default_maintenance_for_creation = False
        default_maintenance_for_creation_objects = request.env[
            'maintenance.stage'].search(
                [('default_stage_for_viewer_creation', '=', True)], limit=1)
        if (default_maintenance_for_creation_objects and len(
                default_maintenance_for_creation_objects) > 0):
            default_maintenance_for_creation = \
                default_maintenance_for_creation_objects[0].id
        user_lang = request.env.user.lang
        maintenance = request.env['maintenance.request'].with_context(
            lang=user_lang)
        priority_labels = {
            value: maintenance._fields['priority'].convert_to_export(
                value, maintenance)
            for value, _ in maintenance._fields['priority'].selection
        }
        maintenance_teams = request.env['maintenance.team'].search([]).mapped(
            lambda team: team.name)
        default_gis_refresh_interval = request.env['ir.values'].get_default(
            'maintenance.config.settings', 'default_gis_refresh_interval') or \
            10
        return {
            'equipments': equipments.mapped(
                lambda equipment: {
                    'id': equipment.id,
                    'name': equipment.name,
                    'category': equipment.category_id.name,
                    'geometry_type': equipment.category_id.geometry_type,
                    'geom': self._get_geojson_from_equipment_id(equipment),
                    'image': equipment.image,
                    'attachments': request.env['ir.attachment'].search([
                        ('res_model', '=', 'maintenance.equipment'),
                        ('res_id', '=', equipment.id),
                    ]).mapped(
                        lambda attachment: {
                            'name': attachment.name,
                            'datas': attachment.datas,
                            'mimetype': attachment.mimetype,
                        }),
                    'maintenance_ids': equipment.maintenance_ids.filtered(
                        lambda maintenance: maintenance.stage_id.
                        requests_visible_on_gis).mapped(
                        lambda maintenance: maintenance.id),
                    'maintenances_without_field_data': equipment.
                    maintenance_ids.filtered(
                            lambda maintenance: maintenance.stage_id.
                            requests_visible_on_gis and not
                            maintenance.field_latitude and not
                            maintenance.field_longitude).mapped(
                        lambda maintenance: maintenance.id),
                }),
            'maintenance_stages': maintenance_stages.mapped(
                lambda stage: {
                    'id': stage.id,
                    'name': stage.name,
                }),
            'priority_labels': priority_labels,
            'maintenance_teams': maintenance_teams,
            'default_interval': default_gis_refresh_interval * 1000,
            'default_maintenance_for_creation':
                default_maintenance_for_creation,
        }

    def _get_attachments_of_message(self, message):
        attachments = message.attachment_ids
        return attachments

    def _get_field_value(self, equipment, field_path):
        field_names = field_path.split('.')
        target = equipment
        if (equipment.category_id and equipment.category_id.model_id):
            target = request.env[equipment.category_id.model_id.model].search(
                [('equipment_id', '=', equipment.id)], limit=1)
        for field_name in field_names:
            if not target:
                return None
            # Check for array indexes
            if '[' in field_name and ']' in field_name:
                field_base, index_str = field_name.split('[')
                index = int(index_str[:-1])
                # get the field value
                target = getattr(target, field_base, None)
                if isinstance(target, list) and len(target) > index:
                    target = target[index]
                else:
                    return None
            else:
                target = getattr(target, field_name, None)
        return target

    def _format_maintenance_for_maintenance_workmode(self, maintenance):
        message_attachment_ids = maintenance.message_ids.mapped(
            'attachment_ids').ids
        maintenance_attachments = request.env['ir.attachment'].search([
            ('res_model', '=', 'maintenance.request'),
            ('res_id', '=', maintenance.id),
            ('id', 'not in', message_attachment_ids),
            ('name', 'not ilike', 'resolution_image%'),
        ])
        dynamic_fields = []
        if maintenance.maintenance_kind_id:
            for field in maintenance.maintenance_kind_id.dynamic_field_ids:
                field_data = {
                    'name': field.name,
                    'field_type': field.field_type,
                    'required': field.required,
                    'field_path': field.field_path,
                    'value': self._get_field_value(
                        maintenance.equipment_id, field.field_path),
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
                    if (maintenance.equipment_id and
                        maintenance.equipment_id.category_id and
                            maintenance.equipment_id.category_id.model_id):
                        model = \
                            maintenance.equipment_id.category_id.model_id.model
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
        # In case some is null, set the 0 value
        priority_selection = "0"
        if (maintenance.priority):
            priority_selection = maintenance.priority
        priority_label = maintenance._fields['priority'].convert_to_export(
            priority_selection, maintenance)
        maintenance_type_label = maintenance._fields['maintenance_type'].\
            convert_to_export(maintenance.maintenance_type, maintenance)
        return {
            'id': maintenance.id,
            'name': maintenance.name,
            'description': maintenance.description or '',
            'category': maintenance.category_id.name,
            'geometry_type': maintenance.category_id.geometry_type,
            'equipment': maintenance.equipment_id.name,
            'equipment_id': maintenance.equipment_id.id,
            'request_date': maintenance.request_date,
            'stage': maintenance.stage_id.name,
            'stage_id': maintenance.stage_id.id,
            'priority': priority_label,
            'hydraulicsector': maintenance.hydraulicsector_id.name,
            'related_element_extradata': maintenance.related_element_extradata,
            'maintenance_type': maintenance_type_label,
            'maintenance_kind': maintenance.maintenance_kind_id.name or '',
            'image_before_required':
                maintenance.maintenance_kind_id.image_before_required,
            'image_after_required':
                maintenance.maintenance_kind_id.image_after_required,
            'image_before_multiple':
                maintenance.maintenance_kind_id.multiple_before_images,
            'image_after_multiple':
                maintenance.maintenance_kind_id.multiple_after_images,
            'mandatory_comment':
                maintenance.maintenance_kind_id.mandatory_comment,
            'maintenance_team':
            maintenance.maintenance_team_id.name if
            maintenance.maintenance_team_id else _('Without team'),
            'procedure_description':
                maintenance.maintenance_kind_id.procedure_description or '',
            'technician': maintenance.technician_user_id.name or '',
            'field_resolved': maintenance.field_resolved,
            'resolution_description': maintenance.resolution_description or '',
            'resolution_time': maintenance.resolution_time,
            'resolved_by': maintenance.resolved_by.name or '',
            'created_on_field': maintenance.created_on_field,
            'field_latitude': maintenance.field_latitude,
            'field_longitude': maintenance.field_longitude,
            'messages': maintenance.message_ids.filtered(
                lambda x: x.body).mapped(
                lambda message: {
                    'author': message.author_id.name,
                    'date': message.date,
                    'body': message.body,
                    'attachments': self._get_attachments_of_message(
                        message).mapped(
                        lambda attachment: {
                            'name': attachment.name,
                            'datas': attachment.datas,
                            'mimetype': attachment.mimetype,
                        }),
                }),
            'attachments': maintenance_attachments.mapped(
                lambda attachment: {
                    'name': attachment.name,
                    'datas': attachment.datas,
                    'mimetype': attachment.mimetype,
                }),
            'image': maintenance.equipment_id.image,
            'dynamic_fields': dynamic_fields,
        }

    @http.route("/maintenance_init_config", auth='user', type='json',
                methods=['POST'], csrf=False)
    def get_maintenance_init_config(self, *args, **kwargs):
        maintenances = request.env['maintenance.request'].search(
            [('stage_id.requests_visible_on_gis', '=', True),
             ('category_id', '!=', False)])
        output = {
            'config': self._get_config_for_maintenance_workmode(maintenances),
            'categories': {},
            'maintenances': [],
        }
        for maintenance in maintenances:
            category_name = maintenance.category_id.name
            if category_name not in output['categories']:
                output['categories'][category_name] = {
                    'id': maintenance.category_id.id,
                    'name': category_name,
                    'geojson_style': maintenance.category_id.
                    geojson_style.replace('\n', '').strip(),
                    'legend_symbology': maintenance.category_id.
                    legend_symbology.replace('\n', '').strip(),
                }
            output['maintenances'].append(
                self._format_maintenance_for_maintenance_workmode(maintenance))
        return json.dumps(output, ensure_ascii=False)
