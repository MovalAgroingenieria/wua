# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    pumpgroupmeasurement_ids = fields.One2many(
        string='Measurements',
        comodel_name='wua.pumpgroupmeasurement',
        inverse_name='agriculturalseason_id')

    number_of_measurements = fields.Integer(
        string='N. of measurements',
        compute='_compute_number_of_measurements')

    @api.multi
    def _compute_number_of_measurements(self):
        for record in self:
            record.number_of_measurements = \
                len(record.pumpgroupmeasurement_ids)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            resp = super(WuaAgriculturalseason, self).write(vals)
            if 'active_agriculturalseason' in vals:
                self._update_active_flag_in_slave_models(
                    self.id, vals['active_agriculturalseason'])
        else:
            resp = super(WuaAgriculturalseason, self).write(vals)
        return resp

    def _update_active_flag_in_slave_models(self, agriculturalseason_id,
                                            active_agriculturalseason):
        if agriculturalseason_id:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE wua_pumpgroupmeasurement
                    SET of_active_agriculturalseason=FALSE WHERE
                    of_active_agriculturalseason=TRUE""")
                if active_agriculturalseason:
                    self.env.cr.execute("""
                        UPDATE wua_pumpgroupmeasurement
                        SET of_active_agriculturalseason=TRUE WHERE
                        agriculturalseason_id=""" + str(agriculturalseason_id))
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_(
                    'Error when updating records '
                    '(\"of_active_agriculturalseason\" field).'))
