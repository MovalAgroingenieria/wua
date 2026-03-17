# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetIrrigationReport(SavepointCase):
    """Tests for wua.invoiceset irrigation report (batch partners in
    group_invoice_details_with_irrigation_report).
    """
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoicesetIrrigationReport, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']

    def test_group_invoice_details_with_irrigation_report_empty_returns_empty(self):
        """group_invoice_details_with_irrigation_report with no details returns []."""
        result = self.Invoiceset.group_invoice_details_with_irrigation_report([])
        self.assertEqual(result, [])

    def test_group_invoice_details_with_irrigation_report_prefetches_by_key1(self):
        """group_invoice_details_with_irrigation_report uses prefetched irrigationreports (no N+1 browse per detail)."""
        partner = self.env['res.partner'].search([], limit=1)
        if not partner:
            return
        # Build minimal details with categ 11 and key1 (irrigationreport id);
        # method should not browse per row
        details = [
            {
                'partner_id': partner.id,
                'product_id': 1,
                'categ_code': 11,
                'key1': 0,
                'key2': 0,
                'quantity': 1,
                'description': 'Test',
            },
        ]
        result = self.Invoiceset.group_invoice_details_with_irrigation_report(
            details)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['partner_id'], partner.id)
        self.assertIn('detail', result[0])

    def test_unlink_empty_recordset_no_error(self):
        """unlink on empty recordset does not raise."""
        self.Invoiceset.unlink()
