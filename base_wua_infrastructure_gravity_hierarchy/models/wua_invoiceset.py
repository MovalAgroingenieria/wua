# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, _


class WuaInvoicesetLineParcel(models.Model):
    _inherit = 'wua.invoiceset.line.parcel'

    SIZE_PATH = 255

    path = fields.Char(
        string="Irrigation Ditch Full name",
        size=SIZE_PATH)


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    # Add path to original method (overwrite)
    def populate_items_select_parcel(self):
        parcels = self.env['wua.parcel'].search([])
        if len(parcels) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_parcel (id, create_uid,
                    write_uid, create_date, write_date, invoicesetline_id,
                    selected, parcel_id, cadastral_reference,
                    is_billable_water, is_billable_expenses,
                    leased_parcel, area_official, partner_id,
                    hydraulic_infrastructure_type,
                    pressurized_irrigation_right, gravityfed_irrigation_right,
                    hydraulicsector_id, irrigationditch_id,
                    with_watering_shift, with_irrigation_worker, employee_id,
                    path)
                    SELECT nextval('wua_invoiceset_line_parcel_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id, cadastral_reference,
                    is_billable_water, is_billable_expenses, leased_parcel,
                    area_official, partner_id, hydraulic_infrastructure_type,
                    pressurized_irrigation_right, gravityfed_irrigation_right,
                    hydraulicsector_id, irrigationditch_id,
                    with_watering_shift, with_irrigation_worker, employee_id,
                    path
                    FROM wua_parcel WHERE active=TRUE
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_parcel_parceltag_rel
                    (invoiceset_line_parcel_id, parceltag_id)
                    SELECT l.id, r.parceltag_id
                    FROM wua_invoiceset_line_parcel as l
                    inner join wua_parcel_parceltag_rel as r
                    on l.parcel_id=r.parcel_id
                    where l.invoicesetline_id=""" + str(invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))
