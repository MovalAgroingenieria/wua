# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'User of WUA (MR)'

    is_wua_user = fields.Boolean(
        string='WUA User',
        store=True,
        compute_sudo=True,
        compute='_compute_is_wua_user',
        help='Employee mapped to WUA user group')

    is_wua_portal_user = fields.Boolean(
        string='WUA Portal User',
        store=True,
        compute_sudo=True,
        compute='_compute_is_wua_portal_user',
        help='Employee mapped to WUA portal user group')

    @api.depends('groups_id')
    def _compute_is_wua_user(self):
        for user in self:
            user.is_wua_user = user.has_group(
                'base_wua.group_wua_user')

    @api.depends('groups_id')
    def _compute_is_wua_portal_user(self):
        for user in self:
            user.is_wua_portal_user = user.has_group(
                'base_wua.group_wua_portal_user')
