# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'
    _description = 'Configuration of invoicing behavior for wua portal'

    liquidation_on_portal = fields.Boolean(
        string='Enable Liquidation on Portal',
        default=False,
        required=True,
        help='If it is marked, liquidation functionality will be '
             'available on the portal instead of invoice functionality')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'liquidation_on_portal',
                           self.liquidation_on_portal)
