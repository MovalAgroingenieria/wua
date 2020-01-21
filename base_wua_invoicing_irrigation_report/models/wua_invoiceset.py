# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to recompute the
    # sum_price_subtotal and number_of_invoicing_processes fields
    # (model: wua.irrigationreport), because these functions are not
    # called when the "invoiceline_ids" field of wua.irrigationreport
    # model is None.
    @api.multi
    def unlink(self):
        irrigationreport_ids = []
        for record in self:
            for line in record.line_ids:
                if line.categ_id.productcategory_code == 11:
                    for l_irrigationreport in line.line_irrigationreport_ids:
                        irrigationreport_ids.append(
                            l_irrigationreport.irrigationreport_id.id)
        res = super(WuaInvoiceset, self).unlink()
        if irrigationreport_ids:
            irrigationreport_ids = list(set(irrigationreport_ids))
            irrigationreports = \
                self.env['wua.irrigationreport'].browse(irrigationreport_ids)
            irrigationreports._compute_sum_price_subtotal()
            irrigationreports._compute_number_of_invoicing_processes()
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 11:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        irrigationreport_ids = []
        for irrigationreport in \
            invoiceset_line.line_irrigationreport_ids.filtered(
                lambda x: x.selected is True):
            irrigationreport_ids.append(
                irrigationreport.irrigationreport_id.id)
        return irrigationreport_ids

    def get_description(self, irrigationreport):
        description = ""
        if irrigationreport:
            intake_name = irrigationreport.intake_id.name
            water_type = irrigationreport.product_id.product_tmpl_id.name
            irrigationreport_num = irrigationreport.irrigationreport_number
            description = intake_name + ', ' + water_type + ', ' + \
                _('Report num. ') + str(irrigationreport_num)
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, False):
        if categ_code != 11:
            partnerlinks = ""
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        invoice_details_categ11 = []
        irrigationreports = self.env['wua.irrigationreport'].browse(item_ids)
        for irrigationreport in irrigationreports:
            partner_id = irrigationreport.partner_id.id
            product_id = product_id
            categ_code = categ_code
            key1 = irrigationreport.id
            key2 = irrigationreport.intake_id.id
            if data_in_hours:
                quantity = irrigationreport.hours
            else:
                quantity = irrigationreport.volume_real
            description = self.get_description(irrigationreport)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': key1,
                'key2': key2,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ11.append(result)
        return invoice_details_categ11

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 11:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['irrigationreport_id'] = invoice_data_line['key1']
        data['intake_id'] = invoice_data_line['key2']
        return data

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        irrigationreport_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 11:
                for line_irrigationreport in line.line_irrigationreport_ids:
                    irrigationreport_ids.append(
                        line_irrigationreport.irrigationreport_id.id)
        if irrigationreport_ids:
            irrigationreport_ids = list(set(irrigationreport_ids))
            irrigationreports = \
                self.env['wua.irrigationreport'].browse(irrigationreport_ids)
            irrigationreports._compute_sum_price_subtotal()
            irrigationreports._compute_number_of_invoicing_processes()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('irrigationreport', 'Irrigation Report')])

    line_irrigationreport_ids = fields.One2many(
        string="Selected items for invoice-set line",
        comodel_name="wua.invoiceset.line.irrigationreport",
        inverse_name="invoicesetline_id")

    def populate_items_select(self):
        if self.linkable_unit_type == 'irrigationreport':
            self.populate_items_select_irrigationreport(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_irrigationreport(self, product_id):
        irrigationreports = self.env['wua.irrigationreport'].search(
            [('of_active_agriculturalseason', '=', True),
             ('is_validated', '=', True),
             ('invoiced', '=', False),
             ('product_id.id', '=', product_id)])
        if len(irrigationreports) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                INSERT INTO wua_invoiceset_line_irrigationreport (id,
                 create_uid,write_uid,create_date,write_date,invoicesetline_id,
                 irrigationreport_id,selected,irrigationreport_number,
                 report_initial_time,report_end_time,intake_id,product_id,
                 partner_id,volume_real)
                SELECT nextval('wua_invoiceset_line_irrigationreport_id_seq'),
                 %s,%s,now(),now(),%s,e.id,TRUE,e.irrigationreport_number,
                 e.report_initial_time,e.report_end_time,e.intake_id,
                 e.product_id,e.partner_id,e.volume_real
                FROM wua_irrigationreport e INNER JOIN wua_agriculturalseason a
                ON e.agriculturalseason_id = a.id""", (user_id, user_id,
                                                       invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))

    @api.depends('line_irrigationreport_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'irrigationreport':
                record.configured_line = \
                    len(record.line_irrigationreport_ids) > 0

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'irrigationreport':
            name = _('Irrigation Report')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.irrigationreport'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineIrrigationreport(models.Model):
    _name = 'wua.invoiceset.line.irrigationreport'
    _description = 'Irrigation reports of a invoice-set line'
    _order = 'invoicesetline_id,irrigationreport_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    irrigationreport_id = fields.Many2one(
        string='Irrigation Report',
        comodel_name='wua.irrigationreport',
        required=True,
        ondelete='restrict')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    irrigationreport_number = fields.Integer(
        string="Report Number")

    report_initial_time = fields.Datetime(
        string='Start Time')

    report_end_time = fields.Datetime(
        string='End Time')

    intake_id = fields.Many2one(
        string="Intake",
        comodel_name="wua.intake",
        ondelete="restrict")

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        ondelete='restrict')

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        ondelete="restrict")

    volume_real = fields.Float(
        string='Real Volume (m3)',
        digits=(32, 4))

    @api.multi
    def add_to_invoiceset(self):
        vals = {'selected': True, }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {'selected': False, }
        self.write(vals)
