# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """Synchronize invoice_state in account_invoice_line with account_invoice
    state.

    Fixes mismatches where invoice_line.invoice_state differs from its parent
    invoice.state due to direct SQL updates or data inconsistencies.
    """
    cr.execute("""
        UPDATE account_invoice_line ail
        SET invoice_state = ai.state
        FROM account_invoice ai
        WHERE ail.invoice_id = ai.id
        AND ail.invoice_state != ai.state
    """)
