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
                self.env.cr.execute("""
                    UPDATE wua_hydricmovement
                    SET invoiced_hydricmovement = FALSE
                    WHERE invoiced_hydricmovement is NULL""")
                self.env.cr.execute("""
                    UPDATE wua_presconsumption
                    SET invoiced_consumption_quota = TRUE WHERE id IN
                    (SELECT DISTINCT(wp1.id) FROM wua_presconsumption wp1
                     INNER JOIN wua_hydricmovement wh1 ON wp1.id =
                     wh1.presconsumption_id WHERE
                     wh1.invoiced_hydricmovement)""")
                self.env.cr.execute("""
                    UPDATE wua_reading
                    SET invoiced_reading_quota = TRUE WHERE id IN
                    (SELECT DISTINCT(wr1.id) FROM wua_reading wr1
                     INNER JOIN wua_presconsumption wp1 ON wp1.id =
                     wr1.presconsumption_id WHERE
                     wp1.invoiced_consumption_quota)""")
                self.env.cr.execute("""
                    UPDATE wua_irrigationreport
                    SET invoiced_irrigationreport_quota = TRUE WHERE id IN
                    (SELECT DISTINCT(wi1.id) FROM wua_irrigationreport wi1
                     INNER JOIN wua_hydricmovement wh1 ON wi1.id =
                     wh1.irrigationreport_id WHERE
                     wh1.invoiced_hydricmovement)""")
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when '
                                             'updating records.'))
        return resp
