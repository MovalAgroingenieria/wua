# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    indexmoisture_ids = fields.One2many(
        string='Moisture Indices',
        comodel_name='wua.parcel.vegetationindex.moisture',
        inverse_name='agriculturalseason_id')

    @api.multi
    def write(self, vals):
        if 'active_agriculturalseason' in vals:
            self._update_active_flag_in_moisture_model(
                self.id, vals['active_agriculturalseason'])
        return super(WuaAgriculturalseason, self).write(vals)

    # This method changes the "of_active_agriculturalseason" field for
    # "wua.parcel.vegetationindex.moisture" model.
    def _update_active_flag_in_moisture_model(self, agriculturalseason_id,
                                              active_agriculturalseason):
        if agriculturalseason_id:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE wua_parcel_vegetationindex_moisture
                    SET of_active_agriculturalseason=FALSE WHERE
                    of_active_agriculturalseason=TRUE""")
                if active_agriculturalseason:
                    self.env.cr.execute("""
                        UPDATE wua_parcel_vegetationindex_moisture
                        SET of_active_agriculturalseason=TRUE WHERE
                        agriculturalseason_id=""" + str(agriculturalseason_id))
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_(
                    'Error when updating records '
                    '(\"of_active_agriculturalseason\" field).'))
