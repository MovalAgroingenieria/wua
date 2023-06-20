# -*- coding: utf-8 -*-
# 2023 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaControlreading(models.Model):
    _inherit = 'wua.controlreading'

    @api.multi
    def write(self, vals):
        resp = super(WuaControlreading, self).write(vals)
        if len(self) == 1:
            if self.controlpresconsumption_id:
                controlpresconsumption = self.controlpresconsumption_id
                validated = self.validated
                quota_model = self.env['wua.quota']
                quota_model.delete_controlhydricmovements_presconsumption(
                    controlpresconsumption)
                if validated:
                    quota_model.create_controlhydricmovements_presconsumption(
                        controlpresconsumption)
        return resp

    @api.multi
    def unlink(self):
        for record in self:
            if (record.controlpresconsumption_id and
               record.controlpresconsumption_id.controlhydricmovement_ids):
                controlpresconsumption = record.controlpresconsumption_id
                controlpresconsumption.controlhydricmovement_ids.with_context(
                    force_unlink=True).sudo().unlink()
        return super(WuaControlreading, self).unlink()
