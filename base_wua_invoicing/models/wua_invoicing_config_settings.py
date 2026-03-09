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

    show_tax_base = fields.Boolean(
        string='Show Tax base in tax summary',
        default=False,
        required=True,
        help='If it is marked, the invoices reports will show the tax base'
             'in the same table of the tax summary')

    group_detail_lines_of_wc_if_same_payer = fields.Boolean(
        string='Group the detail lines of waterconnections if same payer',
        default=False,
        required=True,
        help='If marked, detail lines of waterconnections with the same payer '
             'will be grouped into just one')

    show_irrigationditch = fields.Boolean(
        string='Show Irrigationditch on invoices descriptions',
        default=False,
        required=True,
        help='If it is marked, the invoices reports will show the '
             'irrigationditch name on line description for products of '
             'category 03')

    show_owners = fields.Boolean(
        string='Show all owners on invoices descriptions',
        default=False,
        required=True,
        help='If it is marked, the invoices reports will show the '
             'ownners names on line description for products of '
             'category 03')

    invoiceset_compute_management = fields.Boolean(
        string='Compute management on invoiceset',
        default=False,
    )

    # Calculation and logging (performance / progress logs)
    commit_every_n_invoices = fields.Integer(
        string='Commit every N invoices',
        default=200,
        help='During invoice set calculation, commit the transaction every N '
             'invoices created to avoid one huge transaction (default: 200).')
    log_progress_partners_max_step = fields.Integer(
        string='Log progress (partners) – max step',
        default=100,
        help='Maximum step for progress logs by partners (default: 100).')
    log_progress_partners_divisor = fields.Integer(
        string='Log progress (partners) – divisor',
        default=20,
        help='Divisor to compute progress log step: step = total // divisor '
             '(default: 20).')
    log_milestone_partners_every = fields.Integer(
        string='Log milestone every N partners',
        default=500,
        help='Log a milestone message every N partners during invoice creation '
             '(default: 500).')

    @api.model
    def default_get(self, fields_list):
        res = super(WuaInvoicingConfiguration, self).default_get(fields_list)
        ir_values = self.env['ir.values'].sudo()
        keys_calc = [
            'commit_every_n_invoices',
            'log_progress_partners_max_step',
            'log_progress_partners_divisor',
            'log_milestone_partners_every',
        ]
        for key in keys_calc:
            if key in fields_list:
                val = ir_values.get_default('wua.invoicing.configuration', key)
                if val is not None:
                    res[key] = val
        return res

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
        values.set_default('wua.invoicing.configuration',
                           'show_tax_base',
                           self.show_tax_base)
        values.set_default('wua.invoicing.configuration',
                           'group_detail_lines_of_wc_if_same_payer',
                           self.group_detail_lines_of_wc_if_same_payer)
        values.set_default('wua.invoicing.configuration',
                           'show_irrigationditch',
                           self.show_irrigationditch)
        values.set_default('wua.invoicing.configuration',
                           'show_owners',
                           self.show_owners)
        values.set_default('wua.invoicing.configuration',
                           'invoiceset_compute_management',
                           self.invoiceset_compute_management)
        values.set_default('wua.invoicing.configuration',
                           'commit_every_n_invoices',
                           self.commit_every_n_invoices)
        values.set_default('wua.invoicing.configuration',
                           'log_progress_partners_max_step',
                           self.log_progress_partners_max_step)
        values.set_default('wua.invoicing.configuration',
                           'log_progress_partners_divisor',
                           self.log_progress_partners_divisor)
        values.set_default('wua.invoicing.configuration',
                           'log_milestone_partners_every',
                           self.log_milestone_partners_every)
