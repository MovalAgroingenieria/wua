# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    # Fields
    entity_type_code = fields.Selection([
        ('A', 'Town hall'),
        ('C', 'Water user assotiation')],
        string="Entity type",
        help="The type of entity",
        default="C",
        compute="get_entity_type_code",
        readonly=True)

    # Hooks (wua implemented)
    def get_entity_type_code(self):
        # Entity type code
        # Positions [015-015] Length 1
        # @INFO: It is always C, that identify wua in spanish
        self.entity_type_code = 'C'
        entity_type_code = self.entity_type_code
        return entity_type_code

    def get_fixed_number(self, partner_id):
        # Fixed number
        # Position [223-234] Length 12
        # @INFO: Is the wua associate number
        #        The format depends on each wua
        if partner_id.partner_code:
            # Format 5 numbers padded with zeros
            # and padded to 12 with white spaces
            fixed_number = str(partner_id.partner_code).zfill(5).ljust(12)
        else:
            raise ValidationError(
                _("Fail, partner code not found for partner %s." %
                  (partner_id.name)))
        return fixed_number

    def create_details_lines(self, description, line, invoice):
        # Detail line 1 - Position [244-318] Length 75
        # @INFO: It is filled with invoiceset name, invoice number and amount
        #        Description and line are not used (parent hook)
        line_detail_1 = ""
        if invoice and invoice.invoiceset_id:
            amount_total = self.env['wua.parcel'].transform_float_to_locale(
                invoice.amount_total, 2)
            line_detail_1 = invoice.invoiceset_id.description + ' ' \
                + invoice.number + ' ' + amount_total + ' ' \
                + invoice.currency_id.name
            line_detail_1 = line_detail_1[:75].ljust(75)
        else:
            line_detail_1 = str(" " * 75)

        # Detail line 2 - Position [319-393] Length 75
        # @INFO: Product 1 + total quantity + price currency/unit

        # Detail line 3 - Position [319-393] Length 75
        # @INFO: Product 2 + total quantity + price currency/unit

        # Detail line 3 - Position [319-393] Length 75
        # @INFO: Product 3 + total quantity + price currency/unit

        # Get products
        products = []
        if invoice and invoice.invoice_line_ids:
            for iline in invoice.invoice_line_ids:
                if iline.product_id not in products:
                    products.append(iline.product_id)

        # Construct product lines
        # @INFO [2024.09.18]: Quantity is rounded to 4 decimal places
        product_lines = []
        if products:
            for product in products:
                product_name = ""
                product_total_qty = 0.0
                for iline in invoice.invoice_line_ids:
                    if iline.product_id.id == product.id:
                        product_total_qty = product_total_qty + iline.quantity
                product_total_qty = \
                    self.env['wua.parcel'].transform_float_to_locale(
                        product_total_qty, 4)
                product_price = \
                    self.env['wua.parcel'].transform_float_to_locale(
                        product.lst_price, 2)
                product_unit = product.uom_id.name
                if product.attribute_value_ids:
                    for variant in product.attribute_value_ids:
                        product_name = product.name + ' ' + variant.name
                else:
                    product_name = product.name
                product_line = product_name + ' ' + product_total_qty + ' ' \
                    + product_unit + ' ' + _('to') + ' ' + product_price + ' '\
                    + invoice.currency_id.name + '/' + product_unit
                product_lines.append(product_line)

        lines_dic = {}
        if product_lines:
            detail_line_num = 2
            for i in range(len(product_lines)):
                lines_dic["line_detail_{0}".format(detail_line_num)] = \
                    product_lines[i]
                detail_line_num += 1

        line_detail_2 = line_detail_3 = line_detail_4 = ""
        if lines_dic:
            if "line_detail_2" in lines_dic:
                line_detail_2 = lines_dic["line_detail_2"][:75].ljust(75)
            else:
                line_detail_2 = str(" " * 75)
            if "line_detail_3" in lines_dic:
                line_detail_3 = lines_dic["line_detail_3"][:75].ljust(75)
            else:
                line_detail_3 = str(" " * 75)
            if "line_detail_4" in lines_dic:
                line_detail_4 = lines_dic["line_detail_4"][:75].ljust(75)
            else:
                line_detail_4 = str(" " * 75)
            if "line_detail_5" in lines_dic:
                remaining_products = len(lines_dic) - 2
                line_detail_4 = \
                    _("There are still %s products left, see invoice for "
                      "details.") % remaining_products
                line_detail_4 = line_detail_4[:75].ljust(75)

        return line_detail_1, line_detail_2, line_detail_3, line_detail_4

    @api.multi
    def generated2uploaded(self):
        res = super(AccountPaymentOrder, self).generated2uploaded()
        for order in self:
            if order.payment_mode_id.name == 'SUMA':
                for bline in order.bank_line_ids:
                    if bline.suma_sent:
                        for l in bline.payment_line_ids:
                            if bline.name == l.bank_line_id.name:
                                invoice = l.invoice_id
                                invoice.write({
                                    'in_suma': True,
                                    'suma_ref': bline.suma_ref,
                                })
                                move_lines = self.env[
                                    'account.move.line'].search(
                                        [('invoice_id', '=', invoice.id)])
                            if move_lines:
                                for move_line in move_lines:
                                    move_line.suma_ref = bline.suma_ref
        return res

    def process_missing_functions(self):
        super(AccountPaymentOrder, self).process_missing_functions()
        for order in self:
            if order.payment_mode_id.name == 'SUMA':
                for bline in order.bank_line_ids:
                    if bline.suma_sent:
                        for line in bline.payment_line_ids:
                            if bline.name == line.bank_line_id.name:
                                invoice = line.invoice_id
                                invoice.write({
                                    'in_suma': True,
                                    'suma_ref': bline.suma_ref,
                                })
                                move_lines = self.env[
                                    'account.move.line'].search(
                                        [('invoice_id', '=', invoice.id)])
                            if move_lines:
                                for move_line in move_lines:
                                    move_line.suma_ref = bline.suma_ref
