# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _name = 'wua.agriculturalseason'
    _inherit = ['wua.agriculturalseason', 'mail.thread']

    is_the_active = fields.Boolean(
        string='Active',
        default=False,
        track_visibility='onchange')

    enrollment_initial_date = fields.Date(
        string='Enrollment Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    enrollment_end_date = fields.Date(
        string='Enrollment End Date',
        default=lambda self: fields.datetime.now() + timedelta(days=364),
        required=True)

    _sql_constraints = [
        ('valid_enrollment_dates',
         'CHECK (initial_date <= enrollment_initial_date and \
             enrollment_initial_date <= enrollment_end_date and \
             enrollment_end_date <= end_date)',
         'Incorrect enrollment dates.'),
        ]

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.end_date, '%Y-%m-%d').strftime('%x')
            if (record.description != '' and not self.env.context.get(
               'reduced_name_get_for_agriculturalseason', False)):
                name = initial_date_str + ' - ' + end_date_str + ' ' + \
                    '(' + record.description + ')'
            else:
                name = name = initial_date_str + ' ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def open_agriculturalseason(self):
        self.ensure_one()
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        if active_agriculturalseasons:
            warning_active_agriculturalseason_01 = \
                _('The agricultural season "')
            warning_active_agriculturalseason_02 = \
                _('" is still active. Before it is necessary to close '
                  'that agricultural season.')
            raise exceptions.UserError(warning_active_agriculturalseason_01 +
                                       active_agriculturalseasons[0].
                                       description +
                                       warning_active_agriculturalseason_02)
        # Step 1/4: if there are crop plans in the current agricultural season
        #           (reopen an agricultral season), delete them.
        # Provisional: function "delete_cropplans"
        # Step 2/4: regenerate the subparcels census (each parcel has a
        #           only subparcel of "no-cultivation" type).
        self.regenerate_subparcels_census()
        # Step 3/4: if there are parcels with a permanent crop plan,
        #           a crop plan is created for each group of parcels
        #           associated with a partner.
        # Provisional: function "create_initial_crop_plans".
        # Step 4/4: the current agricultural season is active.
        self.is_the_active = True

    @api.multi
    def close_agriculturalseason(self):
        self.ensure_one()
        # Provisional
        self.is_the_active = False

    def regenerate_subparcels_census(self):
        parcels = self.env['wua.parcel'].search(
            [('hydraulic_infrastructure_type', '=', 1)])
        subparcels = self.env['wua.parcel.subparcel']
        no_cultivation_subparcel_type = self.env.ref(
            'base_wua_crop_planning.subparceltype_00')
        for parcel in parcels:
            subparcels.search([('parcel_id', '=', parcel.id)]).unlink()
            subparcels.create({
                'subparcel_code': parcel.name + '-' +
                '1'.zfill(parcel.SIZE_SUBPARCEL_SUFFIX),
                'parcel_id': parcel.id,
                'pos': 1,
                'area_official': parcel.area_official,
                'area_perc': 100,
                'subparceltype_id': no_cultivation_subparcel_type.id})
