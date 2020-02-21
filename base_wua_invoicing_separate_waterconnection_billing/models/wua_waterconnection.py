# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    @api.model_cr
    def init(self):
        waterconnections_with_populated_partner_id = \
            self.env['wua.waterconnection'].search(
                ['|', ('watercosts_partner_id', '!=', None),
                 ('othercosts_partner_id', '!=', None)])
        if not waterconnections_with_populated_partner_id:
            waterconnections = self.env['wua.waterconnection'].search([])
            waterconnections._compute_watercosts_partner_id()
            waterconnections._compute_othercosts_partner_id()

    watercosts_partner_id = fields.Many2one(
        string='Partner for water costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_watercosts_partner_id')

    othercosts_partner_id = fields.Many2one(
        string='Partner for other costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_othercosts_partner_id')

    watercosts_potentially_billable = fields.Boolean(
        string='With a single payer for water costs',
        store=True,
        compute='_compute_watercosts_potentially_billable')

    othercosts_potentially_billable = fields.Boolean(
        string='With a single payer for other costs',
        store=True,
        compute='_compute_othercosts_potentially_billable')

    watercosts_payment_mode_id = fields.Many2one(
        string='Water Costs: Payment Mode',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    othercosts_payment_mode_id = fields.Many2one(
        string='Other Costs: Payment Mode',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    watercosts_separate_billing = fields.Boolean(
        string='Separate billing for water costs',
        store=True,
        compute='_compute_watercosts_separate_billing')

    othercosts_separate_billing = fields.Boolean(
        string='Separate billing for other costs',
        store=True,
        compute='_compute_othercosts_separate_billing')

    watercosts_mandate_required = fields.Boolean(
        string='Water Costs: Mandate Required',
        compute='_compute_watercosts_mandate_required')

    othercosts_mandate_required = fields.Boolean(
        string='Other Costs: Mandate Required',
        compute='_compute_othercosts_mandate_required')

    watercosts_mandate_id = fields.Many2one(
        string='Water Costs: Direct Debit Mandate',
        comodel_name='account.banking.mandate',
        ondelete='restrict')

    othercosts_mandate_id = fields.Many2one(
        string='Other Costs: Direct Debit Mandate',
        comodel_name='account.banking.mandate',
        ondelete='restrict')

    @api.depends('irrigationpoint_ids.parcel_id',
                 'irrigationpoint_ids.parcel_id.partnerlink_ids')
    def _compute_watercosts_partner_id(self):
        for record in self:
            watercosts_partner_id = None
            possible_partners = []
            for irrigationpoint in record.irrigationpoint_ids:
                parcel = irrigationpoint.parcel_id
                for partnerlink in parcel.partnerlink_ids:
                    if partnerlink.water_costs_percentage > 0:
                        possible_partners.append(partnerlink.partner_id.id)
            if possible_partners:
                possible_partners = list(set(possible_partners))
                if len(possible_partners) == 1:
                    watercosts_partner_id = possible_partners[0]
            record.watercosts_partner_id = watercosts_partner_id

    @api.depends('irrigationpoint_ids.parcel_id',
                 'irrigationpoint_ids.parcel_id.partnerlink_ids')
    def _compute_othercosts_partner_id(self):
        for record in self:
            othercosts_partner_id = None
            possible_partners = []
            for irrigationpoint in record.irrigationpoint_ids:
                parcel = irrigationpoint.parcel_id
                for partnerlink in parcel.partnerlink_ids:
                    if partnerlink.other_costs_percentage > 0:
                        possible_partners.append(partnerlink.partner_id.id)
            if possible_partners:
                possible_partners = list(set(possible_partners))
                if len(possible_partners) == 1:
                    othercosts_partner_id = possible_partners[0]
            record.othercosts_partner_id = othercosts_partner_id

    @api.depends('watercosts_partner_id')
    def _compute_watercosts_potentially_billable(self):
        for record in self:
            watercosts_potentially_billable = False
            if record.watercosts_partner_id:
                watercosts_potentially_billable = True
            record.watercosts_potentially_billable = \
                watercosts_potentially_billable

    @api.depends('othercosts_partner_id')
    def _compute_othercosts_potentially_billable(self):
        for record in self:
            othercosts_potentially_billable = False
            if record.othercosts_partner_id:
                othercosts_potentially_billable = True
            record.othercosts_potentially_billable = \
                othercosts_potentially_billable

    @api.depends('watercosts_payment_mode_id')
    def _compute_watercosts_separate_billing(self):
        for record in self:
            watercosts_separate_billing = False
            if record.watercosts_payment_mode_id:
                watercosts_separate_billing = True
            record.watercosts_separate_billing = \
                watercosts_separate_billing

    @api.depends('othercosts_payment_mode_id')
    def _compute_othercosts_separate_billing(self):
        for record in self:
            othercosts_separate_billing = False
            if record.othercosts_payment_mode_id:
                othercosts_separate_billing = True
            record.othercosts_separate_billing = \
                othercosts_separate_billing

    @api.multi
    def _compute_watercosts_mandate_required(self):
        for record in self:
            watercosts_mandate_required = False
            if (record.watercosts_payment_mode_id and
               record.watercosts_payment_mode_id.payment_method_id.
               mandate_required):
                watercosts_mandate_required = True
            record.watercosts_mandate_required = \
                watercosts_mandate_required

    @api.multi
    def _compute_othercosts_mandate_required(self):
        for record in self:
            othercosts_mandate_required = False
            if (record.othercosts_payment_mode_id and
               record.othercosts_payment_mode_id.payment_method_id.
               mandate_required):
                othercosts_mandate_required = True
            record.othercosts_mandate_required = \
                othercosts_mandate_required

    @api.constrains('watercosts_payment_mode_id',
                    'watercosts_potentially_billable')
    def _check_watercosts_payment_mode_id(self):
        if (len(self) == 1 and (self.watercosts_payment_mode_id and
           not self.watercosts_potentially_billable)):
            raise exceptions.ValidationError(_('Separate water connection '
                                               'billing: there can be no more '
                                               'one water payer.'))

    @api.constrains('othercosts_payment_mode_id',
                    'othercosts_potentially_billable')
    def _check_othercosts_payment_mode_id(self):
        if (len(self) == 1 and (self.othercosts_payment_mode_id and
           not self.othercosts_potentially_billable)):
            raise exceptions.ValidationError(_('Separate water connection '
                                               'billing: there can be no more '
                                               'one payer for the other '
                                               'costs.'))

    @api.constrains('watercosts_mandate_id',
                    'watercosts_payment_mode_id',
                    'watercosts_partner_id')
    def _check_watercosts_mandate_id(self):
        if (len(self) == 1 and self.watercosts_mandate_required):
            if (not self.watercosts_mandate_id or
               not self.watercosts_partner_id or
               self.watercosts_mandate_id.partner_id !=
               self.watercosts_partner_id or
               self.watercosts_mandate_id.state != 'valid'):
                raise exceptions.ValidationError(_('Separate water connection '
                                                   'billing: It is mandatory '
                                                   'to enter a valid mandate '
                                                   'of the only partner that '
                                                   'pays the water costs.'))

    @api.constrains('othercosts_mandate_id',
                    'othercosts_payment_mode_id',
                    'othercosts_partner_id')
    def _check_othercosts_mandate_id(self):
        if (len(self) == 1 and self.othercosts_mandate_required):
            if (not self.othercosts_mandate_id or
               not self.othercosts_partner_id or
               self.othercosts_mandate_id.partner_id !=
               self.othercosts_partner_id or
               self.othercosts_mandate_id.state != 'valid'):
                raise exceptions.ValidationError(_('Separate water connection '
                                                   'billing: It is mandatory '
                                                   'to enter a valid mandate '
                                                   'of the only partner that '
                                                   'pays the other costs.'))

    @api.onchange('watercosts_payment_mode_id')
    def _onchange_watercosts_payment_mode_id(self):
        watercosts_mandate_required = False
        if (self.watercosts_payment_mode_id and
           self.watercosts_payment_mode_id.payment_method_id.mandate_required):
            watercosts_mandate_required = True
        self.watercosts_mandate_required = \
            watercosts_mandate_required

    @api.onchange('othercosts_payment_mode_id')
    def _onchange_othercosts_payment_mode_id(self):
        othercosts_mandate_required = False
        if (self.othercosts_payment_mode_id and
           self.othercosts_payment_mode_id.payment_method_id.mandate_required):
            othercosts_mandate_required = True
        self.othercosts_mandate_required = \
            othercosts_mandate_required

    @api.multi
    def write(self, vals):
        # If a payment mode changes from a with-mandate payment mode to
        # a without-mandate payment mode, then it is necessary to delete
        # the original mandate_id.
        if 'watercosts_payment_mode_id' in vals:
            if self.reset_mandate_id(self.watercosts_payment_mode_id,
                                     vals['watercosts_payment_mode_id']):
                vals['watercosts_mandate_id'] = False
        if 'othercosts_payment_mode_id' in vals:
            if self.reset_mandate_id(self.othercosts_payment_mode_id,
                                     vals['othercosts_payment_mode_id']):
                vals['othercosts_mandate_id'] = False
        return super(WuaWaterconnection, self).write(vals)

    def reset_mandate_id(self, old_payment_mode, new_payment_mode_id):
        resp = False
        if (old_payment_mode and
           old_payment_mode.payment_method_id.mandate_required):
            if not new_payment_mode_id:
                resp = True
            else:
                new_payment_mode = \
                    self.env['account.payment.mode'].browse(
                        new_payment_mode_id)
                if not new_payment_mode.payment_method_id.mandate_required:
                    resp = True
        return resp
