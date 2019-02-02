# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.invoicing.configuration'
    _description = 'Configuration of base_wua_invoicing module'

    default_invoiceset_code_type = fields.Selection([
        (0, 'None'),
        (1, 'Numeric Order'),
        (2, 'Annual Sequence')],
        'Invoice Set Code Type',
        default=0,
        help='Default type for invoice set code')

    default_annual_seq_prefix = fields.Char(
        string='Prefix (annual seq.)',
        size=10,
        help='Default Code for invoice set: <prefix>/<year>/num')

    default_journal_id = fields.Many2one(
        string='Journal',
        comodel_name='account.journal',
        help='Default journal for invoice sets')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'default_invoiceset_code_type',
                           self.default_invoiceset_code_type)
        values.set_default('wua.invoicing.configuration',
                           'default_annual_seq_prefix',
                           self.default_annual_seq_prefix)
        values.set_default('wua.invoicing.configuration',
                           'default_journal_id',
                           self.default_journal_id.id)
