# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


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

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    hydraulicsectorlink_ids = fields.One2many(
        string='Hydraulic sectors of intake',
        comodel_name='wua.intake.hydraulicsectorlink',
        inverse_name='intake_id',)

    sectors_as_text = fields.Char(
        string='List of sectors (as text)',
        compute='_compute_sectors_as_text',)

    image = fields.Binary(
        string='Photo / Image',
        attachment=True)

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

    @api.multi
    def _compute_sectors_as_text(self):
        for record in self:
            sectors_as_text = ''
            if record.hydraulicsectorlink_ids:
                for hydraulicsectorlink in record.hydraulicsectorlink_ids:
                    sectors_as_text = sectors_as_text + \
                        hydraulicsectorlink.hydraulicsector_id.name + ', '
                sectors_as_text = sectors_as_text[:-2]
            record.sectors_as_text = sectors_as_text

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

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_intake_table()
            parcel_model.create_intake_triggers()
        except Exception:
            pass


class WuaIntakeHydraulicsectorlink(models.Model):
    _name = 'wua.intake.hydraulicsectorlink'
    _description = 'Hydraulic sector of intake'

    # Size of "name" field, in the model.
    MAX_SIZE_CODE_INTAKE = 4
    MAX_SIZE_CODE_HYDRAULICSECTOR = 4

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        required=True,
        index=True,
        ondelete='cascade',)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        required=True,
        index=True,
        ondelete='restrict',)

    name = fields.Char(
        string='Identifier of hydraulic-sector link',
        size=MAX_SIZE_CODE_INTAKE + MAX_SIZE_CODE_HYDRAULICSECTOR + 1,
        store=True,
        index=True,
        compute='_compute_name',)

    number_of_irrigationsheds = fields.Integer(
        string='Number of irrigation sheds',
        related='hydraulicsector_id.number_of_irrigationsheds',)

    number_of_waterconnections = fields.Integer(
        string='Number of water connections',
        related='hydraulicsector_id.number_of_waterconnections',)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'There are repeated hydraulic-sector links.'),
        ]

    @api.depends('intake_id',
                 'intake_id.intake_code',
                 'hydraulicsector_id',
                 'hydraulicsector_id.hydraulicsector_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.intake_id and record.hydraulicsector_id:
                name = str(record.intake_id.intake_code).zfill(
                    self.MAX_SIZE_CODE_INTAKE) + '-' + \
                    str(record.hydraulicsector_id.hydraulicsector_code).zfill(
                        self.MAX_SIZE_CODE_HYDRAULICSECTOR)
            record.name = name
