# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    # Hooks (sdto dolores implemented)
    def create_details_lines(self, description, line, invoice):
        # Detail line 1 - Position [244-318] Length 75
        # @INFO: Payment description | Product 1 + quantity x price = amount
        # Detail line 2 - Position [319-393] Length 75
        # @INFO: Product 2 + quantity x price = amount | Product 3 ...
        # Detail line 3 - Position [319-393] Length 75
        # @INFO: Product 4 + quantity x price = amount | Product 5 ...
        # Detail line 3 - Position [319-393] Length 75
        # @INFO: Product 6 + quantity x price = amount | Product 7 ...

        # Get invoice lines
        product_lines = []
        if invoice and invoice.invoice_line_ids:
            for iline in invoice.invoice_line_ids:
                product_name = ""
                product_total_qty = 0.0
                price = 0.0
                product_total_amount = 0.0

                product_name = iline.name
                product_total_qty = iline.quantity
                price = iline.product_id.lst_price
                product_total_amount = product_total_qty * price

                product_name[:11].ljust(11)
                product_total_qty = \
                    self.env['wua.parcel'].transform_float_to_locale(
                        product_total_qty, 2)
                product_price = \
                    self.env['wua.parcel'].transform_float_to_locale(price, 2)
                product_total_amount = \
                    self.env['wua.parcel'].transform_float_to_locale(
                        product_total_amount, 2)

                product_line = product_name + ' ' + product_total_qty + ' x ' \
                    + product_price + ' = ' + product_total_amount
                if len(product_line) > 36:
                    product_line = product_name + ' ' + product_total_qty + \
                        'x' + product_price + '=' + product_total_amount
                if len(product_line) > 36:
                    product_name = product_name[:9].ljust(9)
                    product_line = product_name + ' ' + product_total_qty + \
                        'x' + product_price + '=' + product_total_amount
                product_lines.append(product_line)

        product_lines_dic = {}
        if product_lines:
            product_line_num = 1
            for i in range(len(product_lines)):
                product_lines_dic[
                    "product_line_{0}".format(product_line_num)] = \
                    product_lines[i]
                product_line_num += 1

        line_detail_1 = line_detail_2 = line_detail_3 = line_detail_4 = ""
        if product_lines_dic:
            if "product_line_1" in product_lines_dic:
                line_detail_1 = description[:36].ljust(36) + ' | ' + \
                    product_lines_dic["product_line_1"][:36]
            if "product_line_2" in product_lines_dic:
                line_detail_2 = \
                    product_lines_dic["product_line_2"][:36].ljust(36)
            if "product_line_3" in product_lines_dic:
                line_detail_2 = line_detail_2 + ' | ' + \
                    product_lines_dic["product_line_3"][:36].ljust(36)
            if "product_line_4" in product_lines_dic:
                line_detail_3 = \
                    product_lines_dic["product_line_4"][:36].ljust(36)
            if "product_line_5" in product_lines_dic:
                line_detail_3 = line_detail_3 + ' | ' + \
                    product_lines_dic["product_line_5"][:36].ljust(36)
            if "product_line_6" in product_lines_dic:
                line_detail_4 = \
                    product_lines_dic["product_line_6"][:36].ljust(36)
            if "product_line_7" in product_lines_dic:
                line_detail_4 = line_detail_4 + ' | ' + \
                    product_lines_dic["product_line_7"][:36].ljust(36)

            # Adjust
            line_detail_1 = line_detail_1.ljust(75)
            line_detail_2 = line_detail_2.ljust(75)
            line_detail_3 = line_detail_3.ljust(75)
            line_detail_4 = line_detail_4.ljust(75)

        return line_detail_1, line_detail_2, line_detail_3, line_detail_4
