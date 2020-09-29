# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class GeneralLedgerReport(models.TransientModel):
    _inherit = 'report_general_ledger_qweb'

    hide_account_summary = fields.Boolean()


class GeneralLedgerReportWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    hide_account_summary = fields.Boolean(
        string="Hide account summary",
        help="Do not show account summary line")

    def _prepare_report_general_ledger(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'only_posted_moves': self.target_move == 'posted',
            'hide_account_at_0': self.hide_account_at_0,
            'foreign_currency': self.foreign_currency,
            'show_analytic_tags': self.show_analytic_tags,
            'company_id': self.company_id.id,
            'filter_account_ids': [(6, 0, self.account_ids.ids)],
            'filter_partner_ids': [(6, 0, self.partner_ids.ids)],
            'filter_journal_ids': [(6, 0, self.journal_ids.ids)],
            'filter_cost_center_ids': [(6, 0, self.cost_center_ids.ids)],
            'filter_analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'centralize': self.centralize,
            'fy_start_date': self.fy_start_date,
            'hide_account_summary': self.hide_account_summary,
        }
