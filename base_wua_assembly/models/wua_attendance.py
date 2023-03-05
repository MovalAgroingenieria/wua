# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAttendance(models.Model):
    _name = 'wua.attendance'
    _description = 'Attendance of a partner to an assembly'
    _order = 'name'

    SIZE_ASSEMBLY_NAME = 10
    SIZE_PARTNER_CODE = 6

    assembly_id = fields.Many2one(
        string='Assembly',
        comodel_name='wua.assembly',
        index=True,
        required=True,
        ondelete='cascade',)

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        domain=[('is_wua_partner', '=', True)],
        index=True,
        required=True,
        ondelete='restrict',)

    name = fields.Char(
        string='Attendance Identifier',
        size=SIZE_ASSEMBLY_NAME + SIZE_PARTNER_CODE + 1,
        store=True,
        index=True,
        compute='_compute_name',)

    votes_owned = fields.Integer(
        string='Own Votes',
        default=0,
        required=True,)

    votes_delegation = fields.Integer(
        string='Votes by delegation',
        default=0,
        required=True,)

    votes_total = fields.Integer(
        string='Total Votes',
        store=True,
        index=True,
        compute='_compute_votes_total',)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar attendance record.'),
        ('valid_votes_owned', 'CHECK (votes_owned >= 0)',
         'The number of own votes must be a value greater than or '
         'equal to 0.'),
        ('valid_votes_delegation', 'CHECK (votes_delegation >= 0)',
         'The number of votes by delegation must be a value greater than or '
         'equal to 0.'),
        ]

    @api.depends('assembly_id', 'assembly_id.name',
                 'partner_id', 'partner_id.partner_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.assembly_id and record.assembly_id.name and
               record.partner_id and record.partner_id.partner_code):
                name = record.assembly_id.name + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.SIZE_PARTNER_CODE)
            record.name = name

    @api.depends('votes_owned', 'votes_delegation')
    def _compute_votes_total(self):
        for record in self:
            record.votes_total = record.votes_owned + record.votes_delegation
