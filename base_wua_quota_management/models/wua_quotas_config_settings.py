# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaQuotasConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.quotas.configuration'
    _description = 'Configuration of base_wua_quota_management module'

    sorted_quotas = fields.Boolean(
        string='Sort in superproducts',
        default=False,
        help='Apply superproduct sorting of quota periods to calculate '
             'the hydric consumptions')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.quotas.configuration', 'sorted_quotas',
                           self.sorted_quotas)
