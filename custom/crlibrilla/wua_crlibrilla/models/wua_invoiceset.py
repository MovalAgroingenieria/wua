# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

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
