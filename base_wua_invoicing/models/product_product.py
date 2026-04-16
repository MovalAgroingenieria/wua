from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    show_all_partners = fields.Boolean(
        string='Show All Partners',
        default=False,
    )
