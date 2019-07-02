# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from pyproj import Proj, transform
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaIrrigationgate(models.Model):
    _name = 'wua.irrigationgate'
    _description = 'Entity (irrigation gate)'
    _order = 'irrigationditch_id, hydraulic_order'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 20
    MAX_SIZE_DESCRIPTION = 75

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = True

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        required=True,
        index=True,
        ondelete='restrict')

    hydraulic_order = fields.Integer(
        string="Hydraulic Order",
        required=True)

    image = fields.Binary(
        string='Photo / Image',
        attachment=True)

    gis_viewer_x = fields.Integer(
        string='X coordinate', default=0)

    gis_viewer_y = fields.Integer(
        string='Y coordinate', default=0)

    gis_googlemaps_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_googlemaps_link')

    irrigationpoint_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel.irrigationpoint',
        inverse_name='irrigationgate_id')

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    total_affected_area_official = fields.Float(
        string='Area of parcels',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official')

    total_affected_area_official_hec = fields.Float(
        string='Area of parcels (hectares)',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official_hec')

    delay_time = fields.Integer(
        string='Delay Time (min)',
        default=0,
        required=True)

    to_main_pipe = fields.Boolean(
        string="To main pipe",
        default=True)

    with_flowdivider = fields.Boolean(
        string="With flow divider",
        default=False)

    flowdivider_id = fields.Many2one(
        string='Flow Divider',
        comodel_name='wua.flowdivider',
        index=True,
        ondelete='restrict')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('valid_hydraulic_order',
         'CHECK (hydraulic_order > 0)',
         'The hydraulic_order must be a positive value.'),
        ]

    @api.multi
    def _compute_gis_googlemaps_link(self):
        url = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'url_gis_googlemaps')
        for record in self:
            if url:
                if record.gis_viewer_x > 0 or record.gis_viewer_y > 0:
                    record.gis_googlemaps_link = url
                else:
                    record.gis_googlemaps_link = ''
            else:
                record.gis_googlemaps_link = ''

    @api.depends('irrigationpoint_ids')
    def _compute_number_of_parcels(self):
        irrigationgate_recordset = []
        if len(self) == 1:
            irrigationgate_recordset = [self]
        else:
            irrigationgate_recordset = self
        for irrigationgate in irrigationgate_recordset:
            irrigationgate.number_of_parcels = \
                len(irrigationgate.irrigationpoint_ids)

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official')
    def _compute_total_affected_area_official(self):
        irrigationgate_recordset = []
        if len(self) == 1:
            irrigationgate_recordset = [self]
        else:
            irrigationgate_recordset = self
        for irrigationgate in irrigationgate_recordset:
            irrigationgate.total_affected_area_official = \
                sum(irrigationgate.mapped(
                    'irrigationpoint_ids.parcel_area_official'))
            # total_area = 0
            # for irrigationpoint in irrigationgate.irrigationpoint_ids:
            #     parcel = irrigationpoint.parcel_id
            #     total_area = total_area + parcel.area_official
            # irrigationgate.total_affected_area_official = total_area

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official_hec')
    def _compute_total_affected_area_official_hec(self):
        irrigationgate_recordset = []
        if len(self) == 1:
            irrigationgate_recordset = [self]
        else:
            irrigationgate_recordset = self
        for irrigationgate in irrigationgate_recordset:
            irrigationgate.total_affected_area_official_hec = \
                sum(irrigationgate.mapped(
                    'irrigationpoint_ids.parcel_area_official_hec'))

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    @api.constrains('hydraulic_order')
    def _check_hydraulic_order(self):
        if self.irrigationditch_id:
            if self.hydraulic_order > 0:
                irrigationgates = self.search(
                    [('irrigationditch_id', '=', self.irrigationditch_id.id),
                     ('hydraulic_order', '=', self.hydraulic_order),
                     ('id', '!=', self.id)])
                if len(irrigationgates) > 0:
                    raise exceptions.ValidationError(_('Duplicated ' +
                                                       'hydraulic order.'))

    @api.onchange('irrigationditch_id')
    def _onchange_irrigationditch_id(self):
        if self.irrigationditch_id:
            if self.hydraulic_order == 0:
                irrigationgates = self.search(
                    [('irrigationditch_id', '=', self.irrigationditch_id.id)],
                    limit=1, order='hydraulic_order desc')
                if len(irrigationgates) == 1:
                    self.hydraulic_order = \
                        irrigationgates[0].hydraulic_order + 1
                else:
                    self.hydraulic_order = 1

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationgate, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        doc = etree.XML(res['arch'])
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        area_measurement_name = ''
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode('utf_8')
        if area_measurement_name != '':
            area_measurement_name = ' (' + \
                area_measurement_name.lower() + ')'
            for node in doc.xpath("//field" +
                                  "[@name='total_affected_area_official']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'base_wua_infrastructure',
                        self.__class__.total_affected_area_official.string)
                posBracket = original_label.find(' (')
                if posBracket != -1:
                    original_label = original_label[:posBracket]
                node.set('string', original_label + area_measurement_name)
        res['arch'] = etree.tostring(doc)
        return res

    # No summary for: hydraulic_order field, delay_time
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'hydraulic_order' in fields:
            fields.remove('hydraulic_order')
        if 'delay_time' in fields:
            fields.remove('delay_time')
        return super(WuaIrrigationgate, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        return super(WuaIrrigationgate, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        if 'irrigationditch_id' in vals:
            if len(self) == 1:
                irrigationpoints = \
                    self.env['wua.parcel.irrigationpoint'].search(
                        [('irrigationgate_id', '=', self.id)])
                if len(irrigationpoints) > 0:
                    raise exceptions.UserError(_('This irrigation gate is '
                                                 'present in some parcels: '
                                                 'It is not possible to change'
                                                 ' the irrigation ditch.'))
        return super(WuaIrrigationgate, self).write(vals)

    @api.multi
    def action_see_gis_googlemaps(self):
        self.ensure_one()
        if self.gis_googlemaps_link:
            url_gis_viewer_epsg_code = self.env['ir.values'].get_default(
                'wua.configuration', 'url_gis_viewer_epsg_code')
            if url_gis_viewer_epsg_code:
                epsg_code = 'epsg:' + str(url_gis_viewer_epsg_code)
                url = self.gis_googlemaps_link
                in_proj = Proj(init=epsg_code)
                out_proj = Proj(init='epsg:4326')
                x_in = self.gis_viewer_x
                y_in = self.gis_viewer_y
                x_out, y_out = transform(in_proj, out_proj, x_in, y_in)
                xc = str(x_out)
                yc = str(y_out)
                url = url.replace("ycval", yc)
                url = url.replace("xcval", xc)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                    }

    def refine_name(self, vals):
        name = vals['name']
        if isinstance(name, basestring):
            name = name.strip()
            if self.__class__._lowercase_name:
                name = name.lower()
            if self.__class__._uppercase_name:
                name = name.upper()
            vals.update({'name': name})

    def refine_description(self, vals):
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp
