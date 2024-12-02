# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaPreswateringrequest(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.preswateringrequest'
    _description = 'Preswatering Request'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6

    def _default_partner_id(self):
        resp = None
        partners = self.env['res.partner']
        user = self.env.user
        if not user.has_group('base_wua.group_wua_user'):
            partner = partners.browse(user.partner_id.id)
            if partner.is_wua_partner:
                resp = partner.id
            else:
                parent_partner = False
                if partner.parent_id:
                    parent_partner = partner.parent_id
                if parent_partner and parent_partner.is_wua_partner:
                    resp = parent_partner.id
        return resp

    name = fields.Char(
        string='Code',
        compute='_compute_name',
        store=True,
        index=True,
    )

    preswateringperiod_id = fields.Many2one(
        string='Period',
        comodel_name='wua.preswateringperiod',
        required=True,
        ondelete='restrict',
        index=True,
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id',
        ondelete='restrict',
    )

    partner_id = fields.Many2one(
        string='Irrigator',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict',
        index=True,
        default=_default_partner_id,
    )

    initial_date = fields.Date(
        string='Start Date',
        required=True,
        index=True,
    )

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        required=True,
        readonly=True,
        ondelete='restrict',
        default=lambda self: self.env.user,
    )

    is_portal_user = fields.Boolean(
        string='Created by Irrigator',
        compute='_compute_is_portal_user',
        store=True,
    )

    presresconsumption_ids = fields.One2many(
        string='Consumption Requests',
        comodel_name='wua.presresconsumption',
        inverse_name='preswateringrequest_id',
    )

    number_of_presresconsumptions = fields.Integer(
        string='Number of Consumptions',
        compute='_compute_number_of_presresconsumptions',
        store=False,
    )

    signature_image = fields.Binary(
        string='Signature',
    )

    notes = fields.Html(
        string='Notes',
    )

    notes_user = fields.Html(
        string='Portal Notes',
    )

    is_open = fields.Boolean(
        string='Period is Open',
        compute='_compute_is_open',
        store=True,
        index=True,
    )

    state = fields.Selection(
        string='Status',
        selection=[
            ('01_draft', 'Draft'),
            ('02_validated', 'Validated'),
        ],
        required=True,
        default='01_draft',
        index=True,
    )

    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        compute='_compute_currency_id',
    )

    credit_overdue = fields.Monetary(
        string='Overdue Receivable',
        compute='_compute_credit_overdue',
        help='Overdue amount this customer owes you.',
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The request code must be unique.'),
    ]

    @api.constrains('initial_date', 'preswateringperiod_id')
    def _check_initial_date_within_period(self):
        for record in self:
            if record.initial_date and record.preswateringperiod_id:
                period = record.preswateringperiod_id
                if not (period.initial_date <= record.initial_date <=
                        period.end_date):
                    raise exceptions.ValidationError(_(
                        'The start date of the watering request (%s) must be '
                        'within the period (%s - %s).') % (
                            record.initial_date,
                            period.initial_date,
                            period.end_date,
                        ),
                    )

    @api.constrains('preswateringperiod_id')
    def _check_period_open(self):
        for record in self:
            if (record.preswateringperiod_id and
                    record.preswateringperiod_id.state != '01_open'):
                raise exceptions.ValidationError(_(
                    'Cannot create preswaterinrequests on a closed period '))

    @api.depends('partner_id', 'initial_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.partner_id and record.initial_date:
                name = record.initial_date + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = name

    @api.depends('user_id')
    def _compute_is_portal_user(self):
        for record in self:
            is_portal_user = False
            if (record.user_id):
                is_portal_user = record.user_id.has_group(
                    'base.group_portal')
            record.is_portal_user = is_portal_user

    @api.depends('preswateringperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.preswateringperiod_id:
                agriculturalseason_id = \
                    record.preswateringperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('preswateringperiod_id', 'preswateringperiod_id.state')
    def _compute_is_open(self):
        for record in self:
            is_open = False
            if (record.preswateringperiod_id):
                is_open = record.preswateringperiod_id.state == '01_open'
            record.is_open = is_open

    @api.depends('partner_id')
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.depends('partner_id', 'currency_id')
    def _compute_credit_overdue(self):
        for record in self:
            credit_overdue = 0
            if (record.partner_id and record.currency_id):
                credit_overdue = record.partner_id.credit_overdue
            record.credit_overdue = credit_overdue

    @api.multi
    def _compute_number_of_presresconsumptions(self):
        for record in self:
            number_of_presresconsumptions = 0
            if (record.presresconsumption_ids):
                number_of_presresconsumptions = len(
                    record.presresconsumption_ids)
            record.number_of_presresconsumptions = \
                number_of_presresconsumptions

    @api.model
    def create(self, vals):
        if (not self.env.user.has_group('base_wua.group_wua_user') and
           not self.env['ir.values'].get_default(
               'wua.configuration', 'wua_portal_user_can_edit')):
            raise exceptions.UserError(_(
                'You do not have permission to edit data.'))
        return super(WuaPreswateringrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            if (not self.env.user.has_group('base_wua.group_wua_user') and
               not self.env['ir.values'].get_default(
                   'wua.configuration', 'wua_portal_user_can_edit')):
                raise exceptions.UserError(_(
                    'You do not have permission to edit data.'))
        return super(WuaPreswateringrequest, self).write(vals)

    def change_state_draft(self):
        for record in self:
            record.state = '01_draft'

    def change_state_validated(self):
        for record in self:
            record.state = '02_validated'

    @api.multi
    def unlink(self):
        for record in self:
            if not record.is_open:
                raise exceptions.UserError(_(
                    'You cannot delete a closed press watering request.'))
            if (record.state == '02_validated'):
                raise exceptions.UserError(_(
                    'You cannot delete a validated press watering request.'))
            return super(WuaPreswateringrequest, self).unlink()
