# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaWateringrequest(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.wateringrequest'
    _description = 'Entity (watering request)'
    _order = 'name'

    # Size of field "name".
    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_NAME = 11 + MAX_SIZE_PARTNER_CODE

    def _default_partner_id(self):
        resp = None
        partners = self.env['res.partner']
        user = self.env.user
        if not user.has_group('base_wua.group_wua_user'):
            partner = partners.browse(user.partner_id.id)
            if partner.is_wua_partner:
                resp = partner.id
        return resp

    wateringperiod_id = fields.Many2one(
        string='Watering Period',
        comodel_name='wua.wateringperiod',
        required=True,
        index=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_partner_id)

    name = fields.Char(
        string='Watering Request',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        ondelete='restrict')

    is_open = fields.Boolean(
        string='Open',
        store=True,
        compute='_compute_is_open',
        index=True)

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id',
        ondelete='restrict')

    request_date = fields.Date(
        string='Request Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        required=True,
        readonly=True)

    notes = fields.Html(string='Notes')

    state = fields.Selection([
        ('pending', 'Pending Processing'),
        ('intermediate', 'Intermediate'),
        ('executed', 'Executed'),
        ], string='State',
        index=True,
        store=True,
        compute='_compute_state')

    gravconsumption_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.gravconsumption',
        inverse_name='wateringrequest_id')

    number_of_subparcels = fields.Integer(
        string='Number of subparcels',
        store=True,
        compute='_compute_number_of_subparcels')

    signature_image = fields.Binary(
        string='Signature')

    is_portal_user = fields.Boolean(
        string='Created by the partner',
        default=False,
        store=True,
        compute='_compute_is_portal_user')

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id')

    credit_overdue = fields.Monetary(
        compute='_compute_credit_overdue',
        string='Overdue Receivable',
        help="Overdue amount this customer owes you.")

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Watering Request.'),
        ]

    @api.constrains('gravconsumption_ids')
    def _check_gravconsumption_ids(self):
        if (len(self) == 1 and self.gravconsumption_ids and
                len(self.gravconsumption_ids) > 0):
            for gc in self.gravconsumption_ids:
                if (gc.watering_duration <= 0.0):
                    raise exceptions.ValidationError(_(
                        'Total watering duration must be grater than 0.'))

    @api.depends('wateringperiod_id', 'partner_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.wateringperiod_id and record.partner_id:
                value = record.wateringperiod_id.name + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = value

    @api.depends('wateringperiod_id.state')
    def _compute_is_open(self):
        for record in self:
            if record.wateringperiod_id.state == 'open':
                record.is_open = True
            else:
                record.is_open = False

    @api.depends('wateringperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.wateringperiod_id:
                agriculturalseason_id = \
                    record.wateringperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('gravconsumption_ids')
    def _compute_number_of_subparcels(self):
        for record in self:
            record.number_of_subparcels = \
                len(record.gravconsumption_ids)

    @api.depends('gravconsumption_ids.state')
    def _compute_state(self):
        for record in self:
            state = 'pending'
            is_first = True
            for consumption in record.gravconsumption_ids:
                if consumption.state == 'planned':
                    state = 'intermediate'
                    break
                if is_first:
                    is_first = False
                    if consumption.state == 'executed':
                        state = 'executed'
                else:
                    if (consumption.state == 'executed' and
                       state == 'pending'):
                        state = 'intermediate'
                        break
                    if (consumption.state == 'requested' and
                       state == 'executed'):
                        state = 'intermediate'
                        break
            record.state = state

    @api.depends('user_id')
    def _compute_is_portal_user(self):
        partners = self.env['res.partner']
        for record in self:
            is_portal_user = False
            user = self.env.user
            if not user.has_group('base_wua.group_wua_user'):
                partner = partners.browse(user.partner_id.id)
                if partner.is_wua_partner:
                    is_portal_user = True
            record.is_portal_user = is_portal_user

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

    @api.model
    def create(self, vals):
        if (not self.env.user.has_group('base_wua.group_wua_user') and
           not self.env['ir.values'].get_default(
               'wua.configuration', 'wua_portal_user_can_edit')):
            raise exceptions.UserError(_(
                'You do not have permission to edit data.'))
        if 'irrigationditch_id' in vals:
            del vals['irrigationditch_id']
        self.populate_gravconsumptions_number(vals)
        return super(WuaWateringrequest, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'irrigationditch_id' in vals:
            del vals['irrigationditch_id']
        if len(self) == 1:
            if (not self.env.user.has_group('base_wua.group_wua_user') and
               not self.env['ir.values'].get_default(
                   'wua.configuration', 'wua_portal_user_can_edit')):
                raise exceptions.UserError(_(
                    'You do not have permission to edit data.'))
            self.populate_gravconsumptions_number(vals)
        return super(WuaWateringrequest, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.wateringperiod_id and record.partner_id:
                initial_date_str = datetime.datetime.strptime(
                    record.wateringperiod_id.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.wateringperiod_id.end_date,
                    '%Y-%m-%d').strftime('%x')
                partner_name = record.partner_id.name + ' ' + \
                    '[' + str(record.partner_id.partner_code) + ']'
                name = initial_date_str + ' - ' + end_date_str + ' - ' + \
                    partner_name
            result.append((record.id, name))
        return result

    # A watering request can't be deleted if his state is "executed".
    @api.multi
    def unlink(self):
        for record in self:
            if not record.is_open:
                raise exceptions.UserError(_(
                    'You cannot delete a closed watering request.'))
            if record.state == 'executed':
                raise exceptions.UserError(_(
                    'You cannot delete a executed watering request.'))
            if (not self.env.user.has_group('base_wua.group_wua_user') and
               not self.env['ir.values'].get_default(
                   'wua.configuration', 'wua_portal_user_can_edit')):
                raise exceptions.UserError(_(
                    'You do not have permission to edit data.'))
        return super(WuaWateringrequest, self).unlink()

    def populate_gravconsumptions_number(self, vals):
        if vals and 'gravconsumption_ids' in vals:
            gravconsumption_ids = vals['gravconsumption_ids']
            if gravconsumption_ids:
                # Get a list of dictionaries for parcels with multiple
                # waterings allowed; for each dictionary, the key is
                # the parcel id, and the data is the number of last
                # requested subparcel. ONLY FOR NEW CONSUMPTIONS.
                subparcels = self.env['wua.parcel.subparcel']
                parcels_multiplewaterings_new = []
                for gravconsumption in gravconsumption_ids:
                    if gravconsumption[0] == 0:
                        subparcel_id = gravconsumption[2]['subparcel_id']
                        subparcel_data = subparcels.browse(subparcel_id)
                        if subparcel_data.parcel_id.allow_multiple_waterings:
                            parcels_multiplewaterings_new.append({
                                'parcel_id': subparcel_data.parcel_id.id,
                                'last_number': 0
                                })
                if len(parcels_multiplewaterings_new) > 0:
                    # Get a list of dictionaries for parcels with multiple
                    # waterings allowed; for each dictionary, the key is
                    # the parcel id, and the data is the number of last
                    # requested subparcel. ONLY FOR PRE-EXISTENTS CONSUMPTIONS.
                    gravconsumptions = self.env['wua.gravconsumption']
                    parcels_multiplewaterings_preexist = []
                    for gravconsumption in gravconsumption_ids:
                        if gravconsumption[0] == 4 or gravconsumption[0] == 1:
                            gravconsumption_data = \
                                gravconsumptions.browse(
                                    gravconsumption[1])
                            if (gravconsumption_data.parcel_id.
                               allow_multiple_waterings):
                                parcel_id = gravconsumption_data.parcel_id
                                parcels = filter(
                                    lambda x: x['parcel_id'] == parcel_id,
                                    parcels_multiplewaterings_preexist)
                                if len(parcels) > 0:
                                    parcel = parcels[0]
                                    if (gravconsumption_data.number >
                                       parcel['last_number']):
                                        parcel['last_number'] = \
                                            gravconsumption_data.number
                                else:
                                    parcels_multiplewaterings_preexist.append({
                                        'parcel_id': parcel_id.id,
                                        'last_number':
                                            gravconsumption_data.number
                                        })
                    # Update, if necessary, each item of
                    # parcels_multiplewaterings_new. The last_number will be
                    # updated from last_number of mapped item in
                    # parcels_multiplewaterings_preexist.
                    if len(parcels_multiplewaterings_preexist) > 0:
                        for preexist in parcels_multiplewaterings_preexist:
                            parcel_id = preexist['parcel_id']
                            last_number = preexist['last_number']
                            parcels = filter(
                                lambda x: x['parcel_id'] == parcel_id,
                                parcels_multiplewaterings_new)
                            if len(parcels) > 0:
                                parcel = parcels[0]
                                parcel['last_number'] = last_number
                    # Loop in parcels_multiplewaterings_new to populate
                    # the number field if the consumption is mapped to
                    # a parcel of parcels_multiplewaterings_new.
                    # import wdb; wdb.set_trace()
                    for new in parcels_multiplewaterings_new:
                        parcel_id = new['parcel_id']
                        number = new['last_number'] + 1
                        for gravconsumption in gravconsumption_ids:
                            if gravconsumption[0] == 0:
                                subparcel_id = \
                                    gravconsumption[2]['subparcel_id']
                                subparcel_data = \
                                    subparcels.browse(subparcel_id)
                                if subparcel_data.parcel_id.id == parcel_id:
                                    gravconsumption[2]['number'] = number
                                    number = number + 1
