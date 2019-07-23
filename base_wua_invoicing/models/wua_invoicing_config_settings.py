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

    alter_invoicing_behavior = fields.Boolean(
        string="Alter invoicing behavior",
        help='if it is marked, it allows parameterization of \
             the unit of measurement of the area')

    invoicing_area_measurement_name = fields.Char(
        string='Invoicing Area Unit Name',
        size=20,
        translate=True,
        help='If the area unit type is not the official area unit,\
            indicate here the name of that unit')

    invoicing_area_measurement_equivalence = fields.Float(
        string='Master unit equivalence',
        digits=(32, 5),
        default=0,
        required=True,
        help='If the area unit type is not the official area unit,\
            indicate here equivalence factor')

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
        values.set_default('wua.invoicing.configuration',
                           'alter_invoicing_behavior',
                           self.alter_invoicing_behavior)
        values.set_default('wua.invoicing.configuration',
                           'invoicing_area_measurement_name',
                           self.invoicing_area_measurement_name)
        values.set_default('wua.invoicing.configuration',
                           'invoicing_area_measurement_equivalence',
                           self.invoicing_area_measurement_equivalence)
