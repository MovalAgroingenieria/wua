# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaInvoicesetLineParcel(models.Model):
    _inherit = 'wua.invoiceset.line.parcel'

    irrigationditch_01_id = fields.Many2one(
        string='Level 1 Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict',
    )
    irrigationditch_02_id = fields.Many2one(
        string='Level 2 Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict',
    )
    drainageditch_id = fields.Many2one(
        string='Drainage Ditch',
        comodel_name='wua.drainageditch',
        ondelete='restrict',
    )
    drainageditch_01_id = fields.Many2one(
        string="Level 1 Drainage Ditch",
        comodel_name='wua.drainageditch',
        ondelete='restrict',
    )
    drainageditch_02_id = fields.Many2one(
        string="Level 2 Drainage Ditch",
        comodel_name='wua.drainageditch',
        ondelete='restrict',
    )


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def _get_sql_insert_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_insert_fields_select_parcel() + \
            ', irrigationditch_01_id, ' + ' irrigationditch_02_id, ' + \
            ' drainageditch_id, ' + ' drainageditch_01_id, ' + \
            'drainageditch_02_id '
        return new_sql

    def _get_sql_select_fields_select_parcel(self):
        new_sql = super(WuaInvoicesetLine, self).\
            _get_sql_select_fields_select_parcel() + \
            ', irrigationditch_01_id, ' + ' irrigationditch_02_id, ' + \
            ' drainageditch_id, ' + ' drainageditch_01_id, ' + \
            'drainageditch_02_id '
        return new_sql
