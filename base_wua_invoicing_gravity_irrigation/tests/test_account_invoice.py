# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest
from odoo.tests.common import SavepointCase


class TestAccountInvoiceGravityIrrigation(SavepointCase):
    """Tests for account.invoice gravity irrigation helpers and compute.
    _get_gravconsumptions_from_lines, _compute_amount (amount_untaxed_categ08).
    """
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceGravityIrrigation, cls).setUpClass()
        cls.Invoice = cls.env['account.invoice']
        cls.partner = cls.env['res.partner'].search([], limit=1)
        if not cls.partner:
            raise unittest.SkipTest('No partner in database')
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)

    def test_get_gravconsumptions_from_lines_empty_returns_empty(self):
        """_get_gravconsumptions_from_lines with no lines returns []."""
        result = self.Invoice._get_gravconsumptions_from_lines([])
        self.assertEqual(result, [])

    def test_compute_amount_amount_untaxed_categ08_empty_lines(self):
        """amount_untaxed_categ08 is 0 when invoice has no lines."""
        if not self.journal:
            return
        inv = self.Invoice.create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'account_id': self.partner.property_account_receivable_id.id,
            'type': 'out_invoice',
        })
        inv._compute_amount()
        self.assertEqual(inv.amount_untaxed_categ08, 0.0)
