# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    analysis_ids = fields.One2many(
        comodel_name='law.analysis',
        inverse_name='intake_id',
        string='Analysis',
    )

    number_of_analysis = fields.Integer(
        string='Number of analysis',
        compute='_compute_number_of_analysis',
    )

    def _compute_number_of_analysis(self):
        for record in self:
            record.number_of_analysis = len(record.analysis_ids)

    @api.multi
    def action_see_analysis(self):
        self.ensure_one()
        condition = [('intake_id', '=', self.id)]
        id_form_view = self.env.ref('law_water_quality.'
                                    'law_analysis_view_form').id
        id_tree_view = \
            self.env.ref('law_water_quality.'
                         'law_analysis_view_tree').id
        search_view = self.env.ref('law_water_quality.'
                                   'law_analysis_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Analysis'),
            'res_model': 'law.analysis',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window
