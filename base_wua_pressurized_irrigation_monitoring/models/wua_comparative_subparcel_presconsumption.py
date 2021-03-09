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
        ondelete='cascade',
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

    deviation_percentage = fields.Char(
        string='Deviation Percentage',
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
        string='Number total of drippers'
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

    age_category = fields.Selection([
        ('l', 'Little'),
        ('m', 'Middle'),
        ('b', 'Big')],
        'Age Category')

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
            deviation = record.real_consumption - record.estimated_consumption
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

    @api.depends('deviation')
    def _compute_consumption_category(self):
        percentage_categ_01 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_01')
        percentage_categ_02 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_02')
        for record in self:
            if (record.theoretical_consumption == 0 and
               record.real_consumption == 0):
                record.consumption_category = 'A'
            else:
                deviation = abs(record.deviation)
                consumption_category = 'C'
                deviation_percentage = 100
                if deviation > 0 and record.real_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.real_consumption
                    if (deviation_percentage <= percentage_categ_01):
                        consumption_category = 'A'
                    elif (deviation_percentage <= percentage_categ_02):
                        consumption_category = 'B'
                record.consumption_category = consumption_category

    @api.multi
    def _compute_deviation_percentage(self):
        for record in self:
            if (record.estimated_consumption == 0 and
               record.real_consumption == 0):
                record.deviation_percentage = '0%'
            else:
                deviation_percentage = 100
                is_negative = False
                deviation = record.deviation
                if deviation < 0:
                    deviation = abs(deviation)
                    is_negative = True
                if deviation > 0 and record.real_consumption > 0:
                    deviation_percentage = \
                        (deviation * 100) / record.real_consumption
                if is_negative:
                    deviation_percentage = deviation_percentage * -1
                record.deviation_percentage = \
                    '{:.2f}'.format(deviation_percentage) + '%'

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
        # Create comparative consumption.
        comparative_consumption = \
            super(WuaComparativeSubparcelPresconsumption, self).create(vals)
        # Get the real and theoretical consumptions.
        real_consumption = self.get_real_consumption(
            comparative_consumption.subparcel_id,
            comparative_consumption.controlperiod_id)
        if real_consumption:
            comparative_consumption.real_consumption = real_consumption
        theoretical_consumption = self.get_theoretical_consumption(
            comparative_consumption.subparcel_id,
            comparative_consumption.controlperiod_id)
        if theoretical_consumption:
            comparative_consumption.theoretical_consumption = \
                theoretical_consumption
        return comparative_consumption

    # Get the real consumption of a subparcel comparative-consumption.
    def get_real_consumption(self, subparcel, controlperiod):
        resp = 0
        if subparcel and controlperiod:
            controlpresconsumptions = controlperiod.controlpresconsumption_ids
            for controlpresconsumption in (controlpresconsumptions or []):
                waterconnection = controlpresconsumption.waterconnection_id
                if waterconnection.irrigationpoint_ids:
                    total_area = waterconnection.total_affected_area_official
                    for irrigationpoint in waterconnection.irrigationpoint_ids:
                        subparcels_of_irrigationpoint = \
                            irrigationpoint.parcel_id.subparcel_ids
                        if subparcel in subparcels_of_irrigationpoint:
                            prorrated_consumption = \
                                (controlpresconsumption.volume_real *
                                 (subparcel.area_official / total_area))
                            resp = resp + prorrated_consumption
        return resp

    # Get the theoretical consumption of a subparcel comparative-consumption.
    def get_theoretical_consumption(self, subparcel, controlperiod):
        resp = 0
        if (subparcel and controlperiod and
           subparcel.cultivation_id and subparcel.cultivation_id.monitoring):
            et0 = controlperiod.et0_value
            pe = controlperiod.pe_value
            number_of_period = self.get_number_of_period(controlperiod)
            row_kc = self.env['wua.cultivation.kc'].search(
                [('period_number', '=', number_of_period),
                 ('cultivation_id', '=', subparcel.cultivation_id.id)])
            if row_kc:
                row_kc = row_kc[0]
                kc = row_kc.kc_middle
                if subparcel.age_category == 'm':
                    kc = row_kc.kc_middle
                else:
                    if subparcel.age_category == 'b':
                        kc = row_kc.kc_big
                uniformity_irrig_applic = \
                    self.env['ir.values'].get_default(
                        'wua.monitoring.configuration',
                        'uniformity_irrigation_application')
                if not uniformity_irrig_applic:
                    uniformity_irrig_applic = 0.9
                resp = (10 * subparcel.area_official_hec *
                        (((et0 * kc) - pe) / uniformity_irrig_applic))
                if resp < 0:
                    resp = 0
        return resp

    # Get the number of period of a control period.
    def get_number_of_period(self, controlperiod):
        resp = 1
        control_periodicity = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'control_periodicity')
        if not control_periodicity:
            control_periodicity = 's'
        if control_periodicity == 's' or control_periodicity == 'b':
            year = int(controlperiod.initial_date[0:4])
            month = int(controlperiod.initial_date[5:7])
            day = int(controlperiod.initial_date[8:10])
            first_day_of_year = datetime.date(year, 1, 1)
            first_monday = first_day_of_year
            weekday_of_first_day_of_year = first_day_of_year.weekday()
            if weekday_of_first_day_of_year != 0:
                first_monday = first_day_of_year + \
                    datetime.timedelta(days=7-weekday_of_first_day_of_year)
            first_day_of_controlperiod = datetime.date(year, month, day)
            current_monday = first_monday
            resp = 1
            while current_monday < first_day_of_controlperiod:
                current_monday = current_monday + datetime.timedelta(days=7)
                resp = resp + 1
            if control_periodicity == 'b':
                is_odd = (resp % 2 != 0)
                resp = int(resp / 2)
                if is_odd:
                    resp = resp + 1
        else:
            resp = int(controlperiod.initial_date[5:7])
        return resp

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
