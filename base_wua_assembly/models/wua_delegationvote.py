# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaDelegationvote(models.Model):
    _name = 'wua.delegationvote'
    _description = 'Delegation of vote in assamblies'
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

    assembly_id = fields.Many2one(
        string='Assembly',
        comodel_name='wua.assembly',
        index=True,
        required=True,
        ondelete='cascade',)

    grantor_id = fields.Many2one(
        string='Grantor',
        comodel_name='res.partner',
        domain=[('is_wua_partner', '=', True),
                ('is_owner', '=', True),
                ('number_of_votes', '>', 0)],
        index=True,
        required=True,
        ondelete='restrict',)

    receiver_id = fields.Many2one(
        string='Receiver',
        comodel_name='res.partner',
        domain=[('is_wua_partner', '=', True), ('is_owner', '=', True)],
        index=True,
        required=True,
        ondelete='restrict',)

    name = fields.Char(
        string='Delegation Identifier',
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

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'There is already a similar delegation record.'),
        ]

    @api.depends('assembly_id', 'assembly_id.name',
                 'grantor_id', 'grantor_id.partner_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.assembly_id and record.assembly_id.name and
               record.grantor_id and record.grantor_id.partner_code):
                name = record.assembly_id.name + '-' + \
                    str(record.grantor_id.partner_code).zfill(
                        self.SIZE_PARTNER_CODE)
            record.name = name

    @api.depends('assembly_id', 'assembly_id.state')
    def _compute_assembly_state(self):
        for record in self:
            assembly_state = '01_draft'
            if record.assembly_id and record.assembly_id.state:
                assembly_state = record.assembly_id.state
            record.assembly_state = assembly_state

    @api.depends('grantor_id')
    def _compute_transferred_votes(self):
        for record in self:
            transferred_votes = 0
            if record.grantor_id and record.grantor_id.number_of_votes > 0:
                transferred_votes = record.grantor_id.number_of_votes
            record.transferred_votes = transferred_votes

    @api.constrains('grantor_id')
    def _check_grantor(self):
        for record in self:
            if ((not record.grantor_id.is_wua_partner) or
               (not record.grantor_id.is_owner) or
               record.grantor_id.number_of_votes == 0):
                raise exceptions.UserError(
                    _('The grantor must be a owner with votes.'))
            delegations_to_grantor = self.env['wua.delegationvote'].search(
                [('assembly_id', '=', record.assembly_id.id),
                 ('receiver_id', '=', record.grantor_id.id)])
            if delegations_to_grantor:
                raise exceptions.UserError(
                    _('A partner cannot give their votes if they have '
                      'already received votes from other partners.'))

    @api.constrains('receiver_id')
    def _check_receiver(self):
        for record in self:
            if ((not record.receiver_id.is_wua_partner) or
               (not record.receiver_id.is_owner)):
                raise exceptions.UserError(
                    _('The receiver must be a owner.'))

    @api.constrains('grantor_id', 'receiver_id')
    def _check_grantor_and_receiver(self):
        for record in self:
            if record.grantor_id == record.receiver_id:
                raise exceptions.UserError(
                    _('The grantor and the receiver cannot be the same.'))

    @api.model
    def create(self, vals):
        current_assembly_id = \
            self.env.context.get('default_assembly_id', False)
        if current_assembly_id:
            current_assembly = \
                self.env['wua.assembly'].browse(current_assembly_id)
            if current_assembly and current_assembly.state != '02_called':
                raise exceptions.UserError(_('It is only allowed to create '
                                             'a delegation of vote '
                                             'in \'CALLED\' state.'))
        return super(WuaDelegationvote, self).create(vals)

    @api.multi
    def unlink(self):
        for record in self:
            if record.assembly_state != '02_called':
                raise exceptions.UserError(_('It is only allowed to delete '
                                             'a delegation of vote '
                                             'in \'CALLED\' state.'))
        super(WuaDelegationvote, self).unlink()

    @api.multi
    def action_go_to_state_02_validated(self):
        self.ensure_one()
        self.state = '02_validated'

    @api.multi
    def action_return_to_state_01_draft(self):
        self.ensure_one()
        self.state = '01_draft'

    def validate_delegations_of_vote(self, active_delegations_of_vote):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        delegations_of_vote = \
            self.env['wua.delegationvote'].browse(active_delegations_of_vote)
        for delegation_of_vote in delegations_of_vote:
            if (delegation_of_vote.assembly_state != '02_called'):
                raise exceptions.UserError(_(
                    'It is only possible to validate or cancel voting '
                    'delegations when the assembly is in '
                    'the \'CALLED\' state.'))
            if delegation_of_vote.state == '01_draft':
                delegation_of_vote.action_go_to_state_02_validated()

    def cancel_delegations_of_vote(self, active_delegations_of_vote):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        delegations_of_vote = \
            self.env['wua.delegationvote'].browse(active_delegations_of_vote)
        for delegation_of_vote in delegations_of_vote:
            if (delegation_of_vote.assembly_state != '02_called'):
                raise exceptions.UserError(_(
                    'It is only possible to validate or cancel voting '
                    'delegations when the assembly is in '
                    'the \'CALLED\' state.'))
            if delegation_of_vote.state == '02_validated':
                delegation_of_vote.action_return_to_state_01_draft()
