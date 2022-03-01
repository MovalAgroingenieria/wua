# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaFlowdivider(models.Model):
    _inherit = 'wua.flowdivider'

    can_register_irrigationreport = fields.Boolean(
        string='Can register irrigation reports',)

    irrigationreport_ids = fields.One2many(
        string='Irrigationreports',
        comodel_name='wua.irrigationreport',
        inverse_name='flowdivider_id')
