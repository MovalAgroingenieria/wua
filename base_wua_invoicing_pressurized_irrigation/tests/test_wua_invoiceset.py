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

    def test_unlink_empty_recordset_no_error(self):
        """unlink on empty recordset does not raise."""
        self.Invoiceset.unlink()

    def test_get_detail_of_presconsumption_with_lang_same_as_without(self):
        """get_detail_of_presconsumption with lang=partner.lang returns same as lang=None (avoids N+1 browse)."""
        presconsumption = self.env['wua.presconsumption'].search([], limit=1)
        partner = self.env['res.partner'].search([], limit=1)
        if not presconsumption or not partner:
            return
        desc_without_lang = self.Invoiceset.get_detail_of_presconsumption(
            presconsumption, partner.id)
        desc_with_lang = self.Invoiceset.get_detail_of_presconsumption(
            presconsumption, partner.id, lang=partner.lang)
        self.assertEqual(desc_without_lang, desc_with_lang)
        self.assertIsInstance(desc_without_lang, (str, type(u'')))
        # Volume unit (m³) in description; in Python 2 desc can be UTF-8 bytes
        if type(desc_without_lang) is type(b'') and type(desc_without_lang) is not type(u''):
            desc_unicode = desc_without_lang.decode('utf-8')
        else:
            desc_unicode = desc_without_lang
        self.assertIn(u'm³', desc_unicode)

    def test_get_detail_of_presconsumption_with_explicit_lang_returns_string(self):
        """get_detail_of_presconsumption with lang passed returns non-empty string (no partner browse)."""
        presconsumption = self.env['wua.presconsumption'].search([], limit=1)
        partner = self.env['res.partner'].search([], limit=1)
        if not presconsumption or not partner:
            return
        desc = self.Invoiceset.get_detail_of_presconsumption(
            presconsumption, partner.id, lang=partner.lang or 'en_US')
        self.assertIsInstance(desc, (str, type(u'')))
        self.assertTrue(len(desc) > 0)
