# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    fixed_water = fields.Boolean(
        string='Fixed Water',
        default=False)

    def with_fixed_water(self, active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        for waterconnection in waterconnections:
            waterconnection.fixed_water = True

    def without_fixed_water(self, active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        for waterconnection in waterconnections:
            waterconnection.fixed_water = False
