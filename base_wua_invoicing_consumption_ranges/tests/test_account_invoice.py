# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestAccountInvoiceConsumptionRanges(SavepointCase):
    """Tests for account.invoice helpers used in consumption ranges reports.
    _get_presconsumptions_from_lines, _get_daily_quota_data.
    """
    post_install = True

    def test_get_presconsumptions_from_lines_empty_returns_empty(self):
        """_get_presconsumptions_from_lines with no lines returns []."""
        Invoice = self.env['account.invoice']
        result = Invoice._get_presconsumptions_from_lines([])
        self.assertEqual(result, [])

    def test_get_daily_quota_data_empty_returns_defaults(self):
        """_get_daily_quota_data with no lines returns default dict."""
        Invoice = self.env['account.invoice']
        result = Invoice._get_daily_quota_data([])
        self.assertEqual(result['quota_day'], 0)
        self.assertEqual(result['total_area'], 0)
        self.assertEqual(result['days'], 0)
        self.assertEqual(result['total_consumption'], 0)
        self.assertEqual(result['extra_consumption'], 0)
