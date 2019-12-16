# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIrrigationReport(models.Model):
    _name = 'wua.irrigationreport'
    _description = "WUA Irrigation Report"
    _order = "name"

    def _default_agriculturalseason_id(self):
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        return active_agricultural_season

    report_initial_time = fields.Datetime(
        string='Start Time',
        required=True,
        index=True,
        default=lambda self: fields.datetime.now())

    report_end_time = fields.Datetime(
        string='End Time',
        required=True,
        index=True,
        default=lambda self: fields.datetime.now())

    intake_id = fields.Many2one(
        string="Intake",
        required=True,
        index=True,
        comodel_name="wua.intake",
        ondelete="restrict")

    agriculturalseason_id = fields.Many2one(
        string="Agricultural Season",
        readonly=True,
        index=True,
        required=True,
        default=_default_agriculturalseason_id,
        comodel_name="wua.agriculturalseason",
        ondelete="set null")

    irrigationreport_number = fields.Integer(
        string="Report Number",
        store=True,
        compute="_compute_irrigationreport_number_name")

    name = fields.Char(
        string="Report Code",
        size=36,
        store=True,
        index=True,
        compute="_compute_irrigationreport_number_name")

    partner_id = fields.Many2one(
        string="Partner",
        required=True,
        index=True,
        comodel_name="res.partner",
        ondelete="restrict")

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        readonly=True)

    initial_volume = fields.Float(
        string='Initial Value (m3)',
        digits=(32, 4),
        required=True)

    end_volume = fields.Float(
        string='Final Value (m3)',
        digits=(32, 4),
        required=True)

    volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        store=True,
        compute="_compute_volume")

    adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        required=True,
        default=0)

    volume_real = fields.Float(
        string='Real Volume (m3)',
        digits=(32, 4),
        store=True,
        compute="_compute_volume_real")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated')],
        string="State",
        default="draft",
        store=True,
        compute="_compute_state")

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    notes = fields.Html(string='Notes')

    partner_signature = fields.Binary(
        string='Signature')

    _sql_constraints = [
        ('valid_irrigationreport_time_range',
         'CHECK (report_initial_time <= report_end_time)',
         'The initial time is after the end time.'),
        ('unique_name',
         'UNIQUE (name)',
         'Existing report code.'),
        ('valid_initial_volume',
         'CHECK (initial_volume >= 0)',
         'The initial volume can not be a negative value.'),
        ('valid_end_volume',
         'CHECK (end_volume >= initial_volume)',
         'The final volume must be equal or greather than initial volume.'),
        ]

    @api.depends('intake_id', 'agriculturalseason_id')
    def _compute_irrigationreport_number_name(self):
        for record in self:
            irrigationreport_number = 1
            name = ''
            if record.agriculturalseason_id and record.intake_id:
                initial_date = record.agriculturalseason_id.initial_date
                end_date = record.agriculturalseason_id.end_date
                intake = record.intake_id
                agriculturalseason = record.agriculturalseason_id
                if record.id:
                    last_report = self.env['wua.irrigationreport'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ('intake_id', '=', intake.id),
                         ('id', '!=', record.id)],
                        order='irrigationreport_number desc', limit=1)
                else:
                    last_report = self.env['wua.irrigationreport'].search(
                        [('agriculturalseason_id', '=', agriculturalseason.id),
                         ('intake_id', '=', intake.id)],
                        order='irrigationreport_number desc', limit=1)
                if last_report:
                    irrigationreport_number = \
                        last_report[0].irrigationreport_number + 1
                name = initial_date + '/' + end_date + '/' + \
                    str(intake.intake_code).zfill(6) + '/' + \
                    str(irrigationreport_number).zfill(6)
            record.irrigationreport_number = irrigationreport_number
            record.name = name

    @api.depends('initial_volume', 'end_volume')
    def _compute_volume(self):
        for record in self:
            volume = record.end_volume - record.initial_volume
            if volume < 0:
                volume = 0
            record.volume = volume

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('partner_signature')
    def _compute_state(self):
        for record in self:
            if record.partner_signature:
                record.state = "validated"
            else:
                record.state = "draft"

    @api.depends('agriculturalseason_id',
                 'agriculturalseason_id.active_agriculturalseason')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            record.of_active_agriculturalseason = \
                record.agriculturalseason_id.active_agriculturalseason

    @api.onchange('partner_id')
    def _change_partner_id(self):
        if self.agriculturalseason_id and self.intake_id and self.partner_id:
            last_report = self.env['wua.irrigationreport'].search(
                [('agriculturalseason_id', '=', self.agriculturalseason_id.id),
                 ('intake_id', '=', self.intake_id.id)],
                order='irrigationreport_number desc', limit=1)
            if last_report:
                end_volume_of_last_record = \
                    last_report[0].end_volume
                self.initial_volume = end_volume_of_last_record

    @api.model
    def create(self, vals):
        new_record = super(WuaIrrigationReport, self).create(vals)
        report_initial_time = new_record.report_initial_time
        report_end_time = new_record.report_end_time
        agriculturalseason = new_record.agriculturalseason_id
        if (report_initial_time < agriculturalseason.initial_date or
           report_end_time > agriculturalseason.end_date):
            raise exceptions.ValidationError(_('The dates of the report '
                                               'are out of the '
                                               'agricultural season.'))
        return new_record

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['irrigationreport_number', 'report_initial_volume',
                            'report_end_volume']
        for field_to_remove in fields_to_remove:
            if field_to_remove in fields:
                fields.remove(field_to_remove)
        return super(WuaIrrigationReport, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)
