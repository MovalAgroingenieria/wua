# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, tools, api
import datetime
from Crypto.Cipher import AES
import pytz


class WuaComparativePartnerPresconsumption(models.Model):
    _name = 'wua.comparative.partner.presconsumption'
    _description = 'Comparative Partner Presconsumption'
    _auto = False
    _order = 'agriculturalseason_id,controlperiod_id,partner_id'

    controlperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.controlperiod',
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
    )

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4)
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
    )

    estimated_consumption = fields.Float(
        string='Estimated Consumption',
        digits=(32, 4)
    )

    real_consumption = fields.Float(
        string='Real Consumption',
        digits=(32, 4)
    )

    deviation = fields.Float(
        string='Deviation',
        digits=(32, 4)
    )

    deviation_percentage = fields.Char(
        string='Deviation Percentage',
        compute='_compute_deviation_percentage',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link'
    )

    consumption_category = fields.Selection([
        ('A', 'A (correct irrigation)'),
        ('B', 'B (acceptable irrigation)'),
        ('C', 'C (unsatisfactory irrigation)'),
        ],
        string='Consumption Category'
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_comparative_partner_presconsumption')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_comparative_partner_presconsumption AS (
            SELECT row_number() OVER () AS id, wcsp1.controlperiod_id,
            wcsp1.partner_id, SUM(wcsp1.estimated_consumption) AS
            estimated_consumption, SUM(wcsp1.real_consumption) AS
            real_consumption, SUM(wcsp1.deviation) AS deviation,
            SUM(wcsp1.area_official) AS area_official,
            wcsp1.agriculturalseason_id,
            CASE
             WHEN (
                    (SUM(wcsp1.real_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.real_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_01'
                     )
                    )
                ) THEN 'A'
             WHEN (
                    (SUM(wcsp1.real_consumption) > 0) AND
                    (ABS(SUM(wcsp1.deviation)) * 100 /
                     SUM(wcsp1.real_consumption) <=
                     (SELECT CAST(substring(value FROM \'\\d+.?\\d*\') AS
                      FLOAT) FROM ir_values WHERE model =
                      'wua.monitoring.configuration' AND name LIKE
                      'max_deviation_categ_02'
                     )
                    )
                ) THEN 'B'
             ELSE  'C'
            END AS consumption_category FROM
            wua_comparative_subparcel_presconsumption wcsp1 INNER JOIN
            res_partner rp1 ON rp1.id = wcsp1.partner_id GROUP BY
            wcsp1.agriculturalseason_id, wcsp1.controlperiod_id,
            wcsp1.partner_id)
            """)

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
        partner_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_partner_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if partner_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        partner_param + '=' + \
                        str(record.partner_id.partner_code)
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
