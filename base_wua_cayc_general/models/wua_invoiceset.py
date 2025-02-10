# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, exceptions, _


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_parcel(self):
        parcels = self.env['wua.parcel'].search([], limit=1)
        if len(parcels) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                insert_fields_sql = self._get_sql_insert_fields_select_parcel()
                select_fields_sql = self._get_sql_select_fields_select_parcel()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_parcel (
                    """ + insert_fields_sql + """
                    )
                    SELECT """ + select_fields_sql + """
                    FROM wua_parcel WHERE active=TRUE AND is_primary
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
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))
