# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _



class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

#    area_official = fields.Float(
#        string='Official Area',
#        digits=(32, 4),
#        default=0,
#        track_visibility='onchange')

    #@TODO: check negative numbers
    area_irrigation_percentage = fields.Float(
        string='Irrigation %', 
        digits=(5, 2),
        default=100,
        index=True)

    #@TODO: compute from area_official y area_irrigation_percentage
    area_irrigation = fields.Float(
        string='Irrigation Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute = '_compute_irrigation_area')

    #@TODO: check negative numbers
    area_unproductive_percentage = fields.Float(
        string='Unproductive %',
        digits=(5, 2),
        default=0,
        index=True)

    #@TODO: compute from area_official y area_unproductive_percentage
    area_unproductive = fields.Float(
        string='Unproductive Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute = '_compute_unproductive_area')

    #@TODO: check negative numbers
    area_drainage_percentage = fields.Float(
        string='Drainage %',
        digits=(5, 2),
        default=100,
        index=True)

    #@TODO: compute from area_official y area_drainage_percentage
    area_drainage = fields.Float(
        string='Drainage Area',
        digits=(32, 4),
        index=True,
        readonly=True,
        compute = '_compute_drainage_area')

    billable_irrigation = fields.Boolean(
        string='Billable Irrigation % ',
        default=True)


    #@TODO: check that area_irrigation + area_unproductive = area_official (??? area_drainage) 
    #       hacerlo al mismo tiempo que los valores negativos. SE puede hacer todo con una sola funcion.
    @api.depends('area_official', 'area_irrigation', 'area_unproductive', 'area_drainage')
    def _compute_areas(self):
        pass

    @api.depends('area_official', 'area_irrigation')
    def _compute_irrigation_area(self):
        pass

    @api.depends('area_official', 'area_unproductive')
    def _compute_unproductive_are(self):
        pass

    @api.depends('area_official', 'area_drainage')
    def _compute_drainage_area(self):
        pass

#@TODO: añadir dependiecia del modulo de donde viene (sale?, payments [other_addons]?...)
class product_template(models.Model):
    _inherit = 'product.template'

    weighting_type = fields.Selection([
        ('I', 'irrigation'),
        ('D', 'drainage'),
        ('N', 'none'),
        ], string='Weighting Type',
        required=False,
        default='N')

