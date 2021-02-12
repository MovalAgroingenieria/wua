# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from Crypto.Cipher import AES
import datetime
import pytz


class WuaIntake(models.Model):
    _name = 'wua.intake'
    _description = 'Entity (intake)'
    _order = 'intake_code'

    def _default_intake_code(self):
        resp = 0
        intakes = self.search([('intake_code', '>', 0)], limit=1,
                              order='intake_code desc')
        if len(intakes) == 1:
            resp = intakes[0].intake_code + 1
        else:
            resp = 1
        return resp

    intake_code = fields.Integer(
        string='Code',
        default=_default_intake_code,
        required=True,
        index=True)

    name = fields.Char(
        string='Intake',
        size=30,
        required=True,
        index=True,
        help='Intake Name')

    type = fields.Selection([
        ('pressure', 'Pressure'),
        ('freesheet', 'Free Sheet')],
        string="Type",
        required=True,
        index=True,
        default='pressure',
        help='Type of intake')

    category = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')],
        string="Category",
        required=True,
        index=True,
        help='Intake Category')

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter')

    with_flowmeter = fields.Boolean(
        string="With flowmeter",
        store=True,
        compute='_compute_with_flowmeter')

    with_gis_intake = fields.Boolean(
        string="GIS Intake",
        readonly=True)

    notes = fields.Html(
        string="Notes",
        help="Notes about intake")

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_intake = fields.Boolean(
        string='GIS Intake')

    _sql_constraints = [
        ('unique_intake_code',
         'UNIQUE (intake_code)',
         'Existing intake code.'),
        ('intake_code_positive',
         'CHECK (intake_code >= 0)',
         'Intake code can not be negative.'),
        ('unique_name',
         'UNIQUE (name)',
         'Existing intake.'),
        ]

    @api.depends('flowmeter_id')
    def _compute_with_flowmeter(self):
        for record in self:
            with_flowmeter = False
            if record.flowmeter_id:
                with_flowmeter = True
            record.with_flowmeter = with_flowmeter

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        intake_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_intake_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if intake_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        intake_param + '=' + \
                        str(record.intake_code)
            if url_for_record and username and password:
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

    @api.constrains('flowmeter_id')
    def _check_flowmeter_id(self):
        if len(self) == 1:
            current_intake = self
            if current_intake.flowmeter_id:
                current_flowmeter = current_intake.flowmeter_id
                # The flow-meter for this intake ("current_flowmeter") cannot
                # be assigned to another intake.
                # Provisional
                other_intakes_of_flowmeter = self.env['wua.intake'].search(
                    [('id', '!=', current_intake.id),
                     ('flowmeter_id', '=', current_flowmeter.id)])
                if other_intakes_of_flowmeter:
                    raise exceptions.ValidationError(
                        _('Only one intake per flowmeter is allowed.'))

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }
