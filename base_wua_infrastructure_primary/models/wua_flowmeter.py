# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from Crypto.Cipher import AES
import datetime
import pytz


class WuaFlowmeter(models.Model):
    _name = 'wua.flowmeter'
    _description = 'Entity (flowmeter)'
    _order = 'name'

    name = fields.Char(
        string='Identifier',
        size=30,
        required=True,
        index=True,
        help='The name that identifies the flow-meter')

    state = fields.Selection([
        ('active', 'Active'),
        ('stored', 'Stored'),
        ('discarted', 'Discarted')],
        string="State",
        required=True,
        index=True,
        default='active',
        help='Flow-Meter Status')

    type = fields.Selection([
        ('undefined', 'Undefined'),
        ('woltmann', 'Woltmann'),
        ('electromagnetic', 'Electromagnetic'),
        ('ultrasonic', 'Ultrasonic'),
        ('titrator', 'Titrator'),
        ('levelprobe', 'Level Probe'),
        ('ultrasonicdoppler', 'Doppler-Effect Ultrasonic')],
        string="Type",
        required=True,
        index=True,
        default='undefined',
        help='Type of flow-meter')

    nominal_water_flow = fields.Float(
        string="Water Flow (m3/hour)",
        digits=(32, 2),
        required=True,
        help="The nominal flow rate of flow-meter")

    intake_ids = fields.One2many(
        string='Intakes',
        comodel_name='wua.intake',
        inverse_name='flowmeter_id',
        help="Intakes related to the flow-meter")

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        compute="_compute_intake_id",
        store=True,
        index=True)

    connected_to_intake = fields.Boolean(
        string="In intake",
        store=True,
        compute="_compute_connected_to_intake")

    notes = fields.Html(
        string="Notes",
        help="Notes about flow-meter")

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_flowmeter = fields.Boolean(
        string="GIS Flowmeter",
        readonly=True)

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing flow-meter identifier.'),
        ('nominal_water_flow',
         'CHECK (nominal_water_flow >= 0)',
         'Nominal water flow can not be negative.'),
        ]

    @api.depends('intake_ids')
    def _compute_intake_id(self):
        for record in self:
            intake_id = None
            if record.intake_ids:
                intake_id = record.intake_ids[0]
            record.intake_id = intake_id

    @api.depends('intake_id')
    def _compute_connected_to_intake(self):
        for record in self:
            connected_to_intake = False
            if record.intake_id:
                connected_to_intake = True
            record.connected_to_intake = connected_to_intake

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        flowmeter_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_flowmeter_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if flowmeter_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        flowmeter_param + '=' + \
                        str(record.name)
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
                aes_encryptor = AES.new('z%C*F-JaNdRgUkXp', AES.MODE_CBC, iv)
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

    @api.constrains('name')
    def _check_white_spaces_name(self):
        if (len(self) == 1 and ' ' in self.name):
            raise exceptions.ValidationError(_('Blanks are not '
                                               'allowed in the name '
                                               'of the flowmeter.'))

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }
