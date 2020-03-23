# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    fertconsumption_ids = fields.One2many(
        string='Fertilizers',
        comodel_name='wua.fertconsumption',
        inverse_name='presconsumption_id')

    number_of_fertconsumptions = fields.Integer(
        string='Uses of fert.',
        store=True,
        compute='_compute_number_of_fertconsumptions')

    with_fertconsumptions = fields.Boolean(
        string='With fertilizers',
        store=True,
        compute='_compute_with_fertconsumptions')

    @api.depends('fertconsumption_ids')
    def _compute_number_of_fertconsumptions(self):
        for record in self:
            number_of_fertconsumptions = 0
            if record.fertconsumption_ids:
                number_of_fertconsumptions = len(record.fertconsumption_ids)
            record.number_of_fertconsumptions = number_of_fertconsumptions

    @api.depends('fertconsumption_ids')
    def _compute_with_fertconsumptions(self):
        for record in self:
            with_fertconsumptions = False
            if record.fertconsumption_ids and len(record.fertconsumption_ids):
                with_fertconsumptions = True
            record.with_fertconsumptions = with_fertconsumptions

    @api.multi
    def action_see_fertconsumptions(self):
        self.ensure_one()
        condition = [('presconsumption_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_with_fertilizer.'
            'wua_fertconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumptions'),
            'res_model': 'wua.fertconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
