# -*- coding: utf-8 -*-
# 2019 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    wateringperiod_ids = fields.One2many(
        string='Watering Periods',
        comodel_name='wua.wateringperiod',
        inverse_name='agriculturalseason_id')

    number_of_periods = fields.Integer(
        string='Number of periods',
        store=True,
        compute='_compute_number_of_periods')

    watering_ids = fields.One2many(
        string='Waterings',
        comodel_name='wua.watering',
        inverse_name='agriculturalseason_id')

    number_of_waterings = fields.Integer(
        string='Number of waterings',
        store=True,
        compute='_compute_number_of_waterings')

    @api.depends('wateringperiod_ids')
    def _compute_number_of_periods(self):
        for record in self:
            record.number_of_periods = \
                len(record.wateringperiod_ids)

    @api.depends('watering_ids')
    def _compute_number_of_waterings(self):
        for record in self:
            record.number_of_waterings = \
                len(record.watering_ids)

    @api.multi
    def action_see_waterings(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_form').id
        id_tree_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_tree').id
        search_view = self.env.ref('base_wua_gravity_irrigation.'
                                   'wua_watering_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterings'),
            'res_model': 'wua.watering',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'search_default_watering_period': 1},
            }
        return act_window
