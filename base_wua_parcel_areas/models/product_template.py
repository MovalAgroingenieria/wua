# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class product_template(models.Model):
    _inherit = 'product.template'

    weighting_type = fields.Selection([
        ('I', 'irrigation'),
        ('D', 'drainage'),
        ('N', 'none'),
        ], string='Weighting Type',
        required=False,
        default='N')
