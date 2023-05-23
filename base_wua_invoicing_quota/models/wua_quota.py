# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    invoiceline_ids = fields.One2many(
        string="Invoice Lines",
        comodel_name="account.invoice.line",
        inverse_name="quota_id")

    sum_price_subtotal = fields.Float(
        string='Invoiced Amount',
        store=True,
        index=True,
        compute='_compute_sum_price_subtotal')

    number_of_invoicing_processes = fields.Integer(
        string='Invoicing Processes',
        store=True,
        index=True,
        compute='_compute_number_of_invoicing_processes',
        group_operator=False)

    invoiced = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced',
        default=False,)

    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id')

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.price_subtotal')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('invoiceline_ids')
    def _compute_number_of_invoicing_processes(self):
        for record in self:
            number_of_invoicing_processes = 0
            invoiceset_ids = []
            for invoiceline in record.invoiceline_ids:
                if (invoiceline.invoiceset_id not in invoiceset_ids):
                    number_of_invoicing_processes += 1
                    invoiceset_ids.append(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.depends('number_of_invoicing_processes')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = record.number_of_invoicing_processes > 0

    @api.depends('partner_id')
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('quota_id', '=', self.id)]
        id_tree_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_view_tree').id
        search_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Invoice Lines'),
            'res_model': 'account.invoice.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
