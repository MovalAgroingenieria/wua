# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ16 = fields.Monetary(
        string='C16: Variable surcharge.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount',
    )

    amount_untaxed_categ17 = fields.Monetary(
        string='C17: Fixed surcharge.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount',
    )

    amount_untaxed_categ18 = fields.Monetary(
        string='C18: Variable surcharge (Total amount).',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount',
    )

    invoiceline_variable_surcharge_ids = fields.One2many(
        string='Invoice Lines Variable Surcharges',
        comodel_name='account.invoice.line',
        inverse_name='invoice_with_variable_surcharge_id',
    )

    invoiceline_fixed_surcharge_ids = fields.One2many(
        string='Invoice Lines Fixed Surcharges',
        comodel_name='account.invoice.line',
        inverse_name='invoice_with_fixed_surcharge_id',
    )

    invoiceline_total_variable_surcharge_ids = fields.One2many(
        string='Invoice Lines Variable Surcharges (Total amount)',
        comodel_name='account.invoice.line',
        inverse_name='invoice_with_total_variable_surcharge_id',
    )

    number_of_variable_surcharges = fields.Integer(
        string='Invoicing Processes Variable Surcharges',
        index=True,
    )

    number_of_fixed_surcharges = fields.Integer(
        string='Invoicing Processes Fixed Surcharges',
        index=True,
    )

    number_of_total_variable_surcharges = fields.Integer(
        string='Invoicing Processes Variable Surcharges (Total amount)',
        index=True,
    )

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            subtotal_by_code = record._get_categ_subtotals()
            record.amount_untaxed_categ16 = subtotal_by_code.get(16, 0.0)
            record.amount_untaxed_categ17 = subtotal_by_code.get(17, 0.0)
            record.amount_untaxed_categ18 = subtotal_by_code.get(18, 0.0)
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ16 - \
                record.amount_untaxed_categ17 - record.amount_untaxed_categ18


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_with_fixed_surcharge_id = fields.Many2one(
        string='Invoice (Fixed Surcharge)',
        comodel_name='account.invoice',
        index=True,
        ondelete='restrict',
    )

    invoice_with_variable_surcharge_id = fields.Many2one(
        string='Invoice (Variable Surcharge)',
        comodel_name='account.invoice',
        index=True,
        ondelete='restrict',
    )

    invoice_with_total_variable_surcharge_id = fields.Many2one(
        string='Invoice (Total Variable Surcharge)',
        comodel_name='account.invoice',
        index=True,
        ondelete='restrict',
    )
