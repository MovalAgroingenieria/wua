# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'User of WUA (MR)'

    is_wua_watermeter_reader_user = fields.Boolean(
        string='Watermeter Reader User',
        store=True,
        compute_sudo=True,
        compute='_compute_is_watermeter_reader_user',
        help='Employee mapped to Watermeter Reader user group')

    @api.depends('groups_id')
    def _compute_is_watermeter_reader_user(self):
        for user in self:
            user.is_wua_watermeter_reader_user = user.has_group(
                'base_wua_pressurized_irrigation_reading_period.'
                'group_wua_watermeter_reader')
