# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute("""
        SELECT conname
        FROM pg_constraint
        WHERE conname = 'wua_fertconsumption_valid_amount'
        AND conrelid = 'wua_fertconsumption'::regclass;
    """)

    if cr.fetchone():
        cr.execute("""
            ALTER TABLE wua_fertconsumption
            DROP CONSTRAINT IF EXISTS wua_fertconsumption_valid_amount;
        """)
