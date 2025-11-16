# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unidecode import unidecode
from odoo import models, fields, api, exceptions, _


class WuaCropunit(models.Model):
    _name = 'wua.cropunit'
    _description = 'Crop Unit'
    _order = 'name'

    def _default_agriculturalseason_id(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        default=_default_agriculturalseason_id,
        index=True,
        required=True,
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
        required=True,
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        domain=[('suitable_hydric_estimation', '=', True)],
        index=True,
        required=True,
    )

    initial_date = fields.Date(
        string='Crop cycle initial date',
        required=True,
        index=True,)

    end_date = fields.Date(
        string='Crop cycle end date',
        required=True,
        index=True,)

    order_number = fields.Integer(
        string='Order Number',
        default=1,
        required=True,
    )

    name = fields.Char(
        string='Code of crop unit',
        store=True,
        index=True,
        compute='_compute_name',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'Existing crop unit.'),
        ('dates_ok',
         'CHECK (initial_date < end_date)',
         'The end date of the crop cycle must be later than the start date.'),
        ('order_number_ok',
         'CHECK (order_number > 0)',
         'The order number must be a positive value.')
        ]

    @api.depends('agriculturalseason_id', 'parcel_id', 'cultivation_id',
                 'order_number')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.agriculturalseason_id and record.parcel_id and
               record.cultivation_id):
                initial_year = fields.Date.from_string(
                    record.agriculturalseason_id.initial_date).strftime('%Y')
                end_year = fields.Date.from_string(
                    record.agriculturalseason_id.end_date).strftime('%Y')
                name = (record.parcel_id.name + '-' +
                        initial_year[2:] + '/' + end_year[2:] + '-' +
                        unidecode(record.cultivation_id.name[:3]).upper() + '-' +
                        str(record.order_number).rjust(3, '0'))
            record.name = name

    @api.constrains('cultivation_id',
                    'cultivation_id.suitable_hydric_estimation')
    def _check_cultivation_suitable(self):
        for record in self:
            if (record.cultivation_id and
               (not record.cultivation_id.suitable_hydric_estimation)):
                raise exceptions.ValidationError(
                    _('Not suitable for irrigation recommendations.'))

    @api.constrains('initial_date',
                    'end_date')
    def _check_dates(self):
        for record in self:
            agriculturalseason_id = record.agriculturalseason_id
            initial_date = record.initial_date
            end_date = record.end_date
            if agriculturalseason_id and initial_date and end_date:
                dates_ok = (agriculturalseason_id.initial_date <= initial_date
                            <= end_date <= agriculturalseason_id.end_date)
                if not dates_ok:
                    raise exceptions.ValidationError(
                        _('Dates outside the agricultural season.'))

    @api.onchange('agriculturalseason_id', 'parcel_id', 'cultivation_id')
    def _onchange_cropunit_identification(self):
        if (self.agriculturalseason_id and self.parcel_id and
           self.cultivation_id):
            order_number = 1
            previous_similar_cropunits = self.search(
                [('agriculturalseason_id', '=', self.agriculturalseason_id.id),
                 ('parcel_id', '=', self.parcel_id.id),
                 ('cultivation_id', '=', self.cultivation_id.id)],
                limit=1, order='order_number desc')
            if previous_similar_cropunits:
                order_number = previous_similar_cropunits[0].order_number + 1
            self.order_number = order_number
