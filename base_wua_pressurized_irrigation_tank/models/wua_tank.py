# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaTank(models.Model):
    _name = 'wua.tank'
    _description = 'Tank'

    MAX_SIZE_NAME = 20
    MAX_SIZE_DESCRIPTION = 75

    name = fields.Char(
        string='Tank',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        required=True,
        index=True)

    tankconsumption_ids = fields.One2many(
        string='Consumptions',
        comodel_name='wua.tankconsumption',
        inverse_name='tank_id')

    notes = fields.Html(
        string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Tank.'), ]

    @api.multi
    def action_see_tankconsumptions(self):
        self.ensure_one()
        condition = [('tank_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_tank.'
            'wua_tankconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Tank consumptions'),
            'res_model': 'wua.tankconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
