# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaControlpresconsumption(models.Model):
    _inherit = 'wua.controlpresconsumption'

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        store=True,
        compute='_compute_product_id',
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        index=True,
        store=True,
        compute='_compute_superproduct_id',
        ondelete='restrict')

    particularpresconsumption_ids = fields.One2many(
        string='Particular Consumptions',
        comodel_name='wua.particularpresconsumption',
        inverse_name='controlpresconsumption_id')

    @api.depends('waterconnection_id')
    def _compute_product_id(self):
        for record in self:
            if not record.product_id:
                product_id = None
                if (record.waterconnection_id and
                   record.waterconnection_id.product_id):
                    product_id = record.waterconnection_id.product_id
                if product_id:
                    record.product_id = product_id

    @api.depends('product_id')
    def _compute_superproduct_id(self):
        for record in self:
            superproduct_id = None
            if record.product_id and record.product_id.superproduct_id:
                superproduct_id = record.product_id.superproduct_id
            record.superproduct_id = superproduct_id

    # This method is reimplemented because in the create method is not
    # available the waterconnection_id field. This computed method is called
    # after the create method.
    def _compute_hydraulic_infrastructure_data(self):
        super(WuaControlpresconsumption,
              self)._compute_hydraulic_infrastructure_data()
        creating_cps = getattr(self.env.all, '_creating_cps', None)
        if creating_cps:
            for record in self:
                if record.id in creating_cps:
                    creating_cps.discard(record.id)
                    record.create_particularpresconsumptions()

    @api.model
    def create(self, vals):
        new_controlpresconsumption = \
            super(WuaControlpresconsumption, self).create(vals)
        # Mark this cp as just created using a transaction-scoped set
        # (stored on self.env.all, which is thread-local). The flag
        # is set AFTER super().create() returns so that the first
        # recompute of _compute_hydraulic_infrastructure_data (which
        # fires during super().create() with waterconnection_id still
        # empty) does NOT trigger ppc creation. The second recompute
        # (triggered when the controlreading links to this cp and
        # waterconnection_id is computed) WILL find the id and create
        # ppcs.
        creating_cps = getattr(self.env.all, '_creating_cps', None)
        if creating_cps is None:
            creating_cps = set()
            self.env.all._creating_cps = creating_cps
        creating_cps.add(new_controlpresconsumption.id)
        return new_controlpresconsumption

    @api.multi
    def write(self, vals):
        resp = super(WuaControlpresconsumption, self).write(vals)
        if 'adjustement_volume' in vals:
            self.regenerate_particularpresconsumptions()
        return resp

    @api.multi
    def create_particularpresconsumptions(self):
        for controlpresconsumption in self:
            waterconnection = controlpresconsumption.waterconnection_id
            volume = controlpresconsumption.volume_real
            irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
                [('waterconnection_id', '=', waterconnection.id)])
            if irrigationpoints:
                parcels = [x.parcel_id for x in irrigationpoints]
                total_area_official = sum(x.area_official for x in parcels)
                if total_area_official > 0:
                    data_parcels = []
                    for parcel in parcels:
                        if parcel.area_official > 0:
                            volume_of_parcel = \
                                (volume * parcel.area_official /
                                 total_area_official)
                            data_parcels.append({
                                'parcel_id': parcel.id,
                                'volume': volume_of_parcel,
                                })
                    particularpresconsumption_model = \
                        self.env['wua.particularpresconsumption']
                    for data_parcel in (data_parcels or []):
                        parcel = filter(lambda x: x['id'] ==
                                        data_parcel['parcel_id'], parcels)[0]
                        for partnerlink in (parcel.partnerlink_ids or []):
                            volume_for_partner = \
                                (data_parcel['volume'] *
                                 partnerlink.water_costs_percentage / 100)
                            if volume_for_partner == 0:
                                continue
                            particularpresconsumption_model.create({
                                'controlpresconsumption_id':
                                    controlpresconsumption.id,
                                'parcel_id': parcel.id,
                                'partner_id': partnerlink.partner_id.id,
                                'volume_real': volume_for_partner,
                                })

    @api.multi
    def regenerate_particularpresconsumptions(self):
        for controlpresconsumption in self:
            if controlpresconsumption.particularpresconsumption_ids:
                controlpresconsumption.particularpresconsumption_ids.unlink()
            controlpresconsumption.create_particularpresconsumptions()
