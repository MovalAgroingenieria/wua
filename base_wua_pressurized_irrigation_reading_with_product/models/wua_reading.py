# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        ondelete='restrict')

    @api.onchange('watermeter_id')
    def onchange_watermeter_id(self):
        if (self.watermeter_id and self.watermeter_id.waterconnection_id):
            self.product_id = self.watermeter_id.waterconnection_id.product_id
