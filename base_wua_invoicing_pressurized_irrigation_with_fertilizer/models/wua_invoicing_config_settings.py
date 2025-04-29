# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    group_fertilizer_lines_on_report = fields.Boolean(
        string='Group Fertilizer lines on report',
        help='If marked, fertilizer lines will be grouped on report',
    )

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'group_fertilizer_lines_on_report',
                           self.group_fertilizer_lines_on_report)
