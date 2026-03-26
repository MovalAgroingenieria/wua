# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestWuaInvoicesetVotes(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestWuaInvoicesetVotes, cls).setUpClass()
        cls.Invoiceset = cls.env['wua.invoiceset']
        cls.Partner = cls.env['res.partner']
        cls.partnerlinks = cls.env['wua.parcel.partnerlink'].search([])

    def _get_service_product(self):
        categ = self.env.ref(
            'base_wua_invoicing_votes.categ_22')
        product = self.env['product.product'].search(
            [('categ_id', '=', categ.id)], limit=1)
        if not product:
            product = self.env['product.product'].search(
                [('type', '=', 'service')], limit=1)
        return product

    def _get_partner_and_set_votes(self, votes):
        """Find an existing WUA partner and set its votes."""
        partner = self.Partner.search(
            [('is_wua_partner', '=', True)], limit=1)
        if not partner:
            partner = self.Partner.search([], limit=1)
        if partner:
            partner.write({
                'parcel_owner_number_votes': votes,
            })
        return partner

    # -------------------------------------------------------
    # calculate_invoice_details_others_categ
    # -------------------------------------------------------

    def test_categ22_empty_item_ids_returns_empty(self):
        """categ22 with empty item_ids returns []."""
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                0, 22, [], self.partnerlinks)
        self.assertEqual(result, [])

    def test_categ22_partner_with_votes_returns_detail(self):
        """Partner with votes > 0 must produce a detail."""
        partner = self._get_partner_and_set_votes(5)
        product = self._get_service_product()
        if not partner or not product:
            return
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                product.id, 22, [partner.id],
                self.partnerlinks)
        self.assertEqual(len(result), 1)
        detail = result[0]
        self.assertEqual(detail['partner_id'], partner.id)
        self.assertEqual(detail['product_id'], product.id)
        self.assertEqual(detail['categ_code'], 22)
        self.assertEqual(detail['quantity'], 5)
        self.assertEqual(detail['key1'], partner.id)
        self.assertEqual(detail['key2'], 0)
        self.assertIn('description', detail)

    def test_categ22_partner_zero_votes_excluded(self):
        """Partner with 0 votes must be excluded."""
        partner = self._get_partner_and_set_votes(0)
        product = self._get_service_product()
        if not partner or not product:
            return
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                product.id, 22, [partner.id],
                self.partnerlinks)
        self.assertEqual(result, [])

    def test_categ22_multiple_partners(self):
        """Multiple partners with different votes."""
        partners = self.Partner.search(
            [('is_wua_partner', '=', True)], limit=2)
        if len(partners) < 2:
            return
        product = self._get_service_product()
        if not product:
            return
        partners[0].write({'parcel_owner_number_votes': 3})
        partners[1].write({'parcel_owner_number_votes': 0})
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                product.id, 22,
                partners.ids,
                self.partnerlinks)
        result_ids = [r['partner_id'] for r in result]
        self.assertIn(partners[0].id, result_ids)
        self.assertNotIn(partners[1].id, result_ids)

    def test_categ22_description_contains_votes(self):
        """Description must contain the vote count."""
        partner = self._get_partner_and_set_votes(12)
        product = self._get_service_product()
        if not partner or not product:
            return
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                product.id, 22, [partner.id],
                self.partnerlinks)
        self.assertEqual(len(result), 1)
        self.assertIn('12', result[0]['description'])

    def test_categ22_nonexistent_partner_skipped(self):
        """A non-existent partner id must be skipped."""
        product = self._get_service_product()
        if not product:
            return
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                product.id, 22, [999999999],
                self.partnerlinks)
        self.assertEqual(result, [])

    def test_other_categ_delegates_to_super(self):
        """Non-22 codes must delegate to super."""
        result = self.Invoiceset \
            .calculate_invoice_details_others_categ(
                0, 99, [], self.partnerlinks)
        self.assertEqual(result, [])

    # -------------------------------------------------------
    # select_invoice_items_other_types
    # -------------------------------------------------------

    def test_select_items_other_types_non22_returns_empty(
            self):
        """Non-22 code must delegate to super (empty)."""
        result = self.Invoiceset \
            .select_invoice_items_other_types(
                99, self.env['wua.invoiceset.line'])
        self.assertEqual(result, [])

    # -------------------------------------------------------
    # add_to_invoice_data_line_ref_to_other_types
    # -------------------------------------------------------

    def test_add_ref_categ22_sets_partner_id(self):
        """For categ 22, partner_id must be set."""
        data = {}
        invoice_data_line = {'key1': 42}
        result = self.Invoiceset \
            .add_to_invoice_data_line_ref_to_other_types(
                22, invoice_data_line, data)
        self.assertEqual(result['partner_id'], 42)

    def test_add_ref_other_categ_delegates(self):
        """Non-22 categ must delegate to super."""
        data = {}
        invoice_data_line = {'key1': 42}
        result = self.Invoiceset \
            .add_to_invoice_data_line_ref_to_other_types(
                99, invoice_data_line, data)
        self.assertNotIn('partner_id', result)
