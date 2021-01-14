# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    @api.model_cr
    def init(self):
        parcels_with_populated_partner_id = self.env['wua.parcel'].search(
            [('ownershipcosts_partner_id', '!=', None)])
        if not parcels_with_populated_partner_id:
            parcels = self.env['wua.parcel'].search([])
            for parcel in parcels:
                ownershipcosts_partner_id = None
                number_of_partnerlinks_with_ownershipcosts = 0
                possible_partner_id_for_ownershipcosts = None
                for partnerlink in parcel.partnerlink_ids:
                    if partnerlink.ownership_percentage > 0:
                        possible_partner_id_for_ownershipcosts = \
                            partnerlink.partner_id
                        number_of_partnerlinks_with_ownershipcosts = \
                            number_of_partnerlinks_with_ownershipcosts + 1
                if number_of_partnerlinks_with_ownershipcosts == 1:
                    ownershipcosts_partner_id = \
                        possible_partner_id_for_ownershipcosts
                if ownershipcosts_partner_id is not None:
                    parcel.ownershipcosts_partner_id = \
                        ownershipcosts_partner_id

    ownershipcosts_partner_id = fields.Many2one(
        string='Partner for ownership costs',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_ownershipcosts_partner_id')

    ownershipcosts_potentially_billable = fields.Boolean(
        string='With a single payer for ownership costs',
        store=True,
        compute='_compute_ownershipcosts_potentially_billable')

    ownershipcosts_payment_mode_id = fields.Many2one(
        string='Ownership Costs: Payment Mode',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    ownershipcosts_separate_billing = fields.Boolean(
        string='Separate billing for ownership costs',
        store=True,
        compute='_compute_ownershipcosts_separate_billing')

    ownershipcosts_mandate_required = fields.Boolean(
        string='Ownership Costs: Mandate Required',
        compute='_compute_ownershipcosts_mandate_required')

    ownershipcosts_mandate_id = fields.Many2one(
        string='Ownership Costs: Direct Debit Mandate',
        comodel_name='account.banking.mandate',
        ondelete='restrict')

    @api.depends('partnerlink_ids', 'partnerlink_ids.ownership_percentage')
    def _compute_ownershipcosts_partner_id(self):
        for record in self:
            ownershipcosts_partner_id = None
            number_of_partnerlinks = 0
            possible_partner_id = None
            for partnerlink in record.partnerlink_ids:
                if partnerlink.ownership_percentage > 0:
                    possible_partner_id = partnerlink.partner_id
                    number_of_partnerlinks = number_of_partnerlinks + 1
                    if number_of_partnerlinks > 1:
                        break
            if number_of_partnerlinks == 1:
                ownershipcosts_partner_id = possible_partner_id
            record.ownershipcosts_partner_id = ownershipcosts_partner_id

    @api.depends('ownershipcosts_partner_id')
    def _compute_ownershipcosts_potentially_billable(self):
        for record in self:
            ownershipcosts_potentially_billable = False
            if record.ownershipcosts_partner_id:
                ownershipcosts_potentially_billable = True
            record.ownershipcosts_potentially_billable = \
                ownershipcosts_potentially_billable

    @api.depends('ownershipcosts_payment_mode_id')
    def _compute_ownershipcosts_separate_billing(self):
        for record in self:
            ownershipcosts_separate_billing = False
            if record.ownershipcosts_payment_mode_id:
                ownershipcosts_separate_billing = True
            record.ownershipcosts_separate_billing = \
                ownershipcosts_separate_billing

    @api.multi
    def _compute_ownershipcosts_mandate_required(self):
        for record in self:
            ownershipcosts_mandate_required = False
            if (record.ownershipcosts_payment_mode_id and
               record.ownershipcosts_payment_mode_id.payment_method_id.
               mandate_required):
                ownershipcosts_mandate_required = True
            record.ownershipcosts_mandate_required = \
                ownershipcosts_mandate_required

    @api.constrains('ownershipcosts_payment_mode_id',
                    'ownershipcosts_potentially_billable')
    def _check_ownershipcosts_payment_mode_id(self):
        if (len(self) == 1 and (self.ownershipcosts_payment_mode_id and
           not self.ownershipcosts_potentially_billable)):
            raise exceptions.ValidationError(_('Separate parcel billing: '
                                               'there can be no more one '
                                               'payer for the ownership costs'
                                               '.'))

    @api.constrains('ownershipcosts_mandate_id',
                    'ownershipcosts_payment_mode_id',
                    'ownershipcosts_partner_id')
    def _check_ownershipcosts_mandate_id(self):
        if (len(self) == 1 and self.ownershipcosts_mandate_required):
            if (not self.ownershipcosts_mandate_id or
               not self.ownershipcosts_partner_id or
               self.ownershipcosts_mandate_id.partner_id !=
               self.ownershipcosts_partner_id or
               self.ownershipcosts_mandate_id.state != 'valid'):
                raise exceptions.ValidationError(_('Separate parcel billing: '
                                                   'It is mandatory to enter '
                                                   'a valid mandate of the '
                                                   'only partner that pays '
                                                   'the ownership costs.'))

    @api.onchange('ownershipcosts_payment_mode_id')
    def _onchange_ownershipcosts_payment_mode_id(self):
        ownershipcosts_mandate_required = False
        if (self.ownershipcosts_payment_mode_id and
           self.ownershipcosts_payment_mode_id.payment_method_id.
           mandate_required):
            ownershipcosts_mandate_required = True
        self.ownershipcosts_mandate_required = \
            ownershipcosts_mandate_required

    @api.multi
    def write(self, vals):
        # If a payment mode changes from a with-mandate payment mode to
        # a without-mandate payment mode, then it is necessary to delete
        # the original mandate_id.
        if 'ownershipcosts_payment_mode_id' in vals:
            if self.reset_mandate_id(self.ownershipcosts_payment_mode_id,
                                     vals['ownershipcosts_payment_mode_id']):
                vals['ownershipcosts_mandate_id'] = False
        return super(WuaParcel, self).write(vals)
