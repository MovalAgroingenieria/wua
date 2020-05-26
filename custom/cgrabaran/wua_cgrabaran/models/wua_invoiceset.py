# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _
from odoo.exceptions import ValidationError


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_irrigationreport(self, product_id):
        company = self.env.user.company_id
        current_intake_id = ""
        if not company.parent_id:
            super(WuaInvoicesetLine,
                  self).populate_items_select_irrigationreport(product_id)
        else:
            current_intake_id = self.env['wua.intake'].search([
                ('company_id', '=', company.id)]).id
        if current_intake_id:
            irrigationreports = self.env['wua.irrigationreport'].search(
                [('of_active_agriculturalseason', '=', True),
                 ('is_validated', '=', True),
                 ('invoiced', '=', False),
                 ('product_id.id', '=', product_id),
                 ('intake_id', '=', current_intake_id)])
            if irrigationreports:
                user_id = self.env.user.id
                invoicesetline_id = self.id
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_irrigationreport
                    (id, create_uid,write_uid,create_date,write_date,
                    invoicesetline_id,irrigationreport_id,selected,
                    irrigationreport_number,report_initial_time,
                    report_end_time,intake_id,product_id,partner_id,
                    volume_real)
                    SELECT nextval('wua_invoiceset_line_irrigationreport_id_seq'),
                    %s,%s,now(),now(),%s,i.id,TRUE,i.irrigationreport_number,
                    i.report_initial_time,i.report_end_time,i.intake_id,
                    i.product_id,i.partner_id,i.volume_real
                    FROM wua_irrigationreport i INNER JOIN
                    wua_agriculturalseason a ON i.agriculturalseason_id = a.id
                    WHERE i.is_validated AND a.active_agriculturalseason AND
                    i.invoiced=FALSE AND i.product_id=%s AND i.intake_id=%s""", (
                        user_id, user_id, invoicesetline_id, product_id,
                        current_intake_id))
                    self.env.cr.commit()
                    self.env.invalidate_all()
                    self.configured_line = True
                except Exception:
                    self.env.cr.rollback()
                    raise ValidationError(_('Error when updating records.'))
