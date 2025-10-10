# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env['account.invoice.line'].search([])
    for record in records:
        record.write({
            'invoice_with_fixed_surcharge_id':
                record.invoice_with_variable_surcharge_id.id,
            'invoice_with_variable_surcharge_id':
                record.invoice_with_fixed_surcharge_id.id,
        })
    env.cr.execute("""
        UPDATE account_invoice
        SET number_of_fixed_surcharges = 0,
        number_of_variable_surcharges = 0,
        number_of_total_variable_surcharges = 0
        """)

    env.cr.execute("""
        UPDATE account_invoice
        SET number_of_fixed_surcharges = COALESCE(a.count, 0)
        FROM (
            SELECT invoice_with_fixed_surcharge_id, COUNT(*) as count
            FROM account_invoice_line
            WHERE invoice_with_fixed_surcharge_id IS NOT NULL
            GROUP BY invoice_with_fixed_surcharge_id
        ) AS a
        WHERE account_invoice.id = a.invoice_with_fixed_surcharge_id;
        """)
    env.cr.execute("""
        UPDATE account_invoice
        SET number_of_variable_surcharges = COALESCE(a.count, 0)
        FROM (
            SELECT invoice_with_variable_surcharge_id, COUNT(*) as count
            FROM account_invoice_line
            WHERE invoice_with_variable_surcharge_id IS NOT NULL
            GROUP BY invoice_with_variable_surcharge_id
        ) AS a
        WHERE account_invoice.id = a.invoice_with_variable_surcharge_id;
        """)
    env.cr.execute("""
        UPDATE account_invoice
        SET number_of_total_variable_surcharges = COALESCE(a.count, 0)
        FROM (
            SELECT invoice_with_total_variable_surcharge_id, COUNT(*) as count
            FROM account_invoice_line
            WHERE invoice_with_total_variable_surcharge_id IS NOT NULL
            GROUP BY invoice_with_total_variable_surcharge_id
        ) AS a
        WHERE account_invoice.id = a.invoice_with_total_variable_surcharge_id;
        """)
