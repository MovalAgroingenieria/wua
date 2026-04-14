# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WuaCensusSyncLog(models.Model):
    _name = 'wua.census.sync.log'
    _description = 'Batchline IrriWEB Census Sync Log'
    _order = 'date_start desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        readonly=True,
        index=True,
    )

    date_start = fields.Datetime(
        string='Start Date',
        readonly=True,
        index=True,
    )

    date_end = fields.Datetime(
        string='End Date',
        readonly=True,
    )

    trigger = fields.Selection(
        string='Trigger',
        selection=[
            ('manual', 'Manual'),
            ('cron', 'Scheduled'),
        ],
        readonly=True,
        default='manual',
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('running', 'Running'),
            ('success', 'Success'),
            ('partial', 'Partial'),
            ('error', 'Error'),
        ],
        readonly=True,
        default='running',
        index=True,
    )

    summary = fields.Text(
        string='Summary',
        readonly=True,
    )

    line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Log Lines',
        readonly=True,
    )

    issue_line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Issues',
        domain=[('level', 'in', ['error', 'warning'])],
        readonly=True,
    )

    toma_line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Tomas',
        domain=[('level', '=', 'toma')],
        readonly=True,
    )

    partner_warning_line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Partner Warnings',
        domain=[('level', '=', 'warning_partner')],
        readonly=True,
    )

    parcel_warning_line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Parcel Warnings',
        domain=[('level', '=', 'warning_parcel')],
        readonly=True,
    )

    partnerlink_warning_line_ids = fields.One2many(
        comodel_name='wua.census.sync.log.line',
        inverse_name='log_id',
        string='Partnerlink Warnings',
        domain=[('level', '=', 'warning_partnerlink')],
        readonly=True,
    )

    error_count = fields.Integer(
        string='Errors',
        compute='_compute_line_count',
    )

    warning_count = fields.Integer(
        string='Warnings',
        compute='_compute_line_count',
    )

    toma_count = fields.Integer(
        string='Tomas',
        compute='_compute_line_count',
    )

    partner_warning_count = fields.Integer(
        string='Partner Warnings',
        compute='_compute_line_count',
    )

    parcel_warning_count = fields.Integer(
        string='Parcel Warnings',
        compute='_compute_line_count',
    )

    partnerlink_warning_count = fields.Integer(
        string='Partnerlink Warnings',
        compute='_compute_line_count',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        index=True,
    )

    @api.multi
    def _compute_line_count(self):
        for record in self:
            lines = record.line_ids
            record.error_count = len(
                lines.filtered(lambda l: l.level == 'error'))
            record.warning_count = len(
                lines.filtered(lambda l: l.level in (
                    'warning', 'warning_partner', 'warning_parcel',
                    'warning_partnerlink')))
            record.toma_count = len(
                lines.filtered(lambda l: l.level == 'toma'))
            record.partner_warning_count = len(
                lines.filtered(lambda l: l.level == 'warning_partner'))
            record.parcel_warning_count = len(
                lines.filtered(lambda l: l.level == 'warning_parcel'))
            record.partnerlink_warning_count = len(
                lines.filtered(lambda l: l.level == 'warning_partnerlink'))

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = (
                self.env['ir.sequence'].next_by_code(
                    'wua.census.sync.log') or
                fields.Datetime.now()
            )
        return super(WuaCensusSyncLog, self).create(vals)


class WuaCensusSyncLogLine(models.Model):
    _name = 'wua.census.sync.log.line'
    _description = 'Batchline IrriWEB Census Sync Log Line'
    _order = 'id'

    log_id = fields.Many2one(
        string='Sync Log',
        comodel_name='wua.census.sync.log',
        ondelete='cascade',
        required=True,
        index=True,
    )

    endpoint = fields.Char(
        string='Endpoint',
        readonly=True,
        index=True,
    )

    external_code = fields.Char(
        string='External Code',
        readonly=True,
    )

    message = fields.Text(
        string='Message',
        readonly=True,
    )

    level = fields.Selection(
        string='Level',
        selection=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('warning_partner', 'Partner Warning'),
            ('warning_parcel', 'Parcel Warning'),
            ('warning_partnerlink', 'Partnerlink Warning'),
            ('error', 'Error'),
            ('toma', 'Toma'),
        ],
        readonly=True,
        default='warning',
        index=True,
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        index=True,
    )
