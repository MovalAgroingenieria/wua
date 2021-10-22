# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class WuaParcelVegetationindexMoisture(models.Model):
    _name = 'wua.parcel.vegetationindex.moisture'
    _description = 'Moisture table'
    _inherit = 'wua.parcel.vegetationindex'

    _date_first = True
    _min_allowed_value = -1
    _max_allowed_value = 1

    vegetationindex_img = fields.Binary(
        string='Moisture Image')

    def _get_wms_layer(self):
        layer_moisture = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'layer_moisture')
        return layer_moisture
