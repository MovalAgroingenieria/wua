# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """Add partial index on wua_invoiceset_line_parcel for selected lines.

    Speeds up select_invoice_items_parcel_type which now uses a SQL domain
    search instead of ORM filtered(). The index covers only rows where
    selected=true (the common query pattern), keeping its size minimal.
    """
    cr.execute("""
        CREATE INDEX IF NOT EXISTS wua_isl_parcel_invoicesetline_selected_idx
        ON wua_invoiceset_line_parcel (invoicesetline_id)
        WHERE selected = true
    """)
