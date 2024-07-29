# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import io
import base64
from lxml import etree, html
from xml.etree import ElementTree
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    @api.model
    def create(self, vals):
        new_parcel = super(WuaParcel, self).create(vals)
        for subparcel in (new_parcel.subparcel_ids or []):
            subparcel.regenerate_comparative_consumptions()
        return new_parcel

    def get_wua_parcel_comparative_presconsumption_action(self):
        current_parcel_id = self.env.context.get('active_id')
        condition = [('parcel_id', '=', current_parcel_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_parcel_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_parcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.comparative.parcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window


class WuaParcelSubparcel(models.Model):
    _inherit = 'wua.parcel.subparcel'

    shaded_percentage = fields.Float(
        string='Shaded %',
        digits=(32, 2)
    )

    soil_type = fields.Selection([
        ('loamy', 'Loamy'),
        ('clayey', 'Clayey'),
        ('silty', 'Silty'),
        ('sandy', 'Sandy'),
        ('loam_clayey', 'Loam-Clayey'),
        ('loam_silty', 'Loam-Silty'),
        ('loam_sandy', 'Loam-Sandy'),
        ],
        string='Soil Type',
    )

    soiltype_id = fields.Many2one(
        comodel_name='wua.soiltype',
        string='Soil Type',
        index=True,
    )

    minimum_irrigation_dose = fields.Float(
        string='Minimum Irrigation Dose (m³)',
        digits=(32, 4),
        compute='_compute_minimum_irrigation_dose',
    )

    minimum_irrigation_dose_manual = fields.Float(
        string='Minimum Irrigation Dose Manual (m³)',
        digits=(32, 4),
        required=True,
        default=0,
    )

    irrigation_flow = fields.Float(
        string='Irrigation Flow (m³/h)',
        digits=(32, 4),
        compute='_compute_irrigation_flow',
    )

    irrigation_flow_manual = fields.Float(
        string='Manual Irrigation Flow (m³/h)',
        digits=(32, 4),
        required=True,
        default=0,
    )

    organic_material_percentage = fields.Float(
        string='Organic Material %',
        digits=(32, 2)
    )

    orientation = fields.Integer(
        string='Orientation',
        help='Value between 0 and 359º (0 corresponds to geographic north)'
    )

    drippers_number = fields.Integer(
        string='Number total of drippers',
        store=True,
        compute='_compute_drippers_number'
    )

    drippers_nominal_flow = fields.Float(
        string='Drip. Nom. Flow (l/h)',
        digits=(32, 2)
    )

    tree_lateral_number = fields.Integer(
        string='N. of lateral/tree'
    )

    plantation_year = fields.Integer(
        string='Plantation Year',
    )

    cultivation_age = fields.Integer(
        string='Cultivation Age',
        compute='_compute_cultivation_age',
        search='_search_cultivation_age'
    )

    age_category = fields.Selection([
        ('l', 'Little'),
        ('m', 'Middle'),
        ('b', 'Full production')],
        'Age Category',
        compute='_compute_age_category',
        search='_search_age_category')

    tree_distance = fields.Float(
        string='M. between trees',
        digits=(32, 2)
    )

    row_distance = fields.Float(
        string='M. between rows',
        digits=(32, 2)
    )

    number_of_trees = fields.Integer(
        string='N. of trees',
        store=True,
        compute='_compute_number_of_trees'
    )

    plantation_density = fields.Float(
        string='Density (trees/ha)',
        store=True,
        compute='_compute_plantation_density'
    )

    tree_drippers_number = fields.Integer(
        string='N. of drippers/tree',
    )

    notes = fields.Html(
        string='Notes'
    )

    aerial_img = fields.Binary(
        string="Aerial Image",
        readonly=True,
        attachment=True)

    aerial_img_scale = fields.Integer(
        string='Scale',
        readonly=True)

    aerial_img_date = fields.Date(
        string='Date of aerial image')

    aerial_img_accuracy = fields.Float(
        string='Accuracy (m/px)',
        digits=(32, 2),
        default=0)

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        compute='_compute_cadastral_reference',
        store=True
    )

    cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_cadastral_reference_link',
        store=True
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link'
    )

    updated_in_remotecontrol = fields.Boolean(
        string='Updated in Remote Control',
        compute='_compute_updated_in_telecontrol'
    )

    subparcel_modified = fields.Boolean(
        string='Modified',
        default=False,
    )

    subparcel_presconsumption_ids = fields.One2many(
        string="Comparative Subparcel Presconsumption",
        comodel_name="wua.comparative.subparcel.presconsumption",
        inverse_name="subparcel_id"
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4),
        compute='_compute_estimated_consumption',
        store=True
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4),
        compute='_compute_real_consumption',
        store=True
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True
    )

    deviation_percentage = fields.Char(
        string='Deviation Percentage',
        compute='_compute_deviation_percentage',
    )

    consumption_category = fields.Selection([
        ('A', 'A (correct irrigation)'),
        ('B', 'B (acceptable irrigation)'),
        ('C', 'C (unsatisfactory irrigation)'),
        ],
        string='Consumption Category',
        compute='_compute_consumption_category',
    )

    _sql_constraints = [
        ('valid_shaded_percentage',
         'CHECK (shaded_percentage >= 0 and shaded_percentage <= 100)',
         'The shaded percentage must be a value from 0 to 100.'),
        ('valid_organic_material_percentage',
         'CHECK (organic_material_percentage >= 0 and '
         'organic_material_percentage <= 100)',
         'The organic material percentage must be a value from 0 to 100.'),
        ('valid_orientation',
         'CHECK (orientation >= 0 and orientation <= 360)',
         'The orientation must be a value between 0 and 360 degrees.'),
        ('valid_drippers_number',
         'CHECK (drippers_number >= 0)',
         'The number of drippers cannot be a negative value.'),
        ('valid_drippers_nominal_flow',
         'CHECK (drippers_nominal_flow >= 0)',
         'The drippers nominal-flow cannot be a negative value.'),
        ('valid_plantation_year',
         'CHECK (plantation_year >= 0)',
         'The plantation year cannot be a negative value.'),
        ('valid_tree_distance',
         'CHECK (tree_distance >= 0)',
         'The distance between trees cannot be a negative value.'),
        ('valid_row_distance',
         'CHECK (row_distance >= 0)',
         'The distance between rows cannot be a negative value.'),
        ('valid_irrigation_flow_manual',
         'CHECK (irrigation_flow_manual >= 0)',
         'The manual irrigation flow cannot be a negative value.'),
        ('valid_minimum_irrigation_dose_manual',
         'CHECK (minimum_irrigation_dose_manual >= 0)',
         'The minimal irrigation dose cannot be a negative value.'),
        ]

    @api.multi
    def _compute_cultivation_age(self):
        for record in self:
            cultivation_age = 0
            if record.plantation_year:
                current_year = int(datetime.date.today().strftime("%Y"))
                cultivation_age = current_year - record.plantation_year
            record.cultivation_age = cultivation_age

    @api.multi
    def _compute_age_category(self):
        for record in self:
            age_category = 'l'
            if record.plantation_year and record.cultivation_id:
                lower_age_middle = record.cultivation_id.lower_age_middle
                upper_age_middle = record.cultivation_id.upper_age_middle
                if lower_age_middle or upper_age_middle:
                    current_year = int(datetime.date.today().strftime("%Y"))
                    cultivation_age = current_year - record.plantation_year
                    if (cultivation_age >= lower_age_middle and
                       cultivation_age <= upper_age_middle):
                        age_category = 'm'
                    else:
                        if cultivation_age > upper_age_middle:
                            age_category = 'b'
            record.age_category = age_category

    @api.multi
    def _compute_minimum_irrigation_dose(self):
        model_values = self.env['ir.values'].sudo()
        model_irrigationdose = self.env['wua.irrigationdose'].sudo()
        factor = 1
        area_measurement_type = model_values.get_default(
            'wua.configuration', 'area_measurement_type')
        if (area_measurement_type == 1):
            area_measurement_equivalence = model_values.get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if (area_measurement_equivalence > 0):
                factor = area_measurement_equivalence
        for record in self:
            minimum_irrigation_dose_of_subparcel = 0
            if (record.minimum_irrigation_dose_manual > 0):
                minimum_irrigation_dose_of_subparcel = record.\
                    minimum_irrigation_dose_manual
            else:
                minimum_irrigation_dose_of_cultivation = 0
                cultivation = record.cultivation_id
                soiltype = record.soiltype_id
                age_category = record.age_category
                if (cultivation and soiltype and age_category):
                    record_of_mid_of_cultivation = model_irrigationdose.search(
                        [('cultivation_id', '=', cultivation.id),
                         ('soiltype_id', '=', soiltype.id),
                         ('age_category', '=', age_category)]
                    )
                    if (record_of_mid_of_cultivation):
                        minimum_irrigation_dose_of_cultivation = \
                            record_of_mid_of_cultivation[0].\
                            minimum_irrigation_dose
                if (minimum_irrigation_dose_of_cultivation > 0):
                    minimum_irrigation_dose_of_subparcel = \
                        minimum_irrigation_dose_of_cultivation * 10 * \
                        record.area_official * factor
            record.minimum_irrigation_dose = \
                minimum_irrigation_dose_of_subparcel

    @api.multi
    def _compute_irrigation_flow(self):
        for record in self:
            irrigation_flow = 0.0
            if record.irrigation_flow_manual > 0:
                irrigation_flow = record.irrigation_flow_manual
            elif (record.drippers_nominal_flow and record.drippers_number):
                irrigation_flow = (record.drippers_nominal_flow / 1000) * \
                    record.drippers_number
            record.irrigation_flow = irrigation_flow

    @api.depends('area_official_hec', 'tree_distance', 'row_distance')
    def _compute_number_of_trees(self):
        for record in self:
            number_of_trees = 0
            if (record.area_official_hec and record.tree_distance and
               record.row_distance):
                area_m2 = record.area_official_hec * 10000
                tree_distance = record.tree_distance
                row_distance = record.row_distance
                number_of_trees = area_m2 / (tree_distance * row_distance)
            record.number_of_trees = number_of_trees

    @api.depends('number_of_trees', 'area_official_hec')
    def _compute_plantation_density(self):
        for record in self:
            plantation_density = 0
            if record.area_official_hec:
                area_ha = record.area_official_hec
                number_of_trees = record.number_of_trees
                plantation_density = number_of_trees / area_ha
            record.plantation_density = plantation_density

    @api.depends('number_of_trees', 'tree_drippers_number')
    def _compute_drippers_number(self):
        for record in self:
            drippers_number = 0
            if record.number_of_trees and record.tree_drippers_number:
                number_of_trees = record.number_of_trees
                tree_drippers_number = record.tree_drippers_number
                drippers_number = number_of_trees * tree_drippers_number
            record.drippers_number = drippers_number

    @api.depends('parcel_id', 'parcel_id.cadastral_reference_link')
    def _compute_cadastral_reference_link(self):
        for record in self:
            cadastral_reference_link = None
            if record.parcel_id.cadastral_reference_link:
                cadastral_reference_link = \
                    record.parcel_id.cadastral_reference_link
            record.cadastral_reference_link = cadastral_reference_link

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.estimated_consumption')
    def _compute_estimated_consumption(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
        for record in self:
            estimated_consum = 0
            if (record.subparcel_presconsumption_ids and
               active_agriculturalseason):
                filtered_subparcel_presconsumption_ids = filter(
                    lambda x: x['agriculturalseason_id'] ==
                    active_agriculturalseason,
                    record.subparcel_presconsumption_ids)
                if filtered_subparcel_presconsumption_ids:
                    for sub_presc in filtered_subparcel_presconsumption_ids:
                        estimated_consum += sub_presc.estimated_consumption
            record.estimated_consumption = estimated_consum

    @api.depends('subparcel_presconsumption_ids',
                 'subparcel_presconsumption_ids.real_consumption')
    def _compute_real_consumption(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
        for record in self:
            real_consumption = 0
            if (record.subparcel_presconsumption_ids and
               active_agriculturalseason):
                filtered_subparcel_presconsumption_ids = filter(
                    lambda x: x['agriculturalseason_id'] ==
                    active_agriculturalseason,
                    record.subparcel_presconsumption_ids)
                if filtered_subparcel_presconsumption_ids:
                    for sub_presc in filtered_subparcel_presconsumption_ids:
                        real_consumption += sub_presc.real_consumption
            record.real_consumption = real_consumption

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.real_consumption - record.estimated_consumption
            record.deviation = deviation

    @api.multi
    def _compute_deviation_percentage(self):
        for record in self:
            if record.estimated_consumption == 0 and \
                    record.real_consumption == 0:
                record.deviation_percentage = '0%'
            else:
                deviation_percentage = 100
                is_negative = False
                deviation = record.deviation
                if deviation < 0:
                    deviation = abs(deviation)
                    is_negative = True
                if deviation > 0 and record.estimated_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.estimated_consumption
                if is_negative:
                    deviation_percentage = deviation_percentage * -1
                record.deviation_percentage = \
                    '{:.2f}'.format(deviation_percentage) + '%'

    @api.multi
    def _compute_consumption_category(self):
        percentage_categ_01 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_01')
        percentage_categ_02 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_02')
        for record in self:
            if record.estimated_consumption == 0 and \
                    record.real_consumption == 0:
                record.consumption_category = ''
            else:
                deviation = abs(record.deviation)
                consumption_category = 'C'
                deviation_percentage = 100
                if deviation > 0 and record.estimated_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.estimated_consumption
                    if (deviation_percentage <= percentage_categ_01):
                        consumption_category = 'A'
                    elif (deviation_percentage <= percentage_categ_02):
                        consumption_category = 'B'
                record.consumption_category = consumption_category

    @api.multi
    def action_regenerate_comparative_consumptions(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
            cp_model = self.env['wua.controlperiod']
            controlperiods = cp_model.search(
                [('agriculturalseason_id', '=', active_agriculturalseason.id)])
            for controlperiod in (controlperiods or []):
                cp_model.regenerate_comparative_consumptions_of_controlperiod(
                    controlperiod)

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        subparcel_param = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'url_gis_viewer_subparcel_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                if subparcel_param:
                    url_for_record = url_for_record + sep_char + \
                        subparcel_param + '=' + str(record.subparcel_code)
                elif parcel_param:
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + str(record.parcel_id.name)
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if (cipher_text):
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.depends('parcel_id', 'parcel_id.cadastral_reference')
    def _compute_cadastral_reference(self):
        for record in self:
            cadastral_reference = None
            if record.parcel_id.cadastral_reference:
                cadastral_reference = record.parcel_id.cadastral_reference
            record.cadastral_reference = cadastral_reference

    @api.depends('parcel_id', 'parcel_id.updated_in_remotecontrol')
    def _compute_updated_in_telecontrol(self):
        for record in self:
            updated_in_remotecontrol = None
            if record.parcel_id.updated_in_remotecontrol:
                updated_in_remotecontrol = \
                    record.parcel_id.updated_in_remotecontrol
            record.updated_in_remotecontrol = updated_in_remotecontrol

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_see_cadastral_report(self):
        self.ensure_one()
        if self.cadastral_reference_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.cadastral_reference_link,
                'target': 'new',
            }

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            subparcel_modified = (('area_official' in vals or
                                   'plantation_year' in vals) and
                                  self.cultivation_id and
                                  self.cultivation_id.monitoring)
            if subparcel_modified:
                vals['subparcel_modified'] = True
            resp = super(WuaParcelSubparcel, self).write(vals)
        else:
            resp = super(WuaParcelSubparcel, self).write(vals)
        return resp

    def regenerate_comparative_consumptions(self):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if (len(active_agriculturalseason) == 1):
            for record in self:
                cmp_subp_presc = \
                    self.env['wua.comparative.subparcel.presconsumption']
                cmp_pres_of_subparcel = cmp_subp_presc.search(
                    ['&', ('agriculturalseason_id', '=',
                           active_agriculturalseason.id),
                     ('subparcel_id', '=', record.id)])
                if cmp_pres_of_subparcel:
                    cmp_pres_of_subparcel.unlink()
                if record.cultivation_id and record.cultivation_id.monitoring:
                    for controlperiod in active_agriculturalseason.\
                            controlperiod_ids:
                        cmp_subp_presc.create({
                            'subparcel_id': record.id,
                            'parcel_id': record.parcel_id.id,
                            'cadastral_reference':
                                record.parcel_id.cadastral_reference,
                            'area_perc': record.area_perc,
                            'irrigationsystem_id':
                                record.irrigationsystem_id.id,
                            'tree_distance': record.tree_distance,
                            'tree_drippers_number':
                                record.tree_drippers_number,
                            'tree_lateral_number': record.tree_lateral_number,
                            'row_distance': record.row_distance,
                            'controlperiod_id': controlperiod.id,
                            'partner_id': record.partner_id.id,
                            'hydraulicsector_id': record.hydraulicsector_id.id,
                            'cultivation_id': record.cultivation_id.id,
                            'cultivationvariety_id':
                                record.cultivationvariety_id.id,
                            'area_official': record.area_official,
                            'productionmethod_id':
                                record.productionmethod_id.id,
                            'shaded_percentage': record.shaded_percentage,
                            'soil_type': record.soil_type,
                            'soiltype_id': record.soiltype_id.id,
                            'organic_material_percentage':
                                record.organic_material_percentage,
                            'orientation': record.orientation,
                            'drippers_number': record.drippers_number,
                            'drippers_nominal_flow':
                                record.drippers_nominal_flow,
                            'plantation_year': record.plantation_year,
                            'number_of_trees': record.number_of_trees,
                            'plantation_density': record.plantation_density,
                            'irrigation_flow': record.irrigation_flow
                            })
                    record.subparcel_modified = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def action_regenerate_aerial_img(self):
        subparcels = self.env['wua.parcel.subparcel'].search([])
        subparcels.regenerate_aerial_img()

    def get_sld_body(self):
        body = ''
        body = body + '<?xml version="1.0" encoding="UTF-8"?>' +\
            '<StyledLayerDescriptor version="1.0.0" ' + \
            'xmlns="http://www.opengis.net/sld" xmlns:ogc="' +\
            'http://www.opengis.net/ogc" xmlns:xlink="' +\
            'http://www.w3.org/1999/xlink" xmlns:xsi="' +\
            'http://www.w3.org/2001/XMLSchema-instance"' +\
            'xsi:schemaLocation="http://www.opengis.net/sld ' +\
            'http://schemas.opengis.net/sld/1.0.0/StyledLaye' +\
            'rDescriptor.xsd">' +\
            '<NamedLayer><Name>subparcel</Name>' +\
            '<UserStyle><Title>xxx</Title><FeatureTypeStyle>' +\
            '<Rule><Filter><PropertyIsLike ' +\
            'wildCard="*" singleChar="." escape="!"><Property' +\
            'Name>subp_code</PropertyName><Literal>' + self.subparcel_code +\
            '</Literal></PropertyIsLike></Filter>' +\
            '<PolygonSymbolizer>' +\
            '<Stroke>' +\
            '<CssParameter name="stroke">#000000</CssParameter>' +\
            '<CssParameter name="stroke-width">14</CssParameter>' +\
            '<CssParameter name="stroke-linecap">round</CssParameter>' +\
            '</Stroke>' +\
            '</PolygonSymbolizer>' +\
            '</Rule></FeatureTypeStyle>' +\
            '</UserStyle></NamedLayer>' +\
            '<NamedLayer><Name>subparcel_perimeter</Name>' +\
            '<UserStyle><Title>xxx2</Title><FeatureTypeStyle>' +\
            '<Rule><Filter><PropertyIsLike ' +\
            'wildCard="*" singleChar="." escape="!"><Property' +\
            'Name>subp_code</PropertyName><Literal>' + self.subparcel_code +\
            '</Literal></PropertyIsLike></Filter>' +\
            '<PolygonSymbolizer>' +\
            '<Stroke>' +\
            '<CssParameter name="stroke">#ffffff</CssParameter>' +\
            '<CssParameter name="stroke-width">5</CssParameter>' +\
            '<CssParameter name="stroke-linecap">round</CssParameter>' +\
            '</Stroke>' +\
            '</PolygonSymbolizer>' +\
            '</Rule></FeatureTypeStyle>' +\
            '</UserStyle></NamedLayer>' +\
            '</StyledLayerDescriptor>'
        return body

    # Get a fraction of base closest to the target number
    def getClosestDiv(self, base, target):
        div = base
        result = div
        while div > target:
            result = div
            div = div / 2.0
        return result

    def getClosestMul(self, base, target):
        mul = base
        result = mul
        while mul < target:
            mul = mul * 2.0
            result = mul
        return result

    def regenerate_aerial_img(self):
        url_gis_viewer_wms = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wms')
        url_gis_viewer_wfs = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wfs')
        if (not url_gis_viewer_wms or not url_gis_viewer_wfs):
            raise exceptions.UserError(_('The "URL GIS Viewer WMS" parameter '
                                         'or "URL GIS Viewer WFS" are not '
                                         'populated.'))
        else:
            mapserver_dpi = 90
            wms = WebMapService(url=url_gis_viewer_wms, version='1.1.1')
            wfs = WebFeatureService(url=url_gis_viewer_wfs, version='1.1.0')
            wms_pnoa = WebMapService(url='http://www.ign.es/wms-inspire/'
                                         'pnoa-ma', version='1.1.1')
            for record in self:
                filterxml = '<Filter><PropertyIsEqualTo><ValueReference' +\
                    '>subp_code</ValueReference><Literal>' + \
                    record.subparcel_code + \
                    '</Literal></PropertyIsEqualTo></Filter>'
                sld_body = record.get_sld_body()
                try:
                    response = wfs.getfeature(typename='fes:subparcel',
                                              filter=filterxml)
                    parsed_response = ElementTree.fromstring(
                        response.getvalue())
                    ns = parsed_response[0].tag.split('}')[0] + '}'
                    parcel_member = parsed_response.find(ns + 'boundedBy')
                    parcel_envelop = parcel_member[0]
                    crs = parcel_envelop.attrib['srsName']
                    lowerCorner = [float(n) for n in (parcel_envelop.find(
                        ns + 'lowerCorner').text).split(' ')]
                    upperCorner = [float(n) for n in (parcel_envelop.find(
                        ns + 'upperCorner').text).split(' ')]
                    width = int(upperCorner[0] - lowerCorner[0])
                    height = int(upperCorner[1] - lowerCorner[1])
                    max_width = 824
                    max_height = 824
                    if (width > max_width or height > max_height):
                        increment = (int(self.getClosestMul(
                            max_width, max(height, width))))
                        incrementX = (increment - width)/2
                        incrementY = (increment - height)/2
                        lowerCorner[0] = lowerCorner[0] - incrementX
                        upperCorner[0] = upperCorner[0] + incrementX
                        lowerCorner[1] = lowerCorner[1] - incrementY
                        upperCorner[1] = upperCorner[1] + incrementY
                    elif (width < max_width or height < max_height):
                        increment = int(self.getClosestDiv(
                            max_width, max(height, width)))
                        incrementX = (increment - width)/2
                        incrementY = (increment - height)/2
                        lowerCorner[0] = lowerCorner[0] - incrementX
                        upperCorner[0] = upperCorner[0] + incrementX
                        lowerCorner[1] = lowerCorner[1] - incrementY
                        upperCorner[1] = upperCorner[1] + incrementY
                    width = max_width
                    height = max_height
                    bbox = ((int(lowerCorner[0])), (int(lowerCorner[1])),
                            (int(upperCorner[0])), (int(upperCorner[1])))
                    data_pnoa = wms_pnoa.getfeatureinfo(
                        layers=['OI.MosaicElement'],
                        srs=crs, bbox=bbox, size=(width, height),
                        format='image/jpeg', info_format='text/html',
                        xy=(width/2, height/2))
                    data_pnoa_parsed = html.fromstring(
                        data_pnoa.read())
                    data_pnoa_info_rows = data_pnoa_parsed.find('body').\
                        find('table').findall('tr')
                    date = data_pnoa_info_rows[0].findall('td')[1].text
                    date = datetime.datetime.strptime(date, '%Y-%m')
                    resolution = data_pnoa_info_rows[1].findall('td')[1].\
                        text
                    img = wms.getmap(layers=['pnoa', 'subparcel',
                                             'subparcel_perimeter',
                                             'n_arrow'],
                                     styles=['default', 'default',
                                             'default', 'default'],
                                     srs=crs, bbox=bbox, size=(width, height),
                                     format='image/jpeg', transparent=True,
                                     SLD_BODY=sld_body)
                    image = io.BytesIO(img.read())
                    base64_img = base64.b64encode(image.getvalue())
                    # GET SCALE:
                    # With BBOX get meters in the real world
                    width_in_real_meters = bbox[2] - bbox[0]
                    # With pixels Width and dpi get the size of the image
                    width_in_image_meters = (width / mapserver_dpi) * \
                        0.0254
                    aerial_img_scale = width_in_real_meters /\
                        width_in_image_meters
                    record.write({'aerial_img': base64_img,
                                  'aerial_img_scale': aerial_img_scale,
                                  'aerial_img_accuracy': resolution,
                                  'aerial_img_date': date})
                except Exception:
                    pass

    def _search_cultivation_age(self, operator, value):
        current_year = int(datetime.date.today().strftime("%Y"))
        new_operator = operator
        if operator == '>':
            new_operator = '<'
        elif operator == '>=':
            new_operator = '<='
        elif operator == '<':
            new_operator = '>'
        elif operator == '<=':
            new_operator = '>='
        subparcels = self.env['wua.parcel.subparcel'].search(
            [('plantation_year', '!=', 0),
             ('plantation_year', new_operator, current_year - value)])
        return ([('id', 'in', [x.id for x in subparcels])])

    def _search_age_category(self, operator, value):
        subparcel_ids = []
        operator_of_filter = 'in'
        if (not value):
            # Case #1: subparcels without age category (it is not possible).
            # Case #2: subparcels with age category (all).
            if operator == '!=':
                subparcel_ids = self.env['wua.parcel.subparcel'].search([]).ids
        else:
            # Remaining cases: there is a age category to compare...
            # Case #3, age category is "little" (l): there is not a
            # cultivation, or the "plantation_year" field is empty, or
            # the age cultivation is smaller than the "lower_age_middle"
            # field (of the cultivation).
            # Case #4, age category is "middle" (m): the age cultivation
            # is greather or equal than "lower_age_middle" and it is
            # smaller or equal than "upper_age_middle" (of the cultivation).
            # Case #5, age category is "big" (m): the age cultivation
            # is greather than "upper_age_middle" (of the cultivation).
            subparcel_ids = self.get_subparcel_ids_of_category(value)
            if operator == '!=':
                operator_of_filter = 'not in'
        return ([('id', operator_of_filter, subparcel_ids)])

    def get_subparcel_ids_of_category(self, age_category):
        resp = []
        if age_category in ['l', 'm', 'b']:
            sql_for_litte = """
                select s.id from wua_parcel_subparcel s
                inner join wua_cultivation c
                on s.cultivation_id = c.id
                where date_part('year', CURRENT_DATE) -
                (case when s.plantation_year=0 or s.plantation_year is null
                then date_part('year', CURRENT_DATE) else s.plantation_year
                end) < c.lower_age_middle order by id;"""
            sql_for_middle = """
                select s.id from wua_parcel_subparcel s
                inner join wua_cultivation c
                on s.cultivation_id = c.id
                where date_part('year', CURRENT_DATE) -
                (case when s.plantation_year=0 or s.plantation_year is null
                then date_part('year', CURRENT_DATE) else s.plantation_year
                end) >= c.lower_age_middle and
                date_part('year', CURRENT_DATE) -
                (case when s.plantation_year=0 or s.plantation_year is null
                then date_part('year', CURRENT_DATE) else s.plantation_year
                end) <= c.upper_age_middle order by id;"""
            sql_for_big = """
                select s.id from wua_parcel_subparcel s
                inner join wua_cultivation c
                on s.cultivation_id = c.id
                where date_part('year', CURRENT_DATE) -
                (case when s.plantation_year=0 or s.plantation_year is null
                then date_part('year', CURRENT_DATE) else s.plantation_year
                end) > c.upper_age_middle order by id;"""
            sql_statement = sql_for_litte
            if age_category == 'm':
                sql_statement = sql_for_middle
            else:
                if age_category == 'b':
                    sql_statement = sql_for_big
            self.env.cr.execute(sql_statement)
            sql_resp = self.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    resp.append(item[0])
        return resp

    def get_wua_subparcel_comparative_presconsumption_action(self):
        current_subparcel_id = self.env.context.get('active_id')
        condition = [('subparcel_id', '=', current_subparcel_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_tree').id
        id_form_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_form').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_subparcel_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Subparcels'),
            'res_model': 'wua.comparative.subparcel.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(WuaParcelSubparcel, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            unit = _('(m³/agriculturalseason)')
            for node in doc.xpath("//field[@name='estimated_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.estimated_consumption.string)
                node.set('string', original_label + ' ' + unit)
            for node in doc.xpath("//field[@name='real_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.real_consumption.string)
                node.set('string', original_label + ' ' + unit)
            for node in doc.xpath("//field[@name='deviation']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.deviation.string)
                node.set('string', original_label + ' ' + unit)
            res['arch'] = etree.tostring(doc)
        return res
