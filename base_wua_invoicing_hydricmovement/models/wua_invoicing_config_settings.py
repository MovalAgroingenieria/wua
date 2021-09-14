# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    invoicing_of_negative_hydricmovements_as_negative_values = fields.Boolean(
        string='Invoicing of granted cessions and negative individual '
        'assignements as negative quantities',
        default=False)

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.invoicing.configuration',
            'invoicing_of_negative_hydricmovements_as_negative_values',
            self.invoicing_of_negative_hydricmovements_as_negative_values)
