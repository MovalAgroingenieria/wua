# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    @api.multi
    def refresh_hydric_efficiency(self):
        wp_consumptions = self.env['wua.waterpipeconsumption'].search(
            [('agriculturalseason_id', '=', self.id)])
        if wp_consumptions:
            for record in wp_consumptions:
                record.refresh_hydric_efficiency()
