# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    number_of_quotaperiods = fields.Integer(
        string='Number of Quota Periods',
        compute='_compute_number_of_quotaperiods')

    @api.multi
    def _compute_number_of_quotaperiods(self):
        # Provisional
        for record in self:
            record.number_of_quotaperiods = 0
