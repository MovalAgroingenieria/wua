# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'

    @api.multi
    def unlink(self):
        quotas_to_refresh_ids = []
        # It is necessary to refresh the affected quotas (the consumptions
        # of a watering request are deleted by "cascade" method, then
        # the method "unlink" of wua.gravconsumption model is not fired).
        for record in self:
            for gravconsumption in record.gravconsumption_ids:
                if gravconsumption.hydricmovement_ids:
                    for hydricmovement in (gravconsumption.hydricmovement_ids):
                        quotas_to_refresh_ids.append(
                            hydricmovement.quota_id.id)
                    gravconsumption.hydricmovement_ids.with_context(
                        force_unlink=True).sudo().unlink()
        if quotas_to_refresh_ids:
            quotas_to_refresh_ids = list(set(quotas_to_refresh_ids))
            quotas_to_refresh = self.env['wua.quota'].browse(
                quotas_to_refresh_ids)
            for quota in quotas_to_refresh:
                self.env['wua.quota'].refresh_quota(quota)
        return super(WuaWateringrequest, self).unlink()
