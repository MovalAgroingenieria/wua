# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, _


class WuaInvoicesetLineParcel(models.Model):
    _inherit = 'wua.invoiceset.line.parcel'

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        ondelete='restrict',
    )


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def _get_sql_insert_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_insert_fields_select_parcel() + ', intake_id'
        return new_sql

    def _get_sql_select_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_select_fields_select_parcel() + ', intake_id'
        return new_sql
