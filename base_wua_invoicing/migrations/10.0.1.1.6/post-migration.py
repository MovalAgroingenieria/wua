# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fix invoices left with a wrong state by the payment order sync.

    A bug in account.payment.order.generated2uploaded aborted the whole
    transaction (a raw SQL update referenced a non existing column), so
    invoices paid through a payment order were never marked as paid
    (under-marked). A second flaw forced every invoice in the order to
    'paid' with residual=0 without checking the real reconciliation, so
    some invoices were marked as paid while still having a pending
    balance (over-marked).

    The fix is applied with plain SQL (state, reconciled and the real
    residual recomputed from the move lines) on purpose: calling the ORM
    store computes here would reschedule a recompute that reverts these
    very rows during the module loading flush.
    """
    # Over-marked: flagged as paid but still with a pending residual.
    cr.execute("""
        SELECT ai.id
        FROM account_invoice ai
        WHERE ai.state = 'paid'
        AND EXISTS (
            SELECT 1 FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aml.invoice_id = ai.id
            AND aa.internal_type IN ('receivable', 'payable')
            AND aml.reconciled IS FALSE
            AND COALESCE(aml.amount_residual, 0) <> 0
        )
    """)
    over_ids = [row[0] for row in cr.fetchall()]
    if over_ids:
        cr.execute("""
            UPDATE account_invoice ai
            SET state = 'open',
                reconciled = FALSE,
                residual = ABS(sub.res),
                residual_signed = sub.res,
                residual_company_signed = sub.res
            FROM (
                SELECT aml.invoice_id, SUM(aml.amount_residual) AS res
                FROM account_move_line aml
                JOIN account_account aa ON aa.id = aml.account_id
                WHERE aa.internal_type IN ('receivable', 'payable')
                AND aml.invoice_id IN %s
                GROUP BY aml.invoice_id
            ) sub
            WHERE ai.id = sub.invoice_id
        """, (tuple(over_ids),))
        cr.execute("""
            UPDATE account_invoice_line
            SET invoice_state = 'open'
            WHERE invoice_id IN %s
        """, (tuple(over_ids),))
        _logger.info(
            "base_wua_invoicing: reverted %s over-marked invoices to open: "
            "%s", len(over_ids), over_ids)

    # Under-marked: still open but fully reconciled (nothing pending).
    cr.execute("""
        SELECT ai.id
        FROM account_invoice ai
        WHERE ai.state = 'open'
        AND EXISTS (
            SELECT 1 FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aml.invoice_id = ai.id
            AND aa.internal_type IN ('receivable', 'payable')
        )
        AND NOT EXISTS (
            SELECT 1 FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aml.invoice_id = ai.id
            AND aa.internal_type IN ('receivable', 'payable')
            AND aml.reconciled IS FALSE
            AND COALESCE(aml.amount_residual, 0) <> 0
        )
    """)
    under_ids = [row[0] for row in cr.fetchall()]
    if under_ids:
        cr.execute("""
            UPDATE account_invoice
            SET state = 'paid', reconciled = TRUE, residual = 0,
                residual_signed = 0, residual_company_signed = 0
            WHERE id IN %s
        """, (tuple(under_ids),))
        cr.execute("""
            UPDATE account_invoice_line
            SET invoice_state = 'paid'
            WHERE invoice_id IN %s
        """, (tuple(under_ids),))
        _logger.info(
            "base_wua_invoicing: marked %s under-marked invoices as paid: "
            "%s", len(under_ids), under_ids)
