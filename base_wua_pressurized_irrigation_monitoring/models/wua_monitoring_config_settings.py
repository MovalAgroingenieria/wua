# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaMonitoringConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.monitoring.configuration'
    _description = 'Configuration of base_wua_pressurized_irrigation_' + \
        'monitoring module'

    max_deviation_categ_01 = fields.Float(
        string='Maximun deviation for Categorie 1',
        digits=(32, 2),
        default=5,
        help='Maximun percentage of deviation for being in the categorie 01')

    max_deviation_categ_02 = fields.Float(
        string='Maximun deviation for Categorie 2',
        digits=(32, 2),
        default=10,
        help='Maximun percentage of deviation for being in the categorie 02')

    url_gis_viewer_subparcel_param = fields.Char(
        string='Param for subparcel',
        size=20,
        help='Name of subparcel param in the GIS viewer url')

    control_periodicity = fields.Selection([
        ('s', 'Weekly'),
        ('b', 'Biweekly'),
        ('m', 'Monthly')],
        'Control-Periods Periodicity',
        default='s')

    uniformity_irrigation_application = fields.Float(
        string='Uniformity of irrigation application',
        digits=(32, 2),
        default=0.9)

    incoming_mail_email_from = fields.Char(
        string='Email from',
        size=50,
        required=True,
        default='-',
        help='For incoming mails related to agroclimatic data: '
             'email-account that sends the mail.')

    incoming_mail_subject = fields.Char(
        string='Subject',
        size=50,
        help='For incoming mails related to agroclimatic data: '
             'subject of the incoming mail')

    incoming_mail_only_emails_to_admin = fields.Boolean(
        string='Only to administrator',
        help='For incoming mails related to agroclimatic data: '
             'only attend emails addressed to the administrator')

    incoming_mail_col_finaldate = fields.Char(
        string='Column name for final date',
        help='For incoming mails related to agroclimatic data: '
             'in the attached excel file, name of the final-date column')

    incoming_mail_col_et0 = fields.Char(
        string='Column name for ET0',
        help='For incoming mails related to agroclimatic data: '
             'in the attached excel file, name of the ET0 column')

    incoming_mail_col_pe = fields.Char(
        string='Column name for precipitation',
        help='For incoming mails related to agroclimatic data: '
             'in the attached excel file, name of the precipitation column')

    monitoring_informative_clauses = fields.Html(
        string="Informative clauses",
        help="They will be printed in Partner monitoring report.")

    _sql_constraints = [
        ('valid_max_deviation_categ_01',
         'CHECK (max_deviation_categ_01 >= 0)',
         'The maximum percentage of deviation for category A '
         'must be a value zero or positive.'),
        ('valid_max_deviation_categ_02',
         'CHECK (max_deviation_categ_02 >= 0)',
         'The maximum percentage of deviation for category B '
         'must be a value zero or positive.'),
        ('valid_uniformity_irrigation_application',
         'CHECK (uniformity_irrigation_application >= 0)',
         'The uniformity of irrigation application '
         'must be a value zero or positive.'),
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.monitoring.configuration',
                           'max_deviation_categ_01',
                           self.max_deviation_categ_01)
        values.set_default('wua.monitoring.configuration',
                           'max_deviation_categ_02',
                           self.max_deviation_categ_02)
        values.set_default('wua.monitoring.configuration',
                           'url_gis_viewer_subparcel_param',
                           self.url_gis_viewer_subparcel_param)
        values.set_default('wua.monitoring.configuration',
                           'control_periodicity',
                           self.control_periodicity)
        values.set_default('wua.monitoring.configuration',
                           'uniformity_irrigation_application',
                           self.uniformity_irrigation_application)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_email_from',
                           self.incoming_mail_email_from)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_subject',
                           self.incoming_mail_subject)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_only_emails_to_admin',
                           self.incoming_mail_only_emails_to_admin)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_col_finaldate',
                           self.incoming_mail_col_finaldate)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_col_et0',
                           self.incoming_mail_col_et0)
        values.set_default('wua.monitoring.configuration',
                           'incoming_mail_col_pe',
                           self.incoming_mail_col_pe)
        values.set_default('wua.monitoring.configuration',
                           'monitoring_informative_clauses',
                           self.monitoring_informative_clauses)
