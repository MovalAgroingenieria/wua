# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class WuaParcelVegetationindexNdvi(models.Model):
    _name = 'wua.parcel.vegetationindex.ndvi'
    _description = 'NDVI table'
    _inherit = 'wua.parcel.vegetationindex'

    _date_first = True
    _min_allowed_value = -1
    _max_allowed_value = 1

    vegetationindex_img = fields.Binary(
        string='NDVI Image')

    def _get_wms_layer(self):
        layer_ndvi = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'layer_ndvi')
        return layer_ndvi
