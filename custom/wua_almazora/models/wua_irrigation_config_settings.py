# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'
    _description = 'Configuration of wua_almazora module'

    year = fields.Char(
        string='Year',
        size=20)

    gross_price = fields.Float(
        string='Gross Price/Area U.',
        digits=(32, 4),
        default=0)

    net_coefficient_parcels = fields.Float(
        string='Net coef. for parcels [0-1]',
        digits=(6, 4),
        default=1,
        help='Factor for gross price per area unit. For each parcel, the ' +
             'net amount for the water user association is equal to the ' +
             'parcel area multiplied by the gross price and by this ' +
             'factor (a value between 0 and 1).')

    net_coefficient_workers = fields.Float(
        string='Net coef. for workers',
        digits=(6, 4),
        store=True,
        help='1 minus the net coefficient for parcels. For each parcel, ' +
             'the net amount for the irrigation worker is equal to the ' +
             'parcel area multiplied by the gross price and by this value.',
        compute='_compute_net_coefficient_workers')

    @api.depends('net_coefficient_parcels')
    def _compute_net_coefficient_workers(self):
        for record in self:
            record.net_coefficient_workers = \
                1 - record.net_coefficient_parcels

    @api.constrains('net_coefficient_parcels')
    def _check_net_coefficient_parcels(self):
        if (self.net_coefficient_parcels < 0 or
           self.net_coefficient_parcels > 1):
            raise exceptions.ValidationError(_('The Net coefficient for '
                                               'parcels must be a value '
                                               'from 0 to 1.'))

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'year',
                           self.year)
        values.set_default('wua.irrigation.configuration',
                           'gross_price',
                           self.gross_price)
        values.set_default('wua.irrigation.configuration',
                           'net_coefficient_parcels',
                           self.net_coefficient_parcels)
        values.set_default('wua.irrigation.configuration',
                           'net_coefficient_workers',
                           self.net_coefficient_workers)
