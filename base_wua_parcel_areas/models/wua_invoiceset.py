# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaInvoicesetLineParcel(models.Model):
    _inherit = 'wua.invoiceset.line.parcel'

    area_irrigation = fields.Float(
        string='Irrigation Area',
        digits=(32, 4),
        index=True,
    )

    area_drainage = fields.Float(
        string='Drainage Area',
        digits=(32, 4),
        index=True,
    )


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def _get_sql_insert_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_insert_fields_select_parcel() + ', area_irrigation, ' + \
            'area_drainage '
        return new_sql

    def _get_sql_select_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_select_fields_select_parcel() + ', area_irrigation, ' + \
            'area_drainage '
        return new_sql
