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

    cropplan_ids = fields.One2many(
        string='Crop Plans',
        comodel_name='wua.cropplan',
        inverse_name='agriculturalseason_id')

    number_of_cropplans = fields.Integer(
        string='Number of crop plans',
        store=True,
        index=True,
        compute='_compute_number_of_cropplans')

    initialized = fields.Boolean(
        string='Initialized',
        store=True,
        compute='_compute_initialized')

    enrolledsubparcel_ids = fields.One2many(
        string='Enrolled Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='agriculturalseason_id')

    number_of_enrolledsubparcels = fields.Integer(
        string='Number of enrolled subparcels',
        store=True,
        index=True,
        compute='_compute_number_of_enrolledsubparcels')

    _sql_constraints = [
        ('valid_enrollment_dates',
         'CHECK (initial_date <= enrollment_initial_date and \
             enrollment_initial_date <= enrollment_end_date and \
             enrollment_end_date <= end_date)',
         'Incorrect enrollment dates.'),
        ]

    @api.depends('cropplan_ids')
    def _compute_number_of_cropplans(self):
        for record in self:
            number_of_cropplans = 0
            if record.cropplan_ids:
                number_of_cropplans = len(record.cropplan_ids)
            record.number_of_cropplans = number_of_cropplans

    @api.depends('number_of_cropplans')
    def _compute_initialized(self):
        for record in self:
            initialized = False
            if record.number_of_cropplans > 0:
                initialized = True
            record.initialized = initialized

    @api.depends('cropplan_ids', 'enrolledsubparcel_ids')
    def _compute_number_of_enrolledsubparcels(self):
        for record in self:
            number_of_enrolledsubparcels = 0
            if record.enrolledsubparcel_ids:
                number_of_enrolledsubparcels = \
                    len(record.enrolledsubparcel_ids)
            record.number_of_enrolledsubparcels = number_of_enrolledsubparcels

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.end_date)
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
        self.is_the_active = True
        if self.initialized:
            return self.env['wua.cropplan'].action_regenerate_census(False)
        # Step 1/2: regenerate the subparcels census (each parcel has a
        #           only subparcel of "no-cultivation" type).
        self.regenerate_subparcels_census()
        # Step 2/2: if there are parcels with a permanent crop plan,
        #           a crop plan is created for each group of parcels
        #           associated with a partner. The new crop plan is
        #           based on enrolled subparcels with permanent
        #           cultivation of the previous agricultural season.
        return self.create_initial_crop_plans(self)

    @api.multi
    def close_agriculturalseason(self):
        self.ensure_one()
        # First requirement: Are there crop plans in draft state?
        cropplans_draft_of_current_agriculturalseason = \
            self.env['wua.cropplan'].search(
                [('agriculturalseason_id', '=', self.id),
                 ('state', '=', 'draft')])
        if cropplans_draft_of_current_agriculturalseason:
            raise exceptions.UserError(_('This agricultural season has '
                                         'crop plans in draft state: '
                                         'it is not possible to close it.'))
        self.is_the_active = False
        if not self.initialized:
            return True
        # Step 1/2: Include in the agricultural season all parcels without
        # crop plan.
        parcels_no_cropplan = self.env['wua.parcel'].search(
            [('hydraulic_infrastructure_type', '=', 1),
             ('registered_cropplan', '=', False)])
        subparcels = self.env['wua.parcel.subparcel']
        enrolledsubparcels = self.env['wua.enrolledsubparcel']
        no_cultivation_subparcel_type = self.env.ref(
            'base_wua_crop_planning.subparceltype_00')
        for parcel in parcels_no_cropplan:
            if not parcel.partner_id.registered_cropplan:
                enrolledsubparcel_data = {
                    'parcel_id': parcel.id,
                    'order': 1,
                    'area_official': parcel.area_official,
                    'area_perc': 100,
                    'subparceltype_id': no_cultivation_subparcel_type.id,
                    }
                self.env['wua.cropplan'].create({
                    'agriculturalseason_id': self.id,
                    'partner_id': parcel.partner_id.id,
                    'enrolledsubparcel_ids': [(0, 0, enrolledsubparcel_data)],
                    })
            else:
                cropplan = parcel.partner_id.cropplan_id
                enrolledsubparcels.create({
                    'cropplan_id': cropplan.id,
                    'parcel_id': parcel.id,
                    'order': 1,
                    'area_official': parcel.area_official,
                    'area_perc': 100,
                    'subparceltype_id': no_cultivation_subparcel_type.id,
                    })
                subparcels.search([('parcel_id', '=', parcel.id)]).unlink()
                subparcels.create({
                    'subparcel_code': parcel.name + '-' +
                    '1'.zfill(parcel.SIZE_SUBPARCEL_SUFFIX),
                    'parcel_id': parcel.id,
                    'pos': 1,
                    'area_official': parcel.area_official,
                    'area_perc': 100,
                    'subparceltype_id': no_cultivation_subparcel_type.id,
                    })
                parcel.cropplan_id = cropplan.id
        # Step 2/2: Reset all links of partners and parcels with their
        # crop plans.
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)])
        for partner in partners:
            partner.cropplan_id = None
        parcels = self.env['wua.parcel'].search([])
        for parcel in parcels:
            parcel.cropplan_id = None
        waterconnections = self.env['wua.waterconnection'].search([])
        for waterconnection in waterconnections:
            waterconnection.write({
                'registered_cropplan': False,
                'working': False})
        return True

    @api.multi
    def action_see_cropplans(self):
        self.ensure_one()
        if self.cropplan_ids:
            id_tree_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_cropplan_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_cropplan_view_form').id
            search_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_cropplan_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Crop Plans'),
                'res_model': 'wua.cropplan',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.cropplan_ids.ids)],
                }
            return act_window

    @api.multi
    def action_see_enrolledsubparcels(self):
        self.ensure_one()
        if self.enrolledsubparcel_ids:
            id_tree_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_tree').id
            search_view = self.env.ref(
                'base_wua_crop_planning.'
                'wua_enrolledsubparcel_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Enrolled Subparcels'),
                'res_model': 'wua.enrolledsubparcel',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.enrolledsubparcel_ids.ids)],
                'context': {'reduced_name_get_for_agriculturalseason': True,
                            'reduced_name_get_for_cropplan': True},
                }
            return act_window

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

    def create_initial_crop_plans(self, agriculturalseason):
        if (self.env['wua.cropplan'].search(
           [('agriculturalseason_id', '=', agriculturalseason.id)])):
            return False
        previous_agricultural_season = \
            self.env['wua.agriculturalseason'].search(
                [('name', '<', agriculturalseason.name)],
                limit=1, order='name desc')
        if previous_agricultural_season:
            previous_agricultural_season = previous_agricultural_season[0]
            previous_enrolledsubparcels = \
                self.env['wua.enrolledsubparcel'].search(
                    [('agriculturalseason_id', '=',
                      previous_agricultural_season.id),
                     ('cultivation_id.permanent', '=', True),
                     ('parcel_id.permanent', '=', True)])
            if not previous_enrolledsubparcels:
                return False
            initial_cropplans_data = []
            for enrolledsubparcel in previous_enrolledsubparcels:
                partner_id = enrolledsubparcel.partner_id.id
                enrolledsubparcel_id = enrolledsubparcel.id
                if not initial_cropplans_data:
                    initial_cropplans_data.append({
                        'partner_id': partner_id,
                        'ids_enrolledsubparcel': [enrolledsubparcel_id]})
                else:
                    current_cropplan = filter(
                        lambda cropplan: cropplan['partner_id'] == partner_id,
                        initial_cropplans_data)
                    if current_cropplan:
                        current_cropplan = current_cropplan[0]
                        current_cropplan['ids_enrolledsubparcel'].append(
                            enrolledsubparcel_id)
                    else:
                        initial_cropplans_data.append({
                            'partner_id': partner_id,
                            'ids_enrolledsubparcel': [enrolledsubparcel_id]})
            enrolledsubparcels = self.env['wua.enrolledsubparcel']
            for cropplan_data in initial_cropplans_data:
                enrolledsubparcels_data = []
                order = 1
                for id_esubparcel in cropplan_data['ids_enrolledsubparcel']:
                    enrolledsubparcel = \
                        enrolledsubparcels.browse(id_esubparcel)
                    if enrolledsubparcel:
                        enrolledsubparcel = enrolledsubparcel[0]
                        enrolledsubparcels_data.append((0, 0, {
                            'parcel_id': enrolledsubparcel.parcel_id.id,
                            'order': order,
                            'area_official': enrolledsubparcel.area_official,
                            'area_perc': enrolledsubparcel.area_perc,
                            'subparceltype_id':
                                enrolledsubparcel.subparceltype_id.id,
                            'cultivation_id':
                                enrolledsubparcel.cultivation_id.id,
                            'cultivationvariety_id':
                                enrolledsubparcel.cultivationvariety_id.id,
                            'irrigationsystem_id':
                                enrolledsubparcel.irrigationsystem_id.id,
                            'productionmethod_id':
                                enrolledsubparcel.productionmethod_id.id}))
                        order = order + 1
                if enrolledsubparcels_data:
                    self.env['wua.cropplan'].create({
                        'agriculturalseason_id': agriculturalseason.id,
                        'partner_id': cropplan_data['partner_id'],
                        'enrolledsubparcel_ids': enrolledsubparcels_data})
            return True

    @api.model
    def create(self, vals):
        if 'enrollment_initial_date' not in vals:
            vals['enrollment_initial_date'] = vals['initial_date']
        if 'enrollment_end_date' not in vals:
            vals['enrollment_end_date'] = vals['end_date']
        return super(WuaAgriculturalseason, self).create(vals)
