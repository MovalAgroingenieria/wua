# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# from odoo.tools.profiler import profile
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        store=True,
        compute='_compute_invoiceset_id',
        ondelete='restrict')

    @api.depends('invoice_id')
    def _compute_invoiceset_id(self):
        for record in self:
            invoiceset_id = None
            if record.invoice_id.invoiceset_id:
                invoiceset_id = record.invoice_id.invoiceset_id
            record.invoiceset_id = invoiceset_id

    # @profile
    def auto_reconcile_lines(self):
        """ This function iterates recursively on the recordset given as parameter as long as it
            can find a debit and a credit to reconcile together. It returns the recordset of the
            account move lines that were not reconciled during the process.
        """
        if not self.ids:
            return self
        sm_debit_move, sm_credit_move = self._get_pair_to_reconcile()
        #there is no more pair to reconcile so return what move_line are left
        if not sm_credit_move or not sm_debit_move:
            return self

        field = self[0].account_id.currency_id and 'amount_residual_currency' or 'amount_residual'
        if not sm_debit_move.debit and not sm_debit_move.credit:
            #both debit and credit field are 0, consider the amount_residual_currency field because it's an exchange difference entry
            field = 'amount_residual_currency'
        if self[0].currency_id and all([x.currency_id == self[0].currency_id for x in self]):
            #all the lines have the same currency, so we consider the amount_residual_currency field
            field = 'amount_residual_currency'
        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            field = 'amount_residual'
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            field = 'amount_residual_currency'
        #Reconcile the pair together
        amount_reconcile = min(sm_debit_move[field], -sm_credit_move[field])
        #Remove from recordset the one(s) that will be totally reconciled
        if amount_reconcile == sm_debit_move[field]:
            self -= sm_debit_move
        if amount_reconcile == -sm_credit_move[field]:
            self -= sm_credit_move

        #Check for the currency and amount_currency we can set
        currency = False
        amount_reconcile_currency = 0
        if sm_debit_move.currency_id == sm_credit_move.currency_id and sm_debit_move.currency_id.id:
            currency = sm_credit_move.currency_id.id
            amount_reconcile_currency = min(sm_debit_move.amount_residual_currency, -sm_credit_move.amount_residual_currency)

        amount_reconcile = min(sm_debit_move.amount_residual, -sm_credit_move.amount_residual)

        if self._context.get('skip_full_reconcile_check') == 'amount_currency_excluded':
            amount_reconcile_currency = 0.0
            currency = self._context.get('manual_full_reconcile_currency')
        elif self._context.get('skip_full_reconcile_check') == 'amount_currency_only':
            currency = self._context.get('manual_full_reconcile_currency')

#         self.env['account.partial.reconcile'].create({
#             'debit_move_id': sm_debit_move.id,
#             'credit_move_id': sm_credit_move.id,
#             'amount': amount_reconcile,
#             'amount_currency': amount_reconcile_currency,
#             'currency_id': currency,
#         })
        if currency:
            self.env.cr.execute("""
                INSERT INTO account_partial_reconcile (create_uid,
                company_id, write_uid, create_date, write_date, debit_move_id,
                credit_move_id, amount, amount_currency, currency_id)
                VALUES (%s, %s, %s, now(), now(), %s, %s, %s, %s, %s)
                """, (self.env.user.id, sm_debit_move.company_id.id,
                      self.env.user.id, sm_debit_move.id,
                      sm_credit_move.id, amount_reconcile,
                      amount_reconcile_currency, currency))
        else:
            self.env.cr.execute("""
                INSERT INTO account_partial_reconcile (create_uid,
                company_id, write_uid, create_date, write_date, debit_move_id,
                credit_move_id, amount, amount_currency)
                VALUES (%s, %s, %s, now(), now(), %s, %s, %s, %s)
                """, (self.env.user.id, sm_debit_move.company_id.id,
                      self.env.user.id, sm_debit_move.id,
                      sm_credit_move.id, amount_reconcile,
                      amount_reconcile_currency))
        self.env.cr.commit()
        self.env.invalidate_all()
        self.env.cr.execute("""
            SELECT id FROM account_partial_reconcile ORDER BY id DESC LIMIT 1
            """)
        id_of_created_record = self.env.cr.fetchone()[0]
        if id_of_created_record:
            created_record = self.env['account.partial.reconcile'].browse(
                id_of_created_record)
            created_record._compute_partial_lines()
            self.env.cr.commit()
            self.env.invalidate_all()

        #Iterate process again on self
        return self.auto_reconcile_lines()
