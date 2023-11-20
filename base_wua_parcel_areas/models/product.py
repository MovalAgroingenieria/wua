# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    parcel_area_to_be_invoiced = fields.Selection(
        selection_add=[
            ('area_irrigation', 'Irrigation Area'),
        ],
    )
