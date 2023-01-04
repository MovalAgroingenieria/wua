# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


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
        store=True,
        size=40,
        related="parcel_id.extra_code")


class WuaParcelIrrigationpoint(models.Model):
    _inherit = 'wua.parcel.irrigationpoint'

    extra_code = fields.Char(
        string='Historical Code',
        store=True,
        size=40,
        related="parcel_id.extra_code")
