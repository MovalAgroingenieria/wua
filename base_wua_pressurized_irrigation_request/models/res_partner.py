# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    preswateringrequest_ids = fields.One2many(
        string='PresWatering Requests',
        comodel_name='wua.preswateringrequest',
        inverse_name='partner_id',
    )

    number_of_preswateringrequests = fields.Integer(
        string='Number of preswateringrequests',
        compute='_compute_number_of_preswateringrequests',
        compute_sudo=True,
    )

    presresconsumption_ids = fields.One2many(
        string='Consumption Requests',
        comodel_name='wua.presresconsumption',
        inverse_name='partner_id',
    )

    number_of_presresconsumptions = fields.Integer(
        string='Number of consumptions',
        compute='_compute_number_of_presresconsumptions',
        compute_sudo=True,
    )

    @api.multi
    def _compute_number_of_preswateringrequests(self):
        for record in self:
            number_of_preswateringrequests = 0
            if (record.preswateringrequest_ids):
                number_of_preswateringrequests = \
                    len(record.preswateringrequest_ids)
            record.number_of_preswateringrequests = \
                number_of_preswateringrequests

    @api.multi
    def _compute_number_of_presresconsumptions(self):
        for record in self:
            number_of_presresconsumptions = 0
            if (record.presresconsumption_ids):
                number_of_presresconsumptions = \
                    len(record.presresconsumption_ids)
            record.number_of_presresconsumptions = \
                number_of_presresconsumptions

    @api.multi
    def action_see_preswatering_requests(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_pressurized_irrigation_request.'
                                    'wua_preswateringrequest_view_form').id
        if self.env.user.has_group('base_wua.group_wua_portal_user_edit'):
            id_tree_view = \
                self.env.ref(
                    'base_wua_pressurized_irrigation_request.'
                    'wua_preswateringrequest_partner_edit_view_tree').id
        else:
            id_tree_view = \
                self.env.ref('base_wua_pressurized_irrigation_request.'
                             'wua_preswateringrequest_partner_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_request.'
            'wua_preswateringrequest_partner_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Preswatering Requests'),
            'res_model': 'wua.preswateringrequest',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agricultural_season_inpartner': 1,
                        'search_default_preswatering_period_inpartner': 1},
            }
        return act_window

    @api.multi
    def action_see_presresconsumption(self):
        self.ensure_one()
        condition = [('partner_id', '=', self.id)]
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation_request.'
                                    'wua_presresconsumption_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation_request.'
                                   'wua_presresconsumption_view_search')
        context = {
            'create': False,
            'edit': False,
            'delete': False,
            'search_default_group_by_agriculturalseason': 1,
            # 'search_default_irrigationditch': 1,
            'search_default_group_by_preswateringperiod': 1,
            }
        # if self.env.user.has_group('base_wua.group_wua_user'):
        #     context['search_default_executed'] = 1
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Consumption Requests'),
            'res_model': 'wua.presresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': context,
            }
        return act_window
