# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from jinja2 import Template, TemplateError
from babel import dates
from odoo import models, fields, api, exceptions, _


class WuaRepresentation(models.Model):
    _name = 'wua.representation'
    _description = 'Agent of a partner in assamblies'
    _order = 'name'

    SIZE_ASSEMBLY_NAME = 10
    SIZE_PARTNER_CODE = 6

    def _default_assembly_state(self):
        resp = '01_draft'
        current_assembly_id = \
            self.env.context.get('default_assembly_id', False)
        if current_assembly_id:
            current_assembly = \
                self.env['wua.assembly'].browse(current_assembly_id)
            if current_assembly:
                resp = current_assembly.state
        return resp

    def _default_representation_main_text(self):
        representation_main_text = _(
            '<div style="text-align: justify;">Mr. <b>{{ partner.name }}</b> '
            'with Community Member No. <b>{{ partner.partner_code }}</b>, by '
            'virtue of the provisions of the perminent articles of the Statut'
            'es of the {{ assembly.president_id.company_id.name }}, <b>AUTHOR'
            'IZE</b>:<br><br>Mr. <b>{{ agent.name }}</b> to represent him '
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
            'bsp;&nbsp; The Communard<br><br><br><br><br>VAT {{ agent.vat_w'
            'ua_legalrep}}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nb'
            'sp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&'
            'nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp'
            ';&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nb'
            'sp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&'
            'nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp'
            ';&nbsp; VAT {{ partner.vat }}<br><br><b>THE COMMUNITY SECRETARY<'
            '/b><br><br><br><br>VAT {{ assembly.secretary_id.vat }}<br></div>'
            '</div>')
        last_record = self.env['wua.representation'].search(
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
        last_record = self.env['wua.representation'].search(
            [], order='write_date desc', limit=1)
        if last_record and last_record.representation_footer_text:
            representation_footer_text = \
                last_record.representation_footer_text
        return representation_footer_text

    assembly_id = fields.Many2one(
        string='Assembly',
        comodel_name='wua.assembly',
        index=True,
        required=True,
        ondelete='cascade',)

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        domain=[('is_wua_partner', '=', True),
                ('is_owner', '=', True),
                ('number_of_votes', '>', 0)],
        index=True,
        required=True,
        ondelete='restrict',)

    agent_id = fields.Many2one(
        string='Agent',
        comodel_name='res.partner',
        index=True,
        required=True,
        ondelete='restrict',)

    name = fields.Char(
        string='Representation Identifier',
        size=SIZE_ASSEMBLY_NAME + SIZE_PARTNER_CODE + 1,
        store=True,
        index=True,
        compute='_compute_name',)

    assembly_state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_called', 'Called'),
            ('03_in_progress', 'In progress'),
            ('04_finished', 'Finished'),
        ],
        string='Assembly State',
        default=_default_assembly_state,
        store=True,
        compute='_compute_assembly_state',)

    state = fields.Selection(
        selection=[
            ('01_draft', 'Draft'),
            ('02_validated', 'Validated'),
        ],
        string='State',
        default='01_draft',)

    transferred_votes = fields.Integer(
        string='Transferred Votes',
        store=True,
        index=True,
        compute='_compute_transferred_votes',)

    notes = fields.Html(
        string='Notes',)

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

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar representation.'),
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

    @api.depends('assembly_id', 'assembly_id.state')
    def _compute_assembly_state(self):
        for record in self:
            assembly_state = '01_draft'
            if record.assembly_id and record.assembly_id.state:
                assembly_state = record.assembly_id.state
            record.assembly_state = assembly_state

    @api.depends('partner_id')
    def _compute_transferred_votes(self):
        for record in self:
            transferred_votes = 0
            if record.partner_id and record.partner_id.number_of_votes > 0:
                transferred_votes = record.partner_id.number_of_votes
            record.transferred_votes = transferred_votes

    @api.multi
    def _compute_rendered_representation_main_text(self):
        for record in self:
            rendered_representation_main_text = ''
            if record.representation_main_text:
                rendered_representation_main_text = \
                    record.sudo()._get_rendered_representation_main_text()
            record.rendered_representation_main_text = \
                rendered_representation_main_text

    @api.multi
    def _compute_rendered_representation_footer_text(self):
        for record in self:
            rendered_representation_footer_text = ''
            if record.representation_footer_text:
                rendered_representation_footer_text = \
                    record.sudo()._get_rendered_representation_footer_text()
            record.rendered_representation_footer_text = \
                rendered_representation_footer_text

    @api.constrains('partner_id')
    def _check_partner_id(self):
        for record in self:
            if ((not record.partner_id.is_wua_partner) or
               (not record.partner_id.is_owner) or
               record.partner_id.number_of_votes == 0):
                raise exceptions.UserError(
                    _('The partner must be a owner with votes.'))

    @api.constrains('agent_id')
    def _check_agent_id(self):
        for record in self:
            if ((not record.agent_id.parent_id) or
               (record.agent_id.parent_id != record.partner_id)):
                raise exceptions.UserError(_('The agent is not a contact '
                                             'associated with the partner.'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            return {'domain':
                    {'agent_id': [('parent_id', '=', self.partner_id.id)]}}

    @api.model
    def create(self, vals):
        current_assembly_id = \
            self.env.context.get('default_assembly_id', False)
        if current_assembly_id:
            current_assembly = \
                self.env['wua.assembly'].browse(current_assembly_id)
            if current_assembly and current_assembly.state != '02_called':
                raise exceptions.UserError(_('It is only allowed to create '
                                             'a representation '
                                             'in \'CALLED\' state.'))
        return super(WuaRepresentation, self).create(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if record.assembly_state != '02_called':
                raise exceptions.UserError(_('It is only allowed to delete '
                                             'a representation '
                                             'in \'CALLED\' state.'))
        super(WuaRepresentation, self).unlink()

    @api.multi
    def action_go_to_state_02_validated(self):
        self.ensure_one()
        self.state = '02_validated'

    @api.multi
    def action_return_to_state_01_draft(self):
        self.ensure_one()
        self.state = '01_draft'

    def validate_representations(self, active_representations):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        representations = \
            self.env['wua.representation'].browse(active_representations)
        for representation in representations:
            if (representation.assembly_state != '02_called'):
                raise exceptions.UserError(_(
                    'It is only possible to validate or cancel '
                    'representations when the assembly is in '
                    'the \'CALLED\' state.'))
            if representation.state == '01_draft':
                representation.action_go_to_state_02_validated()

    def cancel_representations(self, active_representations):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        representations = \
            self.env['wua.representation'].browse(active_representations)
        for representation in representations:
            if (representation.assembly_state != '02_called'):
                raise exceptions.UserError(_(
                    'It is only possible to validate or cancel '
                    'representations when the assembly is in '
                    'the \'CALLED\' state.'))
            if representation.state == '02_validated':
                representation.action_return_to_state_01_draft()

    def _get_rendered_representation_main_text(self):
        resp = ''
        lang = self.env.context['lang']
        if not lang:
            lang = 'en_US'
        try:
            if self.assembly_id.assembly_date:
                date_of_assembly = datetime.strptime(
                    self.assembly_id.assembly_date, '%Y-%m-%d')
                template = Template(self.representation_main_text)
                resp = template.render(
                    assembly=self.assembly_id,
                    partner=self.partner_id,
                    agent=self.agent_id,
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
            if self.assembly_id.assembly_date:
                date_of_assembly = datetime.strptime(
                    self.assembly_id.assembly_date, '%Y-%m-%d')
                template = Template(self.representation_footer_text)
                resp = template.render(
                    assembly=self.assembly_id,
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
