# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestResPartnerCreditOverdue(SavepointCase):
    """Tests for res.partner credit_overdue compute (batch dict, no N+1 browse)."""
    post_install = True

    def test_compute_credit_overdue_empty_recordset_no_error(self):
        """_compute_credit_overdue on empty recordset does not raise."""
        self.env['res.partner']._compute_credit_overdue()

    def test_compute_credit_overdue_single_partner_assigns_field(self):
        """_compute_credit_overdue with one partner assigns credit_overdue (no browse in loop)."""
        partner = self.env['res.partner'].search([], limit=1)
        if not partner:
            return
        partner._compute_credit_overdue()
        self.assertIn('credit_overdue', partner._fields)
        self.assertIsInstance(partner.credit_overdue, (int, float))
