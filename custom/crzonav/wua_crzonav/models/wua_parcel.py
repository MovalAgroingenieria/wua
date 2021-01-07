# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    farmproperty_id = fields.Many2one(
        string='Farm Property',
        comodel_name='wua.farmproperty',
        ondelete='restrict',
        store=True,
        compute='_compute_farmproperty_id')

    @api.depends('parcel_id', 'parcel_id.farmproperty_id')
    def _compute_farmproperty_id(self):
        for record in self:
            farmproperty_id = None
            if (record.parcel_id):
                farmproperty_id = record.parcel_id.farmproperty_id
            record.farmproperty_id = farmproperty_id
