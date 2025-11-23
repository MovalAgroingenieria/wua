# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaMonitoringperiod(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.monitoringperiod'
    _description = 'Monitoring Period'
    _order = 'name desc'

    def _default_agriculturalseason_id(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        default=_default_agriculturalseason_id,
        index=True,
        required=True,
    )

    initial_date = fields.Date(
        string='Initial date',
        required=True,
        index=True,
        track_visibility='onchange',
    )

    end_date = fields.Date(
        string='End date',
        required=True,
        index=True,
        track_visibility='onchange',
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('01_uncalculated', 'Uncalculated'),
            ('02_calculated', 'Calculated')
        ],
        default='01_uncalculated',
        index=True,
        track_visibility='onchange',
    )

    name = fields.Char(
        string='Code of monitoring period',
        store=True,
        index=True,
        compute='_compute_name',
    )

    number_of_cropunits = fields.Integer(
        string='Number of crop units',
        store=True,
        index=True,
        compute='_compute_number_of_cropunits',
    )

    number_of_hydricestimations = fields.Integer(
        string='Number of hydric estimations',
        store=True,
        index=True,
        compute='_compute_number_of_hydricestimations',
    )

    notes = fields.Html(
        string='Notes',
    )

    @api.depends('agriculturalseason_id', 'initial_date', 'end_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.agriculturalseason_id and record.initial_date and
               record.end_date):
                initial_year = fields.Date.from_string(
                    record.agriculturalseason_id.initial_date).strftime('%Y')
                end_year = fields.Date.from_string(
                    record.agriculturalseason_id.end_date).strftime('%Y')
                name = (initial_year[2:] + '/' + end_year[2:] + '-' +
                        record.initial_date + '-' + record.end_date)
            record.name = name

    @api.depends('initial_date')
    def _compute_number_of_cropunits(self):
        for record in self:
            number_of_cropunits = 0
            # TODO (provisional... set api.depends!)
            record.number_of_cropunits = number_of_cropunits

    @api.depends('initial_date')
    def _compute_number_of_hydricestimations(self):
        for record in self:
            number_of_hydricestimations = 0
            # TODO (provisional... set api.depends!)
            record.number_of_hydricestimations = number_of_hydricestimations

    @api.multi
    def action_get_hydric_estimations(self):
        self.ensure_one()
        # TODO (provisional)
        print 'action_get_hydric_estimations (from monitoring period)...'
