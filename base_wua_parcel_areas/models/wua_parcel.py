# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

#    area_official = fields.Float(
#        string='Official Area',
#        digits=(32, 4),
#        default=0,
#        track_visibility='onchange')

    area_irrigation_percentage = fields.Float(
        string='Irrigation %',
        digits=(5, 2),
        default=100,
        index=True)

    area_irrigation = fields.Float(
        string='Irrigation Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute='_compute_irrigation_area')

    area_unproductive_percentage = fields.Float(
        string='Unproductive %',
        digits=(5, 2),
        default=0,
        index=True)

    # @TODO: compute from area_official y area_unproductive_percentage
    area_unproductive = fields.Float(
        string='Unproductive Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute='_compute_unproductive_area')

    # @TODO: check negative numbers
    area_drainage_percentage = fields.Float(
        string='Drainage %',
        digits=(5, 2),
        default=100,
        index=True)

    area_drainage = fields.Float(
        string='Drainage Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute='_compute_drainage_area')

    billable_irrigation_percentage = fields.Boolean(
        string='Billable Irrigation %',
        default=True)


    @api.depends('area_official', 'area_irrigation_percentage')
    def _compute_irrigation_area(self):
        pass

    @api.depends('area_official', 'area_unproductive_percentage')
    def _compute_unproductive_area(self):
        pass

    @api.depends('area_official', 'area_drainage_percentage')
    def _compute_drainage_area(self):
        pass

