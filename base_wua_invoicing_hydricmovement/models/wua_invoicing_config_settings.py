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

    allowed_multiple_invoicing_of_hydricmovement = fields.Boolean(
        string='It is allowed to invoice a hydric movement several times',
        default=False)

    invoicing_hydricmovement_grouped_by_wc = fields.Boolean(
        string='Invoicing of Hydric Movements grouped by WC',
        default=False,
        help='If enabled, invoicing of the hydric movements based on '
             'presconsumptions will be grouped using the same waterconnection')

    invoicing_hydricmovement_selected_default = fields.Boolean(
        string='Invoicing of Hydric Movements selected by default',
        default=False,
        help='If enabled, the hydric movements will be selected by default ',
    )

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.invoicing.configuration',
            'invoicing_of_negative_hydricmovements_as_negative_values',
            self.invoicing_of_negative_hydricmovements_as_negative_values)
        values.set_default(
            'wua.invoicing.configuration',
            'allowed_multiple_invoicing_of_hydricmovement',
            self.allowed_multiple_invoicing_of_hydricmovement)
        values.set_default(
            'wua.invoicing.configuration',
            'invoicing_hydricmovement_grouped_by_wc',
            self.invoicing_hydricmovement_grouped_by_wc)
        values.set_default(
            'wua.invoicing.configuration',
            'invoicing_hydricmovement_selected_default',
            self.invoicing_hydricmovement_selected_default)
