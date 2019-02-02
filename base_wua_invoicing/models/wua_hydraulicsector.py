# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'
    _description = 'Hydraulic Sectors (with based-sets invoicing)'

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('hydraulicsector_id', '=', self.id)]
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
