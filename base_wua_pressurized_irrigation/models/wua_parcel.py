# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcelIrrigationpointWC(models.Model):
    _inherit = 'wua.parcel.irrigationpointwc'

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        compute='_compute_watermeter_id')

    @api.multi
    def _compute_watermeter_id(self):
        for record in self:
            record.watermeter_id = record.waterconnection_id.watermeter_id
