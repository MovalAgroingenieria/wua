# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from jinja2 import Template, TemplateError
from datetime import datetime
import json
from odoo import models, fields, api, _
from bs4 import BeautifulSoup


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    def _get_default_team_id(self):
        default_team = self.env['maintenance.team'].search(
            [('default_team', '=', True)], limit=1)
        # Always at least one team
        if not default_team:
            default_team = self.env['maintenance.team'].search(
                [], limit=1)
        return default_team

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Override to handle maintenance request creation from incoming
        emails. Sets the description from the email body and ensures
        a default team is assigned."""
        if custom_values is None:
            custom_values = {}
        # Set description from email body if not already provided
        if not custom_values.get('description'):
            body = msg_dict.get('body', '')
            if body:
                custom_values['description'] = body
        # Ensure maintenance_team_id is set
        if not custom_values.get('maintenance_team_id'):
            default_team = self._get_default_team_id()
            if default_team:
                custom_values['maintenance_team_id'] = default_team.id
        return super(MaintenanceRequest, self).message_new(
            msg_dict, custom_values=custom_values)

    maintenance_team_id = fields.Many2one(
        default=lambda self: self._get_default_team_id(),
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulicsector_id',
    )

    sequence = fields.Char(
        readonly=True,
    )

    related_element_extradata = fields.Text(
        string='Related element extradata',
        copy=False,
    )

    days_since_creation = fields.Integer(
        string='Days since creation',
        default=0,
        readonly=True,
        copy=False,
    )

    field_resolved = fields.Boolean(
        string='Field resolved',
        default=False,
        readonly=True,
        copy=False,
    )

    dynamic_fields_data = fields.Html(
        string='Dynamic Fields Data',
        default='',
        track_visibility='onchange',
        sanitize=False,
        copy=False,
    )

    resolution_time = fields.Datetime(
        string='Resolution Time',
        readonly=False,
        copy=False,
    )

    resolved_by = fields.Many2one(
        comodel_name='res.users',
        string='Resolved by',
        readonly=True,
        copy=False,
    )

    resolution_image_before = fields.Binary(
        string='Resolution Before Image',
        attachment=True,
        copy=False,
    )

    resolution_image_before_filename = fields.Char(
        string='Resolution Before Image Filename',
        attachment=True,
        readonly=True,
        copy=False,
    )

    resolution_image_after = fields.Binary(
        string='Resolution After Image',
        attachment=True,
        copy=False,
    )

    resolution_image_after_filename = fields.Char(
        string='Resolution After Image Filename',
        attachment=True,
        readonly=True,
        copy=False,
    )

    resolution_images_before = fields.One2many(
        string='Before Resolution Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'before')],
        copy=False,
    )

    resolution_images_after = fields.One2many(
        string='After Resolution Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'after')],
        copy=False,
    )

    resolution_description = fields.Html(
        string='Resolution Description',
        readonly=False,
        copy=False,
    )

    created_on_field = fields.Boolean(
        string='Created on field',
        default=False,
        readonly=True,
        copy=False,
    )

    field_image = fields.Binary(
        string='Image from Field',
        attachment=True,
        readonly=True,
        copy=False,
    )

    field_images = fields.One2many(
        string='Field Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'field')],
        copy=False,
    )

    field_latitude = fields.Float(
        string='Field Latitude',
        readonly=True,
        copy=False,
    )

    field_longitude = fields.Float(
        string='Field Longitude',
        readonly=True,
        copy=False,
    )

    resolution_dynamic_fields = fields.Text(
        string='Updated info',
        readonly=False,
        copy=False,
    )

    description = fields.Html(
        string='Description',
    )

    with_infrastructure_gis = fields.Boolean(
        string='With Infrastructure GIS',
        compute='_compute_with_infrastructure_gis',
        search='_search_with_infrastructure_gis',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    @api.depends('equipment_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.equipment_id.hydraulicsector_id

    @api.onchange('category_id', 'equipment_id')
    def onchange_category_equipment_id_render_data(self):
        if (self.category_id and self.equipment_id and
                self.category_id.extradata_template):
            template = Template(self.category_id.extradata_template)
            equipment = self.equipment_id
            try:
                self.related_element_extradata = template.render(
                    equipment=equipment, datetime=datetime)
            except TemplateError:
                pass

    @api.onchange('maintenance_team_id')
    def onchange_maintenance_team_id(self):
        if (self.maintenance_team_id and
                self.maintenance_team_id.partner_ids and
                len(self.maintenance_team_id.partner_ids) == 1 and
                self.maintenance_team_id.partner_ids[0].user_ids):
            self.technician_user_id = self.maintenance_team_id.\
                partner_ids[0].user_ids[0]

    @api.onchange('maintenance_kind_id')
    def onchange_maintenance_kind_id(self):
        if self.maintenance_kind_id:
            kind_category = self.maintenance_kind_id.category_id
            if kind_category:
                if self.equipment_id and \
                        self.equipment_id.category_id != kind_category:
                    self.equipment_id = None
                self.category_id = kind_category.id
                return {
                    'domain': {
                        'equipment_id': [('category_id',
                                          '=',
                                          kind_category.id)],
                    },
                }
            else:
                self.category_id = None
                self.category_id = kind_category.id
                return {
                    'domain': {
                        'equipment_id': [],
                    },
                }
        else:
            if not self.equipment_id:
                self.category_id = None
            return {
                'domain': {
                    'equipment_id': [],
                },
            }

    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        result = super(MaintenanceRequest, self).onchange_equipment_id() or {}
        if self.equipment_id and self.equipment_id.category_id:
            result['domain'] = {
                'maintenance_kind_id': [
                    ('category_id', '=', self.equipment_id.category_id.id),
                ],
            }
        else:
            result['domain'] = {'maintenance_kind_id': []}
        return result

    @api.multi
    def _compute_with_infrastructure_gis(self):
        for record in self:
            with_infrastructure_gis = False
            if record.equipment_id and \
                    record.equipment_id.with_infrastructure_gis:
                with_infrastructure_gis = True
            record.with_infrastructure_gis = with_infrastructure_gis

    @api.model
    def _search_with_infrastructure_gis(self, operator, value):
        if operator not in ('=', '!='):
            return [('id', 'in', [])]
        domain = [('equipment_id.with_infrastructure_gis', '=', True)]
        ids = self.search(domain).ids
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', ids)]
        else:
            return [('id', 'not in', ids)]

    @api.multi
    def action_see_gis_viewer(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        if (url and self.equipment_id and self.equipment_id.geojson_geom):
            cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                username, password)
            if (cipher_text):
                url = '%s?arg=%s&geom=%s' % (
                    url, cipher_text, self.equipment_id.geojson_geom)
            else:
                url = '%s?&geom=%s' % (
                    url, self.equipment_id.geojson_geom)
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }

    @api.model
    def _compute_days_since_creation(self):
        try:
            self.env.cr.execute(
                """
                UPDATE maintenance_request SET days_since_creation =
                (now()::date - request_date::date);
                """)
            self.env.cr.commit()
        except Exception:
            pass

    def _add_maintenance_team_followers(self):
        for record in self:
            if record.maintenance_team_id:
                record.message_subscribe(
                    partner_ids=record.maintenance_team_id.partner_ids.ids)

    def write(self, vals):
        # Ensure no empty resolution images are saved
        if 'resolution_images_before' in vals and not \
                vals['resolution_images_before']:
            vals.pop('resolution_images_before')
        if 'resolution_images_after' in vals and not \
                vals['resolution_images_after']:
            vals.pop('resolution_images_after')
        res = super(MaintenanceRequest, self).write(vals)
        if 'maintenance_team_id' in vals:
            self._add_maintenance_team_followers()
        if 'field_resolved' in vals and vals['field_resolved']:
            self.resolved_by = self.env.user
        return res

    @api.model
    def create(self, vals):
        model_ir_sequence = self.env['ir.sequence'].sudo()
        sequence_maintenance_request_code = None
        sequence_maintenance_request_code_id = \
            self.env['ir.values'].get_default(
                'maintenance.config.settings',
                'sequence_maintenance_request_code_id')
        if sequence_maintenance_request_code_id:
            sequence_maintenance_request_code = \
                model_ir_sequence.browse(sequence_maintenance_request_code_id)
        if sequence_maintenance_request_code:
            vals['sequence'] = model_ir_sequence.next_by_code(
                sequence_maintenance_request_code.code)
        new_request = super(MaintenanceRequest, self).create(vals)
        # Assign default category if created_on_field is True
        if (new_request.created_on_field):
            default_team = self.env['maintenance.team'].search([
                ('default_team_for_viewer_creation', '=', True)],
                limit=1)
            if default_team:
                new_request.maintenance_team_id = default_team.id
            if not new_request.category_id:
                new_request.category_id = self.env.ref(
                    'wua_maintenance.equipment_category_field')
        new_request._add_maintenance_team_followers()
        return new_request

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

    def _get_field_html_markup(self, field_name, value):
        return '<b>%s: </b><span name-value="%s">%s</span>' % (
            field_name, field_name, value)

    def _update_html_field(self, record, html_fields, is_request_field=True):
        if not html_fields:
            return False, []
        html_content = record.dynamic_fields_data or ''
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            for field_html in html_fields:
                field_name = field_html.split('name-value="')[1].split('"')[0]
                existing_span = soup.find(
                    'span', attrs={'name-value': field_name})
                if existing_span:
                    prev_el = existing_span.previous_sibling
                    if prev_el and prev_el.name == 'b':
                        prev_el.decompose()
                    existing_span.decompose()
            if str(soup):
                html_content = str(soup) + '<br/>' + '<br/>'.join(html_fields)
            else:
                html_content = '<div>' + '<br/>'.join(html_fields) + '</div>'
        else:
            html_content = '<div>' + '<br/>'.join(html_fields) + '</div>'
        record.sudo().write({'dynamic_fields_data': html_content})
        return True, ['dynamic_fields_data']

    def _clean_fields_with_path_from_html(self, record, fields_with_paths):
        if not fields_with_paths:
            return False
        html_content = record.dynamic_fields_data or ''
        if not html_content:
            return False
        soup = BeautifulSoup(html_content, 'html.parser')
        changes_made = False
        for field_name in fields_with_paths:
            field_span = soup.find('span', attrs={'name-value': field_name})
            if field_span:
                changes_made = True
                prev_el = field_span.previous_sibling
                if prev_el and prev_el.name == 'b':
                    prev_el.decompose()
                field_span.decompose()
        if changes_made:
            record.sudo().write({'dynamic_fields_data': str(soup)})
        return changes_made

    def _get_dynamic_field_config(self, maintenance):
        configs = {}
        fields_with_paths = set()
        path_to_name = {}
        if (maintenance.maintenance_kind_id and
                maintenance.maintenance_kind_id.dynamic_field_ids):
            for field in maintenance.maintenance_kind_id.dynamic_field_ids:
                configs[field.name] = {
                    'field_path': field.field_path,
                    'is_request_field': field.is_request_field,
                }
                if field.field_path:
                    fields_with_paths.add(field.name)
                    path_to_name[field.field_path] = field.name
        return configs, fields_with_paths, path_to_name

    @api.multi
    def action_reset_field_data(self):
        for record in self:
            record.resolution_images_before.unlink()
            record.resolution_images_after.unlink()
            # Reset all field resolution data
            record.write({
                'field_resolved': False,
                'dynamic_fields_data': '',
                'resolution_time': False,
                'resolved_by': False,
                'resolution_image_before': False,
                'resolution_image_before_filename': False,
                'resolution_image_after': False,
                'resolution_image_after_filename': False,
                'resolution_description': '',
                'resolution_dynamic_fields': False,
            })
            # Add message to chatter
            record.message_post(
                body=_("Field resolution data has been reset by %s") % (
                    self.env.user.name),
                message_type='notification',
                subtype='mail.mt_note',
            )

    @api.model
    def update_dynamic_fields(self, maintenance_id, dynamic_fields):
        response = {'success': False, 'errors': [], 'updated_fields': []}
        maintenance = self.browse(maintenance_id)
        if not maintenance or not maintenance.equipment_id:
            response['errors'].append('Maintenance request not found')
            return response
        equipment = maintenance.equipment_id
        target_record = equipment
        if equipment.category_id.model_id:
            model_name = equipment.category_id.model_id.model
            target_record = self.env[model_name].search(
                [('equipment_id', '=', equipment.id)], limit=1)
        configs = self._get_dynamic_field_config(maintenance)
        field_configs = configs[0]
        fields_with_paths = configs[1]
        path_to_name = configs[2]
        updates_by_target = {}
        updated_dynamic_fields = []
        request_fields_html = []
        equipment_fields_html = []
        for field_key, value in dynamic_fields.items():
            field_config = field_configs.get(field_key, {})
            if not field_config and field_key in path_to_name:
                field_name = path_to_name[field_key]
                field_config = field_configs.get(field_name, {})
                field_key = field_name
            field_path = field_config.get('field_path', '')
            is_request_field = field_config.get('is_request_field', True)
            # Check if looks like a valid field path (has dots, no spaces)
            if not field_config and '.' in field_key and ' ' not in field_key:
                # Additional validation to confirm it's likely a field path
                parts = field_key.split('.')
                if all(part and part[0].isalpha() for part in parts):
                    field_path = field_key
            if field_path:
                target, last_field, parent_target = self._resolve_field_path(
                    target_record, field_path)
                if target is None:
                    response['errors'].append(
                        'Invalid field path: %s' % field_path)
                    continue
                if parent_target:
                    record_to_update = parent_target
                else:
                    record_to_update = target_record
                if record_to_update not in updates_by_target:
                    updates_by_target[record_to_update] = {}
                updates_by_target[record_to_update][last_field] = value
                updated_dynamic_fields.append('%s: %s' % (field_path, value))
            elif field_key not in fields_with_paths:
                html_field = self._get_field_html_markup(field_key, value)
                if is_request_field:
                    request_fields_html.append(html_field)
                else:
                    equipment_fields_html.append(html_field)
                updated_dynamic_fields.append('%s: %s' % (field_key, value))
        if request_fields_html:
            updated, fields = self._update_html_field(
                maintenance, request_fields_html, True)
            if updated:
                response['updated_fields'].extend(fields)
        if equipment_fields_html:
            updated, fields = self._update_html_field(
                equipment, equipment_fields_html, False)
            if updated:
                response['updated_fields'].append(
                    'equipment_dynamic_fields_data')
        self._clean_fields_with_path_from_html(maintenance, fields_with_paths)
        self._clean_fields_with_path_from_html(equipment, fields_with_paths)
        for record, updates in updates_by_target.items():
            try:
                record.sudo().write(updates)
                response['updated_fields'].extend(updates.keys())
            except Exception as e:
                response['errors'].append(
                    'Error writing to %s: %s' % (record, e))
        if updated_dynamic_fields:
            maintenance.resolution_dynamic_fields = ';\n '.join(
                updated_dynamic_fields)
        response['success'] = not response['errors']
        return response

    @api.multi
    def get_served_parcels_and_payer(self):
        self.ensure_one()
        data = {
            'parcels': [],
            'extra_info': False,
        }
        equipment = self.equipment_id
        if not equipment:
            return data
        category = equipment.category_id
        if not category:
            return data
        if category == self.env.ref(
                'wua_maintenance.equipment_category_waterconnection'):
            wc = equipment.waterconnection_id
        elif category == self.env.ref(
                'wua_maintenance.equipment_category_watermeter'):
            wc = equipment.watermeter_id.waterconnection_id if \
                equipment.watermeter_id else False
        else:
            wc = False
        if wc:
            for ip in wc.irrigationpoint_ids:
                parcel = ip.parcel_id
                data['parcels'].append({
                    'code': parcel.name,
                    'polygon': parcel.cadastral_polygon,
                    'parcel': parcel.cadastral_parcel,
                    'area': parcel.area_official,
                    'hydraulic_sector': equipment.hydraulicsector_id.name or
                    '',
                })
            data['extra_info'] = self.related_element_extradata
        return data

    @api.multi
    def get_equipment_coordinates(self):
        """
        Extract and format coordinates from equipment's geojson_geom field.
        Returns a formatted string like "X: 644865, Y: 4233260"
        """
        self.ensure_one()
        if not self.equipment_id or not self.equipment_id.geojson_geom:
            return ''

        try:
            geojson_data = json.loads(self.equipment_id.geojson_geom)
            if 'coordinates' in geojson_data:
                coordinates = geojson_data['coordinates']
                if isinstance(coordinates, list) and len(coordinates) >= 2:
                    # Truncate to integer (remove decimals)
                    x_coord = int(coordinates[0])
                    y_coord = int(coordinates[1])
                    return 'X: %s, Y: %s' % (x_coord, y_coord)
        except (ValueError, TypeError, KeyError):
            pass

        return ''


class MaintenanceRequestAttachment(models.Model):
    _name = 'maintenance.request.attachment'

    maintenance_id = fields.Many2one(
        string='Maintenance',
        comodel_name='maintenance.request',
        ondelete='cascade',
        required=True,
    )

    image_type = fields.Selection(
        [('before', 'Before'),
         ('after', 'After'),
         ('field', 'Field')],
        string='Image Type',
        required=True,
    )

    image = fields.Binary(
        string='Image',
        attachment=True,
        required=True,
    )

    filename = fields.Char(
        string='Filename',
    )

    image_attachment_id = fields.Integer(
        string='Image attachemnt ID',
        compute='_compute_image_attachment_id',
        store=False,
    )

    def action_preview_images(self):
        images = self.search(
            [('maintenance_id', '=', self.maintenance_id.id),
             ('image_type', '=', self.image_type)])
        wizard = self.env['wizard.image.preview'].create({
            'image_ids': [(6, 0, images.ids)],
            'current_index':
                images.ids.index(self.id) if self.id in images.ids else 0,
        })
        return {
            'name': 'Image Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.image.preview',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'readonly'},
        }

    @api.depends('image')
    def _compute_image_attachment_id(self):
        for rec in self:
            image_attachment_id = False
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
                ('res_field', '=', 'image'),
            ], limit=1)
            if attachment:
                image_attachment_id = attachment.id
            rec.image_attachment_id = image_attachment_id

    @api.model
    def create(self, vals):
        record = super(MaintenanceRequestAttachment, self).create(vals)
        if record.image and record.filename:
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id),
                ('res_field', '=', 'image'),
            ], limit=1)
            if attachment:
                attachment.write({
                    'name': record.filename,
                    'datas_fname': record.filename,
                })
        return record
