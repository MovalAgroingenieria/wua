# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WuaParcelSubparcel(models.Model):
    _inherit = 'wua.parcel.subparcel'

    weighing_ids = fields.One2many(
        string='Weighings',
        comodel_name='wua.weighing',
        inverse_name='subparcel_id')


class WuaParcelPartnerlinkWeighing(models.Model):
    _name = 'wua.parcel.partnerlink.weighing'
    _description = 'Partner link of a parcel (for weighings)'

    weighing_id = fields.Many2one(
        string='Weighing',
        comodel_name='wua.weighing',
        index=True,
        ondelete='cascade')

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    irrigation_partner = fields.Boolean(
        string='Main')

    profile = fields.Selection([
        ('O', 'Owner'),
        ('L', 'Lessee'),
        ('P', 'Payer'),
        ], string='Profile',
        default='O')

    ownership_percentage = fields.Float(
        string='Ownership %',
        digits=(5, 2),
        default=100)

    water_costs_percentage = fields.Float(
        string='Water Costs %',
        digits=(5, 2),
        default=100)

    other_costs_percentage = fields.Float(
        string='Other Costs %',
        digits=(5, 2),
        default=100)
