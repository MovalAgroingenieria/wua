# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    invoicing_of_hydricmovements_cancelled = fields.Boolean(
        string='Invoicing of hydricmovements with related elements cancelled',
        default=False,
    )

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.invoicing.configuration',
            'invoicing_of_hydricmovements_cancelled',
            self.invoicing_of_hydricmovements_cancelled)
