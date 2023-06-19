# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardIrrigationDistributionReport(models.TransientModel):
    _name = 'wizard.irrigation.distribution.report'
    _description = 'Dialog box to print Irrigation distribution report'

    def _default_initial_date(self):
        active_ids = self.env.context['active_ids']
        older_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time",
                limit=1)
        initial_date = older_selected_irrigation_report.report_initial_time
        return initial_date

    def _default_end_date(self):
        active_ids = self.env.context['active_ids']
        # Use report initial time for selection
        newer_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time desc",
                limit=1)
        end_date = newer_selected_irrigation_report.report_initial_time
        return end_date

    def _default_num_irrigations_reports(self):
        active_ids = self.env.context['active_ids']
        older_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time",
                limit=1)
        newer_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time desc",
                limit=1)
        selected_irrigationreport_ids = \
            self.env['wua.irrigationreport'].search([
                ('report_initial_time', '>=',
                    older_selected_irrigation_report.report_initial_time),
                ('report_initial_time', '<=',
                    newer_selected_irrigation_report.report_initial_time)
                ], order="report_initial_time").ids
        num_irrigations_reports = len(selected_irrigationreport_ids)
        return num_irrigations_reports

    def _default_irrigationreport_ids(self):
        active_ids = self.env.context['active_ids']
        older_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time",
                limit=1)
        newer_selected_irrigation_report = \
            self.env['wua.irrigationreport'].search(
                [('id', 'in', active_ids)],
                order="report_initial_time desc",
                limit=1)
        selected_irrigationreport_ids = \
            self.env['wua.irrigationreport'].search([
                ('report_initial_time', '>=',
                    older_selected_irrigation_report.report_initial_time),
                ('report_initial_time', '<=',
                    newer_selected_irrigation_report.report_initial_time)
                ], order="report_initial_time").ids
        irrigationreport_ids = selected_irrigationreport_ids
        return irrigationreport_ids

    initial_date = fields.Datetime(
        string='Initial Date',
        default=_default_initial_date,
        required=True)

    end_date = fields.Datetime(
        string='End Date',
        default=_default_end_date,
        required=True)

    num_irrigations_reports = fields.Integer(
        string='Num. of selected reports',
        readonly=True,
        default=_default_num_irrigations_reports,
        compute="_compute_num_irrigations_reports",
        help="Number of irrigations reports to be added to report.")

    irrigationreport_ids = fields.One2many(
        string="Selected reports",
        comodel_name='wua.irrigationreport',
        default=_default_irrigationreport_ids,
        compute="_compute_irrigationreport_ids")

    show_selected_reports = fields.Boolean(
        string="Show selected reports",
        default=False)

    @api.depends('initial_date', 'end_date')
    def _compute_num_irrigations_reports(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        if self.initial_date and self.end_date:
            selected_irrigationreport_ids = \
                self.env['wua.irrigationreport'].search([
                    ('report_initial_time', '>=', self.initial_date),
                    ('report_initial_time', '<=', self.end_date)
                    ], order="report_initial_time").ids
        for record in self:
            record.num_irrigations_reports = len(selected_irrigationreport_ids)

    @api.depends('initial_date', 'end_date')
    def _compute_irrigationreport_ids(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        selected_irrigationreport_ids = \
            self.env['wua.irrigationreport'].search([
                ('report_initial_time', '>=', self.initial_date),
                ('report_initial_time', '<=', self.end_date)
                ], order="report_initial_time").ids
        for record in self:
            record.irrigationreport_ids = selected_irrigationreport_ids

    @api.onchange('initial_date', 'end_date')
    def _recalculate_num_irrigations_reports(self):
        if self.initial_date and self.end_date:
            selected_irrigationreport_ids = \
                self.env['wua.irrigationreport'].search([
                    ('report_initial_time', '>=', self.initial_date),
                    ('report_initial_time', '<=', self.end_date)
                    ], order="report_initial_time").ids
        for record in self:
            record.num_irrigations_reports = len(selected_irrigationreport_ids)

    @api.multi
    def print_irrigation_distribution_report(self):
        self.ensure_one()
        if self.initial_date > self.end_date:
            raise exceptions.UserError(_('Incorrect dates,\
                the initial date is before the end date.'))
        report_name = 'base_wua_irrigation_report.'\
            'irrigation_distribution_report_report_document'
        return self.env['report'].get_action(self, report_name)
