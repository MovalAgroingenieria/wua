# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from jinja2 import Template, TemplateError
from babel import dates
from odoo import models, fields, api, exceptions, _


class WuaAssembly(models.Model):
    _name = 'wua.assembly'
    _description = 'Assembly'
    _inherit = 'mail.thread'
    _order = 'assembly_date desc'

    SIZE_ISSUE = 75
    SIZE_NAME = 19

    def _default_company_id(self):
        resp = ''
        current_company_id = self.env.user.company_id
        if current_company_id:
            resp = current_company_id
        return resp

    def _default_is_multicompany(self):
        resp = False
        company_ids = self.env.user.company_ids
        if len(company_ids) > 1:
            resp = True
        return resp

    def _default_street(self):
        resp = ''
        default_street = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_street')
        if default_street:
            resp = default_street
        return resp

    def _default_zip(self):
        resp = ''
        default_zip = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_zip')
        if default_zip:
            resp = default_zip
        return resp

    def _default_city(self):
        resp = ''
        default_city = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_city')
        if default_city:
            resp = default_city
        return resp

    def _default_state_id(self):
        resp = ''
        default_state_id = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_state_id')
        if default_state_id:
            resp = default_state_id
        return resp

    def _default_country_id(self):
        resp = ''
        default_country_id = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_country_id')
        if default_country_id:
            resp = default_country_id
        else:
            resp = self.env.user.company_id.country_id
        return resp

    def _default_president_id(self):
        resp = ''
        default_president_id = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_president_id')
        if default_president_id:
            resp = default_president_id
        return resp

    def _default_secretary_id(self):
        resp = ''
        default_secretary_id = self.env['ir.values'].get_default(
            'wua.assembly.configuration', 'assembly_secretary_id')
        if default_secretary_id:
            resp = default_secretary_id
        return resp

    def _default_publication_text(self):
        resp = _(
            '<p>{{ assembly.issue }} of the '
            '{{ assembly.company_id.name }}, which will '
            'take place on {{ assembly_month }} '
            '{{ assembly_day }}, at {{ assembly.street }} '
            '({{ assembly.city }}, {{ assembly.state_id.name }}), at '
            '{{ assembly.first_hour_hhmm }}'
            '{% if assembly.second_hour %} in the first call, '
            'and at {{ assembly.second_hour_hhmm }} in second, '
            '{% else %},{% endif %} according to the following '
            '<b>AGENDA</b>:<br></p>')
        return resp

    def _default_attendee_text_on_ballot(self):
        resp = _('''
            <p>Mr./Mrs.:
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            Area:</p><p>Partner Code:</p>
        ''')
        return resp

    def _default_delegation_vote_main_text(self):
        delegation_vote_main_text = _(
            '<div style="text-align: justify;">Mr. &nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '<b></b> with Community Member No. <b>&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>, by '
            'virtue of the provisions of the perminent articles of the Statut'
            'es of the {{ assembly.president_id.company_id.name }}, <b>AUTHOR'
            'IZE</b>:<br><br>Mr. <b>&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '</b> to represent him '
            'at the {{ assembly.issue }} of this Water Association Community,'
            ' which will take place on the next {{ assembly_day }} of {{ asse'
            'mbly_month }} of {{ assembly_year }}.<br><br><div style="text-al'
            'ign: center;"><br>The Authorized&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs'
            'p;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs'
            'p;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp; The Communard<br><br><br><br><br>VAT &nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs'
            'p;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; VAT'
            ' <br><br><b>THE COMMUNITY SECRETARY</b><br><br>'
            '<br><br>VAT {{ assembly.secretary_id.vat }}<br></div></div>')
        last_record = self.env['wua.assembly'].search(
            [], order='write_date desc', limit=1)
        if last_record and last_record.delegation_vote_main_text:
            delegation_vote_main_text = last_record.delegation_vote_main_text
        return delegation_vote_main_text

    def _default_delegation_vote_footer_text(self):
        delegation_vote_footer_text = _(
            '<p><b>NOTE</b>: By virtue of the pertinent Statutes, the Authori'
            'zations must be submitted to the Irrigation Community, for its v'
            'erification and legitimation by the Secretary of the Community. '
            'Failure to comply with this rule will invalidate any Authorizati'
            'on.</p>')
        last_record = self.env['wua.assembly'].search(
            [], order='write_date desc', limit=1)
        if last_record and last_record.delegation_vote_footer_text:
            delegation_vote_footer_text = \
                last_record.delegation_vote_footer_text
        return delegation_vote_footer_text

    def _default_representation_main_text(self):
        representation_main_text = _(
            '<div style="text-align: justify;">Mr. <b>&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '</b> '
            'with Community Member No. <b><b>&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</b>, by '
            'virtue of the provisions of the perminent articles of the Statut'
            'es of the {{ assembly.president_id.company_id.name }}, <b>AUTHOR'
            'IZE</b>:<br><br>Mr. <b>&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '</b> to represent him '
            'at the {{ assembly.issue }} of this Water Association Community,'
            ' which will take place on the next {{ assembly_day }} of {{ asse'
            'mbly_month }} of {{ assembly_year }}.<br><br><div style="text-al'
            'ign: center;"><br>The Authorized&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs'
            'p;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&n'
            'bsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbs'
            'p;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            'The Communard<br><br><br><br><br>VAT &nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;VAT &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
            '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br><br><b>THE '
            'COMMUNITY SECRETARY</b><br><br><br><br>VAT '
            '{{ assembly.secretary_id.vat }}<br></div></div>')
        last_record = self.env['wua.assembly'].search(
            [], order='write_date desc', limit=1)
        if last_record and last_record.representation_main_text:
            representation_main_text = last_record.representation_main_text
        return representation_main_text

    def _default_representation_footer_text(self):
        representation_footer_text = _(
            '<p><b>NOTE</b>: By virtue of the pertinent Statutes, the Authori'
            'zations must be submitted to the Irrigation Community, for its v'
            'erification and legitimation by the Secretary of the Community. '
            'Failure to comply with this rule will invalidate any Authorizati'
            'on.</p>')
        last_record = self.env['wua.assembly'].search(
            [], order='write_date desc', limit=1)
        if last_record and last_record.representation_footer_text:
            representation_footer_text = \
                last_record.representation_footer_text
        return representation_footer_text

    assembly_date = fields.Date(
        string='Date of the assembly',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True,)

    issue = fields.Char(
        string='Issue',
        size=SIZE_ISSUE,
        required=True,)

    name = fields.Char(
        string='Assembly Identifier',
        size=SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name',)

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=_default_company_id,
        compute='_compute_company_id',
        store=True,
        required=True,)

    is_multicompany = fields.Boolean(
        string='Multi company',
        compute_sudo=True,
        default=_default_is_multicompany,
        compute='_compute_is_multicompany',
        store=True)

    street = fields.Char(
        string='Street',
        default=_default_street,
        required=True,)

    zip = fields.Char(
        string='Zip Code',
        default=_default_zip,)

    city = fields.Char(
        string='City',
        default=_default_city,
        required=True,)

    state_id = fields.Many2one(
        string='Province',
        comodel_name='res.country.state',
        default=_default_state_id,
        ondelete='restrict',
        required=True,)

    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        default=_default_country_id,
        ondelete='restrict',
        required=True,)

    president_id = fields.Many2one(
        string='President',
        comodel_name='res.users',
        default=_default_president_id,
        domain=[('is_wua_user', '=', True)],
        required=True,
        track_visibility='onchange',)

    secretary_id = fields.Many2one(
        string='Secretary',
        comodel_name='res.users',
        default=_default_secretary_id,
        domain=[('is_wua_user', '=', True)],
        required=True,
        track_visibility='onchange',)

    state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='State',
        default='01_draft',
        index=True,
        required=True,
        track_visibility='onchange',)

    president_id_portaluser = fields.Many2one(
        string='President (for portal user)',
        comodel_name='res.users',
        compute='_compute_president_id_portaluser',)

    secretary_id_portaluser = fields.Many2one(
        string='Secretary (for portal user)',
        comodel_name='res.users',
        compute='_compute_secretary_id_portaluser',)

    first_hour = fields.Float(
        string='First Hour',
        digits=(32, 4),
        default=0,
        required=True,)

    second_hour = fields.Float(
        string='Second Hour',
        digits=(32, 4),)

    first_hour_hhmm = fields.Char(
        string='First hour (as hh:mm)',
        compute='_compute_first_hour_hhmm',)

    second_hour_hhmm = fields.Char(
        string='Second hour (as hh:mm)',
        compute='_compute_second_hour_hhmm',)

    convocation_date = fields.Date(
        string='Date of convocation',
        track_visibility='onchange',)

    public_notes = fields.Html(
        string='Public Notes',)

    attendee_text_on_ballot = fields.Html(
        string='Public Notes',
        default=_default_attendee_text_on_ballot,
    )

    public_notes_text = fields.Char(
        string="Public Notes (as text)",
        store=True,
        index=True,
        compute='_compute_public_notes_text')

    internal_notes = fields.Html(
        string='Internal Notes',)

    publication_text = fields.Html(
        string='Publication Text',
        default=_default_publication_text,
        translate=True,)

    final_paragraph = fields.Html(
        string='Final Paragraph',
        translate=True,)

    is_wua_portal_user = fields.Boolean(
        string='WUA portal user',
        compute_sudo=True,
        compute='_compute_is_wua_portal_user')

    is_wua_manager = fields.Boolean(
        string='WUA manager',
        compute_sudo=True,
        compute='_compute_is_wua_manager')

    agendaitem_ids = fields.One2many(
        string='Agenda Items',
        comodel_name='wua.agendaitem',
        inverse_name='assembly_id',)

    number_of_agendaitems = fields.Integer(
        string='Number of agenda items',
        compute='_compute_number_of_agendaitems',)

    attendance_ids = fields.One2many(
        string='Attendances',
        comodel_name='wua.attendance',
        inverse_name='assembly_id',)

    number_of_attendances = fields.Integer(
        string='Number of attendances',
        compute='_compute_number_of_attendances',)

    number_of_attendances_in_assembly = fields.Integer(
        string='Number of attendances (in assembly)',
        compute='_compute_number_of_attendances_in_assembly',)

    number_of_ballotpapers_in_assembly = fields.Integer(
        string='Number of ballot papers (in assembly)',
        compute='_compute_number_of_ballotpapers_in_assembly',)

    delegationvote_ids = fields.One2many(
        string='Delegations of vote',
        comodel_name='wua.delegationvote',
        inverse_name='assembly_id',)

    number_of_delegations = fields.Integer(
        string='Number of delegations of vote',
        compute='_compute_number_of_delegations',)

    representation_ids = fields.One2many(
        string='Representations',
        comodel_name='wua.representation',
        inverse_name='assembly_id',)

    number_of_representations = fields.Integer(
        string='Number of representations',
        compute='_compute_number_of_representations',)

    number_of_attendances_with_signature = fields.Integer(
        string='Number of confirmed attendances',
        compute='_compute_number_of_attendances_with_signature',)

    number_of_possible_votes = fields.Integer(
        string='Number of possible votes',
        compute='_compute_number_of_possible_votes',)

    current_year = fields.Boolean(
        string='Current Year',
        compute='_compute_current_year',
        search='_search_current_year',)

    color = fields.Integer(
        string='State Color',
        compute='_compute_color',)

    rendered_publication_text = fields.Html(
        string='Preview of publication text',
        compute='_compute_rendered_publication_text',)

    rendered_final_paragraph = fields.Html(
        string='Preview of final paragraph',
        compute='_compute_rendered_final_paragraph',)

    delegation_vote_main_text = fields.Html(
        string='Delegation vote main text',
        default=_default_delegation_vote_main_text,
    )

    rendered_delegation_vote_main_text = fields.Html(
        string='Rendered delegation vote main text',
        compute="_compute_rendered_delegation_vote_main_text",
    )

    delegation_vote_footer_text = fields.Html(
        string='Delegation vote footer text',
        default=_default_delegation_vote_footer_text,
    )

    rendered_delegation_vote_footer_text = fields.Html(
        string='Rendered delegation vote footer text',
        compute="_compute_rendered_delegation_vote_footer_text",)

    representation_main_text = fields.Html(
        string='Representation main text',
        default=_default_representation_main_text,)

    rendered_representation_main_text = fields.Html(
        string='Rendered representation main text',
        compute="_compute_rendered_representation_main_text",)

    representation_footer_text = fields.Html(
        string='Representation footer text',
        default=_default_representation_footer_text,)

    rendered_representation_footer_text = fields.Html(
        string='Rendered representation footer text',
        compute="_compute_rendered_representation_footer_text",)

    date_now = fields.Datetime(
        default=datetime.datetime.now())

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a call for an assembly for the indicated date.'),
        ('valid_first_hour', 'CHECK (first_hour < 24)',
         'The first hour must be a value less than 24.'),
        ('valid_second_hour', 'CHECK (second_hour < 24)',
         'The second hour must be a value less than 24.'),
        ]

    @api.depends('assembly_date', 'first_hour')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.assembly_date and record.first_hour >= 0:
                name = record.assembly_date + 'T' + \
                    str(int((record.first_hour))).zfill(2) + ':' + \
                    str(int(round((record.first_hour % 1) * 60))).zfill(2) + \
                    ':00'
            record.name = name

    @api.multi
    def _compute_company_id(self):
        for record in self:
            resp = None
            current_company_id = self.env.user.company_id
            if current_company_id:
                resp = current_company_id
            record.company_id = resp

    @api.multi
    def _compute_is_multicompany(self):
        for record in self:
            resp = False
            company_ids = self.env.user.company_ids
            if len(company_ids) > 1:
                resp = True
            record.is_multicompany = resp

    @api.multi
    def _compute_president_id_portaluser(self):
        for record in self:
            president_id_portaluser = None
            if record.president_id:
                president_id_portaluser = record.president_id
            record.president_id_portaluser = president_id_portaluser

    @api.multi
    def _compute_secretary_id_portaluser(self):
        for record in self:
            secretary_id_portaluser = None
            if record.secretary_id:
                secretary_id_portaluser = record.secretary_id
            record.secretary_id_portaluser = secretary_id_portaluser

    @api.multi
    def _compute_first_hour_hhmm(self):
        for record in self:
            record.first_hour_hhmm = self._get_hour_hhmm(record.first_hour)

    @api.multi
    def _compute_second_hour_hhmm(self):
        for record in self:
            record.second_hour_hhmm = self._get_hour_hhmm(record.second_hour)

    def _get_hour_hhmm(self, hour_as_num):
        resp = '00:00'
        if hour_as_num:
            fractional_part = hour_as_num % 1
            hours = int(hour_as_num)
            minutes = int(round(fractional_part * 60))
            resp = str(hours).zfill(2) + ':' + \
                str(minutes).zfill(2)
        return resp

    @api.depends('public_notes')
    def _compute_public_notes_text(self):
        model_converter = self.env["ir.fields.converter"]
        for record in self:
            public_notes_text = ''
            if record.public_notes:
                public_notes_text = model_converter.text_from_html(
                    record.public_notes, 50, 150)
            record.public_notes_text = public_notes_text

    @api.multi
    def _compute_is_wua_portal_user(self):
        is_wua_portal_user = self.env.user.has_group(
            'base_wua.group_wua_portal_user')
        for record in self:
            record.is_wua_portal_user = is_wua_portal_user

    @api.multi
    def _compute_is_wua_manager(self):
        is_wua_manager = self.env.user.has_group(
            'base_wua.group_wua_manager')
        for record in self:
            record.is_wua_manager = is_wua_manager

    @api.multi
    def _compute_number_of_agendaitems(self):
        for record in self:
            number_of_agendaitems = 0
            if record.agendaitem_ids:
                number_of_agendaitems = len(record.agendaitem_ids)
            record.number_of_agendaitems = number_of_agendaitems

    @api.multi
    def _compute_number_of_attendances(self):
        for record in self:
            number_of_attendances = 0
            if record.attendance_ids:
                number_of_attendances = len(record.attendance_ids)
            record.number_of_attendances = number_of_attendances

    @api.multi
    def _compute_number_of_attendances_in_assembly(self):
        for record in self:
            number_of_attendances_in_assembly = 0
            if record.attendance_ids:
                for attendance in record.attendance_ids:
                    if attendance.votes_total > 0:
                        number_of_attendances_in_assembly = \
                            number_of_attendances_in_assembly + 1
            record.number_of_attendances_in_assembly = \
                number_of_attendances_in_assembly

    @api.multi
    def _compute_number_of_ballotpapers_in_assembly(self):
        for record in self:
            record.number_of_ballotpapers_in_assembly = \
                record.number_of_attendances_in_assembly

    @api.multi
    def _compute_number_of_delegations(self):
        for record in self:
            number_of_delegations = 0
            if record.delegationvote_ids:
                number_of_delegations = len(record.delegationvote_ids)
            record.number_of_delegations = number_of_delegations

    @api.multi
    def _compute_number_of_representations(self):
        for record in self:
            number_of_representations = 0
            if record.representation_ids:
                number_of_representations = len(record.representation_ids)
            record.number_of_representations = number_of_representations

    @api.multi
    def _compute_number_of_attendances_with_signature(self):
        for record in self:
            number_of_attendances_with_signature = 0
            if record.attendance_ids:
                attendances_with_signature = filter(
                    lambda x: x['present'],
                    record.attendance_ids)
                number_of_attendances_with_signature = \
                    len(attendances_with_signature)
            record.number_of_attendances_with_signature = \
                number_of_attendances_with_signature

    @api.multi
    def _compute_number_of_possible_votes(self):
        for record in self:
            number_of_possible_votes = 0
            if record.attendance_ids:
                attendances_with_signature = filter(
                    lambda x: x['present'],
                    record.attendance_ids)
                if attendances_with_signature:
                    number_of_possible_votes = \
                        sum(x.votes_total for x in attendances_with_signature)
            record.number_of_possible_votes = number_of_possible_votes

    @api.multi
    def _compute_current_year(self):
        this_year = datetime.datetime.now().year
        for record in self:
            current_year = False
            if record.assembly_date:
                assembly_date_str = str(record.assembly_date)
                if len(assembly_date_str) == 10:
                    year = int(assembly_date_str[:4])
                    if year == this_year:
                        current_year = True
            record.current_year = current_year

    @api.model
    def _search_current_year(self, operator, value):
        record_ids = []
        get_assemblies_of_current_year = (operator == '=' and value)
        this_year = datetime.datetime.now().year
        limit_this_year_lower = str(this_year) + '-01-01'
        limit_this_year_upper = str(this_year) + '-12-31'
        condition = [('assembly_date', '>=', limit_this_year_lower),
                     ('assembly_date', '<=', limit_this_year_upper)]
        if not get_assemblies_of_current_year:
            condition = ['|', ('assembly_date', '<', limit_this_year_lower),
                         ('assembly_date', '>', limit_this_year_upper)]
        assemblies = self.search(condition)
        if assemblies:
            record_ids = assemblies.ids
        return ([('id', 'in', record_ids)])

    @api.multi
    def _compute_color(self):
        for record in self:
            color = 0
            if record.state:
                if record.state == '01_draft':
                    color = 1
                if record.state == '02_called':
                    color = 3
                if record.state == '03_in_progress':
                    color = 7
                if record.state == '04_finished':
                    color = 6
            record.color = color

    @api.model
    def _compute_rendered_publication_text(self):
        for record in self:
            rendered_publication_text = ''
            if record.publication_text:
                rendered_publication_text = \
                    record.sudo()._get_rendered_text()
            record.rendered_publication_text = rendered_publication_text

    @api.model
    def _compute_rendered_final_paragraph(self):
        for record in self:
            rendered_final_paragraph = ''
            if record.final_paragraph:
                rendered_final_paragraph = \
                    record.sudo()._get_rendered_text(publication_text=False)
            record.rendered_final_paragraph = rendered_final_paragraph

    @api.multi
    def _compute_rendered_delegation_vote_footer_text(self):
        for record in self:
            rendered_delegation_vote_footer_text = ''
            if record.delegation_vote_footer_text:
                rendered_delegation_vote_footer_text = \
                    record.sudo()._get_rendered_delegation_vote_footer_text()
            record.rendered_delegation_vote_footer_text = \
                rendered_delegation_vote_footer_text

    @api.multi
    def _compute_rendered_delegation_vote_main_text(self):
        for record in self:
            rendered_delegation_vote_main_text = ''
            if record.delegation_vote_main_text:
                rendered_delegation_vote_main_text = \
                    record.sudo()._get_rendered_delegation_vote_main_text()
            record.rendered_delegation_vote_main_text = \
                rendered_delegation_vote_main_text

    @api.multi
    def _compute_rendered_representation_footer_text(self):
        for record in self:
            rendered_representation_footer_text = ''
            if record.representation_footer_text:
                rendered_representation_footer_text = \
                    record.sudo()._get_rendered_representation_footer_text()
            record.rendered_representation_footer_text = \
                rendered_representation_footer_text

    @api.multi
    def _compute_rendered_representation_main_text(self):
        for record in self:
            rendered_representation_main_text = ''
            if record.representation_main_text:
                rendered_representation_main_text = \
                    record.sudo()._get_rendered_representation_main_text()
            record.rendered_representation_main_text = \
                rendered_representation_main_text

    def _get_rendered_text(self, publication_text=True):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            date_of_assembly = datetime.datetime.strptime(self.assembly_date,
                                                          '%Y-%m-%d')
            text_to_render = self.publication_text
            if not publication_text:
                text_to_render = self.final_paragraph
            template = Template(text_to_render)
            resp = template.render(
                assembly=self,
                assembly_day=dates.format_date(date_of_assembly,
                                               'd', locale=lang),
                assembly_month=dates.format_date(date_of_assembly,
                                                 'LLLL', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    def _get_rendered_delegation_vote_footer_text(self):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            if self.assembly_date:
                date_of_assembly = datetime.datetime.strptime(
                    self.assembly_date, '%Y-%m-%d')
                template = Template(self.delegation_vote_footer_text)
                resp = template.render(
                    assembly=self,
                    assembly_day=dates.format_date(
                        date_of_assembly, 'd', locale=lang),
                    assembly_month=dates.format_date(
                        date_of_assembly, 'LLLL', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    def _get_rendered_delegation_vote_main_text(self):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            if self.assembly_date:
                date_of_assembly = datetime.datetime.strptime(
                    self.assembly_date, '%Y-%m-%d')
                template = Template(self.delegation_vote_main_text)
                resp = template.render(
                    assembly=self,
                    assembly_day=dates.format_date(
                        date_of_assembly, 'd', locale=lang),
                    assembly_month=dates.format_date(
                        date_of_assembly, 'LLLL', locale=lang),
                    assembly_year=dates.format_date(
                        date_of_assembly, 'Y', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    def _get_rendered_representation_main_text(self):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            if self.assembly_date:
                date_of_assembly = datetime.datetime.strptime(
                    self.assembly_date, '%Y-%m-%d')
                template = Template(self.representation_main_text)
                resp = template.render(
                    assembly=self,
                    assembly_day=dates.format_date(
                        date_of_assembly, 'd', locale=lang),
                    assembly_month=dates.format_date(
                        date_of_assembly, 'LLLL', locale=lang),
                    assembly_year=dates.format_date(
                        date_of_assembly, 'Y', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    def _get_rendered_representation_footer_text(self):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            if self.assembly_date:
                date_of_assembly = datetime.datetime.strptime(
                    self.assembly_date, '%Y-%m-%d')
                template = Template(self.representation_footer_text)
                resp = template.render(
                    assembly=self,
                    assembly_day=dates.format_date(
                        date_of_assembly, 'd', locale=lang),
                    assembly_month=dates.format_date(
                        date_of_assembly, 'LLLL', locale=lang),)
        except TemplateError as e:
            resp = '<p style="text-align:center;color:red;">' + \
                '<b><font style="font-size: 14px;">' + \
                _('ERROR IN TEMPLATE') + '</font></b></p>' + \
                '<p><br>' + e.message + '</p>'
        return resp

    @api.constrains('assembly_date', 'convocation_date')
    def _check_assembly_and_convocation_dates(self):
        for record in self:
            if (record.assembly_date and record.convocation_date and
               record.convocation_date >= record.assembly_date):
                raise exceptions.UserError(
                    _('The assembly date must be after the convocation date.'))

    @api.constrains('first_hour', 'second_hour')
    def _check_first_and_second_hours(self):
        for record in self:
            if (record.first_hour and record.second_hour and
               record.first_hour > record.second_hour):
                raise exceptions.UserError(
                    _('The second hour must be after the first hour.'))

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if not self.country_id and self.state_id:
            self.country_id = self.state_id.country_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            return {'domain': {'state_id':
                               [('country_id', '=',
                                 self.country_id.id)]}}
        else:
            return {'domain': {'state_id': []}}

    @api.multi
    def write(self, vals):
        for record in self:
            if (record.state == '03_in_progress' and
               'state' in vals and vals['state'] == '02_called'):
                for agendaitem in record.agendaitem_ids:
                    agendaitem.write({
                        'count_yes': 0,
                        'count_no': 0,
                        'count_abstention': 0,
                        'count_null': 0,
                        'final_summary': '',
                        })
                    if agendaitem.option_ids:
                        agendaitem.option_ids.write({
                            'count_option': 0,
                            })
        super(WuaAssembly, self).write(vals)
        return True

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        if (self.env.context and 'lang' in self.env.context):
            is_english = self.env.context['lang'] == 'en_US'
        else:
            is_english = True
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                assembly_date_str = datetime.datetime.strptime(
                    record.assembly_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = assembly_date_str + ' (' + record.issue + ')'
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != '01_draft':
                raise exceptions.UserError(_('It is only allowed to delete '
                                             'an assembly '
                                             'in \'DRAFT\' state.'))
        super(WuaAssembly, self).unlink()

    @api.multi
    def action_go_to_state_02_called(self):
        self.ensure_one()
        new_data = {'state': '02_called'}
        if not self.convocation_date:
            new_data.update({'convocation_date': fields.datetime.now()})
        self.write(new_data)
        self.generate_attendances()

    @api.multi
    def action_return_to_state_01_draft(self):
        self.ensure_one()
        self.state = '01_draft'
        self.reset_attendances()

    @api.multi
    def action_go_to_state_03_in_progress(self):
        self.ensure_one()
        delegationvote_draft = self.env['wua.delegationvote'].search(
            [('state', '=', '01_draft')])
        representation_draft = self.env['wua.representation'].search(
            [('state', '=', '01_draft')])
        if delegationvote_draft or representation_draft:
           raise exceptions.UserError(_('There are still delegations of vote or representations in draft state.'))
        else:
            self.generate_attendances(final_list=True)
            self.state = '03_in_progress'

    @api.multi
    def action_return_to_state_02_called(self):
        self.ensure_one()
        self.generate_attendances()
        self.state = '02_called'

    @api.multi
    def action_go_to_state_04_finished(self):
        self.ensure_one()
        self.state = '04_finished'

    @api.multi
    def action_return_to_state_03_in_progress(self):
        self.ensure_one()
        self.state = '03_in_progress'

    @api.multi
    def reset_attendances(self):
        self.ensure_one()
        self.attendance_ids.unlink()

    @api.multi
    def _get_partners_domain(self):
        return [('is_wua_partner', '=', True), ('is_owner', '=', True)]

    @api.multi
    def generate_attendances(self, final_list=False):
        self.ensure_one()
        self.reset_attendances()
        partner_domain = self._get_partners_domain()
        partners = self.env['res.partner'].search(partner_domain)
        if partners:
            model_wua_attendance = self.env['wua.attendance']
            for partner in partners:
                assembly_id = self.id
                partner_id = partner.id
                votes_owned = partner.number_of_votes
                model_wua_attendance.create({
                    'assembly_id': assembly_id,
                    'partner_id': partner_id,
                    'votes_owned': votes_owned,
                    })
            if final_list:
                # Delegations of vote
                for delegationvote in (self.delegationvote_ids or []):
                    if delegationvote.state == '01_draft':
                        continue
                    grantor_attendance = model_wua_attendance.search(
                        [('assembly_id', '=', self.id),
                         ('partner_id', '=', delegationvote.grantor_id.id)])
                    receiver_attendance = model_wua_attendance.search(
                        [('assembly_id', '=', self.id),
                         ('partner_id', '=', delegationvote.receiver_id.id)])
                    if grantor_attendance and receiver_attendance:
                        grantor_attendance = grantor_attendance[0]
                        receiver_attendance = receiver_attendance[0]
                        votes_delegation = \
                            delegationvote.grantor_id.number_of_votes
                        grantor_attendance.write({
                            'votes_delegation': -votes_delegation,
                            'receiver_id': receiver_attendance.partner_id.id,
                            })
                        receiver_attendance.write({
                            'votes_delegation':
                                receiver_attendance.votes_delegation +
                                votes_delegation,
                            })
                # Final test: is the TIN present?
                vat_required = self.env['ir.values'].get_default(
                    'wua.assembly.configuration', 'vat_required')
                if vat_required:
                    attendances_without_vat = model_wua_attendance.search(
                        [('assembly_id', '=', self.id),
                         ('votes_total', '>', 0),
                         ('vat_participant', '=', False)])
                    if attendances_without_vat:
                        names_without_vat = ''
                        for attendance in attendances_without_vat:
                            names_without_vat = names_without_vat + '\n' + \
                                attendance.participant_id.name
                        error_message = _('The next participants does not '
                                          'have TIN assigned (assigning a '
                                          'TIN is required):')
                        raise exceptions.UserError(
                            error_message + '\n' + names_without_vat)

    @api.multi
    def action_preview_publication_text(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Preview of the header of the assembly convocation'),
            'res_model': 'wizard.preview.publicationtext',
            'src_model': 'wua.assembly',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    @api.multi
    def action_preview_final_paragraph(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Preview of the final paragraph of the assembly convocation'),
            'res_model': 'wizard.preview.publicationtext',
            'src_model': 'wua.assembly',
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_final_paragraph': True},
            }
        return act_window

    @api.multi
    def action_get_agendaitems(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_agendaitem_particular_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_assembly.wua_agendaitem_particular_view_form').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_agendaitem_particular_view_search')
        custom_context = \
            {'default_assembly_id': current_assembly.id,
             'show_only_itemnumber': True, }
        suffix_title = current_assembly._get_state_clarification()
        if (current_assembly.state == '03_in_progress' or
           current_assembly.state == '04_finished'):
            suffix_title = suffix_title + ' - ' + \
                str(current_assembly.number_of_possible_votes) + ' ' + \
                _('possible votes') + ' -'
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Agenda Items') + ' ' + suffix_title,
            'res_model': 'wua.agendaitem',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id)],
            'context': custom_context,
            }
        return act_window

    @api.multi
    def _get_state_clarification(self):
        self.ensure_one()
        resp = ''
        if self.state:
            resp = '('
            if self.state == '01_draft':
                resp = resp + _('DRAFT')
            if self.state == '02_called':
                resp = resp + _('CALLED')
            if self.state == '03_in_progress':
                resp = resp + _('IN PROGRESS')
            if self.state == '04_finished':
                resp = resp + _('FINISHED')
            resp = resp + ')'
        return resp

    @api.multi
    def action_get_delegationvotes(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_delegationvote_particular_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_assembly.wua_delegationvote_particular_view_form').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_delegationvote_particular_view_search')
        custom_context = \
            {'default_assembly_id': current_assembly.id,
             'show_only_grantor': True, }
        suffix_title = current_assembly._get_state_clarification()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Delegations of vote') + ' ' + suffix_title,
            'res_model': 'wua.delegationvote',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id)],
            'context': custom_context,
            }
        return act_window

    @api.multi
    def action_get_representations(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_representation_particular_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_assembly.wua_representation_particular_view_form').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_representation_particular_view_search')
        custom_context = \
            {'default_assembly_id': current_assembly.id,
             'show_only_partner': True, }
        suffix_title = current_assembly._get_state_clarification()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Representations') + ' ' + suffix_title,
            'res_model': 'wua.representation',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id)],
            'context': custom_context,
            }
        return act_window

    @api.multi
    def action_get_attendances_calls(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_attendance_calls_particular_view_tree').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_attendance_calls_particular_view_search')
        custom_context = {'initial_calls': True}
        suffix_title = current_assembly._get_state_clarification()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Calls') + ' ' + suffix_title,
            'res_model': 'wua.attendance',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id)],
            'context': custom_context,
            'limit': 10000000,
            }
        return act_window

    @api.multi
    def action_get_ballotpapers(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_attendance_ballotpaper_view_tree').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_attendance_ballotpaper_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('BALLOT PAPERS'),
            'res_model': 'wua.attendance',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id),
                       ('potential_attendee', '=', True)],
            }
        return act_window

    @api.multi
    def action_get_attendances(self):
        self.ensure_one()
        current_assembly = self
        id_tree_view = self.env.ref(
            'base_wua_assembly.wua_attendance_particular_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_assembly.wua_attendance_particular_view_form').id
        search_view = self.env.ref(
            'base_wua_assembly.wua_attendance_particular_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('ATTENDEES'),
            'res_model': 'wua.attendance',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': [search_view.id],
            'target': 'current',
            'domain': [('assembly_id', '=', current_assembly.id),
                       ('potential_attendee', '=', True),
                       ('votes_total', '>', 0)],
            'context': {'show_only_participant': True},
            }
        if self.is_wua_manager and self.state == '03_in_progress':
            act_window['flags'] = {'initial_mode': 'edit'}
        return act_window
