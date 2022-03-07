# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ReportOverdue(models.AbstractModel):
    _inherit = 'report.account.report_overdue'

    def _get_account_move_lines(self, partner_ids):
        user_company_id = self.env.user.company_id.id
        res = dict(map(lambda x: (x, []), partner_ids))
        self.env.cr.execute(
            "SELECT m.name AS move_id, l.date, l.name, l.ref, "
            "l.date_maturity, l.partner_id, l.blocked, l.amount_currency, "
            "l.currency_id, l.journal_id, j.name AS journal_name,"
            "CASE WHEN at.type = 'receivable' "
                "THEN SUM(l.debit) "
                "ELSE SUM(l.credit * -1) "
            "END AS debit, "
            "CASE WHEN at.type = 'receivable' "
                "THEN SUM(l.credit) "
                "ELSE SUM(l.debit * -1) "
            "END AS credit, "
            "CASE WHEN l.date_maturity < %s "
                "THEN SUM(l.debit - l.credit) "
                "ELSE 0 "
            "END AS mat "
            "FROM account_move_line l "
            "JOIN account_account_type at ON (l.user_type_id = at.id) "
            "JOIN account_move m ON (l.move_id = m.id) "
            "JOIN account_journal j ON (l.journal_id = j.id) "
            "WHERE l.partner_id IN %s AND at.type IN ('receivable','payable') "
            "AND l.full_reconcile_id IS NULL "
            "AND l.company_id = %s"
            "GROUP BY l.date, l.name, l.ref, l.date_maturity, l.partner_id, "
            "at.type, l.blocked, l.amount_currency, l.currency_id, l.move_id, "
            "m.name, l.journal_id, j.name",
            (((fields.date.today(), ) + (tuple(partner_ids),
                                         user_company_id))))
        for row in self.env.cr.dictfetchall():
            res[row.pop('partner_id')].append(row)
        return res
