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
            self._generate_hm_from_gravconsumption_of_request(
                wateringrequest, vals['subparcel_id'],
                vals['watering_duration'], new_gravconsumption)
        return new_gravconsumption

    @api.multi
    def write(self, vals):
        super(WuaGravconsumption, self).write(vals)
        if len(self) == 1:
            updated_gravconsumption = self
            delete_hydricmovements, create_hydricmovements = \
                self._force_refresh_hydricmovements(updated_gravconsumption,
                                                    vals)
            # It is not possible to create hydric movements and not
            # eliminate previous movements.
            if (create_hydricmovements and (not delete_hydricmovements)):
                create_hydricmovements = False
            is_modified_consumption_of_request = False
            if (self.is_valid_gravconsumption(updated_gravconsumption) and
               (not delete_hydricmovements) and (not create_hydricmovements)):
                is_gravconsumption_of_type_request = \
                    updated_gravconsumption.gravconsumption_type == 'request'
                if (is_gravconsumption_of_type_request and
                   updated_gravconsumption.state == 'proposed' and
                   ('watering_duration' in vals or 'subparcel_id' in vals) and
                   ('watering_initial_time' not in vals)):
                    is_modified_consumption_of_request = True
                    delete_hydricmovements = True
                    create_hydricmovements = True
                else:
                    if ('state' in vals or 'cancelled' in vals or
                       'watering_duration' in vals):
                        if 'cancelled' in vals:
                            if updated_gravconsumption.cancelled:
                                delete_hydricmovements = True
                            else:
                                if (is_gravconsumption_of_type_request or
                                   updated_gravconsumption == 'executed'):
                                    create_hydricmovements = True
                        else:
                            delete_hydricmovements = True
                            if (is_gravconsumption_of_type_request or
                               updated_gravconsumption.state == 'executed'):
                                create_hydricmovements = True
                        if (create_hydricmovements and
                           is_gravconsumption_of_type_request and
                           updated_gravconsumption.state != 'executed' and
                           ('watering_initial_time' not in vals)):
                            is_modified_consumption_of_request = True
            if delete_hydricmovements or create_hydricmovements:
                quota_model = self.env['wua.quota']
                if delete_hydricmovements:
                    quota_model.delete_hydricmovements_gravconsumption(
                        updated_gravconsumption)
                if create_hydricmovements:
                    if (is_modified_consumption_of_request):
                        subparcel_id = \
                            updated_gravconsumption.subparcel_id.id
                        watering_duration = \
                            updated_gravconsumption.watering_duration
                        if 'subparcel_id' in vals:
                            subparcel_id = vals['subparcel_id']
                        if 'watering_duration' in vals:
                            watering_duration = vals['watering_duration']
                        self._generate_hm_from_gravconsumption_of_request(
                            updated_gravconsumption.wateringrequest_id,
                            subparcel_id, watering_duration,
                            updated_gravconsumption)
                    else:
                        quota_model.create_hydricmovements_gravconsumption(
                            updated_gravconsumption)
        return True

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

    # Hook
    def is_valid_gravconsumption(self, updated_gravconsumption):
        return True

    # Hook
    def _force_refresh_hydricmovements(self, updated_gravconsumption, vals):
        return False, False

    def _generate_hm_from_gravconsumption_of_request(
            self, wateringrequest, subparcel_id, watering_duration,
            gravconsumption):
        wateringperiod = wateringrequest.wateringperiod_id
        product = wateringrequest.product_id
        superproduct = None
        if product.product_tmpl_id.superproduct_id:
            superproduct = product.product_tmpl_id.superproduct_id
        quotaperiod = self.env['wua.quota']._get_quotaperiod_for_timeframe(
            wateringperiod.initial_date, wateringperiod.end_date)
        if superproduct and quotaperiod:
            subparcel = self.env['wua.parcel.subparcel'].browse(subparcel_id)
            parcel = subparcel.parcel_id
            model_quota = self.env['wua.quota']
            model_quota.create_hydricmovements_gravconsumption_of_request(
                quotaperiod, wateringperiod, superproduct, parcel,
                watering_duration, gravconsumption)
