# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    irrigationsrequest_ids = fields.One2many(
        string="Irrigations Requests",
        comodel_name="wua.irrigationsrequest",
        inverse_name="agriculturalseason_id")

    @api.multi
    def write(self, vals):
        resp = super(WuaAgriculturalseason, self).write(vals)
        if 'active_agriculturalseason' in vals:
            self._sync_irrigationsrequest_active_flag()
        return resp

    @api.multi
    def _sync_irrigationsrequest_active_flag(self):
        self.env.cr.execute(
            """
            UPDATE wua_irrigationsrequest AS irrigationsrequest
               SET of_active_agriculturalseason =
                    agriculturalseason.active_agriculturalseason
              FROM wua_agriculturalseason AS agriculturalseason
             WHERE agriculturalseason.id =
                    irrigationsrequest.agriculturalseason_id
               AND irrigationsrequest.agriculturalseason_id IN %s
            """, (tuple(self.ids),))
