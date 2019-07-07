# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaIrrigationditch(models.Model):
    _name = 'wua.irrigationditch'
    _description = 'Entity (irrigation ditch)'
    _order = 'irrigationditch_code'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 50
    MAX_SIZE_DESCRIPTION = 100

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = False

    def _default_irrigationditch_code(self):
        resp = 0
        irrigationditches = self.search([('irrigationditch_code', '>', 0)],
                                        limit=1,
                                        order='irrigationditch_code desc')
        if len(irrigationditches) == 1:
            resp = irrigationditches[0].irrigationditch_code + 1
        else:
            resp = 1
        return resp

    name = fields.Char(
        string='Name',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    irrigationditch_code = fields.Integer(
        string='Code',
        default=_default_irrigationditch_code,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    early_shutdown_time = fields.Integer(
        string='Early Shutdow Time (min)',
        default=0,
        required=True)

    wateringduration_area_ratio = fields.Integer(
        string='Watering Duration x Area Ratio (min)',
        default=0,
        required=True)

    wateringduration_area_ratio_hec = fields.Float(
        string='Watering Duration x Hec Ratio (min)',
        digits=(32, 4),
        store=True,
        compute='_compute_wateringduration_area_ratio_hec')

    water_flow = fields.Integer(
        string='Water Flow (liters/sec)',
        default=0,
        required=True)

    notes = fields.Html(string='Notes')

    irrigationgate_ids = fields.One2many(
        string='Irrigation Gates',
        comodel_name='wua.irrigationgate',
        inverse_name='irrigationditch_id')

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='irrigationditch_id')

    flowdivider_ids = fields.One2many(
        string='Flow Dividers',
        comodel_name='wua.flowdivider',
        inverse_name='irrigationditch_id')

    number_of_irrigationgates = fields.Integer(
        string='Number of irrigation gates',
        store=True,
        compute='_compute_number_of_irrigationgates')

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    number_of_flowdividers = fields.Integer(
        string='Number of flow dividers',
        store=True,
        compute='_compute_number_of_flowdividers')

    total_affected_area_official = fields.Float(
        string='Cumulative area of parcels',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official')

    total_affected_area_official_hec = fields.Float(
        string='Cumulative area of parcels (hectares)',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official_hec')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('valid_early_shutdown_time',
         'CHECK (early_shutdown_time > = 0)',
         'The early shutdown time must be a value zero or positive.'),
        ('valid_wateringduration_area_ratio',
         'CHECK (wateringduration_area_ratio > = 0)',
         'The watering dur. x area ratio must be a value zero or positive.'),
        ('valid_water_flow',
         'CHECK (water_flow > = 0)',
         'The water flow must be a value zero or positive.')]

    @api.depends('irrigationgate_ids')
    def _compute_number_of_irrigationgates(self):
        irrigationditch_recordset = []
        if len(self) == 1:
            irrigationditch_recordset = [self]
        else:
            irrigationditch_recordset = self
        for irrigationditch in irrigationditch_recordset:
            irrigationditch.number_of_irrigationgates = \
                len(irrigationditch.irrigationgate_ids)

    @api.depends('irrigationgate_ids', 'irrigationgate_ids.number_of_parcels')
    def _compute_number_of_parcels(self):
        irrigationditch_recordset = []
        if len(self) == 1:
            irrigationditch_recordset = [self]
        else:
            irrigationditch_recordset = self
        for irrigationditch in irrigationditch_recordset:
            irrigationditch.number_of_parcels = \
                sum(irrigationditch.mapped(
                    'irrigationgate_ids.number_of_parcels'))

    @api.depends('flowdivider_ids')
    def _compute_number_of_flowdividers(self):
        for record in self:
            record.number_of_flowdividers = \
                len(record.flowdivider_ids)

    @api.depends('wateringduration_area_ratio')
    def _compute_wateringduration_area_ratio_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        for record in self:
            record.wateringduration_area_ratio_hec = \
                record.wateringduration_area_ratio / factor

    @api.depends('irrigationgate_ids',
                 'irrigationgate_ids.total_affected_area_official')
    def _compute_total_affected_area_official(self):
        for record in self:
            record.total_affected_area_official = \
                sum(record.mapped(
                    'irrigationgate_ids.total_affected_area_official'))

    @api.depends('total_affected_area_official')
    def _compute_total_affected_area_official_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        for record in self:
            record.total_affected_area_official_hec = \
                factor * record.total_affected_area_official

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    @api.constrains('irrigationditch_code')
    def _check_irrigationditch_code(self):
        if self.irrigationditch_code <= 0:
            raise exceptions.ValidationError(_('The irrigation ditch code '
                                               'must be a positive value.'))

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        new_irrigationditch = super(WuaIrrigationditch, self).create(vals)
        if 'irrigationditch_code' in vals:
            correct_irrigationditch_code = \
                not self.exists_irrigationditch_code(
                    vals['irrigationditch_code'], new_irrigationditch.id)
            if not correct_irrigationditch_code:
                raise exceptions.UserError(_('The irrigation ditch '
                                             'code already exists.'))
        return new_irrigationditch

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        if 'irrigationditch_code' in vals:
            correct_irrigationditch_code = \
                not self.exists_irrigationditch_code(
                    vals['irrigationditch_code'], self.id)
            if not correct_irrigationditch_code:
                raise exceptions.UserError(_('The irrigation ditch code '
                                             'already exists.'))
        return super(WuaIrrigationditch, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.irrigationditch_code > 0:
                name = record.name + ' ' + \
                    '[' + str(record.irrigationditch_code) + ']'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIrrigationditch, self).fields_view_get(
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

    def exists_irrigationditch_code(self, irrigationditch_code, excluded_id):
        resp = False
        if irrigationditch_code > 0:
            irrigationditchs = self.env['wua.irrigationditch'].search([])
            for irrigationditch in irrigationditchs:
                if (irrigationditch.irrigationditch_code ==
                   irrigationditch_code and
                   excluded_id != irrigationditch.id):
                    resp = True
                    break
        return resp

    def get_wua_irrigationditch_parcels_action(self):
        current_irrigationditch_id = self.env.context.get('active_id')
        current_irrigationditch = self.browse(current_irrigationditch_id)
        if current_irrigationditch:
            parcel_ids = []
            parcel_irrigation_points = self.env['wua.parcel.irrigationpoint']
            for irrigationgate in current_irrigationditch.irrigationgate_ids:
                filtered_parcel_irrigation_points = \
                    parcel_irrigation_points.search(
                        [('irrigationgate_id', '=', irrigationgate.id)])
                for parcel_irrig_point in filtered_parcel_irrigation_points:
                    parcel_ids.append(parcel_irrig_point.parcel_id.id)
            condition = [('id', 'in', parcel_ids)]
            id_tree_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_tree').id
            id_form_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_form').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Parcels'),
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'domain': condition,
                'target': 'current',
                'context': self.env.context,
                }
            return act_window

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
