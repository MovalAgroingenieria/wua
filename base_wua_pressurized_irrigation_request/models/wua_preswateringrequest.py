# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json
from lxml import etree
from odoo import models, fields, api, exceptions, _
from datetime import timedelta


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
        track_visibility='onchange',
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

    modification_deadline = fields.Datetime(
        string='Modification Deadline',
        compute='_compute_modification_deadline_data',
    )

    modification_deadline_message = fields.Char(
        string='Modification Deadline Message',
        compute='_compute_modification_deadline_data',
        store=False,
    )

    is_recurrence = fields.Boolean(
        string='Recurrence',
        default=False,
    )

    recurrence_interval = fields.Integer(
        string='Recurrence Interval (days)',
        default=1,
    )

    recurrence_end_date = fields.Date(
        string='Recurrence End Date',
    )

    recurrence_alredy_created = fields.Boolean(
        string='Recurrence Alredy Created',
        default=False,
    )

    from_recurrence = fields.Boolean(
        string='From Recurrence',
        default=False,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The request code must be unique.'),
    ]

    @api.constrains('initial_date', 'partner_id')
    def _check_initial_date_earlier_than_today(self):
        lock_modification_hours = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'lock_modification_hours')
        for record in self:
            initial_datetime = fields.Datetime.from_string(record.initial_date)
            if (fields.Datetime.from_string(fields.Datetime.now()) >=
                    initial_datetime - timedelta(
                        hours=lock_modification_hours)):
                raise exceptions.ValidationError(_(
                    'The start date of the watering request must not be'
                    'earlier than the current date.'))

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

    @api.constrains('recurrence_end_date', 'preswateringperiod_id',
                    'is_recurrence')
    def _check_recurrence_end_date_within_period(self):
        for record in self:
            if record.recurrence_end_date and \
                    record.preswateringperiod_id and record.is_recurrence:
                period = record.preswateringperiod_id
                if not (period.initial_date <= record.recurrence_end_date <=
                        period.end_date):
                    raise exceptions.ValidationError(_(
                        'The end date of the recurrence (%s) must be within '
                        'the period (%s - %s).') % (
                            record.recurrence_end_date,
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

    @api.multi
    def _compute_modification_deadline_data(self):
        for record in self:
            modification_deadline_message = ''
            modification_deadline = None
            if record.presresconsumption_ids:
                modification_deadline_message = record.\
                    presresconsumption_ids[0].modification_deadline_message
                modification_deadline = record.\
                    presresconsumption_ids[0].modification_deadline
            # Write?
            record.modification_deadline_message = \
                modification_deadline_message
            record.modification_deadline = \
                modification_deadline

    def _copy_single_request(self, request, copy_date):
        copy_date_str = copy_date.strftime('%Y-%m-%d')
        new_request_vals = {
            'preswateringperiod_id': request.preswateringperiod_id.id,
            'initial_date': copy_date_str,
            'partner_id': request.partner_id.id,
            'from_recurrence': True,
            'user_id': request.user_id.id,
        }
        if request.presresconsumption_ids:
            presresconsumption_vals = []
            for presresconsumption in request.presresconsumption_ids:
                presresconsumption_vals.append((0, 0, {
                    'waterconnection_id':
                        presresconsumption.waterconnection_id.id,
                    'watering_duration':
                        presresconsumption.watering_duration,
                    'nominal_flow':
                        presresconsumption.nominal_flow,
                    'nominal_flow_ls':
                        presresconsumption.nominal_flow_ls,
                    'initial_hour':
                        presresconsumption.initial_hour,
                }))
            new_request_vals['presresconsumption_ids'] = \
                presresconsumption_vals
        self.env['wua.preswateringrequest'].create(new_request_vals)

    @api.multi
    def generate_recurrences_preswateringrequests(self):
        preswaternigrequests = self.env['wua.preswateringrequest'].search([
            ('is_recurrence', '=', True),
            ('recurrence_alredy_created', '=', False),
        ])
        for record in preswaternigrequests:
            current_date = datetime.datetime.strptime(
                str(record.initial_date), '%Y-%m-%d')
            current_date += timedelta(days=record.recurrence_interval)
            end_date = datetime.datetime.strptime(
                str(record.recurrence_end_date), '%Y-%m-%d')
            while current_date <= end_date:
                self._copy_single_request(record, current_date)
                current_date += timedelta(days=record.recurrence_interval)
            record.recurrence_alredy_created = True

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

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaPreswateringrequest, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        use_flow_ls = self.env['ir.values'].sudo().get_default(
            'wua.irrigation.configuration',
            'preswateringrequest_flow_liters_per_second',
        )
        if view_type in ['form']:
            fields = res.get('fields', {})
            presresconsumption_ids = fields.get('presresconsumption_ids', {})
            views = presresconsumption_ids.get('views', {})
            tree_data = views.get('tree', None)
            if tree_data is not None:
                doc = etree.XML(tree_data['arch'])
                field_visibility = {
                    'nominal_flow': not use_flow_ls,
                    'nominal_flow_ls': use_flow_ls,
                    'nominal_flow_granted': not use_flow_ls,
                    'nominal_flow_ls_granted': use_flow_ls,
                    'nominal_flow_issued': not use_flow_ls,
                    'nominal_flow_ls_issued': use_flow_ls,
                }
                for field, visible in field_visibility.items():
                    for node in doc.xpath("//field[@name='%s']" % field):
                        node.set('invisible', '0' if visible else '1')
                        modifiers = node.get('modifiers')
                        if modifiers:
                            modifiers_dict = json.loads(modifiers)
                        else:
                            modifiers_dict = {}
                        modifiers_dict['tree_invisible'] = not visible
                        modifiers_dict['invisible'] = not visible
                        node.set('modifiers', json.dumps(modifiers_dict))
                tree_data['arch'] = etree.tostring(doc, encoding='unicode')
                res['fields']['presresconsumption_ids']['views']['tree'] = \
                    tree_data
        return res

    @api.multi
    def action_get_waterconnections(self):
        self.ensure_one()
        if self.partner_id and self.partner_id.waterconnectionlink_ids:
            presresconsumptions = []
            waterconnections = self.partner_id.waterconnectionlink_ids.mapped(
                lambda x: x.waterconnection_id)
            for wc in waterconnections:
                presresconsumptions.append((0, 0, {
                    'waterconnection_id': wc.id,
                    # TODO: Needed with 0,0?
                    'preswateringrequest_id': self.id,
                    'nominal_flow': 0,
                    'nominal_flow_ls': 0,
                    'initial_hour': 0,
                }))
            self.presresconsumption_ids = presresconsumptions
            for pres in self.presresconsumption_ids:
                pres._onchange_waterconnection_id()

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
