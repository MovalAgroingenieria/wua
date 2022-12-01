# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    irrigationreport_payment_mode_id = fields.Many2one(
        string='Irrigation report: Payment Mode',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    irrigationreport_mandate_required = fields.Boolean(
        string='Irrigation report: Mandate Required',
        compute='_compute_irrigationreport_mandate_required')

    irrigationreport_mandate_id = fields.Many2one(
        string='Irrigation report: Direct Debit Mandate',
        comodel_name='account.banking.mandate',
        ondelete='restrict')

    irrigationreport_separate_invoicing = fields.Boolean(
        string='Irrigation report invoicing ',
        compute='_compute_irrigationreport_separate_invoicing')

    @api.multi
    @api.onchange('irrigationreport_payment_mode_id')
    def _compute_irrigationreport_mandate_required(self):
        for record in self:
            irrigationreport_mandate_required = False
            if (record.irrigationreport_payment_mode_id and
               record.irrigationreport_payment_mode_id.payment_method_id.
               mandate_required):
                irrigationreport_mandate_required = True
            record.irrigationreport_mandate_required = \
                irrigationreport_mandate_required

    @api.multi
    def _compute_irrigationreport_separate_invoicing(self):
        irrigationreport_separate_invoicing = self.env['ir.values'].\
            get_default('wua.invoicing.configuration',
                        'irrigationreport_separate_invoicing')
        for record in self:
            record.irrigationreport_separate_invoicing = \
                irrigationreport_separate_invoicing

    @api.constrains('irrigationreport_mandate_id',
                    'irrigationreport_payment_mode_id', 'id')
    def _check_irrigationreport_mandate_id(self):
        if (len(self) == 1 and self.irrigationreport_mandate_required):
            if (not self.irrigationreport_mandate_id or
               not self.id or
               self.irrigationreport_mandate_id.partner_id.id !=
               self.id or
               self.irrigationreport_mandate_id.state != 'valid'):
                raise exceptions.ValidationError(_(
                    'Irrigation report billing: It is mandatory '
                    'to enter a valid mandate of the partner.')
                )
