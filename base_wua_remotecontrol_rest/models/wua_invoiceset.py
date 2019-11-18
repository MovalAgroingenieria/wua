# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, exceptions, _


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_presconsumption(self, product_id):
        presconsumptions = self.env['wua.presconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
        if len(presconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_presconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, presconsumption_id,
                    reading_id, reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_presconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    reading_id, reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real
                    FROM wua_presconsumption
                    WHERE product_id=%s and invoiceset_id is null and validated
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_presconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE product_id=""" + str(product_id) + """ and
                    invoiceset_id is null""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))
