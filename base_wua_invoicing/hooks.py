# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """
    Create composite and partial indexes for account_invoice,
    account_invoice_line, account_move and account_move_line.
    Only creates indexes when the table exists (safe on empty DB / install).
    """
    indexes = [
        ("account_invoice_partner_id_idx", "account_invoice",
         "CREATE INDEX IF NOT EXISTS account_invoice_partner_id_idx "
         "ON account_invoice (partner_id)"),
        ("account_invoice_partner_state_idx", "account_invoice",
         "CREATE INDEX IF NOT EXISTS account_invoice_partner_state_idx "
         "ON account_invoice (partner_id, state)"),
        ("account_invoice_line_waterconnection_id_idx", "account_invoice_line",
         "CREATE INDEX IF NOT EXISTS "
         "account_invoice_line_waterconnection_id_idx "
         "ON account_invoice_line (waterconnection_id) "
         "WHERE waterconnection_id IS NOT NULL"),
        ("account_invoice_line_invoiceset_id_idx", "account_invoice_line",
         "CREATE INDEX IF NOT EXISTS account_invoice_line_invoiceset_id_idx "
         "ON account_invoice_line (invoiceset_id) "
         "WHERE invoiceset_id IS NOT NULL"),
        ("account_move_journal_id_idx", "account_move",
         "CREATE INDEX IF NOT EXISTS account_move_journal_id_idx "
         "ON account_move (journal_id)"),
        ("account_move_state_idx", "account_move",
         "CREATE INDEX IF NOT EXISTS account_move_state_idx "
         "ON account_move (state)"),
        ("account_move_journal_date_idx", "account_move",
         "CREATE INDEX IF NOT EXISTS account_move_journal_date_idx "
         "ON account_move (journal_id, date)"),
        ("account_move_company_id_idx", "account_move",
         "CREATE INDEX IF NOT EXISTS account_move_company_id_idx "
         "ON account_move (company_id)"),
        ("account_move_line_partner_id_idx", "account_move_line",
         "CREATE INDEX IF NOT EXISTS account_move_line_partner_id_idx "
         "ON account_move_line (partner_id)"),
        ("account_move_line_reconciled_idx", "account_move_line",
         "CREATE INDEX IF NOT EXISTS account_move_line_reconciled_idx "
         "ON account_move_line (reconciled) WHERE reconciled = false"),
        ("account_move_line_statement_id_idx", "account_move_line",
         "CREATE INDEX IF NOT EXISTS account_move_line_statement_id_idx "
         "ON account_move_line (statement_id) "
         "WHERE statement_id IS NOT NULL"),
        ("account_move_line_invoice_id_idx", "account_move_line",
         "CREATE INDEX IF NOT EXISTS account_move_line_invoice_id_idx "
         "ON account_move_line (invoice_id) WHERE invoice_id IS NOT NULL"),
        ("account_move_line_account_partner_idx", "account_move_line",
         "CREATE INDEX IF NOT EXISTS account_move_line_account_partner_idx "
         "ON account_move_line (account_id, partner_id)"),
        ("wua_isl_parcel_invoicesetline_selected_idx",
         "wua_invoiceset_line_parcel",
         "CREATE INDEX IF NOT EXISTS "
         "wua_isl_parcel_invoicesetline_selected_idx "
         "ON wua_invoiceset_line_parcel (invoicesetline_id) "
         "WHERE selected = true"),
    ]
    run_performance_indexes(cr, _logger, 'base_wua_invoicing', indexes)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
