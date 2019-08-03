# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _
from odoo.exceptions import UserError


class BankPaymentLine(models.Model):
    _inherit = 'bank.payment.line'

    @api.multi
    def reconcile(self):
        self.ensure_one()
        amlo = self.env['account.move.line']
        transit_mlines = amlo.search([('bank_payment_line_id', '=', self.id)])
        assert len(transit_mlines) == 1, 'We should have only 1 move'
        transit_mline = transit_mlines[0]
        assert not transit_mline.reconciled,\
            'Transit move should not be reconciled'
        lines_to_rec = transit_mline
        for payment_line in self.payment_line_ids:

            if not payment_line.move_line_id:
                raise UserError(_(
                    "Can not reconcile: no move line for "
                    "payment line %s of partner '%s'.") % (
                        payment_line.name,
                        payment_line.partner_id.name))
            if payment_line.move_line_id.reconciled:
                raise UserError(_(
                    "Move line '%s' of partner '%s' has already "
                    "been reconciled") % (
                        payment_line.move_line_id.name,
                        payment_line.partner_id.name))
            if (
                    payment_line.move_line_id.account_id !=
                    transit_mline.account_id):
                raise UserError(_(
                    "For partner '%s', the account of the account "
                    "move line to pay (%s) is different from the "
                    "account of of the transit move line (%s).") % (
                        payment_line.move_line_id.partner_id.name,
                        payment_line.move_line_id.account_id.code,
                        transit_mline.account_id.code))

            lines_to_rec += payment_line.move_line_id

        with self.env.norecompute():
            lines_to_rec.reconcile()
        self.recompute()
