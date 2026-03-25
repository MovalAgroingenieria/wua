# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue')

    use_ownership_percentage_on_invoicing = fields.Boolean(
        string='Use Ownership Percentage On Invoicing',
        default=False,
        store=True)

    @api.multi
    def _compute_overdue(self):
        if not self:
            return
        InvoiceLine = self.env['account.invoice.line']
        lines = InvoiceLine.search([('parcel_id', 'in', self.ids)])
        lines.mapped('invoice_id')
        lines.mapped('invoice_id.overdue')
        overdue_by_parcel = {}
        for line in lines:
            if line.invoice_id.overdue:
                overdue_by_parcel[line.parcel_id.id] = True
        for record in self:
            record.overdue = overdue_by_parcel.get(record.id, False)

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('parcel_id', '=', self.id)]
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


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue')

    @api.multi
    def _compute_overdue(self):
        if not self:
            return
        parcel_ids = self.mapped('parcel_id').ids
        if not parcel_ids:
            for record in self:
                record.overdue = False
            return
        InvoiceLine = self.env['account.invoice.line']
        lines = InvoiceLine.search([('parcel_id', 'in', parcel_ids)])
        lines.mapped('invoice_id')
        lines.mapped('invoice_id.overdue')
        overdue_by_parcel = {}
        for line in lines:
            if line.invoice_id.overdue:
                overdue_by_parcel[line.parcel_id.id] = True
        for record in self:
            record.overdue = overdue_by_parcel.get(
                record.parcel_id.id, False)
