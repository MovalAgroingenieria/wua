# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)

# Indexes created by an earlier version of base_wua_invoicing.hooks that
# turned out to DUPLICATE the native Odoo single-column indexes (same column,
# no WHERE/expression). Each duplicate had to be maintained on every INSERT /
# UPDATE of these very hot accounting tables, slowing down invoice posting for
# no read benefit (the native "*_index" is the one actually used). The hook no
# longer creates them; this migration removes them from existing databases.
DUPLICATE_INDEXES = [
    "account_invoice_type_idx",
    "account_invoice_state_idx",
    "account_invoice_date_invoice_idx",
    "account_invoice_line_invoice_id_idx",
    "account_invoice_line_parcel_id_idx",
    "account_invoice_line_product_id_idx",
    "account_move_date_idx",
    "account_move_line_move_id_idx",
    "account_move_line_account_id_idx",
    "account_move_line_date_maturity_idx",
    # Redundant composite (account_id, partner_id) that is never used: the
    # hook keeps account_move_line_account_partner_idx, which covers it.
    "account_move_line_account_id_partner_id_index",
]


def migrate(cr, version):
    for index_name in DUPLICATE_INDEXES:
        cr.execute("DROP INDEX IF EXISTS %s" % index_name)
        _logger.info(
            "[base_wua_invoicing] dropped duplicate index %s", index_name)
    # ANALYZE refreshes the planner statistics after the index changes. It is
    # transactional (unlike VACUUM), so it is safe inside the migration. The
    # physical bloat left by old dead tuples is reclaimed by autovacuum; run a
    # manual VACUUM ANALYZE out of the update transaction if you want it now.
    for table in (
        "account_invoice", "account_invoice_line",
        "account_move", "account_move_line",
    ):
        cr.execute("ANALYZE %s" % table)
    _logger.info(
        "[base_wua_invoicing] dropped %s duplicate indexes and re-analyzed "
        "the accounting tables.", len(DUPLICATE_INDEXES))
