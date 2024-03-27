# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'

    hydraulicsectorlink_ids = fields.One2many(
        string='Intakes of hydraulic sector',
        comodel_name='wua.intake.hydraulicsectorlink',
        inverse_name='hydraulicsector_id',)

    @api.multi
    def action_show_intakes(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_infrastructure_primary.'
            'wua_intake_hydraulicsectorlink_view_tree').id
        search_view = self.env.ref(
            'base_wua_infrastructure_primary.'
            'wua_intake_hydraulicsectorlink_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Intakes'),
            'res_model': 'wua.intake.hydraulicsectorlink',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('hydraulicsector_id', '=', self.id)],
            }
        return act_window
