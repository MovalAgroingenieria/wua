# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


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

    description = fields.Char(
        string='Description',
        index=True,
    )

    nominal_diameter = fields.Integer(
        string='Nominal Diameter',
        default=0,
        track_visibility='onchange',
    )

    serial_number = fields.Char(
        size=40,
        string="Serial Number",
        index=True,
        track_visibility='onchange',
    )

    flowmeter_brand = fields.Char(
        string="Brand",
        track_visibility='onchange',
    )

    flowmeter_model = fields.Char(
        string="Model",
        track_visibility='onchange',
    )

    installation_date = fields.Date(
        string="Installation date",
        track_visibility='onchange',
    )

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

    flow_direction = fields.Selection([
        ('incoming', 'Incoming flow'),
        ('outgoing', 'Outgoing flow'),
        ('bidirectional', 'Bidirectional'),
        ('independent', 'Independent')],
        string="Flow direction",
        default='incoming',
        required=True,
        help='The direction of the water flow.')

    bidirectional_flow_1_def = fields.Char(
        string='Flow def. 1',
        help="The definition of the flow as it appears in the irrigation "
             "remote control.")

    bidirectional_flow_2_def = fields.Char(
        string='Flow def. 2',
        help="The definition of the flow as it appears in the irrigation "
             "remote control.")

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

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
                        _(record.name)
            if url_for_record and username and password:
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

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_flowmeter_table()
            parcel_model.create_flowmeter_triggers()
        except Exception:
            pass
