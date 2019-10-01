# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    extra_code = fields.Char(
        string='Historical Code',
        size=40,
        index=True)


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    extra_code = fields.Char(
        string='Historical Code',
        size=40,
        compute="_compute_extra_code")

    @api.multi
    def _compute_extra_code(self):
        for record in self:
            record.extra_code = record.parcel_id.extra_code


class WuaParcelIrrigationpoint(models.Model):
    _inherit = 'wua.parcel.irrigationpoint'

    extra_code = fields.Char(
        string='Historical Code',
        size=40,
        compute="_compute_extra_code")

    @api.multi
    def _compute_extra_code(self):
        for record in self:
            record.extra_code = record.parcel_id.extra_code
