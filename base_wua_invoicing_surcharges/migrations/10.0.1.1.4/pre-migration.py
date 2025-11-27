# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    """Drop old truncated indexes that exceed PostgreSQL 63-char limit.

    These indexes were automatically created by Odoo with names that
    exceeded 63 characters and were truncated by PostgreSQL, causing
    conflicts when trying to recreate them.
    """
    # Drop truncated indexes for the three surcharge models
    cr.execute("""
        DROP INDEX IF EXISTS
            wua_invoiceset_line_invoice_surcharge_variable_invoiceset;
        DROP INDEX IF EXISTS
            wua_invoiceset_line_invoice_surcharge_fixed_invoiceset_id;
        DROP INDEX IF EXISTS
            wua_invoiceset_line_invoice_total_surcharge_variable_invoiceset;
    """)
