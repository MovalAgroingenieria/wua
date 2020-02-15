# -*- coding: utf-8 -*-
# 2020 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'

    hydricmovement_ids = fields.One2many(
        string='Hydric Consumptions',
        comodel_name='wua.hydricmovement',
        inverse_name='gravconsumption_id')

    @api.model
    def create(self, vals):
        new_gravconsumption = super(WuaGravconsumption, self).create(vals)
        if 'wateringrequest_id' in vals:
            wateringrequest = self.env['wua.wateringrequest'].browse(
                vals['wateringrequest_id'])
            wateringperiod = wateringrequest.wateringperiod_id
            product = wateringrequest.product_id
            superproduct = None
            if product.product_tmpl_id.superproduct_id:
                superproduct = product.product_tmpl_id.superproduct_id
            quotaperiod = self.env['wua.quota']._get_quotaperiod_for_timeframe(
                wateringperiod.initial_date, wateringperiod.end_date)
            if superproduct and quotaperiod:
                subparcel = self.env['wua.parcel.subparcel'].browse(
                    vals['subparcel_id'])
                parcel = subparcel.parcel_id
                model_quota = self.env['wua.quota']
                model_quota.create_hydricmovements_gravconsumption_of_request(
                    quotaperiod, superproduct, parcel,
                    vals['watering_duration'], new_gravconsumption)
        return new_gravconsumption

    @api.multi
    def unlink(self):
        quotas_to_refresh_ids = []
        for record in self:
            # It is necessary to refresh the affected quotas
            if record.hydricmovement_ids:
                for hydricmovement in record.hydricmovement_ids:
                    quotas_to_refresh_ids.append(hydricmovement.quota_id.id)
                record.hydricmovement_ids.with_context(
                    force_unlink=True).sudo().unlink()
        if quotas_to_refresh_ids:
            quotas_to_refresh_ids = list(set(quotas_to_refresh_ids))
            quotas_to_refresh = self.env['wua.quota'].browse(
                quotas_to_refresh_ids)
            for quota in quotas_to_refresh:
                self.env['wua.quota'].refresh_quota(quota)
        return super(WuaGravconsumption, self).unlink()
