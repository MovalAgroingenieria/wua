# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'
    _description = 'Partner link of a parcel with irrigation infrastructure ' \
                   '(C.R.Merancho)'

    hydraulic_infrastructure_type = fields.Selection([
        (0, 'No infrastructure'),
        (1, 'Pressurized Irrigation'),
        (2, 'Gravity Irrigation'),
        (3, 'Pressurized and Gravity fed Irrigation'),
        ], string='Infrastructure',
        store=True,
        compute='_compute_hydraulic_infrastructure_type')

    pressurized_irrigation_right = fields.Boolean(
        string="Water Right (pres)",
        store=True,
        compute='_compute_pressurized_irrigation_right')

    gravityfed_irrigation_right = fields.Boolean(
        string="Water Right (grav)",
        store=True,
        compute='_compute_gravityfed_irrigation_right')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_hydraulicsector_id')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_irrigationditch_id')

    @api.depends('parcel_id.hydraulic_infrastructure_type')
    def _compute_hydraulic_infrastructure_type(self):
        for record in self:
            record.hydraulic_infrastructure_type = \
                record.parcel_id.hydraulic_infrastructure_type

    @api.depends('parcel_id.pressurized_irrigation_right')
    def _compute_pressurized_irrigation_right(self):
        for record in self:
            record.pressurized_irrigation_right = \
                record.parcel_id.pressurized_irrigation_right

    @api.depends('parcel_id.gravityfed_irrigation_right')
    def _compute_gravityfed_irrigation_right(self):
        for record in self:
            record.gravityfed_irrigation_right = \
                record.parcel_id.gravityfed_irrigation_right

    @api.depends('parcel_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.parcel_id.hydraulicsector_id

    @api.depends('parcel_id.irrigationditch_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            record.irrigationditch_id = record.parcel_id.irrigationditch_id
