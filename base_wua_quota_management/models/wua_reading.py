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
                quota_model.delete_hydricmovements_presconsumption(
                    presconsumption)
                if validated:
                    quota_model.create_hydricmovements_presconsumption(
                        presconsumption)
        return resp

    @api.multi
    def unlink(self):
        quotas_to_refresh_ids = []
        for record in self:
            # It is necessary to refresh the affected quotas
            if (record.presconsumption_id and
               record.presconsumption_id.hydricmovement_ids):
                presconsumption = record.presconsumption_id
                if presconsumption.hydricmovement_ids:
                    for hydricmovement in presconsumption.hydricmovement_ids:
                        quotas_to_refresh_ids.append(
                            hydricmovement.quota_id.id)
                    presconsumption.hydricmovement_ids.with_context(
                        force_unlink=True).sudo().unlink()
        if quotas_to_refresh_ids:
            quotas_to_refresh_ids = list(set(quotas_to_refresh_ids))
            quotas_to_refresh = self.env['wua.quota'].browse(
                quotas_to_refresh_ids)
            for quota in quotas_to_refresh:
                self.env['wua.quota'].refresh_quota(quota)
        return super(WuaReading, self).unlink()
