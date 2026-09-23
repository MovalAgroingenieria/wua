# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    user_count = fields.Integer(
        string='Number of users',
        compute='_compute_user_count',
    )

    @api.multi
    def _compute_user_count(self):
        for partner in self:
            partner.user_count = len(partner.user_ids)

    @api.multi
    def action_view_users(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Users'),
            'res_model': 'res.users',
            'target': 'current',
            'domain': [('id', 'in', self.user_ids.ids)],
        }
        if len(self.user_ids) == 1:
            act_window.update({
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_users_form').id,
                'res_id': self.user_ids.id,
            })
        else:
            act_window.update({
                'view_mode': 'tree,form',
            })
        return act_window
