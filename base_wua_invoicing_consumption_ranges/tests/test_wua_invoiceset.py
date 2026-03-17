# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetConsumptionRanges(SavepointCase):
    """Tests for wua.invoiceset consumption ranges logic (batch/grouping)."""
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoicesetConsumptionRanges, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']
        cls.product = cls.env['product.product'].search([], limit=1)

    def test_reorganize_invoice_details_product_empty_details_returns_empty(self):
        """reorganize_invoice_details_product with empty invoice_details returns []."""
        if not self.product:
            return
        result = self.Invoiceset.reorganize_invoice_details_product(
            self.product, [], [])
        self.assertEqual(result, [])
