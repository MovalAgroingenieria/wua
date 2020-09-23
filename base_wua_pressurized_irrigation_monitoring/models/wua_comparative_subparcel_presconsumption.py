# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import datetime
import locale
from Crypto.Cipher import AES
import pytz


class WuaComparativeSubparcelPresconsumption(models.Model):
    _name = 'wua.comparative.subparcel.presconsumption'
    _description = 'Comparative Subparcel Presconsumption'
    _order = 'name'

    MAX_SIZE_SUBPARCEL_CODE = 25
    MAX_SIZE_NAME = 11 + MAX_SIZE_SUBPARCEL_CODE

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        index=True,
    )

    subparcel_id = fields.Many2one(
        string='Subparcel Code',
        comodel_name='wua.parcel.subparcel',
        required=True,
        index=True,
        ondelete='restrict',
    )

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
        required=True,
        index=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Subparcel Comparative-Consumption',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id'
    )

    theoretical_consumption = fields.Float(
        string='Theoretical Consumption',
        digits=(32, 4),
        default=0
    )

    regularization = fields.Float(
        string='Regularization',
        digits=(32, 4),
        default=0
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
        default=0
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
        compute='_compute_deviation',
        store=True,
    )

    deviation_percentage = fields.Float(
        string='Deviation Percentage',
        digits=(32, 2),
        compute='_compute_deviation_percentage',
    )

    notes = fields.Html(
        string='Notes'
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict'
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict'
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        required=True,
        ondelete='restrict'
    )

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        ondelete='restrict'
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0
    )

    area_perc = fields.Float(
        string='Parcel %',
        digits=(5, 2),
    )

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        ondelete='restrict'
    )

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
    )

    cadastral_reference = fields.Char(
        string='Cadastral Reference'
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

    tree_development = fields.Selection([
        ('seedlings', 'Seedlings'),
        ('intermediate', 'Intermediate'),
        ('full_production', 'Full production')],
        string='Tree Development'
    )

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
        string='Soil Type'
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
        string='Number of drippers'
    )

    drippers_nominal_flow = fields.Float(
        string='Drip. Nom. Flow (l/h)',
        digits=(32, 2)
    )

    tree_lateral_number = fields.Integer(
        string='N. of lateral/tree',
    )

    plantation_year = fields.Integer(
        string='Plantation Year'
    )

    cultivation_age = fields.Integer(
        string='Cultivation Age'
    )

    tree_distance = fields.Float(
        string='M. between trees',
        digits=(32, 2),
    )

    row_distance = fields.Float(
        string='M. between rows',
        digits=(32, 2),
    )

    tree_drippers_number = fields.Integer(
        string='N. of drippers/tree',
    )

    consumption_category = fields.Selection([
        ('A', 'A (correct irrigation)'),
        ('B', 'B (acceptable irrigation)'),
        ('C', 'C (unsatisfactory irrigation)'),
        ],
        string='Consumption Category',
        compute='_compute_consumption_category',
        store=True
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Subparcel Comparative-Consumption.'),
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
        ('valid_tree_lateral_number',
         'CHECK (tree_lateral_number >= 0 and tree_lateral_number <= 2)',
         'The \"N. of lateral/tree\" value must be 1 or 2.'),
        ('valid_tree_distance',
         'CHECK (tree_distance >= 0)',
         'The distance between trees cannot be a negative value.'),
        ('valid_row_distance',
         'CHECK (row_distance >= 0)',
         'The distance between rows cannot be a negative value.'),
        ('valid_tree_drippers_number',
         'CHECK (tree_drippers_number >= 0 and tree_drippers_number <= 2)',
         'The \"N. of drippers/tree\" value must be 1 or 2.'),
        ]

    @api.depends('partner_id', 'partner_id.partner_code',
                 'controlperiod_id', 'controlperiod_id.initial_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.controlperiod_id and record.partner_id):
                name = record.controlperiod_id.initial_date + '-' + \
                    str(record.subparcel_id.subparcel_code)
            record.name = name

    @api.depends('theoretical_consumption', 'regularization')
    def _compute_estimated_consumption(self):
        for record in self:
            record.estimated_consumption = \
                record.theoretical_consumption + record.regularization

    @api.depends('estimated_consumption', 'real_consumption')
    def _compute_deviation(self):
        for record in self:
            deviation = record.estimated_consumption - record.real_consumption
            record.deviation = deviation

    @api.depends('controlperiod_id', 'controlperiod_id.agriculturalseason_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if (record.controlperiod_id):
                agriculturalseason_id = \
                    record.controlperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('parcel_id', 'parcel_id.cadastral_reference_link')
    def _compute_cadastral_reference_link(self):
        for record in self:
            cadastral_reference_link = None
            if record.parcel_id.cadastral_reference_link:
                cadastral_reference_link = \
                    record.parcel_id.cadastral_reference_link
            record.cadastral_reference_link = cadastral_reference_link

    @api.depends('parcel_id', 'parcel_id.updated_in_remotecontrol')
    def _compute_updated_in_telecontrol(self):
        for record in self:
            updated_in_remotecontrol = None
            if record.parcel_id.updated_in_remotecontrol:
                updated_in_remotecontrol = \
                    record.parcel_id.updated_in_remotecontrol
            record.updated_in_remotecontrol = updated_in_remotecontrol

    @api.depends('deviation', 'real_consumption')
    def _compute_consumption_category(self):
        percentage_categ_01 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_01')
        percentage_categ_02 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_02')
        for record in self:
            deviation = abs(record.deviation)
            consumption_category = 'A'
            if (deviation != 0 and record.real_consumption > 0):
                deviation_percentage = (deviation * 100) / record.\
                    real_consumption
                if (deviation_percentage > percentage_categ_02):
                    consumption_category = 'C'
                elif (deviation_percentage > percentage_categ_01):
                    consumption_category = 'B'
            record.consumption_category = consumption_category

    @api.multi
    def _compute_deviation_percentage(self):
        for record in self:
            deviation_percentage = 0
            deviation = abs(record.deviation)
            if (deviation != 0 and record.real_consumption > 0):
                deviation_percentage = (deviation * 100) / record.\
                    real_consumption
            record.deviation_percentage = deviation_percentage

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        subparcel_param = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'url_gis_viewer_subparcel_param')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                if subparcel_param:
                    url_for_record = url_for_record + sep_char + \
                        subparcel_param + '=' + \
                        str(record.subparcel_id.subparcel_code)
                elif parcel_param:
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + \
                        str(record.parcel_id.name)
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                credentials = username + "-" + password
                credentials = credentials.ljust(32)
                current_datetime = pytz.utc.localize(datetime.datetime.now())
                current_datetime = current_datetime.astimezone(
                    pytz.timezone('Europe/Madrid'))
                current_datetime = str(current_datetime)[:16].replace(' ', 'T')
                minimum = int(current_datetime[14:])
                if minimum < 30:
                    minimum = '00'
                else:
                    minimum = '30'
                iv = current_datetime[:14] + minimum
                aes_encryptor = AES.new('hZj<?*aS9w.Rg)3"', AES.MODE_CBC, iv)
                cipher_text = aes_encryptor.encrypt(credentials)
                cipher_text = cipher_text.encode('base64')
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                url_for_record = url_for_record + sep_char + \
                    "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            subparcel_code = record.subparcel_id.subparcel_code
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.controlperiod_id.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.controlperiod_id.end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + end_date_str + \
                ', ' + subparcel_code
            result.append((record.id, name))
        return result

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

    @api.model
    def create(self, vals):
        cmp_pres = super(WuaComparativeSubparcelPresconsumption, self).\
            create(vals)
        if (cmp_pres.controlperiod_id.controlpresconsumption_ids):
            for ctrl_pres in \
                    cmp_pres.controlperiod_id.controlpresconsumption_ids:
                total_area = ctrl_pres.waterconnection_id.\
                    total_affected_area_official
                for ip in ctrl_pres.waterconnection_id.irrigationpoint_ids:
                    if (cmp_pres.subparcel_id in ip.parcel_id.subparcel_ids):
                        prorrated = ctrl_pres.volume_real * \
                            ((cmp_pres.subparcel_id.area_official)/total_area)
                        cmp_pres.real_consumption += prorrated
        return cmp_pres

    def get_wua_cmp_subp_presconsumption_control_presconsumptionaction(self):
        current_cmp_pres_id = self.env.context.get('active_id')
        current_cmp_pres = \
            self.env['wua.comparative.subparcel.presconsumption'].search(
                [('id', '=', current_cmp_pres_id)])
        waterconnections_ids = map(
            lambda x: x.waterconnection_id.id,
            current_cmp_pres.parcel_id.irrigationpoint_ids)
        condition = [('waterconnection_id', 'in', waterconnections_ids)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_tree').id
        id_form_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_form').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_controlpresconsumption_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Control Consumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': self.env.context,
            }
        return act_window
