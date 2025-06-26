# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    created_from_field = fields.Boolean(
        string='Created from field',
        default=False,
    )

    inventory_extra_data = fields.Html(
        string='Inventory Extra Data',
        default='',
        track_visibility='onchange',
        sanitize=False,
    )

    def _resolve_field_path(self, record, field_path):
        field_names = field_path.split('.')
        target = record
        parent_target = None
        for i, field_name in enumerate(field_names):
            if '[' in field_name and ']' in field_name:
                field_base, index_str = field_name.split('[')
                index = int(index_str[:-1])
                target = getattr(target, field_base, None)
                if isinstance(target, list) and len(target) > index:
                    target = target[index]
                else:
                    return None, None, None
            else:
                parent_target = target
                target = getattr(target, field_name, None)
            if target is None and i < len(field_names) - 1:
                return None, None, None
        return target, field_names[-1], parent_target

    @api.model
    def create_related_records(self, related_new_records, geometry=None):
        response = {
            'success': False, 'errors': [], 'created_ids': {},
            'equipments': [],
        }
        if not related_new_records:
            response['success'] = True
            return response
        for field_path, rel in related_new_records.iteritems():
            sub_resp = self.create_infrastructure_element(
                rel['related_category_id'],
                rel['dynamicFields'],
                rel.get('relatedNewRecords', {}),
                attachments=[],
                geometry=geometry,
            )
            if not sub_resp.get('success'):
                response['errors'].extend(
                    ["[%s] %s" % (field_path, e)
                        for e in sub_resp.get('errors', [])],
                )
            else:
                response['created_ids'][field_path] = sub_resp['relation_id']
                response['equipments'].extend(sub_resp.get('equipments', []))
        response['success'] = not response['errors']
        return response

    @api.model
    def create_infrastructure_element(
            self, category_id, values, related_new_records=None,
            attachments=None, geometry=None):
        response = {'success': False, 'errors': [], 'equipments': [],
                    'relation_id': -1}
        related_new_records = related_new_records or {}
        attachments = attachments or []
        created_related_ids = {}
        for field_path, rel in related_new_records.iteritems():
            sub_resp = self.create_infrastructure_element(
                rel['related_category_id'],
                rel['dynamicFields'],
                rel.get('relatedNewRecords', {}),
                attachments=[],
                geometry=geometry,
            )
            if not sub_resp.get('success'):
                for e in sub_resp.get('errors', []):
                    response['errors'].append("[%s] %s" % (field_path, e))
            else:
                created_related_ids[field_path] = sub_resp['relation_id']
                response['equipments'].extend(sub_resp.get('equipments', []))
        if response['errors']:
            return response
        for field_path, new_id in created_related_ids.iteritems():
            if field_path in values:
                values[field_path]['value'] = new_id
            else:
                values[field_path] = {
                    'field_path': field_path,
                    'value': new_id,
                }
        direct_vals = {}
        dynamic_vals = {}
        for k, v in values.iteritems():
            path = v.get('field_path', '')
            if path and '.' not in path:
                direct_vals[path] = v.get('value')
            elif (not path and not v.get('gis_path', '')) or '.' in path:
                dynamic_vals[k] = v
        category = self.env['maintenance.equipment.category'].browse(
            category_id)
        if category.model_id and category.model_id.model:
            infra_rec = self.env[category.model_id.model].sudo().create(
                direct_vals)
            equipment_rec = infra_rec.equipment_id
            if equipment_rec:
                equipment_rec.created_from_field = True
            relation_id = infra_rec.id
        else:
            direct_vals.update({
                'category_id': category.id,
                'created_from_field': True,
            })
            equipment_rec = self.env['maintenance.equipment'].create(
                direct_vals)
            relation_id = equipment_rec.id
        if not equipment_rec:
            response['errors'].append('Equipment could not be created')
            return response
        response['equipments'].append(equipment_rec.id)
        response['relation_id'] = relation_id
        dyn_resp = self.update_dynamic_fields(equipment_rec.id, dynamic_vals)
        response['errors'].extend(dyn_resp.get('errors', []))
        for att in attachments:
            self.env['ir.attachment'].sudo().create({
                'name': att.get('filename'),
                'datas_fname': att.get('filename'),
                'datas': att.get('data'),
                'res_model': 'maintenance.equipment',
                'res_id': equipment_rec.id,
                'type': 'binary',
                'mimetype': att.get('content_type'),
            })
        if geometry:
            gis_resp = self.update_dynamic_gis_fields(
                equipment_rec.id, values,
                geometry,
            )
            response['errors'].extend(gis_resp.get('errors', []))
        response['success'] = not response['errors']
        return response

    @api.model
    def update_dynamic_fields(self, equipment_id, dynamic_fields):
        response = {'success': False, 'errors': [], 'updated_fields': []}
        equipment = self.browse(equipment_id)
        if not equipment:
            response['errors'].append('Equipment not found')
        else:
            # ORM Updates
            target_record = equipment
            if (equipment.category_id and
                    equipment.category_id.model_id):
                model_name = equipment.category_id.model_id.model
                target_record = self.env[model_name].search(
                    [('equipment_id', '=', equipment.id)], limit=1)
            updates_by_target = {}
            updated_dynamic_fields = []
            updated_dynamic_extra_fields = []
            for field in dynamic_fields.values():
                field_path = field.get('field_path')
                gis_path = field.get('gis_path')
                value = field.get('value')
                if field_path:
                    target, last_field, parent_target = self.\
                        _resolve_field_path(target_record, field_path)
                    if target is None:
                        response['errors'].append(
                            'Invalid field path: %s' % field_path)
                        continue
                    record_to_update = parent_target if parent_target else \
                        target_record
                    if record_to_update not in updates_by_target:
                        updates_by_target[record_to_update] = {}
                    updates_by_target[record_to_update][last_field] = value
                    updated_dynamic_fields.append('%s: %s' % (
                        field_path, value))
                elif not gis_path and not field_path:
                    updated_dynamic_extra_fields.append(
                        '<b>%s: </b><span name-value="%s">%s</span>' % (
                            field.get('name'), field.get('name'), value))
            for record, updates in updates_by_target.items():
                try:
                    record.sudo().write(updates)
                    response['updated_fields'].extend(updates.keys())
                except Exception as e:
                    response['errors'].append(
                        'Error writing to %s: %s' % (record, str(e)))
            response['success'] = not response['errors']
            if updated_dynamic_extra_fields:
                equipment.inventory_extra_data = '<br>'.join(
                    updated_dynamic_extra_fields)
        return response

    @api.model
    def update_dynamic_gis_fields(
            self, equipment_id, dynamic_fields, geometry):
        response = {'success': False, 'errors': [], 'updated_fields': []}
        equipment = self.browse(equipment_id)
        if not equipment:
            response['errors'].append('Equipment not found')
        else:
            # GIS UPDATES
            category_mapping = self._get_category_table_mapping()
            category_id = equipment.category_id.id
            while category_id not in category_mapping and equipment.parent_id:
                equipment = equipment.parent_id
                category_id = equipment.category_id.id
            # If category is directly mapped, use the associated geom of
            # gis element
            # else, use the equipment geom directly
            if category_id in category_mapping:
                mapping = category_mapping[category_id]
                base_table = mapping['base_table']
                base_field = mapping['base_field']
                gis_table = mapping['gis_table']
                gis_field = mapping['gis_field']
                intermediate_table = mapping['intermediate_table']
                intermediate_field = mapping['intermediate_field']
                intermediate_gis_field = mapping['intermediate_gis_field']
                gis_updates = {}
                for field_data in dynamic_fields.values():
                    gis_path = field_data.get('gis_path', '')
                    field_value = field_data.get('value')
                    field_type = field_data.get('field_type')
                    if not gis_path:
                        continue
                    if field_type in ['text', 'selection', 'date']:
                        field_value = "'%s'" % field_value
                    elif field_type == 'checkbox':
                        field_value = 'TRUE' if field_value else 'FALSE'
                    elif field_type in ['number']:
                        try:
                            field_value = float(field_value) if '.' in str(
                                field_value) else int(field_value)
                        except ValueError:
                            response['errors'].append(
                                "Invalid number format for field %s" %
                                gis_path,
                            )
                            continue
                    gis_updates[gis_path] = field_value
                # If the category has a parent, the sql update will come from
                # the parent category, so we need to get the parent category
                if (intermediate_table and intermediate_field and
                        intermediate_gis_field):
                    sql_query = '''
                        SELECT gis.gid
                        FROM {base_table} bt
                        INNER JOIN {intermediate_table} it ON
                            bt.{base_field} = it.{intermediate_field}
                        INNER JOIN {gis_table} gis ON
                            it.{intermediate_gis_field} = gis.{gis_field}
                        WHERE bt.equipment_id = %s
                    '''.format(
                        base_table=base_table,
                        base_field=base_field,
                        intermediate_table=intermediate_table,
                        intermediate_field=intermediate_field,
                        intermediate_gis_field=intermediate_gis_field,
                        gis_table=gis_table,
                        gis_field=gis_field,
                    )
                else:
                    sql_query = '''
                        SELECT gis.gid
                        FROM {base_table} bt
                        INNER JOIN {gis_table} gis ON bt.{base_field} =
                            gis.{gis_field}
                        WHERE bt.equipment_id = %s
                    '''.format(
                        base_table=base_table,
                        gis_table=gis_table,
                        base_field=base_field,
                        gis_field=gis_field,
                    )
                self.env.cr.execute(sql_query, (equipment.id,))
                result = self.env.cr.fetchone()
                gid = result[0] if result else None
                if gid:
                    if gis_updates:
                        update_fields = ", ".join(
                            ["%s = %s" % (key, gis_updates[key]) for key in
                                gis_updates.keys()],
                        )
                        sql_update = u'''
                            UPDATE {gis_table}
                            SET {fields}, geom = ST_GeomFromGeoJSON(%s)
                            WHERE gid = %s
                        '''.format(
                            gis_table=gis_table,
                            fields=update_fields,
                        )
                    else:
                        sql_update = u'''
                            UPDATE {gis_table}
                            SET geom = ST_GeomFromGeoJSON(%s)
                            WHERE gid = %s
                        '''.format(
                            gis_table=gis_table,
                        )
                    try:
                        self.env.cr.savepoint()
                        self.env.cr.execute(sql_update, [geometry, gid])
                        self.env.cr.commit()
                        self.env.invalidate_all()
                        response['updated_fields'].extend(
                            gis_updates.keys())
                    except Exception as e:
                        self.env.cr.rollback()
                        response['errors'].append(
                            'Error updating GIS table %s: %s' % (
                                gis_table, str(e)),
                        )
                else:
                    if gis_updates:
                        fields = u", ".join(gis_updates.keys())
                        values = u", ".join(
                            [unicode(v, 'utf-8') if isinstance(v, str)
                                else unicode(v)
                                for v in gis_updates.values()])
                        sql_insert = u'''
                            INSERT INTO {gis_table} ({fields}, geom)
                            VALUES ({values}, ST_GeomFromGeoJSON(%s))
                            RETURNING gid
                        '''.format(
                            gis_table=gis_table,
                            fields=fields,
                            values=values,
                        )
                    else:
                        sql_insert = u'''
                            INSERT INTO {gis_table} (geom)
                            VALUES (ST_GeomFromGeoJSON(%s))
                            RETURNING gid
                        '''.format(gis_table=gis_table)
                    try:
                        self.env.cr.savepoint()
                        self.env.cr.execute(sql_insert, [geometry])
                        gid = self.env.cr.fetchone()[0]
                        self.env.cr.commit()
                        self.env.invalidate_all()
                        response['updated_fields'].extend(
                            gis_updates.keys())
                    except Exception as e:
                        self.env.cr.rollback()
                        response['errors'].append(
                            'Error inserting into GIS table %s: %s' % (
                                gis_table, str(e)),
                        )
                # Update the equipment's geojson_geom field with the geometry
                # from the GIS table for an inmediate return of data
                # even this will be overwritten later
                equipment.geojson_geom = geometry
                response['success'] = not response['errors']
            else:
                # If not category found on mapping, just update the
                # equipment's geojson field
                equipment.geojson_geom = geometry
                response['success'] = not response['errors']
        return response
