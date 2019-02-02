# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner of a WUA with gravity irrigation infrastructure'

    wateringrequest_ids = fields.One2many(
        string='Watering Requests',
        comodel_name='wua.wateringrequest',
        inverse_name='partner_id')

    number_of_requests = fields.Integer(
        string='Number of requests',
        store=True,
        compute='_compute_number_of_requests',
        compute_sudo=True)

    @api.depends('wateringrequest_ids')
    def _compute_number_of_requests(self):
        for record in self:
            record.number_of_requests = \
                len(record.wateringrequest_ids)

    @api.multi
    def action_see_watering_requests(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_wateringrequest_view_form').id
        id_tree_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_wateringrequest_parner_view_tree').id
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
