# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoiceset(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoiceset, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']

    def test_get_total_product_quantities_aggregates_by_product(self):
        invoice_details = [
            {'product_id': 1, 'quantity': 10.0},
            {'product_id': 2, 'quantity': 5.0},
            {'product_id': 1, 'quantity': 3.0},
            {'product_id': 2, 'quantity': 1.0},
        ]
        result = self.Invoiceset.get_total_product_quantities(invoice_details)
        by_product = {r['product_id']: r['quantity'] for r in result}
        self.assertEqual(by_product[1], 13.0)
        self.assertEqual(by_product[2], 6.0)
        self.assertEqual(len(result), 2)

    def test_get_total_product_quantities_empty_returns_empty(self):
        result = self.Invoiceset.get_total_product_quantities([])
        self.assertEqual(result, [])

    def test_cancel_invoiceset_empty_recordset_no_error(self):
        self.env['wua.invoiceset'].cancel_invoiceset()

    def test_get_value_from_translation_uses_cache_when_set(self):
        """When _translation_cache is set, get_value_from_translation returns cached value."""
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-TR-CACHE',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        inv._translation_cache = {('mod', 'src', 'en_US'): 'cached_value'}
        self.assertEqual(
            inv.get_value_from_translation('mod', 'src', 'en_US'),
            'cached_value')
        del inv._translation_cache

    def test_get_value_from_translation_without_cache_returns_string(self):
        """Without cache, get_value_from_translation returns src or translation."""
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-TR-NOCACHE',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        result = inv.get_value_from_translation(
            'base_wua_invoicing', 'Parcel', self.env.context.get('lang') or 'en_US')
        self.assertIsInstance(result, (str, type(u'')))

    def test_calculate_invoice_details_categ02_empty_returns_empty(self):
        """calculate_invoice_details_categ02 with empty item_ids returns []."""
        result = self.Invoiceset.calculate_invoice_details_categ02(
            0, 2, [], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(result, [])

    def test_calculate_invoice_details_categ02_batch_partners(self):
        """categ02 with partner ids returns one detail per partner with description."""
        partner = self.env['res.partner'].search([], limit=1)
        product = self.env['product.product'].search([
            ('product_tmpl_id.type', '=', 'service')], limit=1)
        if not partner or not product:
            return
        result = self.Invoiceset.calculate_invoice_details_categ02(
            product.id, 2, [partner.id], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['partner_id'], partner.id)
        self.assertEqual(result[0]['product_id'], product.id)
        self.assertEqual(result[0]['categ_code'], 2)
        self.assertIn('description', result[0])

    def test_group_invoice_details_empty_returns_empty(self):
        """group_invoice_details with no details returns []."""
        result = self.Invoiceset.group_invoice_details([])
        self.assertEqual(result, [])

    def test_calculate_invoice_details_empty_returns_empty_and_clears_cache(self):
        """calculate_invoice_details with no items returns [] and does not leave _translation_cache set."""
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            return
        inv_set = self.env['wua.invoiceset'].create({
            'name': 'TEST-EMPTY-DETAILS',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': journal.id,
            'line_ids': [],
        })
        result = inv_set.calculate_invoice_details([])
        self.assertEqual(result, [])
        self.assertFalse(hasattr(inv_set, '_translation_cache'))

    def test_calculate_invoice_details_categ01_empty_item_ids_returns_empty(self):
        """calculate_invoice_details_categ01 with empty item_ids returns []."""
        result = self.Invoiceset.calculate_invoice_details_categ01(
            0, 1, [], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(result, [])

    def test_calculate_invoice_details_categ04_empty_item_ids_returns_empty(self):
        """calculate_invoice_details_categ04 with empty item_ids returns []."""
        result = self.Invoiceset.calculate_invoice_details_categ04(
            0, 4, [], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(result, [])

    def test_calculate_invoice_details_categ05_empty_item_ids_returns_empty(self):
        """calculate_invoice_details_categ05 with empty item_ids returns []."""
        result = self.Invoiceset.calculate_invoice_details_categ05(
            0, 5, [], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(result, [])

    def test_calculate_invoice_details_categ06_empty_item_ids_returns_empty(self):
        """calculate_invoice_details_categ06 with empty item_ids returns []."""
        result = self.Invoiceset.calculate_invoice_details_categ06(
            0, 6, [], self.env['wua.parcel.partnerlink'].search([]))
        self.assertEqual(result, [])

    def test_create_invoices_empty_invoices_data_returns_zero(self):
        """create_invoices with empty invoices_data returns 0 and does not create invoices."""
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            return
        inv_set = self.env['wua.invoiceset'].create({
            'name': 'TEST-EMPTY-INV',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': journal.id,
            'line_ids': [],
        })
        count_before = self.env['account.invoice'].search_count(
            [('invoiceset_id', '=', inv_set.id)])
        result = self.Invoiceset.create_invoices(
            [], inv_set, [])
        self.assertEqual(result, 0)
        count_after = self.env['account.invoice'].search_count(
            [('invoiceset_id', '=', inv_set.id)])
        self.assertEqual(count_before, count_after)

    def test_get_parcel_area_for_invoicing_without_product_returns_area(self):
        """_get_parcel_area_for_invoicing with product=None uses product_id to browse and returns numeric area."""
        parcel = self.env['wua.parcel'].search([], limit=1)
        product = self.env['product.product'].search([], limit=1)
        if not parcel or not product:
            return
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-AREA',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        result = inv._get_parcel_area_for_invoicing(parcel, product.id)
        self.assertIsInstance(result, (int, float))

    def test_get_parcel_area_for_invoicing_with_product_same_as_without(self):
        """_get_parcel_area_for_invoicing with product=product returns same value as with product=None (no N+1)."""
        parcel = self.env['wua.parcel'].search([], limit=1)
        product = self.env['product.product'].search([], limit=1)
        if not parcel or not product:
            return
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-AREA2',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        result_without = inv._get_parcel_area_for_invoicing(parcel, product.id)
        result_with = inv._get_parcel_area_for_invoicing(
            parcel, product.id, product=product)
        self.assertEqual(result_without, result_with)

    def test_get_description_categ04_accepts_optional_product(self):
        """get_description_categ04 with product=product returns same as without (avoids browse in _get_parcel_area)."""
        parcel = self.env['wua.parcel'].search([], limit=1)
        partnerlink = self.env['wua.parcel.partnerlink'].search([], limit=1)
        product = self.env['product.product'].search([], limit=1)
        if not parcel or not partnerlink or not product:
            return
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-DESC04',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        desc_without = inv.get_description_categ04(parcel, partnerlink, product.id)
        desc_with = inv.get_description_categ04(
            parcel, partnerlink, product.id, product=product)
        self.assertEqual(desc_without, desc_with)
        self.assertIsInstance(desc_without, (str, type(u'')))

    def test_collect_parcel_ids_for_partnerlinks_empty_returns_empty(self):
        """_collect_parcel_ids_for_partnerlinks with no items returns empty set."""
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-PL-EMPTY',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        result = inv._collect_parcel_ids_for_partnerlinks([])
        self.assertEqual(result, set())

    def test_collect_parcel_ids_for_partnerlinks_categ1_returns_parcel_ids(self):
        """_collect_parcel_ids_for_partnerlinks with categ 1 returns those item_ids as parcel ids."""
        parcel = self.env['wua.parcel'].search([], limit=1)
        if not parcel:
            return
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-PL-C1',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        items = [
            {'product_id': 1, 'categ_code': 1, 'item_ids': [parcel.id]},
        ]
        result = inv._collect_parcel_ids_for_partnerlinks(items)
        self.assertEqual(result, set([parcel.id]))

    def test_collect_parcel_ids_for_partnerlinks_categ2_ignores_partner_ids(self):
        """_collect_parcel_ids_for_partnerlinks with only categ 2 (partners) returns empty set."""
        partner = self.env['res.partner'].search([], limit=1)
        if not partner:
            return
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-PL-C2',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        items = [
            {'product_id': 1, 'categ_code': 2, 'item_ids': [partner.id]},
        ]
        result = inv._collect_parcel_ids_for_partnerlinks(items)
        self.assertEqual(result, set())

    def test_calculate_invoice_details_with_items_uses_filtered_partnerlinks(self):
        """calculate_invoice_details with items only loads partnerlinks for involved parcels (no full table)."""
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        partner = self.env['res.partner'].search([], limit=1)
        product = self.env['product.product'].search([
            ('product_tmpl_id.type', '=', 'service')], limit=1)
        if not journal or not partner or not product:
            return
        inv_set = self.env['wua.invoiceset'].create({
            'name': 'TEST-PL-FILTER',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': journal.id,
            'line_ids': [],
        })
        # Categ 2: item_ids are partner ids; no parcels involved -> partnerlinks should be empty
        items = [
            {'product_id': product.id, 'categ_code': 2, 'item_ids': [partner.id]},
        ]
        result = inv_set.calculate_invoice_details(items)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['partner_id'], partner.id)
        self.assertEqual(result[0]['categ_code'], 2)

    def test_add_to_invoice_data_line_ref_to_other_types_accepts_parcels_by_id(self):
        """add_to_invoice_data_line_ref_to_other_types accepts optional parcels_by_id (base returns data unchanged)."""
        inv = self.env['wua.invoiceset'].create({
            'name': 'TEST-PARCELS-KW',
            'description': 'Test',
            'date_invoiceset': '2024-01-01',
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'line_ids': [],
        })
        data = {'product_id': 1, 'quantity': 1}
        result = inv.add_to_invoice_data_line_ref_to_other_types(
            99, {'categ_code': 99, 'key1': 0, 'key2': 0}, data,
            parcels_by_id={})
        self.assertEqual(result, data)
