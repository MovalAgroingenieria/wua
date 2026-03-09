# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetPressurized(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoicesetPressurized, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']

    def test_group_invoice_details_by_wc_empty_returns_empty(self):
        result = self.Invoiceset.group_invoice_details_by_wc([])
        self.assertEqual(result, [])
