# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaTank(models.Model):
    _inherit = 'wua.tank'

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('tank_id', '=', self.id)]
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
