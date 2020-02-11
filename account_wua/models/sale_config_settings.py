# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    group_sale_delivery_address = fields.Selection([
        (0, "Invoicing and shipping addresses are always the same (Example: services companies)"),
        (1, 'Show invoicing and shipping addresses if they are different')
        ], "Addresses", implied_group='sale.group_delivery_invoice_address')
