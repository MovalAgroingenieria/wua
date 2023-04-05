# -*- coding: utf-8 -*-
# 2023 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields, _


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='wateringrequest_id')

    number_of_hydricmovements = fields.Integer(
        string='Number of hydric mov.',
        compute='_compute_number_of_hydricmovements')

    @api.multi
    def _compute_number_of_hydricmovements(self):
        for record in self:
            number_of_hydricmovements = 0
            if record.hydricmovement_ids:
                number_of_hydricmovements = len(record.hydricmovement_ids)
            record.number_of_hydricmovements = number_of_hydricmovements

    @api.multi
    def unlink(self):
        quotas_to_refresh_ids = []
        # It is necessary to refresh the affected quotas (the consumptions
        # of a watering request are deleted by "cascade" method, then
        # the method "unlink" of wua.gravconsumption model is not fired).
        for record in self:
            for gravconsumption in record.gravconsumption_ids:
                if gravconsumption.hydricmovement_ids:
                    for hydricmovement in (gravconsumption.hydricmovement_ids):
                        quotas_to_refresh_ids.append(
                            hydricmovement.quota_id.id)
                    gravconsumption.hydricmovement_ids.with_context(
                        force_unlink=True).sudo().unlink()
        if quotas_to_refresh_ids:
            quotas_to_refresh_ids = list(set(quotas_to_refresh_ids))
            quotas_to_refresh = self.env['wua.quota'].browse(
                quotas_to_refresh_ids)
            for quota in quotas_to_refresh:
                self.env['wua.quota'].refresh_quota(quota)
        return super(WuaWateringrequest, self).unlink()

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        if self.hydricmovement_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Hydric Movements'),
                'res_model': 'wua.hydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovement_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True}
                }
            return act_window
