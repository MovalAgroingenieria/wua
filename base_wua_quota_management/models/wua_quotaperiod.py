# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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

    name = fields.Char(
        string='Quota Period',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    notes = fields.Html(string='Notes')

    @api.depends('agriculturalseason_id', 'initial_date')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.agriculturalseason_id and record.initial_date:
                value = record.agriculturalseason_id.initial_date + '/' + \
                    record.initial_date
            record.name = value

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ]
