# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    permanent = fields.Boolean(
        string='Permanent',
        default=False)

    enrolledsubparcel_ids = fields.One2many(
        string='Enrolled Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='cultivation_id')

    number_of_enrolledsubparcels = fields.Integer(
        string='Number of enrolled subp.',
        compute='_compute_number_of_enrolledsubparcels')

    @api.multi
    def _compute_number_of_enrolledsubparcels(self):
        for record in self:
            number_of_enrolledsubparcels = 0
            if record.enrolledsubparcel_ids:
                number_of_enrolledsubparcels = \
                    len(record.enrolledsubparcel_ids)
            record.number_of_enrolledsubparcels = number_of_enrolledsubparcels

    @api.multi
    def action_see_enrolledsubparcels(self):
        self.ensure_one()
        if self.enrolledsubparcel_ids:
            id_tree_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_form').id
            search_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Enrolled Subparcels'),
                'res_model': 'wua.enrolledsubparcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.enrolledsubparcel_ids.ids)],
                'context': {'search_default_active_agriculturalseason': 1,
                            'reduced_name_get_for_agriculturalseason': True,
                            'reduced_name_get_for_cropplan': True}
                }
            return act_window
