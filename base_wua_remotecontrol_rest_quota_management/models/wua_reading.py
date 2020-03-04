# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.multi
    def write(self, vals):
        resp = super(WuaReading, self).write(vals)
        if len(self) == 1:
            if self.presconsumption_id:
                presconsumption = self.presconsumption_id
                validated = self.validated
                quota_model = self.env['wua.quota']
                if validated:
                    quota_model.create_hydricmovements_presconsumption(
                        presconsumption)
                else:
                    quota_model.delete_hydricmovements_presconsumption(
                        presconsumption)
        return resp
