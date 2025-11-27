# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def uninstall_hook(cr, registry):
    """Remove custom indexes created to avoid PostgreSQL 63-char limit.

    These indexes were created manually in _auto_init() methods with
    shorter names to avoid conflicts with PostgreSQL's character limit.
    """
    cr.execute("""
        DROP INDEX IF EXISTS wua_invsetln_invsurch_var_invset_idx;
        DROP INDEX IF EXISTS wua_invsetln_invsurch_fix_invset_idx;
        DROP INDEX IF EXISTS wua_invsetln_invtot_surchvar_invset_idx;
    """)
