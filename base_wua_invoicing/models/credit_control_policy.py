# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class CreditControlLine(models.Model):
    _inherit = "credit.control.line"

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null',
        compute="_compute_invoiceset_id")

    @api.multi
    def _compute_invoiceset_id(self):
        for record in self:
            invoiceset_id = None
            if record.invoice_id.invoiceset_id:
                invoiceset_id = record.invoice_id.invoiceset_id
            record.invoiceset_id = invoiceset_id
