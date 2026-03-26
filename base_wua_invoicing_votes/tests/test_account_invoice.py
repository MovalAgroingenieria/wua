# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestAccountInvoiceVotes(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceVotes, cls).setUpClass()
        cls.AccountInvoice = cls.env['account.invoice']

    def test_amount_untaxed_categ22_field_exists(self):
        """amount_untaxed_categ22 field must exist on account.invoice."""
        self.assertIn(
            'amount_untaxed_categ22',
            self.AccountInvoice._fields)

    def test_compute_amount_categ22_zero_without_lines(self):
        """An invoice without lines must have categ22 amount = 0."""
        partner = self.env['res.partner'].search([], limit=1)
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        account = self.env['account.account'].search(
            [('internal_type', '=', 'receivable')], limit=1)
        if not (partner and journal and account):
            return
        invoice = self.AccountInvoice.create({
            'partner_id': partner.id,
            'journal_id': journal.id,
            'account_id': account.id,
        })
        self.assertEqual(invoice.amount_untaxed_categ22, 0)
