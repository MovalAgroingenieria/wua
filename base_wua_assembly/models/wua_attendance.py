# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import locale
from datetime import datetime
from odoo import models, fields, api, modules


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

    participant_id = fields.Many2one(
        string='Participant',
        comodel_name='res.partner',
        index=True,
        store=True,
        compute='_compute_participant_id',)

    participant_name = fields.Char(
        string='Participant Name',
        index=True,
        store=True,
        compute='_compute_participant_name',)

    vat_participant = fields.Char(
        string='TIN (participant)',
        index=True,
        store=True,
        compute='_compute_vat_participant',)

    represented_partner = fields.Char(
        string='Represented Partner',
        compute='_compute_represented_partner',)

    assembly_state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='Assembly State',
        default='02_called',
        store=True,
        compute='_compute_assembly_state',)

    receiver_id = fields.Many2one(
        string='Receiver (if there is voting delegation)',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',)

    potential_attendee = fields.Boolean(
        string='Potential Attendee (y/n)',
        store=True,
        compute='_compute_potential_attendee',)

    present = fields.Boolean(
        string='Present',
        default=False,)

    icon_present = fields.Binary(
        string='Icon for the attendance',
        compute='_compute_icon_present')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar attendance record.'),
        ('valid_votes_owned', 'CHECK (votes_owned >= 0)',
         'The number of own votes must be a value greater than or '
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

    @api.depends('partner_id')
    def _compute_participant_id(self):
        for record in self:
            participant_id = record.partner_id
            agent_id = self._get_agent_of_participant(
                record.assembly_id, record.partner_id)
            if agent_id or record.partner_id.legalrep_id:
                if agent_id:
                    participant_id = agent_id.id
                else:
                    participant_id = record.partner_id.legalrep_id
            record.participant_id = participant_id

    @api.depends('participant_id')
    def _compute_participant_name(self):
        for record in self:
            participant_name = ''
            if record.participant_id:
                participant_name = record.participant_id.name
            record.participant_name = participant_name

    @api.depends('participant_id')
    def _compute_vat_participant(self):
        for record in self:
            vat_participant = ''
            if record.participant_id:
                if record.participant_id.is_wua_partner:
                    vat_participant = record.participant_id.vat
                else:
                    vat_participant = record.participant_id.vat_wua_legalrep
            record.vat_participant = vat_participant

    @api.multi
    def _compute_represented_partner(self):
        for record in self:
            represented_partner = ''
            if record.participant_name != record.partner_id.name:
                represented_partner = record.partner_id.name
            record.represented_partner = represented_partner

    @api.depends('assembly_id', 'assembly_id.state')
    def _compute_assembly_state(self):
        for record in self:
            assembly_state = '01_draft'
            if record.assembly_id and record.assembly_id.state:
                assembly_state = record.assembly_id.state
            record.assembly_state = assembly_state

    @api.depends('receiver_id')
    def _compute_potential_attendee(self):
        for record in self:
            potential_attendee = True
            if record.receiver_id:
                potential_attendee = False
            record.potential_attendee = potential_attendee

    @api.multi
    def _compute_icon_present(self):
        image_path_present_yes = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_yes.png')
        image_path_present_no = modules.module.get_resource_path(
            'base_wua_assembly', 'static/img', 'icon_approved_no.png')
        for record in self:
            icon_present = None
            image_path = None
            if record.present:
                image_path = image_path_present_yes
            else:
                image_path = image_path_present_no
            if image_path:
                image_file = open(image_path, 'rb')
                icon_present = base64.b64encode(image_file.read())
            record.icon_present = icon_present

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = ('lang' in self.env.context and
                      self.env.context['lang'] == 'en_US')
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                assembly_date_str = datetime.strptime(
                    record.assembly_id.assembly_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = assembly_date_str + ' (' + record.participant_name + ')'
            result.append((record.id, name))
        return result

    def _get_agent_of_participant(self, assembly, partner):
        resp = None
        representation = self.env['wua.representation'].search(
            [('assembly_id', '=', assembly.id),
             ('partner_id', '=', partner.id),
             ('state', '=', '02_validated')])
        if representation:
            resp = representation[0].agent_id
        return resp

    @api.multi
    def confirm_present_value(self):
        self.ensure_one()
        return {'type': 'ir.actions.client', 'tag': 'history_back'}
