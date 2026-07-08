# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    reportrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.reportrequest",
        inverse_name="agriculturalseason_id")

    @api.multi
    def write(self, vals):
        resp = super(WuaAgriculturalseason, self).write(vals)
        if 'active_agriculturalseason' in vals:
            self._sync_reportrequest_active_flag()
        return resp

    @api.multi
    def _sync_reportrequest_active_flag(self):
        self.env.cr.execute(
            """
            UPDATE wua_reportrequest AS reportrequest
               SET of_active_agriculturalseason =
                    agriculturalseason.active_agriculturalseason
              FROM wua_agriculturalseason AS agriculturalseason
             WHERE agriculturalseason.id =
                    reportrequest.agriculturalseason_id
               AND reportrequest.agriculturalseason_id IN %s
            """, (tuple(self.ids),))
