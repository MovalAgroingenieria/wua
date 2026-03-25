# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest
from odoo.tests.common import SavepointCase


class TestAccountInvoiceComputePressurized(SavepointCase):
    """Tests for account.invoice _compute_amount (amount_untaxed_categ07).
    Marked post_install so they run in the "All post-tested" phase.
    """
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceComputePressurized, cls).setUpClass()
        cls.Invoice = cls.env['account.invoice']
        cls.partner = cls.env['res.partner'].search([], limit=1)
        if not cls.partner:
            raise unittest.SkipTest('No partner in database')
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        cls.product_categ7 = cls.env['product.product'].search([
            ('product_tmpl_id.categ_id.productcategory_code', '=', 7)
        ], limit=1)

    def test_compute_amount_amount_untaxed_categ07_empty_lines(self):
        """amount_untaxed_categ07 is 0 when invoice has no lines."""
        if not self.journal:
            return
        inv = self.Invoice.create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'account_id': self.partner.property_account_receivable_id.id,
            'type': 'out_invoice',
        })
        inv._compute_amount()
        self.assertEqual(inv.amount_untaxed_categ07, 0.0)

    def test_compute_amount_amount_untaxed_categ07_with_categ7_line(self):
        """amount_untaxed_categ07 sums price_subtotal of lines with categ 7."""
        if not self.journal or not self.product_categ7:
            return
        account_revenue = self.env['account.account'].search([
            ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id)
        ], limit=1)
        if not account_revenue:
            return
        inv = self.Invoice.create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'account_id': self.partner.property_account_receivable_id.id,
            'type': 'out_invoice',
        })
        self.env['account.invoice.line'].create({
            'invoice_id': inv.id,
            'product_id': self.product_categ7.id,
            'name': 'Test water',
            'quantity': 10.0,
            'price_unit': 0.5,
            'account_id': account_revenue.id,
        })
        inv._compute_amount()
        self.assertEqual(inv.amount_untaxed_categ07, 5.0)

    def test_get_presconsumptions_from_lines_empty_returns_empty(self):
        """_get_presconsumptions_from_lines with no lines returns []."""
        result = self.Invoice._get_presconsumptions_from_lines([])
        self.assertEqual(result, [])
