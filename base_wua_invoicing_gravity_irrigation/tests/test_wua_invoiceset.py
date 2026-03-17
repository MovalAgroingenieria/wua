# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetGravityIrrigation(SavepointCase):
    """Tests for wua.invoiceset gravity irrigation (unlink batch, parcels_by_id)."""
    post_install = True

    def test_add_to_invoice_data_line_ref_other_types_uses_parcels_by_id(self):
        """add_to_invoice_data_line_ref_to_other_types uses parcels_by_id when provided (no N+1)."""
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-GRAV-PARCELS',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        parcel = self.env['wua.parcel'].search([], limit=1)
        if not parcel:
            return
        data = {'product_id': 1, 'quantity': 1, 'price_unit': 10}
        line = {'categ_code': 8, 'key1': 0, 'key2': parcel.id}
        parcels_by_id = {parcel.id: parcel}
        result = inv.add_to_invoice_data_line_ref_to_other_types(
            8, line, data.copy(), parcels_by_id=parcels_by_id)
        self.assertEqual(result.get('parcel_id'), parcel.id)
        self.assertEqual(result.get('irrigationgate_id'), 0)

    def test_unlink_empty_recordset_no_error(self):
        """unlink on empty recordset does not raise."""
        self.env['wua.invoiceset'].unlink()
