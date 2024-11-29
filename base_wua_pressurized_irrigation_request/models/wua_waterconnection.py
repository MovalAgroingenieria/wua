# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    presresconsumption_ids = fields.One2many(
        string='Consumption Requests',
        comodel_name='wua.presresconsumption',
        inverse_name='waterconnection_id',
    )

    number_of_presresconsumptions = fields.Integer(
        string='Number of consumptions',
        store=True,
        compute='_compute_number_of_presresconsumptions',
        compute_sudo=True,
    )

    default_request_duration = fields.Integer(
        string='Default Request Duration',
        default=0,
        required=True,
    )

    default_request_initial_hour = fields.Float(
        string='Default Request Initial Hour',
        default=0.0,
        required=True,
    )

    @api.depends('presresconsumption_ids')
    def _compute_number_of_presresconsumptions(self):
        for record in self:
            record.number_of_presresconsumptions = \
                len(record.presresconsumption_ids)

    @api.multi
    def action_see_presresconsumption(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation_request.'
                                    'wua_presresconsumption_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation_request.'
                                   'wua_presresconsumption_view_search')
        context = {
            'create': False,
            'edit': False,
            'delete': False,
            # 'search_default_agriculturalseason': 1,
            # 'search_default_irrigationditch': 1,
            'search_default_preswateringperiod': 1,
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
