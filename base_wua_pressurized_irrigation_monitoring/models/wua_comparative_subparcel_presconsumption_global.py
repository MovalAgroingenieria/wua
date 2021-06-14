# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from Crypto.Cipher import AES
from lxml import etree
from odoo import models, fields, api, _, tools


class WuaComparativeSubparcelPresconsumptionGlobal(models.Model):
    _name = 'wua.comparative.subparcel.presconsumption.global'
    _description = 'Comparative Subparcel Presconsumption Global'
    _auto = False
    _order = 'subparcel_id'

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
    )

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
    )

    subparcel_id = fields.Many2one(
        string='Subparcel Code',
        comodel_name='wua.parcel.subparcel',
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
    )

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4),
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4),
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4),
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
    )

    cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_cadastral_reference_link',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link'
    )

    def init(self):
        tools.drop_view_if_exists(
            self.env.cr, 'wua_comparative_subparcel_presconsumption_global')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW
            wua_comparative_subparcel_presconsumption_global AS (
            SELECT row_number() OVER () AS id, wcsp1.agriculturalseason_id,
            wcsp1.parcel_id, wcsp1.subparcel_id, wcsp1.hydraulicsector_id,
            wcsp1.partner_id, wcsp1.area_official, wcsp1.cultivation_id,
            wcsp1.cultivationvariety_id,
            SUM(wcsp1.estimated_consumption) AS
            estimated_consumption, SUM(wcsp1.real_consumption) AS
            real_consumption, SUM(wcsp1.deviation) AS deviation,
            CASE
             WHEN (
                    (SUM(wcsp1.real_consumption) = 0) AND
                    (SUM(wcsp1.estimated_consumption) = 0)
                ) THEN ''
             WHEN (
                    (SUM(wcsp1.estimated_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.estimated_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_01'
                     )
                    )
                ) THEN 'A'
             WHEN (
                    (SUM(wcsp1.estimated_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.estimated_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_02'
                     )
                    )
                ) THEN 'B'
             ELSE  'C'
            END AS consumption_category FROM
            wua_comparative_subparcel_presconsumption wcsp1 GROUP BY
            wcsp1.agriculturalseason_id,  wcsp1.parcel_id, wcsp1.subparcel_id,
            wcsp1.cultivation_id, wcsp1.cultivationvariety_id,
            wcsp1.hydraulicsector_id, wcsp1.partner_id, wcsp1.area_official)
            """)

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
    def _compute_cadastral_reference_link(self):
        for record in self:
            cadastral_reference_link = None
            if record.parcel_id.cadastral_reference_link:
                cadastral_reference_link = \
                    record.parcel_id.cadastral_reference_link
            record.cadastral_reference_link = cadastral_reference_link

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
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(WuaComparativeSubparcelPresconsumptionGlobal, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            control_periodicity = area_measure_name = ""
            doc = etree.XML(res['arch'])
            area_measure_name = \
                self.env['wua.parcel'].sudo()._compute_area_measurement_name()
            control_periodicity = _('(m³/agriculturalseason)')
            if view_type == 'form':
                for node in doc.xpath(
                        "//field[@name='theoretical_consumption']"):
                    original_label = self.env['wua.parcel'].sudo().\
                        get_value_from_translation(
                            'base_wua_pressurized_irrigation_monitoring',
                            self.__class__.theoretical_consumption.string)
                    node.set(
                        'string', original_label + ' ' + control_periodicity)
                for node in doc.xpath(
                        "//field[@name='regularization']"):
                    original_label = self.env['wua.parcel'].sudo().\
                        get_value_from_translation(
                            'base_wua_pressurized_irrigation_monitoring',
                            self.__class__.regularization.string)
                    node.set(
                        'string', original_label + ' ' + control_periodicity)
            for node in doc.xpath("//field[@name='estimated_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.estimated_consumption.string)
                node.set('string', original_label + ' ' + control_periodicity)
            for node in doc.xpath("//field[@name='real_consumption']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.real_consumption.string)
                node.set('string', original_label + ' ' + control_periodicity)
            for node in doc.xpath("//field[@name='deviation']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua_pressurized_irrigation_monitoring',
                        self.__class__.deviation.string)
                node.set('string', original_label + ' ' + control_periodicity)
            for node in doc.xpath("//field[@name='area_official']"):
                original_label = self.env['wua.parcel'].sudo().\
                    get_value_from_translation(
                        'base_wua', self.__class__.area_official.string)
                node.set(
                    'string', original_label + ' (' + area_measure_name + ')')
            res['arch'] = etree.tostring(doc)
        return res
