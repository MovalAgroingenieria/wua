# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# from odoo.tools.profiler import profile
from odoo import models, fields, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def generated2uploaded(self):
        for order in self:
            if order.payment_mode_id.generate_move:
                order.with_context(
                    from_account_payment_order=True).generate_move()
        self.write({
            'state': 'uploaded',
            'date_uploaded': fields.Date.context_today(self),
            })
        # New
        invoices = []
        for order in self:
            for payment_line in order.payment_line_ids:
                if payment_line.move_line_id.invoice_id:
                    invoices.append(payment_line.move_line_id.invoice_id.id)
        if invoices:
            invoices = list(set(invoices))
            invoices_str = ''
            for item in invoices:
                invoices_str = invoices_str + ', ' + str(item)
            invoices_str = invoices_str[2:]
            self.env.cr.execute("""
                UPDATE account_invoice
                set reconciled=TRUE, state='paid', residual_signed=0
                WHERE id in (""" + invoices_str + """)""")
            self.env.cr.commit()
            self.env.invalidate_all()
        return True
