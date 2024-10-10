# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, exceptions, _


class WuaQuotaperiod(models.Model):
    _inherit = 'wua.quotaperiod'

    def _apply_multiple_assignment_for_superproduct(self, quotaperiodline):
        resp = super(WuaQuotaperiod, self).\
            _apply_multiple_assignment_for_superproduct(quotaperiodline)
        if resp:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    """
                    UPDATE wua_quota
                    SET invoiced = FALSE
                    WHERE invoiced is NULL
                    AND superproduct_id = %s
                    AND quotaperiod_id = %s""",
                    (quotaperiodline.superproduct_id.id,
                     quotaperiodline.quotaperiod_id.id),
                )
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when '
                                             'updating records.'))
        return resp
