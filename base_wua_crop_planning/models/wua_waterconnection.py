# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False)

    working = fields.Boolean(
        string='Working',
        default=False)

    exists_active_agriculturalseason = fields.Boolean(
        string='Exists a active agricultural season',
        compute='_compute_exists_active_agriculturalseason')

    @api.multi
    def _compute_exists_active_agriculturalseason(self):
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        exists_active_agriculturalseason = False
        if active_agriculturalseasons:
            exists_active_agriculturalseason = True
        for record in self:
            record.exists_active_agriculturalseason = \
                exists_active_agriculturalseason


class WuaParcelIrrigationpoint(models.Model):
    _inherit = 'wua.parcel.irrigationpoint'

    can_be_watered = fields.Boolean(
        string='Can be watered',
        compute='_compute_can_be_watered')

    @api.multi
    def _compute_can_be_watered(self):
        for record in self:
            record.can_be_watered = record.parcel_id.can_be_watered
