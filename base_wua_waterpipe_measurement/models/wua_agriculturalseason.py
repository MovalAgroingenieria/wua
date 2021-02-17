# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    waterpipeconsumption_ids = fields.One2many(
        string='Waterpipe Consumptions',
        comodel_name='wua.waterpipeconsumption',
        inverse_name='agriculturalseason_id')

    number_of_waterpipeconsumptions = fields.Integer(
        string='Number of waterpipe cons.',
        store=True,
        compute='_compute_number_of_waterpipeconsumptions')

    total_waterpipevolume = fields.Float(
        string='Total waterpipe volume',
        digits=(32, 4),
        store=True,
        compute='_compute_total_waterpipevolume')

    @api.depends('waterpipeconsumption_ids')
    def _compute_number_of_waterpipeconsumptions(self):
        for record in self:
            number_of_waterpipeconsumptions = 0
            if record.waterpipeconsumption_ids:
                number_of_waterpipeconsumptions = \
                    len(record.waterpipeconsumption_ids)
            record.number_of_waterpipeconsumptions = \
                number_of_waterpipeconsumptions

    @api.depends('waterpipeconsumption_ids')
    def _compute_total_waterpipevolume(self):
        for record in self:
            total_waterpipevolume = 0.0
            if record.waterpipeconsumption_ids:
                for waterpipe_consumption_id in \
                        record.waterpipeconsumption_ids:
                    if waterpipe_consumption_id.volume_real:
                        total_waterpipevolume += \
                            waterpipe_consumption_id.volume_real
            record.total_waterpipevolume = total_waterpipevolume

    @api.multi
    def action_see_waterpipeconsumptions(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_waterpipe_measurement.'
                                    'wua_waterpipeconsumption_view_form').id
        id_tree_view = self.env.ref('base_wua_waterpipe_measurement.'
                                    'wua_waterpipeconsumption_view_tree').id
        search_view = self.env.ref('base_wua_waterpipe_measurement.'
                                   'wua_waterpipeconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterpipe Consumptions'),
            'res_model': 'wua.waterpipeconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
