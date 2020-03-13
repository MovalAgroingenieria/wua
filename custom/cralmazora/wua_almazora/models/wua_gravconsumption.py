# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'
    _description = 'Gravity Consumption (Almassora)'

    gross_amount = fields.Float(
        string='Gross Amount',
        digits=(32, 2),
        store=True,
        compute='_compute_gross_amount')

    net_parcel_amount = fields.Float(
        string='Net for parcel',
        digits=(32, 2),
        store=True,
        compute='_compute_net_parcel_amount')

    net_worker_amount = fields.Float(
        string='Net for worker',
        digits=(32, 2),
        store=True,
        compute='_compute_net_worker_amount')

    area_irrigation = fields.Float(
        string='Irrigation Area',
        digits=(32, 4),
        index=True,
        store=True,
        compute='_compute_area_irrigation')

    @api.depends('parcel_id')
    def _compute_gross_amount(self):
        for record in self:
            gross_amount = 0
            if record.parcel_id:
                gross_amount = record.parcel_id.gross_amount
            record.gross_amount = gross_amount

    @api.depends('parcel_id')
    def _compute_net_parcel_amount(self):
        for record in self:
            net_parcel_amount = 0
            if record.parcel_id:
                net_parcel_amount = record.parcel_id.net_parcel_amount
            record.net_parcel_amount = net_parcel_amount

    @api.depends('parcel_id')
    def _compute_net_worker_amount(self):
        for record in self:
            net_worker_amount = 0
            if record.parcel_id:
                net_worker_amount = record.parcel_id.net_worker_amount
            record.net_worker_amount = net_worker_amount

    @api.depends('parcel_id')
    def _compute_area_irrigation(self):
        for record in self:
            area_irrigation = 0
            if record.parcel_id:
                area_irrigation = record.parcel_id.area_irrigation
            record.area_irrigation = area_irrigation
