# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaHydricmovement(models.Model):
    _inherit = 'wua.hydricmovement'

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null')

    invoiced_hydricmovement = fields.Boolean(
        string='Hydricmovement Invoiced',
        default=False)

    invoiceline_ids = fields.One2many(
        string='Invoice Lines',
        comodel_name='account.invoice.line',
        inverse_name='hydricmovement_id')

    number_of_invoices = fields.Integer(
        string='Billings',
        compute='_compute_number_of_invoices')

    @api.multi
    def _compute_number_of_invoices(self):
        for record in self:
            number_of_invoices = 0
            invoiceline_ids = record.sudo().with_context(
                force_company=False).invoiceline_ids
            if invoiceline_ids:
                number_of_invoices = len(invoiceline_ids)
            record.number_of_invoices = number_of_invoices
