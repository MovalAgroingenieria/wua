# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wateringrequest_ids = fields.One2many(
        string='Watering Requests',
        comodel_name='wua.wateringrequest',
        inverse_name='partner_id')

    number_of_requests = fields.Integer(
        string='Number of requests',
        store=True,
        compute='_compute_number_of_requests',
        compute_sudo=True)

    gravconsumption_ids = fields.One2many(
        string='Consumptions',
        comodel_name='wua.gravconsumption',
        inverse_name='partner_id')

    number_of_gravconsumptions = fields.Integer(
        string='Number of consumptions',
        store=True,
        compute='_compute_number_of_gravconsumptions',
        compute_sudo=True)

    @api.depends('wateringrequest_ids')
    def _compute_number_of_requests(self):
        for record in self:
            record.number_of_requests = \
                len(record.wateringrequest_ids)

    @api.depends('gravconsumption_ids')
    def _compute_number_of_gravconsumptions(self):
        for record in self:
            record.number_of_gravconsumptions = \
                len(record.gravconsumption_ids)

    @api.multi
    def action_see_watering_requests(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_wateringrequest_view_form').id
        if self.env.user.has_group('base_wua.group_wua_portal_user_edit'):
            id_tree_view = \
                self.env.ref('base_wua_gravity_irrigation.'
                             'wua_wateringrequest_partner_edit_view_tree').id
        else:
            id_tree_view = \
                self.env.ref('base_wua_gravity_irrigation.'
                             'wua_wateringrequest_partner_view_tree').id
        search_view = self.env.ref('base_wua_gravity_irrigation.'
                                   'wua_wateringrequest_partner_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Watering Requests'),
            'res_model': 'wua.wateringrequest',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agricultural_season_inpartner': 1},
            }
        return act_window

    @api.multi
    def action_see_gravity_consumptions(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_tree_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_gravconsumption_view_tree').id
        search_view = self.env.ref('base_wua_gravity_irrigation.'
                                   'wua_gravconsumption_view_search')
        context = {
            'create': False,
            'edit': False,
            'delete': False,
            'search_default_agriculturalseason': 1,
            'search_default_irrigationditch': 1,
            'search_default_wateringperiod': 1
            }
        if self.env.user.has_group('base_wua.group_wua_user'):
            context['search_default_executed'] = 1
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Gravity Consumptions'),
            'res_model': 'wua.gravconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': context,
            }
        return act_window
