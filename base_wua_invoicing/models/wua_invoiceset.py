# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import datetime
from odoo import models, fields, api, exceptions, _
from operator import itemgetter
from lxml import etree


class WuaInvoiceset(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.invoiceset'
    _description = 'Entity (invoice set)'
    _order = 'name'

    SIZE_NAME = 20
    SIZE_DESCRIPTION = 100
    SIZE_NUMERIC_CODE = 6
    SIZE_ANNUALSEQ_CODE = 4
    SIZE_INVOICESETLINE_SUFFIX = 2

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS (SELECT * FROM information_schema.tables
            WHERE table_name='wua_invoicing_configuration')
            """)
        if not self.env.cr.fetchone()[0]:
            self.env.cr.execute("""
                DELETE from ir_values
                WHERE model = 'wua.invoicing.configuration'
                """)
        # For all window actions without group assigned related to
        # account.invoice model: assign the "employee" group
        # (hide the window actions to portal users).
        group_user_id = self.env.ref('base.group_user').id
        self.env.cr.execute("""
            SELECT id FROM ir_act_window
            WHERE src_model = 'account.invoice'
            """)
        action_ids = self.env.cr.fetchall()
        if action_ids:
            for action in action_ids:
                action_id = action[0]
                sql_find_group_rel = 'SELECT EXISTS (SELECT * FROM ' + \
                    'ir_act_window_group_rel WHERE act_id = ' + \
                    str(action_id) + ')'
                self.env.cr.execute(sql_find_group_rel)
                if not self.env.cr.fetchone()[0]:
                    sql_insert_group_rel = 'INSERT INTO ' + \
                        'ir_act_window_group_rel(act_id, gid) VALUES(' + \
                        str(action_id) + ', ' + str(group_user_id) + ')'
                    self.env.cr.execute(sql_insert_group_rel)

    def _default_invoiceset_code(self):
        resp = ''
        default_invoiceset_code_type = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'default_invoiceset_code_type')
        if default_invoiceset_code_type == 1:
            resp = '1'.zfill(self.SIZE_NUMERIC_CODE)
            invoicesets = self.search([], limit=1, order='name desc')
            if len(invoicesets) == 1:
                try:
                    proposed_code = int(invoicesets[0].name)
                except Exception:
                    proposed_code = 0
                if proposed_code > 0:
                    resp = str(proposed_code + 1).zfill(self.SIZE_NUMERIC_CODE)
        if default_invoiceset_code_type == 2:
            current_year = datetime.datetime.now().year
            prefix = ''
            default_annual_seq_prefix = self.env['ir.values'].get_default(
                'wua.invoicing.configuration', 'default_annual_seq_prefix')
            if default_annual_seq_prefix:
                default_annual_seq_prefix = default_annual_seq_prefix.strip()
                if default_annual_seq_prefix != '':
                    prefix = default_annual_seq_prefix
            if prefix != '':
                prefix = prefix + '/'
            full_prefix = prefix + str(current_year).zfill(4) + '/'
            resp = full_prefix + '1'.zfill(self.SIZE_ANNUALSEQ_CODE)
            invoicesets = self.search([('name', 'like', full_prefix)],
                                      limit=1, order='name desc')
            if len(invoicesets) == 1:
                last_code = invoicesets[0].name
                if len(last_code) > len(full_prefix):
                    numeric_suffix = \
                        last_code[-(len(last_code) - len(full_prefix)):]
                    try:
                        proposed_code = int(numeric_suffix)
                    except Exception:
                        proposed_code = 0
                    if proposed_code > 0:
                        resp = full_prefix + \
                            str(proposed_code + 1).zfill(
                                self.SIZE_ANNUALSEQ_CODE)
        return resp

    def _default_journal_id(self):
        resp = None
        default_journal_id = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'default_journal_id')
        if default_journal_id:
            resp = default_journal_id
        return resp

    name = fields.Char(
        string='Code',
        size=SIZE_NAME,
        default=_default_invoiceset_code,
        required=True,
        index=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    description = fields.Char(
        string='Description',
        required=True,
        size=SIZE_DESCRIPTION)

    journal_id = fields.Many2one(
        string='Journal',
        comodel_name='account.journal',
        default=_default_journal_id,
        required=True,
        ondelete='restrict')

    date_invoiceset = fields.Date(
        string='Invoicing Date',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    date_due_invoiceset = fields.Date(
        string='Due Date')

    property_payment_term_invoiceset_id = fields.Many2one(
        string='Customer Payment Terms',
        comodel_name='account.payment.term')

    year_invoiceset = fields.Integer(
        string='Year',
        store=True,
        compute='_compute_year_invoiceset')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ], string='State',
        default='draft',
        track_visibility='onchange')

    is_being_computed = fields.Boolean(
        string='Is being computed',
        default=False,
    )

    user_id = fields.Many2one(
        string='Salesperson',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        required=True,
        readonly=True)

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice'),
        required=True,
        readonly=True)

    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True)

    number_of_invoices = fields.Integer(
        string='Invoices',
        default=0,
        readonly=True)

    amount_untaxed = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        readonly=True)

    amount_tax = fields.Monetary(
        string='Taxes',
        currency_field='currency_id',
        readonly=True)

    amount_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        readonly=True)

    notes = fields.Html(string='Notes')

    line_ids = fields.One2many(
        string='Lines',
        comodel_name='wua.invoiceset.line',
        inverse_name='invoiceset_id')

    invoice_ids = fields.One2many(
        string='Invoices',
        comodel_name='account.invoice',
        inverse_name='invoiceset_id')

    configured_invoiceset = fields.Boolean(
        string="Configured",
        store=True,
        compute='_compute_configured_invoiceset')

    comment_template1_invoiceset_id = fields.Many2one(
        string='Top Comment Template',
        comodel_name='base.comment.template')

    comment_template2_invoiceset_id = fields.Many2one(
        string='Bottom Comment Template',
        comodel_name='base.comment.template')

    note1_invoiceset = fields.Html(
        string='Top Comment',
        translate=True)

    note2_invoiceset = fields.Html(
        string='Bottom Comment',
        translate=True)

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing invoice set code.'),
        ]

    @api.depends('date_invoiceset')
    def _compute_year_invoiceset(self):
        for record in self:
            record.year_invoiceset = int(record.date_invoiceset[:4])

    @api.depends('line_ids', 'line_ids.configured_line')
    def _compute_configured_invoiceset(self):
        for record in self:
            configured = len(record.line_ids) > 0
            if configured:
                for line in record.line_ids:
                    if not line.configured_line:
                        configured = False
                        break
            record.configured_invoiceset = configured

    @api.onchange('comment_template1_invoiceset_id')
    def _set_note1_invoiceset(self):
        comment = self.comment_template1_invoiceset_id
        if comment:
            self.note1_invoiceset = comment.get_value()

    @api.onchange('comment_template2_invoiceset_id')
    def _set_note2_invoiceset(self):
        comment = self.comment_template2_invoiceset_id
        if comment:
            self.note2_invoiceset = comment.get_value()

    @api.model
    def create(self, vals):
        self.populate_lines_code_pos(self.name, vals)
        new_invoiceset = super(WuaInvoiceset, self).create(vals)
        if not self.invoicesetlines_no_repeat(vals['line_ids']):
            raise exceptions.UserError(_('There are repeated products.'))
        return new_invoiceset

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            if 'line_ids' in vals and \
               (not self.invoicesetlines_no_repeat(vals['line_ids'])):
                raise exceptions.UserError(_('There are repeated products.'))
            self.populate_lines_code_pos(self.name, vals)
        super(WuaInvoiceset, self).write(vals)
        return True

    # A invoice-set can't be deleted if there is some validated invoices
    # mapped to the invoice-set.
    @api.multi
    def unlink(self):
        for record in self:
            for invoice in record.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    raise exceptions.UserError(_(
                        'You cannot delete an invoice-set if there is a '
                        'invoice which is not draft or cancelled.'))
        return super(WuaInvoiceset, self).unlink()

    @api.multi
    def name_get(self):
        result = []
        for invoiceset in self:
            if invoiceset.description != '':
                name = invoiceset.name + ' ' + \
                    '[' + invoiceset.description + ']'
            else:
                name = invoiceset.name
            result.append((invoiceset.id, name))
        return result

    @api.multi
    def configure_invoiceset(self):
        self.ensure_one()
        view_id = self.env.ref(
            'base_wua_invoicing.wua_config_invoiceset_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Configuration of Invoice-Set Lines'),
            'res_model': 'wua.invoiceset',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'res_id': self.id,
            }
        return act_window

    @api.multi
    def calculate_invoiceset(self):
        _logger = logging.getLogger(__name__)
        compute_management = self.env['ir.values'].sudo().get_default(
            'wua.invoicing.configuration', 'invoiceset_compute_management')
        for record in self:
            if (record.is_being_computed):
                raise exceptions.UserError(_(
                    'The invoice-set is being computed. Please, wait.'))
            _logger.info('Invoiceset ' + record.name + ': Calculus started')
            if (compute_management):
                record.message_post(
                    body=_('Invoiceset calculus started'),
                )
                record.is_being_computed = True
                self.env.cr.commit()
            invoice_items = self.select_invoice_items(record)
            if len(invoice_items) > 0:
                invoice_details = self.calculate_invoice_details(invoice_items)
                if len(invoice_details) > 0:
                    invoices_data = self.group_invoice_details(invoice_details)
                    product_data = self.get_product_data(record.line_ids)
                    number_of_invoices = self.create_invoices(
                        invoices_data, record, product_data)
                    if number_of_invoices > 0:
                        total_product_quantities = \
                            self.get_total_product_quantities(invoice_details)
                        self.update_invoiceset_quantities(
                            record, total_product_quantities)
                        amounts = self.update_invoiceset_amounts(record)
                        record.write({
                            'amount_untaxed': amounts['amount_untaxed'],
                            'amount_tax': amounts['amount_tax'],
                            'amount_total': amounts['amount_total'],
                            'number_of_invoices': number_of_invoices,
                            'state': 'generated',
                            })
                        # Hook: run after the calculation
                        self.after_calculate_invoiceset(record)
            if (compute_management):
                record.message_post(
                    body=_('Invoiceset calculus ended'),
                )
                record.is_being_computed = False
            _logger.info('Invoiceset ' + record.name + ': Calculus ended')

    @api.multi
    def action_set_as_not_being_computed(self):
        self.ensure_one()
        self.is_being_computed = False

    # This method receives the invoiceset to calculate, then it loops
    # from their lines to get the linked items. The method gets a list of
    # dictionaries, a dictionary for each product. A dictionary contains:
    # - The product id.
    # - The product category code.
    # - The list of ids of the linked items (parcels, partners, water
    #   connections, irrigation gates, or others).
    def select_invoice_items(self, invoiceset):
        invoice_items = []
        for line in invoiceset.line_ids:
            if line.categ_id and line.categ_id.is_wua_product_category:
                productcategory_code = line.categ_id.productcategory_code
                if (productcategory_code == 1 or productcategory_code == 3 or
                   productcategory_code == 4):
                    item_ids = self.select_invoice_items_parcel_type(line)
                elif productcategory_code == 2:
                    item_ids = self.select_invoice_items_partner_type(line)
                elif productcategory_code == 5:
                    item_ids = self.select_invoice_items_waterconnection_type(
                        line)
                elif productcategory_code == 6:
                    item_ids = self.select_invoice_items_irrigationgate_type(
                        line)
                else:
                    # Hook for categories defined in a daugther class.
                    item_ids = self.select_invoice_items_other_types(
                        productcategory_code, line)
                if item_ids and len(item_ids) > 0:
                    item_ids.sort()
                    invoice_item = {
                        'product_id': line.product_id.id,
                        'categ_code': productcategory_code,
                        'item_ids': item_ids,
                        }
                    invoice_items.append(invoice_item)
        if len(invoice_items) > 0:
            invoice_items = sorted(invoice_items,
                                   key=itemgetter('categ_code', 'product_id'))
        return invoice_items

    def select_invoice_items_parcel_type(self, invoiceset_line):
        parcel_ids = []
        for parcel in \
            invoiceset_line.line_parcel_ids.filtered(
                lambda x: x.selected is True):
            parcel_ids.append(parcel.parcel_id.id)
        return parcel_ids

    def select_invoice_items_partner_type(self, invoiceset_line):
        partner_ids = []
        for partner in \
            invoiceset_line.line_partner_ids.filtered(
                lambda x: x.selected is True):
            partner_ids.append(partner.partner_id.id)
        return partner_ids

    def select_invoice_items_waterconnection_type(self, invoiceset_line):
        waterconnection_ids = []
        for wc in \
            invoiceset_line.line_waterconnection_ids.filtered(
                lambda x: x.selected is True):
            waterconnection_ids.append(wc.waterconnection_id.id)
        return waterconnection_ids

    def select_invoice_items_irrigationgate_type(self, invoiceset_line):
        irrigationgate_ids = []
        for ig in \
            invoiceset_line.line_irrigationgate_ids.filtered(
                lambda x: x.selected is True):
            irrigationgate_ids.append(ig.irrigationgate_id.id)
        return irrigationgate_ids

    # Hook.
    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        return []

    # This method receives a list of dictionaries with the data to
    # calculate, a dictionary for each product. These dictionaries
    # contain:
    # - The product id.
    # - The product category code.
    # - The list of ids of the linked items (parcels, partners, water
    #   connections, irrigation gates, or others).
    # From this list of data-input dictionaries, the method gets a list of
    # results dictionaries. Each calculated results dictionary will be
    # an invoice line, and it contains:
    # - The partner id.
    # - The product id.
    # - The product category code.
    # - A first additional key (examples: parcel id for categories #1,
    #   #3 and #4; partner id for category #2; water-connection id for
    #   category #5; irrigation-gate id for category #6.
    # - A second additional key, if necessary (example: parcel id for
    #   categories #5 and #6).
    # - The product quantity.
    # - The invoice line description.
    def calculate_invoice_details(self, invoice_items):
        partnerlinks = self.env['wua.parcel.partnerlink'].search([])
        invoice_details = []
        for invoice_item in invoice_items:
            product_id = invoice_item['product_id']
            categ_code = invoice_item['categ_code']
            item_ids = invoice_item['item_ids']
            invoice_details_product = []
            if categ_code == 1:
                invoice_details_product = \
                    self.calculate_invoice_details_categ01(
                        product_id, categ_code, item_ids, partnerlinks)
            elif categ_code == 2:
                invoice_details_product = \
                    self.calculate_invoice_details_categ02(
                        product_id, categ_code, item_ids, partnerlinks)
            elif categ_code == 3:
                invoice_details_product = \
                    self.calculate_invoice_details_categ03(
                        product_id, categ_code, item_ids, partnerlinks)
            elif categ_code == 4:
                invoice_details_product = \
                    self.calculate_invoice_details_categ04(
                        product_id, categ_code, item_ids, partnerlinks)
            elif categ_code == 5:
                invoice_details_product = \
                    self.calculate_invoice_details_categ05(
                        product_id, categ_code, item_ids, partnerlinks)
            elif categ_code == 6:
                invoice_details_product = \
                    self.calculate_invoice_details_categ06(
                        product_id, categ_code, item_ids, partnerlinks)
            else:
                # Hook for categories defined in a daugther class.
                invoice_details_product = \
                    self.calculate_invoice_details_others_categ(
                        product_id, categ_code, item_ids, partnerlinks)
            if len(invoice_details_product) > 0:
                invoice_details = invoice_details + invoice_details_product
        return invoice_details

    def calculate_invoice_details_categ01(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ01 = []
        parcels = self.env['wua.parcel'].browse(item_ids).filtered(
            lambda x: x.is_billable_expenses is True)
        area_measurement_name = self.get_area_measurement_name()
        for parcel in parcels:
            partnerlinks_of_parcel = partnerlinks.filtered(
                lambda x: x.parcel_id.id == parcel.id and
                x.other_costs_percentage > 0)
            if len(partnerlinks_of_parcel) > 0:
                for partnerlink in partnerlinks_of_parcel:
                    partner_id = partnerlink.partner_id.id
                    profile = partnerlink.profile
                    parcel_code = parcel.name
                    area_official = self._get_parcel_area_for_invoicing(
                        parcel, product_id)
                    area_official_str = ('%.4f' % area_official).\
                        replace('.', ',')
                    percentage = partnerlink.other_costs_percentage
                    percentage_str = '%.2f' % percentage
                    quantity = percentage / 100
                    default_parcel_label = _('Parcel')
                    parcel_label = self.get_value_from_translation(
                        'base_wua_invoicing', 'Parcel',
                        partnerlink.partner_id.lang)
                    if not parcel_label:
                        parcel_label = default_parcel_label
                    profile_name_label = self.get_profile_name(
                        profile, partnerlink.partner_id.lang)
                    default_cost_label = _('cost:')
                    cost_label = self.get_value_from_translation(
                        'base_wua_invoicing', 'cost:',
                        partnerlink.partner_id.lang)
                    if not cost_label:
                        cost_label = default_cost_label
                    description = parcel_label + ' ' + parcel_code + ' ' + \
                        '(' + area_official_str + ' ' +  \
                        area_measurement_name + '), ' + \
                        profile_name_label + \
                        ' (' + cost_label + ' ' + percentage_str + ' %)'
                    result = {
                        'partner_id': partner_id,
                        'product_id': product_id,
                        'categ_code': categ_code,
                        'key1': parcel.id,
                        'key2': 0,
                        'quantity': quantity,
                        'description': description,
                        }
                    invoice_details_categ01.append(result)
        return invoice_details_categ01

    def get_area_measurement_name(self):
        area_measurement_name = _('ha')
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode('utf_8')
        return area_measurement_name

    def get_alter_invoicing_behavior(self):
        alter_invoicing_behavior = self.get_invoicing_configuration_parameter(
            'alter_invoicing_behavior')
        return alter_invoicing_behavior

    def get_invoicing_configuration_parameter(self, field_name):
        parameter = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', field_name)
        return parameter

    def get_invoicing_area_measurement_name(self):
        configured_invoicing_area_measurement_name = ''
        alter_invoicing_behavior = self.get_alter_invoicing_behavior()
        if alter_invoicing_behavior:
            invoicing_area_measurement_name = \
                self.get_invoicing_configuration_parameter(
                    'invoicing_area_measurement_name')
            configured_invoicing_area_measurement_name = \
                invoicing_area_measurement_name.decode('utf_8')
        return configured_invoicing_area_measurement_name

    def get_invoicing_area_measurement_equivalence(self):
        configured_invoicing_area_measurement_equivalence = 0
        alter_invoicing_behavior = self.get_alter_invoicing_behavior()
        if alter_invoicing_behavior:
            invoicing_area_measurement_equivalence = \
                self.get_invoicing_configuration_parameter(
                    'invoicing_area_measurement_equivalence')
            configured_invoicing_area_measurement_equivalence = \
                invoicing_area_measurement_equivalence
        return configured_invoicing_area_measurement_equivalence

    def get_profile_name(self, profile, lang):
        resp = ''
        default_profile_o = _('owner')
        default_profile_l = _('lessee')
        default_profile_p = _('payer')
        if profile == 'O':
            resp = self.get_value_from_translation(
                'base_wua_invoicing', 'owner', lang)
            if not resp:
                resp = default_profile_o
        if profile == 'L':
            resp = self.get_value_from_translation(
                'base_wua_invoicing', 'lessee', lang)
            if not resp:
                resp = default_profile_l
        if profile == 'P':
            resp = self.get_value_from_translation(
                'base_wua_invoicing', 'payer', lang)
            if not resp:
                resp = default_profile_p
        return resp

    def calculate_invoice_details_categ02(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ02 = []
        description = ''
        product = self.env['product.product'].browse(product_id)
        for item in item_ids:
            if product:
                partner = self.env['res.partner'].browse(item)
                description = product.with_context(lang=partner.lang).name
            result = {
                'partner_id': item,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': item,
                'key2': 0,
                'quantity': 1,
                'description': description,
                }
            invoice_details_categ02.append(result)
        return invoice_details_categ02

    # Function for future modules to modify the area of the parcel used by the
    # invoicing
    # Only affects products of category 3, 4
    def _get_parcel_area_for_invoicing(self, parcel, product_id):
        area_to_return = parcel.area_official
        product = self.env['product.product'].browse(product_id)
        if (product.parcel_area_to_be_invoiced):
            # Selection field parcel_area_to_be_invoiced must have the same
            # value as the area field name: This make extensions easier
            area_to_return = getattr(
                parcel, product.parcel_area_to_be_invoiced)
        return area_to_return

    def calculate_invoice_details_categ03(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ03 = []
        parcels = self.env['wua.parcel'].browse(item_ids).filtered(
            lambda x: x.is_billable_expenses is True)
        area_measurement_name = self.get_area_measurement_name()
        # Get Invoicing Area settings
        alter_invoicing_behavior = self.get_alter_invoicing_behavior()
        show_irrigationditch = self.get_invoicing_configuration_parameter(
            'show_irrigationditch')
        show_owners = self.get_invoicing_configuration_parameter(
            'show_owners')
        if alter_invoicing_behavior:
            area_invoicing_measurement_name = \
                self.get_invoicing_area_measurement_name()
            area_invoicing_measurement_equivalence = \
                self.get_invoicing_area_measurement_equivalence()
        default_irrigationditch_label = _('Irrigationditch')
        default_parcel_label = _('Parcel')
        default_cost_label = _('cost:')
        for parcel in parcels:
            owner_percentage = (
                self.env['product.product'].browse(
                    product_id).product_tmpl_id.allow_ownerhsip_percentage and
                parcel.use_ownership_percentage_on_invoicing)
            # Conditional Owners content
            owners_of_parcel = partnerlinks.filtered(
                lambda x: x.parcel_id.id == parcel.id and
                x.ownership_percentage > 0.0)
            if (owner_percentage):
                partnerlinks_of_parcel = parcel.partnerlink_ids.filtered(
                    lambda x: x.ownership_percentage > 0.0)
            else:
                partnerlinks_of_parcel = parcel.partnerlink_ids.filtered(
                    lambda x: x.other_costs_percentage > 0.0)
            # Conditional irrigationditc content
            irrigationditch_content = ''
            if len(partnerlinks_of_parcel) > 0:
                for partnerlink in partnerlinks_of_parcel:
                    partner_id = partnerlink.partner_id.id
                    profile = partnerlink.profile
                    parcel_code = parcel.name
                    area_official = self._get_parcel_area_for_invoicing(
                        parcel, product_id)
                    area_official_str = ('%.4f' % area_official).\
                        replace('.', ',')
                    # Calculate area according to Invoicing Area setting
                    if alter_invoicing_behavior:
                        invoicing_area_official = \
                            area_official / \
                            area_invoicing_measurement_equivalence
                        invoicing_area_official_str = \
                            ('%.4f' % invoicing_area_official).\
                            replace('.', ',')
                    if (owner_percentage):
                        percentage = partnerlink.ownership_percentage
                    else:
                        percentage = partnerlink.other_costs_percentage
                    percentage_str = '%.2f' % percentage
                    # Set quantity according to Invoicing Area setting
                    if alter_invoicing_behavior:
                        quantity = invoicing_area_official * (percentage / 100)
                    else:
                        quantity = area_official * (percentage / 100)
                    parcel_label = self.get_value_from_translation(
                        'base_wua_invoicing', 'Parcel',
                        partnerlink.partner_id.lang)
                    if not parcel_label:
                        parcel_label = default_parcel_label
                    profile_name_label = self.get_profile_name(
                        profile, partnerlink.partner_id.lang)
                    cost_label = self.get_value_from_translation(
                        'base_wua_invoicing', 'cost:',
                        partnerlink.partner_id.lang)
                    if (show_irrigationditch and parcel.irrigationditch_id):
                        irrigationditch_label = self.\
                            get_value_from_translation(
                                'base_wua_invoicing', 'Irrigationditch',
                                partnerlink.partner_id.lang)
                        if not irrigationditch_label:
                            irrigationditch_label = \
                                default_irrigationditch_label
                        irrigationditch_content = '. ' + \
                            irrigationditch_label + ': ' + \
                            parcel.irrigationditch_id.name
                    if not cost_label:
                        cost_label = default_cost_label
                    # Set description according to Invoicing Area setting
                    if alter_invoicing_behavior:
                        description = parcel_label + ' ' + parcel_code + ' ' \
                            + '(' + area_official_str + ' ' + \
                            area_measurement_name + ', ' + \
                            invoicing_area_official_str + ' ' \
                            + area_invoicing_measurement_name + \
                            irrigationditch_content + '), ' + \
                            profile_name_label + \
                            ' (' + cost_label + ' ' + percentage_str + ' %)'
                    else:
                        description = parcel_label + ' ' + parcel_code \
                            + ' ' + '(' + area_official_str + ' ' +  \
                            area_measurement_name + irrigationditch_content + \
                            '), ' + profile_name_label + ' (' + cost_label + \
                            ' ' + percentage_str + ' %)'
                    # Add owners with ownership percentage list to the
                    # description
                    if (show_owners and profile != 'O'):
                        default_owners_label = _('owners')
                        owners_label = self.get_value_from_translation(
                            'base_wua_invoicing', 'owners',
                            partnerlink.partner_id.lang)
                        if not owners_label:
                            owners_label = default_owners_label
                        description += ', ' + owners_label + ': '
                        owners_descriptions = []
                        for owner in owners_of_parcel:
                            owners_descriptions.append(
                                owner.partner_id.name + ' (' + '%.2f' %
                                owner.ownership_percentage + ' %)')
                        description += ', '.join(owners_descriptions)
                    result = {
                        'partner_id': partner_id,
                        'product_id': product_id,
                        'categ_code': categ_code,
                        'key1': parcel.id,
                        'key2': 0,
                        'quantity': quantity,
                        'description': description,
                        }
                    invoice_details_categ03.append(result)
        return invoice_details_categ03

    def get_description_categ04(self, parcel, partnerlink, product_id):
        description = ''
        area_measurement_name = self.get_area_measurement_name()
        alter_invoicing_behavior = self.get_alter_invoicing_behavior()
        # Parecel info
        parcel_code = parcel.name
        area_official = self._get_parcel_area_for_invoicing(
            parcel, product_id)
        # Partnerlink info
        profile = partnerlink.profile
        percentage = partnerlink.ownership_percentage
        # Labels:
        default_parcel_label = _('Parcel')
        parcel_label = self.get_value_from_translation(
            'base_wua_invoicing', 'Parcel',
            partnerlink.partner_id.lang)
        if not parcel_label:
            parcel_label = default_parcel_label
        profile_name_label = self.get_profile_name(
            profile, partnerlink.partner_id.lang)
        default_cost_label = _('cost:')
        cost_label = self.get_value_from_translation(
            'base_wua_invoicing', 'cost:',
            partnerlink.partner_id.lang)
        if not cost_label:
            cost_label = default_cost_label
        # Values to str
        area_official_str = ('%.4f' % area_official).replace('.', ',')
        percentage_str = '%.2f' % percentage
        if alter_invoicing_behavior:
            area_invoicing_measurement_name = \
                self.get_invoicing_area_measurement_name()
            area_invoicing_measurement_equivalence = \
                self.get_invoicing_area_measurement_equivalence()
            invoicing_area_official = \
                area_official / \
                area_invoicing_measurement_equivalence
            invoicing_area_official_str = \
                ('%.4f' % invoicing_area_official).\
                replace('.', ',')
            description = parcel_label + ' ' + parcel_code + ' ' \
                + '(' + area_official_str + ' ' + \
                area_measurement_name + ', ' + \
                invoicing_area_official_str + ' ' \
                + area_invoicing_measurement_name + '), ' + \
                profile_name_label + \
                ' (' + cost_label + ' ' + percentage_str + ' %)'
        else:
            description = parcel_label + ' ' + parcel_code \
                + ' ' + '(' + area_official_str + ' ' +  \
                area_measurement_name + '), ' + \
                profile_name_label + \
                ' (' + cost_label + ' ' + percentage_str + ' %)'
        return description

    def calculate_invoice_details_categ04(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ04 = []
        parcels = self.env['wua.parcel'].browse(item_ids).filtered(
            lambda x: x.is_billable_expenses is True)
        alter_invoicing_behavior = self.get_alter_invoicing_behavior()
        # Get Invoicing Area settings
        for parcel in parcels:
            partnerlinks_of_parcel = partnerlinks.filtered(
                lambda x: x.parcel_id.id == parcel.id and
                x.ownership_percentage > 0)
            if len(partnerlinks_of_parcel) > 0:
                for partnerlink in partnerlinks_of_parcel:
                    partner_id = partnerlink.partner_id.id
                    area_official = self._get_parcel_area_for_invoicing(
                        parcel, product_id)
                    # Calculate area according to Invoicing Area setting
                    if alter_invoicing_behavior:
                        area_invoicing_measurement_equivalence = \
                            self.get_invoicing_area_measurement_equivalence()
                        invoicing_area_official = \
                            area_official / \
                            area_invoicing_measurement_equivalence
                    percentage = partnerlink.ownership_percentage
                    # Set quantity according to Invoicing Area setting
                    if alter_invoicing_behavior:
                        quantity = invoicing_area_official * (percentage / 100)
                    else:
                        quantity = area_official * (percentage / 100)
                    # Set description according to Invoicing Area setting
                    description = self.get_description_categ04(
                        parcel, partnerlink, product_id)
                    result = {
                        'partner_id': partner_id,
                        'product_id': product_id,
                        'categ_code': categ_code,
                        'key1': parcel.id,
                        'key2': 0,
                        'quantity': quantity,
                        'description': description,
                        }
                    invoice_details_categ04.append(result)
        return invoice_details_categ04

    # Return ID of the only payer (if there's only one)
    def have_same_payer_other_costs(self, parcels, partnerlinks):
        payers = []
        for parcel in parcels:
            partnerlinks_of_parcel = partnerlinks.filtered(
                lambda x: x.parcel_id.id == parcel.id and
                x.other_costs_percentage > 0)
            for partnerlink in partnerlinks_of_parcel:
                if (len(payers) == 1 and partnerlink.partner_id.id not in
                        payers):
                    return None
                else:
                    payers.append(partnerlink.partner_id.id)
        return payers[0]

    def calculate_invoice_details_categ05(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ05 = []
        waterconnections = self.env['wua.waterconnection'].browse(item_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        area_measurement_name = self.get_area_measurement_name()
        # precision = self.env['decimal.precision'].precision_get(
        #     'Product Unit of Measure')
        # The invoice line quantity always has an accuracy equal to 2
        precision = 2
        # Checked if want to group the waterconnection details if same payer
        # of other costs
        grouped_same_payer = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'group_detail_lines_of_wc_if_same_payer')
        for waterconnection in waterconnections:
            waterconnection_code = waterconnection.name
            irrigationpoints_of_waterconnection = irrigationpoints.filtered(
                lambda x: x.waterconnection_id.id == waterconnection.id)
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_expenses]
            number_of_parcels = len(parcels_of_waterconnection)
            if number_of_parcels > 0:
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                single_payer = self.is_parcels_with_a_single_payer(
                    parcels_of_waterconnection, True)
                cumulative_quantity = 0
                processed_parcels = 0
                # Checks if all parcels same water_costs
                group_parcels = False
                if (grouped_same_payer):
                    payer_id = self.have_same_payer_other_costs(
                        parcels_of_waterconnection,
                        partnerlinks)
                    if (payer_id):
                        group_parcels = True
                if (group_parcels and not total_area_official == 0):
                    partner_payer = self.env['res.partner'].browse(payer_id)
                    biggest_parcel = max(parcels_of_waterconnection,
                                         key=lambda x: x.area_official)
                    default_waterconnection_label = _('Water Connection')
                    waterconnection_label = \
                        self.get_value_from_translation(
                            'base_wua_invoicing', 'Water Connection',
                            partner_payer.lang)
                    description = waterconnection_label + ' ' + \
                        waterconnection_code
                    result = {
                        'partner_id': partner_payer.id,
                        'product_id': product_id,
                        'categ_code': categ_code,
                        'key1': waterconnection.id,
                        'key2': biggest_parcel.id,
                        'quantity': 1,
                        'description': description,
                        }
                    invoice_details_categ05.append(result)
                else:
                    for parcel in parcels_of_waterconnection:
                        if total_area_official == 0:
                            continue
                        waterconnection_quantity = \
                            round(parcel.area_official / total_area_official,
                                  precision)
                        processed_parcels = processed_parcels + 1
                        if single_payer and processed_parcels == \
                                number_of_parcels:
                            waterconnection_quantity = 1 - cumulative_quantity
                        else:
                            cumulative_quantity = cumulative_quantity + \
                                waterconnection_quantity
                        waterconnection_quantity_str = \
                            '%.2f' % (waterconnection_quantity * 100)
                        partnerlinks_of_parcel = partnerlinks.filtered(
                            lambda x: x.parcel_id.id == parcel.id and
                            x.other_costs_percentage > 0)
                        if len(partnerlinks_of_parcel) > 0:
                            for partnerlink in partnerlinks_of_parcel:
                                partner_id = partnerlink.partner_id.id
                                profile = partnerlink.profile
                                parcel_code = parcel.name
                                area_official = parcel.area_official
                                area_official_str = ('%.4f' % area_official).\
                                    replace('.', ',')
                                percentage = partnerlink.other_costs_percentage
                                percentage_str = '%.2f' % percentage
                                quantity = waterconnection_quantity * \
                                    (percentage / 100)
                                default_waterconnection_label = \
                                    _('Water Connection')
                                waterconnection_label = \
                                    self.get_value_from_translation(
                                        'base_wua_invoicing', 'Water Connectio'
                                        'n', partnerlink.partner_id.lang)
                                if not waterconnection_label:
                                    waterconnection_label = \
                                        default_waterconnection_label
                                default_parcel_label = _('parcel')
                                parcel_label = self.get_value_from_translation(
                                    'base_wua_invoicing', 'parcel',
                                    partnerlink.partner_id.lang)
                                if not parcel_label:
                                    parcel_label = default_parcel_label
                                profile_name_label = self.get_profile_name(
                                    profile, partnerlink.partner_id.lang)
                                default_cost_label = _('cost:')
                                cost_label = self.get_value_from_translation(
                                    'base_wua_invoicing', 'cost:',
                                    partnerlink.partner_id.lang)
                                if not cost_label:
                                    cost_label = default_cost_label
                                description = waterconnection_label + ' ' + \
                                    waterconnection_code + ' (' + \
                                    waterconnection_quantity_str + ' %), ' + \
                                    parcel_label + ' ' + parcel_code + ' ' + \
                                    '(' + area_official_str + ' ' +  \
                                    area_measurement_name + '), ' + \
                                    profile_name_label + \
                                    ' (' + cost_label + ' ' + \
                                    percentage_str + ' %)'
                                result = {
                                    'partner_id': partner_id,
                                    'product_id': product_id,
                                    'categ_code': categ_code,
                                    'key1': waterconnection.id,
                                    'key2': parcel.id,
                                    'quantity': quantity,
                                    'description': description,
                                    }
                                invoice_details_categ05.append(result)
        return invoice_details_categ05

    def calculate_invoice_details_categ06(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ06 = []
        irrigationgates = self.env['wua.irrigationgate'].browse(item_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'IG')])
        area_measurement_name = self.get_area_measurement_name()
        for irrigationgate in irrigationgates:
            irrigationgate_code = irrigationgate.name
            irrigationpoints_of_irrigationgate = irrigationpoints.filtered(
                lambda x: x.irrigationgate_id.id == irrigationgate.id)
            parcels_of_irrigationgate = \
                [x.parcel_id for x in irrigationpoints_of_irrigationgate
                 if x.parcel_id.is_billable_expenses]
            if len(parcels_of_irrigationgate) > 0:
                total_area_official = \
                    sum(x.area_official for x in parcels_of_irrigationgate)
                for parcel in parcels_of_irrigationgate:
                    if total_area_official == 0:
                        continue
                    irrigationgate_quantity = \
                        parcel.area_official / total_area_official
                    partnerlinks_of_parcel = partnerlinks.filtered(
                        lambda x: x.parcel_id.id == parcel.id and
                        x.other_costs_percentage > 0)
                    if len(partnerlinks_of_parcel) > 0:
                        for partnerlink in partnerlinks_of_parcel:
                            partner_id = partnerlink.partner_id.id
                            profile = partnerlink.profile
                            parcel_code = parcel.name
                            area_official = parcel.area_official
                            area_official_str = ('%.4f' % area_official).\
                                replace('.', ',')
                            percentage = partnerlink.other_costs_percentage
                            percentage_str = '%.2f' % percentage
                            quantity = irrigationgate_quantity * \
                                (percentage / 100)
                            default_irrigationgate_label = \
                                _('Irrigation Gate')
                            irrigationgate_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing', 'Irrigation Gate',
                                    partnerlink.partner_id.lang)
                            if not irrigationgate_label:
                                irrigationgate_label = \
                                    default_irrigationgate_label
                            default_parcel_label = _('parcel')
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing', 'parcel',
                                partnerlink.partner_id.lang)
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            profile_name_label = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            default_cost_label = _('cost:')
                            cost_label = self.get_value_from_translation(
                                'base_wua_invoicing', 'cost:',
                                partnerlink.partner_id.lang)
                            if not cost_label:
                                cost_label = default_cost_label
                            description = irrigationgate_label + ' ' + \
                                irrigationgate_code + ', ' + \
                                parcel_label + ' ' + parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '), ' + \
                                profile_name_label + \
                                ' (' + cost_label + ' ' + \
                                percentage_str + ' %)'
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': irrigationgate.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ06.append(result)
        return invoice_details_categ06

    # Hook.
    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        return []

    # This method receives a list of results dictionaries, and it
    # groups these results by partner id. The method gets a list of final
    # dictionaries, which are suitable for making the invoices. Each
    # list item contains:
    # - The partner id.
    # - The partner code.
    # - A list of results dictionaries; this list only contains the results
    #   dictionaries assigned to the current partner.
    # The returned list of final dictionaries is sorted by partner code.
    def group_invoice_details(self, invoice_details):
        invoices_data = []
        partner_ids = []
        for item in invoice_details:
            partner_ids.append(item['partner_id'])
        partner_ids = list(set(partner_ids))
        partners = self.env['res.partner'].browse(partner_ids).sorted(
            key=lambda x: x.partner_code)
        for partner in partners:
            result = {
                'partner_id': partner.id,
                'partner_code': partner.partner_code,
                'account_id': partner.property_account_receivable_id.id,
                'payment_term_id': partner.property_payment_term_id.id,
                'payment_mode_id': partner.customer_payment_mode_id.id,
                'customer_invoice_transmit_method_id':
                    partner.customer_invoice_transmit_method_id.id,
                'detail': filter(
                    lambda x: x['partner_id'] == partner.id, invoice_details),
                }
            invoices_data.append(result)
        return invoices_data

    # Get the product list with their data.
    def get_product_data(self, invoiceset_lines):
        product_data = []
        for line in invoiceset_lines:
            item = {
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'account_id': line.product_id.property_account_income_id.id or
                line.product_id.categ_id.property_account_income_categ_id.id,
                'tax_ids': [x.id for x in line.taxes_id],
                'uom_id': line.product_id.uom_id.id,
                }
            product_data.append(item)
        return product_data

    # Get price and account of a product.
    def get_price_account_product(self, product_data, product_id):
        resp = False
        price_account_products = \
            filter(lambda x: x['product_id'] == product_id, product_data)
        if len(price_account_products) == 1:
            resp = price_account_products[0]
        return resp

    # This method receives the list of final dictionaries from
    # group_invoice_details method, and it creates the invoices of
    # invoice set (second parameter).
    def create_invoices(self, invoices_data, record, product_data):
        number_of_invoices = 0
        paymentterms = self.env['account.payment.term']
        partners = self.env['res.partner']
        mandates = self.env['account.banking.mandate']
        for invoice_data in invoices_data:
            lines = []
            for invoice_data_line in invoice_data['detail']:
                product_id = invoice_data_line['product_id']
                price_account = self.get_price_account_product(
                    product_data, product_id)
                if price_account:
                    data = {
                        'product_id': product_id,
                        'name': invoice_data_line['description'],
                        'quantity': invoice_data_line['quantity'],
                        'price_unit': price_account['price_unit'],
                        'uom_id': price_account['uom_id'],
                        'account_id': price_account['account_id'],
                        'invoice_line_tax_ids':
                        [(4, x) for x in price_account['tax_ids']],
                        'invoiceset_id': record.id,
                        }
                    # Check if account analytic default exists for product
                    # variant and in that case add the account_analytic
                    analytic_default = self.env['account.analytic.default'].\
                        search([('product_id', '=', product_id)])
                    if (analytic_default and len(analytic_default) > 0):
                        analytic_id = analytic_default[0].analytic_id.id
                        data['account_analytic_id'] = analytic_id
                    categ_code = invoice_data_line['categ_code']
                    if categ_code == 1 or categ_code == 3 or categ_code == 4:
                        data = self.add_to_invoice_data_line_ref_to_parcel(
                            invoice_data_line, data)
                    elif categ_code == 2:
                        data = self.add_to_invoice_data_line_ref_to_partner(
                            invoice_data_line, data)
                    elif categ_code == 5:
                        data = self.add_to_invoice_data_line_ref_to_wc(
                            invoice_data_line, data)
                    elif categ_code == 6:
                        data = self.add_to_invoice_data_line_ref_to_ig(
                            invoice_data_line, data)
                    else:
                        data = \
                            self.add_to_invoice_data_line_ref_to_other_types(
                                categ_code, invoice_data_line, data)
                    data = self.add_to_invoice_data_line_other_data(
                        categ_code, invoice_data_line, data)
                    lines.append((0, 0, data))
            if (len(lines) > 0 and (not self.is_invoice_zero(lines))):
                partner_id = invoice_data['partner_id']
                date_invoice = record.date_invoiceset
                date_due = record.date_due_invoiceset
                payment_term_id = record.property_payment_term_invoiceset_id.id
                if not payment_term_id:
                    payment_term_id = invoice_data['payment_term_id']
                if not date_due:
                    if payment_term_id:
                        pterm = paymentterms.browse(payment_term_id)
                        if pterm:
                            pterm_list = pterm.with_context(
                                currency_id=self.company_id.currency_id.id).\
                                compute(value=1, date_ref=date_invoice)[0]
                            date_due = max(line[0] for line in pterm_list)
                    else:
                        date_due = date_invoice
                lang = self.env['res.partner'].browse(partner_id).lang
                note1 = record.with_context({'lang': lang}).note1_invoiceset
                note2 = record.with_context({'lang': lang}).note2_invoiceset
                invoice_vals = {
                    'partner_id': partner_id,
                    'date_invoice': date_invoice,
                    'journal_id': record.journal_id.id,
                    'account_id': invoice_data['account_id'],
                    'payment_term_id': payment_term_id,
                    'payment_mode_id': invoice_data['payment_mode_id'],
                    'date_due': date_due,
                    'transmit_method_id':
                        invoice_data['customer_invoice_transmit_method_id'],
                    'invoiceset_id': record.id,
                    'note1': note1,
                    'note2': note2,
                    'invoice_line_ids': lines,
                    }
                partner = partners.browse(partner_id)
                mandate_id = 0
                if (partner.customer_payment_mode_id.
                   payment_type == 'inbound' and partner.
                   customer_payment_mode_id.
                   payment_method_id.mandate_required):
                    mandates_of_partner_id = mandates.search([
                        ('state', '=', 'valid'),
                        ('partner_id', '=', partner_id),
                    ])
                    if mandates_of_partner_id:
                        mandate_id = mandates_of_partner_id[0].id
                if mandate_id > 0:
                    invoice_vals.update({'mandate_id': mandate_id})
                partner_shipping_id = partner.address_get(
                    ['delivery']).get('delivery')
                if partner.id != partner_shipping_id:
                    invoice_vals.update({'partner_shipping_id':
                                         partner_shipping_id})
                self.env['account.invoice'].create(invoice_vals)
                number_of_invoices = number_of_invoices + 1
        return number_of_invoices

    def add_to_invoice_data_line_ref_to_parcel(self, invoice_data_line, data):
        data['parcel_id'] = invoice_data_line['key1']
        return data

    def add_to_invoice_data_line_ref_to_partner(self, invoice_data_line, data):
        data['partner_id_frominvoiceset'] = invoice_data_line['key1']
        return data

    def add_to_invoice_data_line_ref_to_wc(
            self, invoice_data_line, data):
        data['waterconnection_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        return data

    def add_to_invoice_data_line_ref_to_ig(
            self, invoice_data_line, data):
        data['irrigationgate_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        return data

    # Hook
    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        return data

    # Hook
    def add_to_invoice_data_line_other_data(
            self, categ_code, invoice_data_line, data):
        return data

    # This method receives a list of results dictionaries, and it
    # groups these results by product id. The method gets a list of
    # dictionaries with the product and the total quantity. Each
    # list item contains:
    # - The product id.
    # - The total cumulative quantity.
    def get_total_product_quantities(self, invoice_details):
        total_product_quantities = []
        product_ids = []
        for item in invoice_details:
            product_ids.append(item['product_id'])
        product_ids = list(set(product_ids))
        for product_id in product_ids:
            result = {
                'product_id': product_id,
                'quantity': sum(x['quantity'] for x in invoice_details
                                if x['product_id'] == product_id),
                }
            total_product_quantities.append(result)
        return total_product_quantities

    # This method update the total quantity for each invoice-set line.
    def update_invoiceset_quantities(self, invoiceset,
                                     total_product_quantities):
        for line in invoiceset.line_ids:
            quantities_filtered = filter(
                lambda x: x['product_id'] == line.product_id.id,
                total_product_quantities)
            if len(quantities_filtered) == 1:
                quantity = quantities_filtered[0]['quantity']
                line.quantity = quantity

    # This method update the amount_untaxed, amount_tax and
    # amount_total fields of a invoice-set.
    def update_invoiceset_amounts(self, invoiceset):
        amount_untaxed = \
            sum(line.amount_untaxed for line in invoiceset.line_ids)
        amount_tax = \
            sum(line.amount_tax for line in invoiceset.line_ids)
        return {
            'amount_untaxed': amount_untaxed,
            'amount_tax': amount_tax,
            'amount_total': amount_untaxed + amount_tax,
            }

    # Run after the calculation (hook).
    def after_calculate_invoiceset(self, invoiceset):
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code in [1, 3, 4]:
                unselected_parcel_lines = \
                    line.line_parcel_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_parcel_lines:
                    unselected_parcel_lines.unlink()
            elif line.categ_id.productcategory_code in [2]:
                unselected_partner_lines = \
                    line.line_partner_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_partner_lines:
                    unselected_partner_lines.unlink()
            elif line.categ_id.productcategory_code in [5]:
                unselected_waterconnection_lines = \
                    line.line_waterconnection_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_waterconnection_lines:
                    unselected_waterconnection_lines.unlink()
            elif line.categ_id.productcategory_code in [6]:
                unselected_irrigationgate_lines = \
                    line.line_irrigationgate_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_irrigationgate_lines:
                    unselected_irrigationgate_lines.unlink()

    @api.multi
    def cancel_invoiceset(self):
        for record in self:
            for invoice in record.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    raise exceptions.UserError(_(
                        'You cannot cancel an invoice-set if there is a '
                        'invoice which is not draft or cancelled.'))
            self.env['account.invoice'].search(
                [('invoiceset_id', '=', record.id)]).unlink()
            for line in record.line_ids:
                line.quantity = 0
            invoiceset_vals = {
                'state': 'draft',
                'number_of_invoices': 0,
                'amount_untaxed': 0,
                'amount_tax': 0,
                'amount_total': 0,
                }
            record.write(invoiceset_vals)
            # Hook: run after the calculation
            self.after_cancel_invoiceset(record)

    # Run after cancel a invoice set (hook).
    def after_cancel_invoiceset(self, invoiceset):
        pass

    # This function returns "True" if a list of parcels has the same
    # payer (of water or other costs, depending of "water_costs" parameter.
    def is_parcels_with_a_single_payer(self, parcels, water_costs=True):
        resp = False
        if parcels:
            parcel_ids = [x.id for x in parcels]
            condition_costs = ('water_costs_percentage', '>', 0)
            if not water_costs:
                condition_costs = ('other_costs_percentage', '>', 0)
            partnerlinks = self.env['wua.parcel.partnerlink'].search(
                [('parcel_id', 'in', parcel_ids), condition_costs])
            if len(partnerlinks) > 0:
                partner_ids = [x.partner_id.id for x in partnerlinks]
                if len(list(set(partner_ids))) == 1:
                    resp = True
        return resp

    @api.multi
    def action_see_invoices(self):
        self.ensure_one()
        invoice_ids = [x.id for x in self.invoice_ids]
        if len(invoice_ids) > 0:
            condition = [('id', 'in', invoice_ids)]
            id_tree_view = self.env.ref('account.invoice_tree').id
            id_form_view = self.env.ref('account.invoice_form').id
            search_view = self.env.ref('account.view_account_invoice_filter')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Invoices'),
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                }
            return act_window

    def populate_lines_code_pos(self, invoiceset_name, vals):
        if vals and 'line_ids' in vals:
            if not invoiceset_name:
                invoiceset_name = vals['name']
            last_pos = 0
            max_invoicesetline_id = 0
            for invoicesetline in vals['line_ids']:
                invoicesetline_oper = invoicesetline[0]
                invoicesetline_id = invoicesetline[1]
                if invoicesetline_oper == 1 or invoicesetline_oper == 4:
                    if invoicesetline_id > max_invoicesetline_id:
                        max_invoicesetline_id = invoicesetline_id
            if max_invoicesetline_id > 0:
                invoicesetlines = self.env['wua.invoiceset.line']
                last_invoicesetline = \
                    invoicesetlines.browse(max_invoicesetline_id)
                if last_invoicesetline:
                    last_pos = last_invoicesetline.pos
            pos = last_pos + 1
            for invoicesetline in vals['line_ids']:
                invoicesetline_oper = invoicesetline[0]
                invoicesetline_vals = invoicesetline[2]
                if invoicesetline_oper == 0:
                    invoicesetline_vals['name'] = \
                        invoiceset_name + "-" + \
                        str(pos).zfill(self.SIZE_INVOICESETLINE_SUFFIX)
                    invoicesetline_vals['pos'] = pos
                    pos = pos + 1

    def invoicesetlines_no_repeat(self, line_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for invoicesetline in line_ids:
            invoicesetline_oper = invoicesetline[0]
            invoicesetline_id = invoicesetline[1]
            invoicesetline_vals = invoicesetline[2]
            if invoicesetline_oper == 4 or (invoicesetline_oper == 1 and
               'product_id' not in invoicesetline_vals):
                unchanged_ids.append(invoicesetline_id)
            if invoicesetline_oper == 0 or (invoicesetline_oper == 1 and
               'product_id' in invoicesetline_vals):
                implied_ids.append(invoicesetline_vals['product_id'])
        if len(unchanged_ids) > 0:
            filtered_invoicesetlines = \
                self.env['wua.invoiceset.line'].search(
                    [('id', 'in', unchanged_ids)])
            for invoicesetline in filtered_invoicesetlines:
                implied_ids.append(invoicesetline.product_id.id)
        len_of_implied_ids_original = len(implied_ids)
        if len_of_implied_ids_original > 0:
            implied_ids = list(set(implied_ids))
            len_of_implied_ids_no_repeat = len(implied_ids)
            resp = len_of_implied_ids_original == len_of_implied_ids_no_repeat
        return resp

    def is_invoice_zero(self, lines):
        resp = True
        for line in lines:
            data = line[2]
            if data['quantity'] != 0:
                resp = False
                break
        return resp

    def get_value_from_translation(self, module, src, lang):
        resp = src
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp


class WuaInvoicesetLine(models.Model):
    _name = 'wua.invoiceset.line'
    _description = 'Line of a WUA invoice set'
    _order = 'name'

    SIZE_NAME = 25

    name = fields.Char(
        string='Invoice-Set Line Code',
        size=SIZE_NAME,
        required=True,
        index=True)

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Line',
        required=True,
        default=0)

    pos_str = fields.Char(
        string='Number',
        compute='_compute_pos_str')

    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        required=True,
        index=True,
        ondelete='restrict',
        domain=[('invoiceset_selectable', '=', True)])

    categ_id = fields.Many2one(
        string='Internal Category',
        comodel_name='product.category',
        store=True,
        compute='_compute_categ_id')

    linkable_unit_type = fields.Selection([
        ('none', 'None'),
        ('parcel', 'Parcels'),
        ('partner', 'Partners'),
        ('waterconnection', 'Water Connections'),
        ('irrigationgate', 'Irrigation Gates'),
        ], string='Linkable Unit Type',
        default='none',
        store=True,
        compute='_compute_linkable_unit_type')

    quantity = fields.Float(
        string='Quantity',
        digits=(32, 4),
        required=True,
        readonly=True,
        default=0)

    price_unit = fields.Float(
        string='Unit Price',
        store=True,
        compute='_compute_price_unit')

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice'),
        required=True,
        readonly=True)

    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        related='company_id.currency_id',
        readonly=True)

    amount_untaxed = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount_untaxed')

    taxes_id = fields.Many2many(
        string='Tax Types',
        comodel_name='account.tax',
        relation='wua_invoiceset_line_account_tax_rel',
        column1='invoicesetline_id',
        column2='tax_id',
        store=True,
        compute='_compute_taxes_id')

    amount_tax = fields.Monetary(
        string='Taxes',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount_tax')

    amount_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount_total')

    # Add more types
    line_parcel_ids = fields.One2many(
        string='Lines for parcels',
        comodel_name='wua.invoiceset.line.parcel',
        inverse_name='invoicesetline_id')

    line_partner_ids = fields.One2many(
        string='Lines for partners',
        comodel_name='wua.invoiceset.line.partner',
        inverse_name='invoicesetline_id')

    line_waterconnection_ids = fields.One2many(
        string='Lines for water connections',
        comodel_name='wua.invoiceset.line.waterconnection',
        inverse_name='invoicesetline_id')

    line_irrigationgate_ids = fields.One2many(
        string='Lines for irrigation gates',
        comodel_name='wua.invoiceset.line.irrigationgate',
        inverse_name='invoicesetline_id')

    configured_line = fields.Boolean(
        string="Configured",
        store=True,
        compute='_compute_configured_line')

    @api.multi
    def _compute_pos_str(self):
        for record in self:
            pos = record.pos
            if pos:
                record.pos_str = str(pos)
            else:
                record.pos_str = ''

    @api.depends('product_id')
    def _compute_categ_id(self):
        for record in self:
            record.categ_id = record.product_id.categ_id

    @api.depends('product_id')
    def _compute_linkable_unit_type(self):
        for record in self:
            record.linkable_unit_type = record.product_id.linkable_unit_type

    @api.depends('product_id')
    def _compute_price_unit(self):
        for record in self:
            record.price_unit = record.product_id.lst_price

    @api.depends('product_id', 'quantity')
    def _compute_amount_untaxed(self):
        for record in self:
            record.amount_untaxed = \
                record.product_id.lst_price * record.quantity

    @api.depends('product_id')
    def _compute_taxes_id(self):
        for record in self:
            taxes = record.product_id.taxes_id.filtered(
                lambda x: x.type_tax_use == 'sale')
            record.taxes_id = [(5, 0)]
            if taxes:
                record.taxes_id = [(4, x.id) for x in taxes]

    @api.depends('amount_untaxed', 'taxes_id')
    def _compute_amount_tax(self):
        for record in self:
            record.amount_tax = record.amount_untaxed * \
                (sum(item.amount for item in record.taxes_id) / 100)

    # Add more types
    @api.depends('line_parcel_ids', 'line_partner_ids',
                 'line_waterconnection_ids', 'line_irrigationgate_ids')
    def _compute_configured_line(self):
        for record in self:
            # Add more types
            if record.linkable_unit_type == 'parcel':
                record.configured_line = len(record.line_parcel_ids) > 0
            if record.linkable_unit_type == 'partner':
                record.configured_line = len(record.line_partner_ids) > 0
            if record.linkable_unit_type == 'waterconnection':
                record.configured_line = \
                    len(record.line_waterconnection_ids) > 0
            if record.linkable_unit_type == 'irrigationgate':
                record.configured_line = \
                    len(record.line_irrigationgate_ids) > 0

    @api.depends('amount_untaxed', 'amount_tax')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = record.amount_untaxed + record.amount_tax

    @api.multi
    def action_select_linked_items(self):
        self.ensure_one()
        if not self.configured_line:
            self.populate_items_select()
        data_items_select = self.get_data_items_select(self.product_id.name)
        if data_items_select:
            if ('name' in data_items_select and
               'res_model' in data_items_select):
                if (data_items_select['name'] != '' and
                   data_items_select['res_model'] != ''):
                    act_window = {
                        'type': 'ir.actions.act_window',
                        'name': data_items_select['name'],
                        'res_model': data_items_select['res_model'],
                        'view_type': 'form',
                        'view_mode': 'tree',
                        'domain': [["invoicesetline_id", "=", self.id]],
                        'limit': 10000000,
                        }
                    return act_window

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaInvoicesetLine, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        compute_management = self.env['ir.values'].get_default(
            'base_wua_invoicing', 'compute_management')
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if not compute_management:
                for node in doc.xpath(
                        "//button[@name='action_set_as_not_being_computed']"):
                    node.set('invisible', 1)
                res['arch'] = etree.tostring(doc)
        return res

    def populate_items_select(self):
        # Add more types
        if self.linkable_unit_type == 'parcel':
            self.populate_items_select_parcel()
        if self.linkable_unit_type == 'partner':
            self.populate_items_select_partner()
        if self.linkable_unit_type == 'waterconnection':
            self.populate_items_select_waterconnection()
        if self.linkable_unit_type == 'irrigationgate':
            self.populate_items_select_irrigationgate()

    # Hook function for other modules to add new fields on query without
    # Rewriting all
    def _get_sql_insert_fields_select_parcel(self):
        return """
        id, create_uid, write_uid, create_date, write_date, invoicesetline_id,
        selected, parcel_id, cadastral_reference, is_billable_water,
        is_billable_expenses, leased_parcel, area_official, partner_id,
        hydraulic_infrastructure_type, pressurized_irrigation_right,
        gravityfed_irrigation_right, hydraulicsector_id, irrigationditch_id,
        with_watering_shift, with_irrigation_worker, employee_id,
        farmproperty_id"""

    # Hook function for other modules to add new fields on query without
    # Rewriting all
    def _get_sql_select_fields_select_parcel(self):
        return """
        nextval('wua_invoiceset_line_parcel_id_seq'), %s, %s, now(), now(),
        %s, TRUE, id, cadastral_reference, is_billable_water,
        is_billable_expenses, leased_parcel, area_official, partner_id,
        hydraulic_infrastructure_type, pressurized_irrigation_right,
        gravityfed_irrigation_right, hydraulicsector_id, irrigationditch_id,
        with_watering_shift, with_irrigation_worker, employee_id,
        farmproperty_id"""

    # Add more types
    def populate_items_select_parcel(self):
        parcels = self.env['wua.parcel'].search([], limit=1)
        if len(parcels) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                insert_fields_sql = self._get_sql_insert_fields_select_parcel()
                select_fields_sql = self._get_sql_select_fields_select_parcel()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_parcel (
                    """ + insert_fields_sql + """
                    )
                    SELECT """ + select_fields_sql + """
                    FROM wua_parcel WHERE active=TRUE
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_parcel_parceltag_rel
                    (invoiceset_line_parcel_id, parceltag_id)
                    SELECT l.id, r.parceltag_id
                    FROM wua_invoiceset_line_parcel as l
                    inner join wua_parcel_parceltag_rel as r
                    on l.parcel_id=r.parcel_id
                    where l.invoicesetline_id=""" + str(invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def populate_items_select_partner(self):
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)])
        if len(partners) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_partner (id, create_uid,
                    write_uid, create_date, write_date, invoicesetline_id,
                    selected, partner_id, is_company, is_owner, is_lessee,
                    is_payer, parcel_owner_number, parcel_owner_area,
                    parcel_lessee_number, parcel_lessee_area,
                    parcel_payer_number, parcel_payer_area, number_of_votes)
                    SELECT nextval('wua_invoiceset_line_partner_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id, is_company, is_owner,
                    is_lessee, is_payer, parcel_owner_number,
                    parcel_owner_area, parcel_lessee_number,
                    parcel_lessee_area, parcel_payer_number,
                    parcel_payer_area, number_of_votes
                    FROM res_partner WHERE active=TRUE and
                    is_wua_partner=TRUE
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def populate_items_select_waterconnection(self):
        waterconnections = self.env['wua.waterconnection'].search([])
        if len(waterconnections) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_waterconnection (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, waterconnection_id,
                    irrigationshed_id, hydraulicsector_id, position,
                    number_of_parcels, total_affected_area_official)
                    SELECT
                    nextval('wua_invoiceset_line_waterconnection_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id, irrigationshed_id,
                    hydraulicsector_id, position, number_of_parcels,
                    total_affected_area_official
                    FROM wua_waterconnection WHERE active
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def populate_items_select_irrigationgate(self):
        irrigationgates = self.env['wua.irrigationgate'].search([])
        if len(irrigationgates) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_irrigationgate (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, irrigationgate_id,
                    irrigationditch_id, hydraulic_order,
                    number_of_parcels, total_affected_area_official)
                    SELECT
                    nextval('wua_invoiceset_line_irrigationgate_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    irrigationditch_id, hydraulic_order,
                    number_of_parcels, total_affected_area_official
                    FROM wua_irrigationgate
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        # Add more types
        if self.linkable_unit_type == 'parcel':
            name = _('Parcels')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.parcel'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        if self.linkable_unit_type == 'partner':
            name = _('Partners')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.partner'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        if self.linkable_unit_type == 'waterconnection':
            name = _('Water Connections')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.waterconnection'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        if self.linkable_unit_type == 'irrigationgate':
            name = _('Irrigation Gates')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.irrigationgate'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select


class WuaInvoicesetLineParcel(models.Model):
    _name = 'wua.invoiceset.line.parcel'
    _description = 'Parcels of a invoice-set line'
    _order = 'invoicesetline_id,parcel_id'

    SIZE_CADASTRAL_REFERENCE = 14

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    parcel_id = fields.Many2one(
        string='Code',
        comodel_name='wua.parcel',
        required=True,
        ondelete='restrict')

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=SIZE_CADASTRAL_REFERENCE)

    is_billable_water = fields.Boolean(
        string='Billable Water', default=True)

    is_billable_expenses = fields.Boolean(
        string='Billable Expenses', default=True)

    leased_parcel = fields.Boolean(
        string='Leased Parcel', default=False)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    hydraulic_infrastructure_type = fields.Selection([
        (0, 'No infrastructure'),
        (1, 'Pressurized Irrigation'),
        (2, 'Gravity Irrigation'),
        (3, 'Pressurized and Gravity fed Irrigation'),
        ], string='Infrastructure',
        default=0)

    pressurized_irrigation_right = fields.Boolean(
        string="Water Right (pres)",
        default=True)

    gravityfed_irrigation_right = fields.Boolean(
        string="Water Right (grav)",
        default=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    with_watering_shift = fields.Boolean(
        string="With Watering Shift",
        default=True)

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker",
        default=False)

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        ondelete='restrict')

    farmproperty_id = fields.Many2one(
        string='Farm Property',
        comodel_name='wua.farmproperty',
        ondelete='restrict')

    tag_ids = fields.Many2many(
        string='Parcel Tags',
        comodel_name='wua.parceltag',
        relation='wua_invoiceset_line_parcel_parceltag_rel',
        column1='invoiceset_line_parcel_id', column2='parceltag_id',
        ondelete='cascade')

    @api.multi
    def add_to_invoiceset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)


class WuaInvoicesetLinePartner(models.Model):
    _name = 'wua.invoiceset.line.partner'
    _description = 'Partners of a invoice-set line'
    _order = 'invoicesetline_id,partner_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    partner_id = fields.Many2one(
        string='Name',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict')

    is_company = fields.Boolean(
        string='Is a Company', default=False)

    is_owner = fields.Boolean(
        string="Is Owner", default=False)

    is_lessee = fields.Boolean(
        string="Is Lessee", default=False)

    is_payer = fields.Boolean(
        string="Is Payer", default=False)

    parcel_owner_number = fields.Integer(
        string="Parcels, as owner",
        default=0)

    parcel_owner_area = fields.Float(
        string="Area, as owner",
        digits=(32, 4),
        default=0)

    parcel_lessee_number = fields.Integer(
        string="Parcels, as lessee",
        default=0)

    parcel_lessee_area = fields.Float(
        string="Area, as lessee",
        digits=(32, 4),
        default=0)

    parcel_payer_number = fields.Integer(
        string="Parcels, as payer",
        default=0)

    parcel_payer_area = fields.Float(
        string="Area, as payer",
        digits=(32, 4),
        default=0)

    number_of_votes = fields.Integer(
        string="Number of votes", default=0)

    @api.multi
    def add_to_invoiceset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)


class WuaInvoicesetLineWaterconnection(models.Model):
    _name = 'wua.invoiceset.line.waterconnection'
    _description = 'Water connections of a invoice-set line'
    _order = 'invoicesetline_id,waterconnection_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    waterconnection_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='cascade')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='cascade')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='cascade')

    position = fields.Integer(
        string="Position", default=0)

    number_of_parcels = fields.Integer(
        string='Number of parcels', default=0)

    total_affected_area_official = fields.Float(
        string='Area of parcels',
        digits=(32, 4), default=0)

    @api.multi
    def add_to_invoiceset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)


class WuaInvoicesetLineIrrigationgate(models.Model):
    _name = 'wua.invoiceset.line.irrigationgate'
    _description = 'Irrigation gates of a invoice-set line'
    _order = 'invoicesetline_id,irrigationgate_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    irrigationgate_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.irrigationgate',
        required=True,
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    hydraulic_order = fields.Integer(
        string="Hydraulic Order", default=0)

    number_of_parcels = fields.Integer(
        string='Number of parcels', default=0)

    total_affected_area_official = fields.Float(
        string='Area of parcels',
        digits=(32, 4), default=0)

    @api.multi
    def add_to_invoiceset(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {
            'selected': False,
            }
        self.write(vals)
