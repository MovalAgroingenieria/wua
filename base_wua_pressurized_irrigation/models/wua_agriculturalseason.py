# -*- coding: utf-8 -*-
# 2019 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    presconsumption_ids = fields.One2many(
        string='Consumptions',
        comodel_name='wua.presconsumption',
        inverse_name='agriculturalseason_id')

    number_of_presconsumptions = fields.Integer(
        string='Number of consumptions',
        store=True,
        compute='_compute_number_of_presconsumptions')

    @api.depends('presconsumption_ids')
    def _compute_number_of_presconsumptions(self):
        for record in self:
            record.number_of_presconsumptions = \
                len(record.presconsumption_ids)

    @api.multi
    def action_see_presconsumptions(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_view_form').id
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_presconsumption_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation.'
                                   'wua_presconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
