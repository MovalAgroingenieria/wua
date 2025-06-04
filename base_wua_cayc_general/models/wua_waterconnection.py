# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    maximum_nominal_flow = fields.Float(
        string='Maximum nominal flow (l/s)',
        digits=(32, 4),
        compute='_compute_maximum_nominal_flow',
    )

    from_san_salvador_pumping = fields.Boolean(
        string='From San Salvador Pumping',
        default=False,
    )

    from_san_salvador_gravity = fields.Boolean(
        string='From San Salvador Gravity',
        default=False,
    )

    from_san_salvador_esplus = fields.Boolean(
        string='From San Salvador Esplús',
        default=False,
    )

    @api.multi
    def _compute_maximum_nominal_flow(self):
        for record in self:
            maximum_nominal_flow = 0.0
            if (record.watermeter_id and
                    record.watermeter_id.maximum_nominal_flow):
                maximum_nominal_flow = record.watermeter_id.\
                    maximum_nominal_flow
            record.maximum_nominal_flow = maximum_nominal_flow

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
