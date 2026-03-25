# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetHydricmovement(SavepointCase):
    """Tests for wua.invoiceset hydricmovement (batch unlink, guard)."""
    post_install = True

    def test_unlink_empty_recordset_no_error(self):
        """unlink on empty recordset does not raise."""
        self.env['wua.invoiceset'].unlink()
