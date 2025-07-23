# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_portal_user = fields.Boolean(
        string='Is Portal User',
        compute='_compute_is_portal_user',
        store=True,
    )

    @api.depends('groups_id')
    def _compute_is_portal_user(self):
        for user in self:
            user.is_portal_user = user.has_group('base.group_portal')
