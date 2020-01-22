# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaQuotaperiod(models.Model):
    _name = 'wua.quotaperiod'
    _description = 'Quota Period'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_NAME = 22
    MAX_SIZE_DESCRIPTION = 40

    def _default_agriculturalseason_id(self):
        resp = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            resp = active_agriculturalseasons[0].id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
        index=True)

    end_date = fields.Date(
        string='End Date',
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    name = fields.Char(
        string='Quota Period',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    number_of_superproducts = fields.Integer(
        string='Number of superproducts',
        store=True,
        compute='_compute_number_of_superproducts')

    sorted_quotas = fields.Boolean(
        string='Sort in superproducts',
        default=False)

    volume_total = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 4),
        default=0,
        readonly=True)

    is_closed = fields.Boolean(
        string='Closed Period',
        default=False,
        track_visibility='onchange')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('configured', 'Configured'),
            ('generated', 'Generated'),
        ],
        index=True,
        required=True,
        string='State',
        default='draft',
        track_visibility='onchange')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('agriculturalseason_id', 'initial_date')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.agriculturalseason_id and record.initial_date:
                value = record.agriculturalseason_id.initial_date + '/' + \
                    record.initial_date
            record.name = value

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('agriculturalseason_id')
    def _compute_number_of_superproducts(self):
        # Provisional
        for record in self:
            record.number_of_superproducts = 0

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1 and
           ((self.initial_date < self.agriculturalseason_id.initial_date) or
           (self.end_date > self.agriculturalseason_id.end_date))):
            raise exceptions.ValidationError(_(
                'The quota period limits are outside the agricultural '
                'season.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.end_date, '%Y-%m-%d').strftime('%x')
            name = initial_date_str + ' - ' + end_date_str
            description = ''
            if record.description:
                description = record.description.strip()
            if description:
                name = name + ' (' + description + ')'
            result.append((record.id, name))
        return result

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_partner_quotas'

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        # Provisional
        print 'action_get_hydric_movements'
