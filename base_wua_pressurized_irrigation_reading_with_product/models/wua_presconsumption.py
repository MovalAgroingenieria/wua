# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'

    @api.depends('waterconnection_id', 'waterconnection_id.product_id',
                 'reading_id', 'reading_id.product_id')
    def _compute_product_id(self):
        for record in self:
            product_id = None
            # reading id product is prioritary, in ohter case get the
            # waterconnection
            if (record.reading_id):
                product_id = record.reading_id.product_id
            elif (record.waterconnection_id):
                product_id = record.waterconnection_id.product_id
            record.product_id = product_id
