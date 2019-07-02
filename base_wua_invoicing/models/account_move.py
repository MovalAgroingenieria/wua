# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        store=True,
        compute='_compute_invoiceset_id',
        ondelete='restrict')

    @api.depends('invoice_id')
    def _compute_invoiceset_id(self):
        for record in self:
            invoiceset_id = None
            if record.invoice_id.invoiceset_id:
                invoiceset_id = record.invoice_id.invoiceset_id
            record.invoiceset_id = invoiceset_id
