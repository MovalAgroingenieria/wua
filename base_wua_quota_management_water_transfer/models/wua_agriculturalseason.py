# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import exceptions, models, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    def _update_active_flag_in_slave_models(self, agriculturalseason_id,
                                            active_agriculturalseason):
        super(WuaAgriculturalseason, self)._update_active_flag_in_slave_models(
            agriculturalseason_id, active_agriculturalseason)
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                UPDATE wua_watertransfer
                SET of_active_agriculturalseason =
                    (CASE WHEN agriculturalseason_id IN
                        (SELECT id FROM wua_agriculturalseason WHERE
                            active_agriculturalseason)
                        THEN TRUE
                        ELSE FALSE
                        END)""")
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            raise exceptions.UserError(_(
                'Error when updating records '
                '(\"of_active_agriculturalseason\" field).'))
