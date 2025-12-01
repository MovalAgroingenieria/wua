# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to recompute the
    # sum_price_subtotal and number_of_invoicing_processes fields
    # (model: wua.enrolledparcel), because these functions are not
    # called when the "invoiceline_ids" field of wua.enrolledparcel
    # model is None.
    @api.multi
    def unlink(self):
        watertransfer_ids = []
        for record in self:
            for line in record.line_ids:
                if line.categ_id.productcategory_code == 21:
                    for l_watertransfer in line.line_watertransfer_ids:
                        watertransfer_ids.append(
                            l_watertransfer.watertransfer_id.id)
        res = super(WuaInvoiceset, self).unlink()
        if watertransfer_ids:
            watertransfer_ids = list(set(watertransfer_ids))
            watertransfers = \
                self.env['wua.watertransfer'].browse(watertransfer_ids)
            watertransfers._compute_sum_price_subtotal()
            watertransfers._compute_number_of_invoicing_processes()
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 21:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        watertransfer_ids = []
        for watertransfer in \
            invoiceset_line.line_watertransfer_ids.filtered(
                lambda x: x.selected is True):
            watertransfer_ids.append(
                watertransfer.watertransfer_id.id)
        return watertransfer_ids

    def get_description_categ21(self, watertransfer,
                                product_id, quantity):
        description = ""
        product = self.env['product.product'].browse(product_id)
        uom = product.uom_id.name
        description = _("Water Transfer: ") + str(watertransfer.volume) + \
            " " + uom
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 21:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ21 = []
        watertransfers = self.env['wua.watertransfer'].browse(item_ids)
        for watertransfer in watertransfers:
            partner_id = watertransfer.partner_id.id
            quantity = watertransfer.volume
            description = self.get_description_categ21(
                watertransfer, product_id, quantity)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': watertransfer.id,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ21.append(result)
        return invoice_details_categ21

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 21:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['watertransfer_id'] = invoice_data_line['key1']
        return data

    # See comment of "unlink".
    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        watertransfer_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 21:
                for line_watertransfer in line.line_watertransfer_ids:
                    watertransfer_ids.append(
                        line_watertransfer.watertransfer_id.id)
        if watertransfer_ids:
            watertransfer_ids = list(set(watertransfer_ids))
            watertransfers = \
                self.env['wua.watertransfer'].browse(watertransfer_ids)
            watertransfers._compute_sum_price_subtotal()
            watertransfers._compute_number_of_invoicing_processes()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('watertransfer', 'Water transfers')])

    line_watertransfer_ids = fields.One2many(
        string='Lines for Water transfers',
        comodel_name='wua.invoiceset.line.watertransfer',
        inverse_name='invoicesetline_id')

    @api.depends('line_watertransfer_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'watertransfer':
                record.configured_line = \
                    len(record.line_watertransfer_ids) > 0

    def populate_items_select(self):
        if self.linkable_unit_type == 'watertransfer':
            self.populate_items_select_watertransfer(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_watertransfer(self, product_id):
        watertransfers = self.env['wua.watertransfer'].search(
            [('number_of_invoicing_processes', '=', 0)]
        )
        if len(watertransfers) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_watertransfer (
                        id, create_uid, write_uid, create_date, write_date,
                        invoicesetline_id, selected,
                        watertransfer_id, partner_id,
                        volume, number_of_invoicing_processes,
                        sum_price_subtotal
                    )
                    SELECT
                        nextval('wua_invoiceset_line_watertransfer_id_seq'),
                        %s, %s, now(), now(),
                        %s, TRUE,
                        e.id,
                        e.partner_id,
                        e.volume,
                        e.number_of_invoicing_processes,
                        e.sum_price_subtotal
                    FROM wua_watertransfer e
                    WHERE e.number_of_invoicing_processes = 0
                """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'watertransfer':
            name = _('Water Transfer')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.watertransfer'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLinewatertransfer(models.Model):
    _name = 'wua.invoiceset.line.watertransfer'
    _description = 'Water transfer of a invoice-set line'
    _order = 'invoicesetline_id,watertransfer_id'

    MAX_SIZE_SUBPARCEL_CODE = 25

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    watertransfer_id = fields.Many2one(
        string='Water transfer',
        comodel_name='wua.watertransfer',
        required=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 2),
        default=0,
        compute='_compute_volume',
        store=True,
    )

    sum_price_subtotal = fields.Float(
        string='Invoiced Amount')

    number_of_invoicing_processes = fields.Integer(
        string='Invoicing Processes')

    @api.depends('invoicesetline_id')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('watertransfer_id',
                 'watertransfer_id.volume')
    def _compute_volume(self):
        for record in self:
            volume = 0
            if (record.watertransfer_id):
                volume = record.watertransfer_id.volume
            record.volume = volume

    @api.depends('invoicesetline_id')
    def _compute_number_of_invoicing_processes(self):
        for record in self:
            number_of_invoicing_processes = 0
            invoiceset_ids = []
            for invoiceline in record.invoiceline_ids:
                if (invoiceline.invoiceset_id not in invoiceset_ids):
                    number_of_invoicing_processes += 1
                    invoiceset_ids.appends(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.multi
    def add_to_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': True,
                }
            self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': False,
                }
            self.write(vals)

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp
