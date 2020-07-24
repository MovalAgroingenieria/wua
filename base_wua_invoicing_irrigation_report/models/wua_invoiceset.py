# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
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

    def group_invoice_details(self, invoice_details):
        individual_invoice = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'irrigationreport_individual_invoice')
        invoices_data = []
        if (individual_invoice):
            invoice_details_with_irrigation_report =  \
                self.get_invoice_details_with_irrigation_report(
                    invoice_details)
            invoice_details_without_irrigation_report = \
                [x for x in invoice_details
                    if x not in invoice_details_with_irrigation_report]
            invoices_data = self.group_invoice_details_with_irrigation_report(
                invoice_details_with_irrigation_report) + \
                super(WuaInvoiceset, self).group_invoice_details(
                    invoice_details_without_irrigation_report)
        else:
            invoices_data = super(WuaInvoiceset, self).group_invoice_details(
                invoice_details)
        return invoices_data

    def get_invoice_details_with_irrigation_report(self, invoice_details):
        invoice_details_with_irrigation_report = []
        for invoice_detail in invoice_details:
            if (invoice_detail['categ_code'] == 11):
                invoice_details_with_irrigation_report.append(invoice_detail)
        return invoice_details_with_irrigation_report

    def group_invoice_details_with_irrigation_report(self, invoice_details):
        invoices_data = []
        for invoice_detail in invoice_details:
            partner = self.env['res.partner'].browse(
                invoice_detail['partner_id'])
            if partner:
                result = {
                    'partner_id': invoice_detail['partner_id'],
                    'partner_code': partner.partner_code,
                    'account_id': partner.property_account_receivable_id.id,
                    'payment_term_id': partner.property_payment_term_id.id,
                    'payment_mode_id': partner.customer_payment_mode_id.id,
                    'customer_invoice_transmit_method_id':
                        partner.customer_invoice_transmit_method_id.id,
                    'detail': [invoice_detail],
                    }
                invoices_data.append(result)
        return invoices_data

    def get_description(self, irrigationreport):
        description = ""
        if irrigationreport:
            intake_name = irrigationreport.intake_id.name
            language = irrigationreport.partner_id.lang
            water_type = irrigationreport.with_context(
                {'lang': language}).product_id.product_tmpl_id.name
            delivery_note = irrigationreport.delivery_note
            reading_times_info = ''
            default_consumption_label = _('Consumption')
            data_in_hours = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'data_in_hours')
            hours_in_sexagesimal = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'hours_sexagesimal')
            initial_reading_label = self.get_value_from_translation(
                'base_wua_invoicing_irrigation_report',
                'Start Time', language)
            final_reading_label = self.get_value_from_translation(
                'base_wua_invoicing_irrigation_report',
                'End Time', language)
            consumption_label = self.get_value_from_translation(
                'base_wua_invoicing_irrigation_report',
                'Consumption', language)
            if not consumption_label:
                consumption_label = default_consumption_label
            report_initial_time = datetime.datetime.strptime(
                irrigationreport.report_initial_time, '%Y-%m-%d %H:%M:%S')
            if (data_in_hours):
                report_initial_time = report_initial_time.strftime('%x') + \
                    ' ' + report_initial_time.strftime('%H:%M')
            else:
                report_initial_time = report_initial_time.strftime('%x')
            report_end_time = datetime.datetime.strptime(
                irrigationreport.report_end_time, '%Y-%m-%d %H:%M:%S')
            if (data_in_hours):
                report_end_time = report_end_time.strftime('%x') + ' ' + \
                    report_end_time.strftime('%H:%M')
            else:
                report_end_time = report_end_time.strftime('%x')
            date_str = '. '
            reading_details = ''
            time_duration = ''
            if (not data_in_hours):
                reading_in_detail = self.env['ir.values'].get_default(
                    'wua.invoicing.configuration',
                    'irrigationreport_readings_data_in_detail')
                if (reading_in_detail):
                    reading_details = '. '
                    initial_value_label = self.get_value_from_translation(
                        'base_wua_invoicing_irrigation_report',
                        'Initial Reading', language)
                    if (not initial_value_label):
                        initial_value_label = _('Initial Reading')
                    end_value_label = self.get_value_from_translation(
                        'base_wua_invoicing_irrigation_report',
                        'End Reading', language)
                    if (not end_value_label):
                        end_value_label = _('End Reading')
                    reading_details = reading_details + ' ' + \
                        initial_value_label + ': ' + \
                        str(irrigationreport.initial_volume) + ' - ' + \
                        end_value_label + ': ' + \
                        str(irrigationreport.end_volume)
            else:
                duration_label = self.get_value_from_translation(
                    'base_wua_invoicing_irrigation_report',
                    'Duration', language)
                if (not duration_label):
                    duration_label = _('Duration')
                hours = ''
                if (hours_in_sexagesimal):
                    hours_value = int(irrigationreport.hours)
                    minutes_value = (irrigationreport.hours*60) % 60
                    hours = "%02d:%02d" % (hours_value, minutes_value)
                else:
                    hours = str(irrigationreport.hours)
                time_duration = time_duration + duration_label + ': ' + \
                    hours + '. '
            if (report_initial_time == report_end_time):
                date_reading_label = _('Date')
                date_reading_label = self.get_value_from_translation(
                    'base_wua_invoicing_irrigation_report',
                    'Date', language)
                date_str = date_reading_label + ': ' + report_end_time + \
                    '. '
            else:
                date_str = initial_reading_label + ': ' + \
                    report_initial_time + '. ' + \
                    final_reading_label + ': ' + report_end_time + '. '
            volume = irrigationreport.volume_real
            reading_times_info = date_str + time_duration + \
                consumption_label + ': ' + \
                '{0:.0f}'.format(volume) + ' m3'
            description = intake_name + ', ' + water_type + ', ' + \
                _('delivery note num. ') + str(delivery_note) + '. ' + \
                reading_times_info + reading_details
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 11:
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
        if irrigationreports:
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
                %s,%s,now(),now(),%s,i.id,TRUE,i.irrigationreport_number,
                i.report_initial_time,i.report_end_time,i.intake_id,
                i.product_id,i.partner_id,i.volume_real
                FROM wua_irrigationreport i INNER JOIN wua_agriculturalseason a
                ON i.agriculturalseason_id = a.id WHERE i.is_validated AND
                a.active_agriculturalseason AND i.invoiced=FALSE AND
                i.product_id=%s""", (user_id, user_id, invoicesetline_id,
                                     product_id))
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
