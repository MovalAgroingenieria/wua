# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class WuaIrrigationReport(models.Model):
    _name = 'wua.irrigationreport'
    _description = "WUA Irrigation Report"

    # Defaults
    def _compute_default_agriculturalseason_id(self):
        # Get active agricultural season
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        return active_agricultural_season

    # Fields
    report_initial_time = fields.Datetime(
        string='Start Time',
        required=True,
        index=True,
        default=datetime.now())

    report_end_time = fields.Datetime(
        string='End Time',
        required=True,
        index=True,
        default=datetime.now())

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
        default=_compute_default_agriculturalseason_id,
        comodel_name="wua.agriculturalseason",
        ondelete="set null")

    irrigationreport_number = fields.Integer(
        string="Report Number",
        readonly=True,
        store=True,
        compute="_compute_irrigation_report_number")

    name = fields.Char(
        string="Report Code",
        size=36,
        store=True,
        readonly=True,
        index=True,
        compute="_compute_report_name")

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
        required=True,
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
        required=True,
        default="draft",
        compute="_compute_validated_by_signature")

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
         'CHECK (end_volume >= 0)',
         'The end volume can not be a negative value.'),
        ]

    @api.depends('intake_id')
    def _compute_irrigation_report_number(self):
        if self.id:
            current_intake_irrigation_reports = \
                self.env['wua.irrigationreport'].search([
                    ('intake_id', '=', self.intake_id.id),
                    ('id', '!=', self.id)],
                    order='irrigationreport_number desc')
        else:
            current_intake_irrigation_reports = \
                self.env['wua.irrigationreport'].search([
                    ('intake_id', '=', self.intake_id.id)],
                    order='irrigationreport_number desc')
        if current_intake_irrigation_reports:
            self.irrigationreport_number = \
                current_intake_irrigation_reports[
                    0].irrigationreport_number + 1
        else:
            self.irrigationreport_number = 1

    @api.onchange('report_end_time')
    @api.constrains('report_end_time')
    def _detect_out_of_date_agricultural_season(self):
        active_agricultural_season = self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agricultural_season:
            if not active_agricultural_season.initial_date <= \
                self.report_end_time <= \
                    active_agricultural_season.end_date:
                raise ValidationError(
                    _("The end time (%s) is out of agricultural season (%s)" %
                      (self.report_end_time,
                       active_agricultural_season.description)))

    @api.depends('agriculturalseason_id', 'agriculturalseason_id.initial_date',
                 'agriculturalseason_id.initial_date', 'intake_id',
                 'intake_id.intake_code', 'irrigationreport_number')
    def _compute_report_name(self):
        for record in self:
            name = ''
            if record.agriculturalseason_id and record.intake_id and \
                    record.irrigationreport_number:
                initial_date = record.agriculturalseason_id.initial_date
                end_date = record.agriculturalseason_id.end_date
                name = initial_date + '/' + end_date + '/' + \
                    str(record.intake_id.intake_code).zfill(6) + '/' + \
                    str(record.irrigationreport_number).zfill(6)
            record.name = name

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            record.of_active_agriculturalseason = \
                record.agriculturalseason_id.active_agriculturalseason

    @api.depends('initial_volume', 'end_volume')
    def _compute_volume(self):
        for record in self:
            record.volume = record.end_volume - record.initial_volume

    @api.depends('volume', 'adjustement_volume')
    def _compute_volume_real(self):
        for record in self:
            record.volume_real = record.volume + record.adjustement_volume

    @api.depends('partner_signature')
    def _compute_validated_by_signature(self):
        for record in self:
            if record.partner_signature:
                record.state = "validated"
            else:
                record.state = "draft"

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
