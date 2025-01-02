# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import datetime
from datetime import datetime
from odoo import models, fields, api, exceptions, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to reset the invoiceset_id
    # and invoiced_consumption fields for the affected consumptions.
    @api.multi
    def unlink(self):
        tankconsumptions_ids = []
        for record in self:
            tankconsumptions = self.env['wua.tankconsumption'].search(
                [('invoiceset_id', '=', record.id)])
            for tankconsumption in tankconsumptions:
                tankconsumptions_ids.append(tankconsumption.id)
        res = super(WuaInvoiceset, self).unlink()
        if tankconsumptions_ids:
            tankconsumptions = self.env['wua.tankconsumption'].browse(
                tankconsumptions_ids)
            vals = {
                'invoiceset_id': None,
                'invoiced_consumption': False,
                }
            tankconsumptions.write(vals)
        return res

    def select_invoice_items_other_types(
            self, productcategory_code, invoiceset_line):
        if productcategory_code != 15:
            return super(
                WuaInvoiceset, self).select_invoice_items_other_types(
                    productcategory_code, invoiceset_line)
        tankconsumption_ids = []
        for tankconsumption in \
            invoiceset_line.line_tankconsumption_ids.filtered(
                lambda x: x.selected is True):
            tankconsumption_ids.append(tankconsumption.tankconsumption_id.id)
        return tankconsumption_ids

    def calculate_invoice_details_others_categ(
            self, product_id, categ_code, item_ids, partnerlinks):
        if categ_code != 15:
            return super(
                WuaInvoiceset, self).calculate_invoice_details_others_categ(
                    product_id, categ_code, item_ids, partnerlinks)

        utc_tz = pytz.timezone('UTC')
        invoice_details_categ15 = []
        tankconsumptions = self.env['wua.tankconsumption'].browse(item_ids)
        for tankconsumption in tankconsumptions:
            partner_id = tankconsumption.partner_id.id
            tz = tankconsumption.partner_id.tz
            if (not tz):
                tz = 'Europe/Madrid'
            user_tz = pytz.timezone(tz)
            key1 = tankconsumption.tank_id
            quantity = tankconsumption.volume_real
            end_date_time = datetime.strptime(
                tankconsumption.end_time, "%Y-%m-%d %H:%M:%S")
            end_date_es_str = str(utc_tz.localize(
                end_date_time).astimezone(user_tz)).split('+')[0]
            end_time_es = datetime.strptime(
                end_date_es_str, '%Y-%m-%d %H:%M:%S').strftime(
                '%d/%m/%Y %H:%M:%S')
            description = _('Tank consumption') + ' ' + \
                tankconsumption.tank_id.name + ' ' + end_time_es
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': key1,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ15.append(result)
        return invoice_details_categ15

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 15:
                unselected_tankconsumptions = \
                    line.line_tankconsumption_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_tankconsumptions:
                    tankconsumptions_ids = []
                    for line_tankconsumption in unselected_tankconsumptions:
                        tankconsumptions_ids.append(
                            line_tankconsumption.tankconsumption_id.id)
                    if tankconsumptions_ids:
                        tankconsumptions = \
                            self.env['wua.tankconsumption'].browse(
                                tankconsumptions_ids)
                        vals = {
                            'invoiceset_id': None,
                            'invoiced_consumption': False,
                            }
                        tankconsumptions.write(vals)
                    unselected_tankconsumptions.unlink()

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 15:
                tankconsumptions_ids = []
                for line_tankconsumption in line.line_tankconsumption_ids:
                    tankconsumptions_ids.append(
                        line_tankconsumption.tankconsumption_id.id)
                if tankconsumptions_ids:
                    tankconsumptions = self.env['wua.tankconsumption'].browse(
                        tankconsumptions_ids)
                    vals = {
                        'invoiceset_id': None,
                        'invoiced_consumption': False,
                        }
                    tankconsumptions.write(vals)
                line.line_tankconsumption_ids.unlink()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('tankconsumption', 'Tank Consumptions')])

    line_tankconsumption_ids = fields.One2many(
        string='Lines for tank consumptions',
        comodel_name='wua.invoiceset.line.tankconsumption',
        inverse_name='invoicesetline_id')

    @api.depends('line_tankconsumption_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'tankconsumption':
                record.configured_line = \
                    len(record.line_tankconsumption_ids) > 0

    # If a tank consumption line is deleted, it is necessary to reset
    # the invoiceset_id field for the affected consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            tankconsumptions_ids = []
            for line_tankconsumption in record.line_tankconsumption_ids:
                tankconsumptions_ids.append(
                    line_tankconsumption.tankconsumption_id.id)
            if tankconsumptions_ids:
                tankconsumptions = self.env['wua.tankconsumption'].browse(
                    tankconsumptions_ids)
                vals = {
                    'invoiceset_id': None,
                    'invoiced_consumption': False,
                    }
                tankconsumptions.write(vals)
        return super(WuaInvoicesetLine, self).unlink()

    def populate_items_select(self):
        if self.linkable_unit_type == 'tankconsumption':
            self.populate_items_select_tankconsumption(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_tankconsumption(self, product_id):
        tankconsumptions = self.env['wua.tankconsumption'].search([
            ('product_id', '=', product_id), ('invoiceset_id', '=', False)])
        if len(tankconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_tankconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, tankconsumption_id,
                    tank_id, hydraulicsector_id, initial_time, end_time,
                    volume_request, volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_tankconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id, tank_id,
                    hydraulicsector_id, initial_time, end_time,
                    volume_request, volume_real
                    FROM wua_tankconsumption
                    WHERE product_id=%s and invoiceset_id IS NULL AND validated
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_tankconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null AND validated""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'tankconsumption':
            name = _('Tank Consumptions')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.tankconsumption'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineTankconsumption(models.Model):
    _name = 'wua.invoiceset.line.tankconsumption'
    _description = 'Tank consumptions of a invoice-set line'
    _order = 'invoicesetline_id,tankconsumption_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    tankconsumption_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.tankconsumption',
        required=True,
        ondelete='restrict')

    tank_id = fields.Many2one(
        string='Tank',
        comodel_name='wua.tank',
        required=True,
        ondelete='restrict')

    initial_time = fields.Datetime(
        string='Start filling',
        required=True)

    end_time = fields.Datetime(
        string='End filling',
        required=True)

    volume_request = fields.Float(
        string='Vol. requested (m³)',
        digits=(32, 4),
        required=True)

    volume_real = fields.Float(
        string='Vol. consumed (m³)',
        digits=(32, 4),
        required=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        required=True,
        ondelete='restrict')

    @api.multi
    def add_to_invoiceset(self):
        vals = {'selected': True, }
        self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        vals = {'selected': False, }
        self.write(vals)
