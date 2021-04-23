# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParticularpresconsumption(models.Model):
    _name = 'wua.particularpresconsumption'
    _description = 'Pressurized consumption (particular)'
    _order = 'reading_end_time desc, name'

    controlpresconsumption_id = fields.Many2one(
        string='Control Consumption',
        comodel_name='wua.controlpresconsumption',
        readonly=True,
        index=True,
        required=True,
        ondelete='cascade')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        readonly=True,
        required=True,
        ondelete='cascade')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        readonly=True,
        index=True,
        required=True,
        ondelete='cascade')

    name = fields.Char(
        string='Particular Consumption',
        size=84,
        store=True,
        index=True,
        compute='_compute_name')

    volume_real = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_waterconnection_id',
        ondelete='cascade')

    reading_end_time = fields.Datetime(
        string='Reading End Time',
        index=True,
        store=True,
        compute='_compute_reading_end_time')

    controlreading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.controlreading',
        store=True,
        compute='_compute_controlreading_id',
        ondelete='cascade')

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        store=True,
        compute='_compute_product_id',
        ondelete='cascade')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        index=True,
        store=True,
        compute='_compute_superproduct_id',
        ondelete='cascade')

    validated = fields.Boolean(
        string='Validated',
        store=True,
        compute='_compute_validated')

    @api.depends('controlpresconsumption_id', 'controlpresconsumption_id.name',
                 'parcel_id', 'parcel_id.name',
                 'partner_id', 'partner_id.partner_code')
    def _compute_name(self):
        for record in self:
            record.name = record.controlpresconsumption_id.name + ' - ' + \
                record.parcel_id.name + ' - ' + \
                str(record.partner_id.partner_code).zfill(6)

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.waterconnection_id')
    def _compute_waterconnection_id(self):
        for record in self:
            record.waterconnection_id = \
                record.controlpresconsumption_id.waterconnection_id

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.reading_end_time')
    def _compute_reading_end_time(self):
        for record in self:
            record.reading_end_time = \
                record.controlpresconsumption_id.reading_end_time

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.controlreading_id')
    def _compute_controlreading_id(self):
        for record in self:
            record.controlreading_id = \
                record.controlpresconsumption_id.controlreading_id

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.product_id')
    def _compute_product_id(self):
        for record in self:
            record.product_id = \
                record.controlpresconsumption_id.product_id

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.superproduct_id')
    def _compute_superproduct_id(self):
        for record in self:
            record.superproduct_id = \
                record.controlpresconsumption_id.superproduct_id

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.validated')
    def _compute_validated(self):
        for record in self:
            record.validated = \
                record.controlpresconsumption_id.validated
