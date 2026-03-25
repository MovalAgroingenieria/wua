# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetCompute(SavepointCase):
    """Tests for compute methods. Marked post_install so they run in the
    "All post-tested" phase and appear in the log (otherwise 0.00s, 0 queries).
    """
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoicesetCompute, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)

    def test_compute_year_invoiceset(self):
        """year_invoiceset is computed from date_invoiceset (first 4 chars)."""
        inv = self.Invoiceset.create({
            'name': 'TEST-YEAR',
            'description': 'Test year',
            'date_invoiceset': '2024-06-15',
            'journal_id': self.journal.id,
            'line_ids': [],
        })
        self.assertEqual(inv.year_invoiceset, 2024)
        inv.write({'date_invoiceset': '2023-01-01'})
        self.assertEqual(inv.year_invoiceset, 2023)

    def test_compute_configured_invoiceset_empty_lines(self):
        """configured_invoiceset is False when there are no lines."""
        inv = self.Invoiceset.create({
            'name': 'TEST-CFG-EMPTY',
            'description': 'Test empty',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.journal.id,
            'line_ids': [],
        })
        self.assertFalse(inv.configured_invoiceset)

    def test_compute_configured_invoiceset_with_lines_not_configured(self):
        """configured_invoiceset is False when any line has configured_line False."""
        inv = self.Invoiceset.create({
            'name': 'TEST-CFG-PARTIAL',
            'description': 'Test partial',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.journal.id,
            'line_ids': [],
        })
        product = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.env.ref('base_wua_invoicing.product_01').id)
        ], limit=1)
        if not product:
            return
        line = self.env['wua.invoiceset.line'].create({
            'invoiceset_id': inv.id,
            'product_id': product.id,
            'name': 'Test line',
            'quantity': 1.0,
        })
        inv.invalidate_cache()
        # Line has no line_parcel_ids etc, so configured_line is False
        self.assertFalse(inv.configured_invoiceset)
