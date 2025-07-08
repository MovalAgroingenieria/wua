# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from jinja2 import Template, TemplateError
from datetime import datetime
from odoo import models, fields, api


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

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
    )

    days_since_creation = fields.Integer(
        string='Days since creation',
        default=0,
        readonly=True,
    )

    field_resolved = fields.Boolean(
        string='Field resolved',
        default=False,
        readonly=True,
    )

    resolution_time = fields.Datetime(
        string='Resolution Time',
        readonly=True,
    )

    resolved_by = fields.Many2one(
        comodel_name='res.users',
        string='Resolved by',
        readonly=True,
    )

    resolution_image_before = fields.Binary(
        string='Resolution Before Image',
        attachment=True,
    )

    resolution_image_before_filename = fields.Char(
        string='Resolution Before Image Filename',
        attachment=True,
        readonly=True,
    )

    resolution_image_after = fields.Binary(
        string='Resolution After Image',
        attachment=True,
    )

    resolution_image_after_filename = fields.Char(
        string='Resolution After Image Filename',
        attachment=True,
        readonly=True,
    )

    resolution_images_before = fields.One2many(
        string='Before Resolution Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'before')],
    )

    resolution_images_after = fields.One2many(
        string='After Resolution Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'after')],
    )

    resolution_description = fields.Html(
        string='Resolution Description',
        readonly=True,
    )

    created_on_field = fields.Boolean(
        string='Created on field',
        default=False,
        readonly=True,
    )

    field_image = fields.Binary(
        string='Image from Field',
        attachment=True,
        readonly=True,
    )

    field_images = fields.One2many(
        string='Field Images',
        comodel_name='maintenance.request.attachment',
        inverse_name='maintenance_id',
        domain=[('image_type', '=', 'field')],
    )

    field_latitude = fields.Float(
        string='Field Latitude',
        readonly=True,
    )

    field_longitude = fields.Float(
        string='Field Longitude',
        readonly=True,
    )

    resolution_dynamic_fields = fields.Text(
        string='Updated info',
        readonly=True,
    )

    description = fields.Html(
        string='Description',
    )

    with_infrastructure_gis = fields.Boolean(
        string='With Infrastructure GIS',
        compute='_compute_with_infrastructure_gis',
        search='_search_with_infrastructure_gis',
    )

    active = fields.Boolean(default=True)

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

    @api.model
    def update_dynamic_fields(self, maintenance_id, dynamic_fields):
        response = {'success': False, 'errors': [], 'updated_fields': []}
        maintenance = self.browse(maintenance_id)
        if not maintenance or not maintenance.equipment_id:
            response['errors'].append('Maintenance request not found')
        else:
            equipment = maintenance.equipment_id
            target_record = equipment
            if (equipment.category_id.model_id):
                model_name = equipment.category_id.model_id.model
                target_record = self.env[model_name].search(
                    [('equipment_id', '=', equipment.id)], limit=1)
            updates_by_target = {}
            updated_dynamic_fields = []
            for field_path, value in dynamic_fields.items():
                target, last_field, parent_target = self._resolve_field_path(
                    target_record, field_path)
                if target is None:
                    response['errors'].append(
                        'Invalid field path: %s' % field_path)
                    continue
                record_to_update = parent_target if parent_target else \
                    target_record
                if record_to_update not in updates_by_target:
                    updates_by_target[record_to_update] = {}
                updates_by_target[record_to_update][last_field] = value
                updated_dynamic_fields.append('%s: %s' % (field_path, value))
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
