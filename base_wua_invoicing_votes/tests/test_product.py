# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestProductVotes(SavepointCase):
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestProductVotes, cls).setUpClass()
        cls.ProductCategory = cls.env['product.category']

    def test_categ_22_exists_with_correct_code(self):
        """Category 22 (Votes) must exist with productcategory_code = 22."""
        categ = self.env.ref('base_wua_invoicing_votes.categ_22')
        self.assertTrue(categ)
        self.assertEqual(categ.productcategory_code, 22)

    def test_categ_22_parent_is_wua_service(self):
        """Category 22 must be a child of categ_00 (WUA Service)."""
        categ = self.env.ref('base_wua_invoicing_votes.categ_22')
        categ_00 = self.env.ref('base_wua_invoicing.categ_00')
        self.assertEqual(categ.parent_id.id, categ_00.id)

    def test_categ_22_is_wua_product_category(self):
        """Category 22 must be flagged as a WUA product category."""
        categ = self.env.ref('base_wua_invoicing_votes.categ_22')
        self.assertTrue(categ.is_wua_product_category)

    def test_linkable_unit_type_code_22_is_partner(self):
        """productcategory_code 22 must resolve to linkable_unit_type 'partner'."""
        result = self.ProductCategory._get_linkable_unit_type_from_category(22)
        self.assertEqual(result, 'partner')

    def test_linkable_unit_type_other_codes_unchanged(self):
        """Other codes must still resolve to their original types."""
        self.assertEqual(
            self.ProductCategory._get_linkable_unit_type_from_category(1),
            'parcel')
        self.assertEqual(
            self.ProductCategory._get_linkable_unit_type_from_category(2),
            'partner')
        self.assertEqual(
            self.ProductCategory._get_linkable_unit_type_from_category(5),
            'waterconnection')

    def test_product_22_exists(self):
        """Product template for votes must exist."""
        product = self.env.ref('base_wua_invoicing_votes.product_22')
        self.assertTrue(product)
        self.assertEqual(product.type, 'service')
        categ = self.env.ref('base_wua_invoicing_votes.categ_22')
        self.assertEqual(product.categ_id.id, categ.id)
