# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _, exceptions


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def calculate_quantity_gravconsumption(self, quantity):
        volume_time_equivalence = self.env['ir.values'].\
            get_default('wua.configuration', 'volume_time_equivalence')
        quantity_float = str(round(quantity / volume_time_equivalence, 1))
        quantity_float = quantity_float.split('.')
        real_quantity = float(quantity_float[0])
        if (len(quantity_float) > 1):
            decimal_part = int(quantity_float[1])
            if (decimal_part > 2 and decimal_part < 8):
                decimal_part = 0.5
            else:
                decimal_part = 0
                if (decimal_part > 7):
                    real_quantity = real_quantity + 1
            real_quantity = real_quantity + decimal_part
        return real_quantity

    def get_watering_volume_real_of_irrigationgate_str(
            self, watering_volume_real_of_irrigationgate):
        watering_volume_real_of_irrigationgate = self.\
            calculate_quantity_gravconsumption(
                watering_volume_real_of_irrigationgate)
        return ('%.1f' % watering_volume_real_of_irrigationgate).\
            replace('.', ',')

    def remove_final_lines(self,original_description):
        first_line = ""
        if original_description:
            first_line = original_description.split('\n')[0]
        return first_line
 
    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        invoice_details = \
            super(WuaInvoiceset, self).calculate_invoice_details_others_categ(
                product_id, categ_code, item_ids, partnerlinks)
        if categ_code == 8:
            for invoice_detail in (invoice_details or []):
                original_description = invoice_detail['description']
                final_description = \
                    self.remove_final_lines(original_description)
                invoice_detail['description'] = final_description
        return invoice_details


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_gravconsumption(self, product_id):
        gravconsumptions = self.env['wua.gravconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
        if len(gravconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_gravconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, gravconsumption_id,
                    wateringperiod_id, number, agriculturalseason_id,
                    parcel_id, subparcel_id, cadastral_reference,
                    irrigationgate_id, irrigationditch_id, watering_duration,
                    watering_duration_dechours,
                    watering_id, gravconsumption_type, partner_id, vat,
                    with_irrigation_worker, employee_id, area_official,
                    watering_volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_gravconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    wateringperiod_id, number, agriculturalseason_id,
                    parcel_id, subparcel_id, cadastral_reference,
                    irrigationgate_id, irrigationditch_id, watering_duration,
                    watering_duration_dechours,
                    watering_id, gravconsumption_type, partner_id, vat,
                    with_irrigation_worker, employee_id, area_official,
                    watering_volume_real
                    FROM wua_gravconsumption
                    WHERE product_id=%s and invoiceset_id is null and
                          state='executed' and watering_volume_real>0
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_gravconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null and state='executed' and
                    watering_volume_real>0""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))


class WuaInvoicesetLineGravconsumption(models.Model):
    _inherit = 'wua.invoiceset.line.gravconsumption'

    watering_duration_dechours = fields.Float(
        string='Time (Hour)',
        digits=(32, 1))
