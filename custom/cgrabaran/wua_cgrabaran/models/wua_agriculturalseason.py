# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    balance_id = fields.Many2one(
        string='Intakeconsumption Balance',
        comodel_name='wua.intakeconsumption.balance',
        index=True,
        ondelete='set null')

    @api.multi
    def action_see_sum_intakeconsumption_invoicing(self):
        self.ensure_one()
        condition = [('balance_id', '=', self.balance_id.id)]
        id_tree_view = self.env.ref('wua_cgrabaran.'
                                    'wua_sum_intakeconsumption_invoicing_view'
                                    '_tree').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumption balance'),
            'res_model': 'wua.sum.intakeconsumption.invoicing',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.model
    def create(self, vals):
        agriculturalseason_created =  \
            super(WuaAgriculturalseason, self).create(vals)
        if agriculturalseason_created:
            start_date = agriculturalseason_created
            end_date = agriculturalseason_created
            initial_date_str = datetime.datetime.strptime(
                start_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                end_date, '%Y-%m-%d').strftime('%x')
            description = initial_date_str + ' - ' + end_date_str
            self.env['wua.intakeconsumption.balance'].create({
                'agriculturalseason_id': agriculturalseason_created.id,
                'balance_type': 'C',
                'description': description
                })
        return agriculturalseason_created
