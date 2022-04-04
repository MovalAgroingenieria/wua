# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaCropplan(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.cropplan'
    _description = 'Crop Plan'
    _order = 'name'

    # Size of fields.
    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_NAME = 22 + MAX_SIZE_PARTNER_CODE
    ORDER_NUMBER_SIZE = 6

    @api.model_cr
    def init(self):
        cropplans_with_order_number = self.env['wua.cropplan'].search(
            [('order_number', '!=', '')])
        if not cropplans_with_order_number:
            cropplans = self.env['wua.cropplan'].search([], order='id')
            for cropplan in cropplans:
                cropplan.order_number = self.env['ir.sequence'].next_by_code(
                    'wua.cropplan.ordernumber')
        cropplans_with_state = self.env['wua.cropplan'].search(
            [('state', '!=', '')])
        if not cropplans_with_state:
            cropplans = self.env['wua.cropplan'].search([])
            if cropplans:
                cropplans.write({'state': 'validated'})

    def _default_agriculturalseason_id(self):
        resp = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        if active_agriculturalseasons:
            resp = active_agriculturalseasons[0].id
        return resp

    def _default_partner_id(self):
        resp = 0
        partners = self.env['res.partner']
        user = self.env.user
        if not user.has_group('base_wua.group_wua_user'):
            partner = partners.browse(user.partner_id.id)
            if partner.is_wua_partner:
                resp = partner.id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        readonly=True,
        default=_default_agriculturalseason_id)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_partner_id)

    name = fields.Char(
        string='Crop Plan',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    request_date = fields.Date(
        string='Request Date',
        required=True,
        index=True,
        default=lambda self: fields.datetime.now())

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        required=True,
        index=True,
        readonly=True,
        default=lambda self: self.env.user,)

    enrolledsubparcel_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='cropplan_id')

    number_of_enrolledsubparcels = fields.Integer(
        string='Enrolled Subparcels',
        store=True,
        index=True,
        compute='_compute_number_of_enrolledsubparcels',
        track_visibility='onchange')

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_official',
        track_visibility='onchange')

    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id')

    credit_overdue = fields.Monetary(
        compute='_compute_credit_overdue',
        string='Overdue Receivable',
        help="Overdue amount this customer owes you.")

    out_of_time = fields.Boolean(
        string='Out of time',
        store=True,
        compute='_compute_out_of_time')

    notes = fields.Html(string='Notes')

    signature_image = fields.Binary(
        string='Signature')

    order_number = fields.Char(
        string='Order Number',
        size=ORDER_NUMBER_SIZE,
        index=True,
        readonly=True)

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('validated', 'Validated'),
        ],
        index=True,
        required=True,
        string='State',
        track_visibility='onchange')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Crop Plan.'),
        ]

    is_portal_user = fields.Boolean(
        string='Created by the partner',
        default=False,
        store=True,
        compute='_compute_is_portal_user')

    @api.constrains('state', 'enrolledsubparcel_ids')
    def _check_flowmeter_id(self):
        if len(self) == 1:
            if self.state == 'validated' and \
                    len(self.enrolledsubparcel_ids) <= 0:
                raise exceptions.ValidationError(
                    _('The crop plan must have one or more parcels.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = str(record.partner_id.partner_code)
            if (not self.env.context.get(
               'reduced_name_get_for_cropplan', False)):
                initial_date_str = datetime.datetime.strptime(
                    record.agriculturalseason_id.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.agriculturalseason_id.end_date,
                    '%Y-%m-%d').strftime('%x')
                name = initial_date_str + ' - ' + end_date_str + ' ' + \
                    '[' + name + ']'
            result.append((record.id, name))
        return result

    @api.depends('agriculturalseason_id', 'partner_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.agriculturalseason_id and record.partner_id:
                value = record.agriculturalseason_id.initial_date + '/' + \
                    record.agriculturalseason_id.end_date + '/' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = value

    @api.depends('enrolledsubparcel_ids')
    def _compute_number_of_enrolledsubparcels(self):
        for record in self:
            number_of_enrolledsubparcels = 0
            if record.enrolledsubparcel_ids:
                number_of_enrolledsubparcels = \
                    len(record.enrolledsubparcel_ids)
            record.number_of_enrolledsubparcels = number_of_enrolledsubparcels

    @api.depends('enrolledsubparcel_ids',
                 'enrolledsubparcel_ids.area_official')
    def _compute_area_official(self):
        for record in self:
            area_official = 0
            if record.enrolledsubparcel_ids:
                area_official = sum(map(lambda x: x.area_official,
                                        record.enrolledsubparcel_ids))
            record.area_official = area_official

    @api.depends('partner_id')
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.depends('partner_id', 'currency_id')
    def _compute_credit_overdue(self):
        for record in self:
            credit_overdue = 0
            if (record.partner_id and record.currency_id):
                credit_overdue = record.partner_id.credit_overdue
            record.credit_overdue = credit_overdue

    @api.depends('request_date',
                 'agriculturalseason_id.enrollment_initial_date',
                 'agriculturalseason_id.enrollment_end_date')
    def _compute_out_of_time(self):
        for record in self:
            out_of_time = False
            if (record.request_date <
               record.agriculturalseason_id.enrollment_initial_date or
               record.request_date >
               record.agriculturalseason_id.enrollment_end_date):
                out_of_time = True
            record.out_of_time = out_of_time

    @api.depends('user_id')
    def _compute_is_portal_user(self):
        partners = self.env['res.partner']
        for record in self:
            is_portal_user = False
            user = self.env.user
            if not user.has_group('base_wua.group_wua_user'):
                partner = partners.browse(user.partner_id.id)
                if partner.is_wua_partner:
                    is_portal_user = True
            record.is_portal_user = is_portal_user

    @api.model
    def create(self, vals):
        if (not self.env.user.has_group('base_wua.group_wua_user') and
           not self.env['ir.values'].get_default(
               'wua.configuration', 'wua_portal_user_can_edit')):
            raise exceptions.UserError(_(
                'You do not have permission to edit data.'))
        accumulative_data = []
        user = self.env.user
        if not user.has_group('base_wua.group_wua_user'):
            partner_id = self.env['res.partner'].browse(user.partner_id.id).id
        else:
            partner_id = vals['partner_id']
        if vals['enrolledsubparcel_ids'] is not None:
            accumulative_data = self.process_vals_enrolledsubparcel_ids(
                vals['enrolledsubparcel_ids'])
        if self.has_a_cropplan(partner_id):
            raise exceptions.UserError(_('The partner already has a previous '
                                         'crop plan. For each agricultural '
                                         'season, only one crop plan '
                                         'per partner is accepted.'))
        vals['order_number'] = self.env['ir.sequence'].next_by_code(
            'wua.cropplan.ordernumber')
        vals['state'] = 'draft'
        new_cropplan = super(WuaCropplan, self).create(vals)
        if accumulative_data:
            if not self.all_enrolledparcels_with_correct_partner(
               partner_id, accumulative_data):
                raise exceptions.UserError(_('There is some parcel with a '
                                             'different partner.'))
            self.sudo().update_census(new_cropplan.id, accumulative_data,
                                      new_cropplan.enrolledsubparcel_ids)
            new_ids_parcel = self.get_ids_parcel_from_accumulative_data(
                accumulative_data)
            self.sudo().update_cropplan_for_parcels(new_ids_parcel,
                                                    new_cropplan.id)
            self.sudo().update_registered_cropplan_for_waterconnections(
                new_ids_parcel, new_cropplan.id)
        self.sudo().update_cropplan_for_partner(partner_id,
                                                new_cropplan.id)
        return new_cropplan

    @api.multi
    def write(self, vals):
        if len(self) == 1 and 'order_number' not in vals:
            if ((not self.env.user.has_group('base_wua.group_wua_user') and
               (not self.env['ir.values'].get_default(
                   'wua.configuration', 'wua_portal_user_can_edit')) or
               not self.agriculturalseason_id.is_the_active)):
                raise exceptions.UserError(_(
                    'You do not have permission to edit data.'))
            if not self.agriculturalseason_id.is_the_active:
                super(WuaCropplan, self).write(vals)
                return True
            accumulative_data = []
            new_ids_parcel = []
            old_ids_parcel = self.get_ids_parcel_from_enrolledsubparcels(
                self.enrolledsubparcel_ids)
            if 'enrolledsubparcel_ids' in vals:
                accumulative_data = self.process_vals_enrolledsubparcel_ids(
                    vals['enrolledsubparcel_ids'])
            super(WuaCropplan, self).write(vals)
            # Control if deleted all enrollwsaubparcels
            if (self.number_of_enrolledsubparcels == 0 and old_ids_parcel):
                self.sudo().update_cropplan_for_parcels(old_ids_parcel, 0)
                self.sudo().update_registered_cropplan_for_waterconnections(
                    old_ids_parcel, 0)
            if accumulative_data:
                self.sudo().update_census(self.id, accumulative_data,
                                          self.enrolledsubparcel_ids)
                new_ids_parcel = self.get_ids_parcel_from_accumulative_data(
                    accumulative_data)
                invariable_ids_parcel = \
                    list(set(old_ids_parcel) & set(new_ids_parcel))
                for parcel_id in invariable_ids_parcel:
                    old_ids_parcel.remove(parcel_id)
                    new_ids_parcel.remove(parcel_id)
                self.sudo().update_cropplan_for_parcels(old_ids_parcel, 0)
                self.sudo().update_registered_cropplan_for_waterconnections(
                    old_ids_parcel, 0)
                self.sudo().update_cropplan_for_parcels(
                    new_ids_parcel, self.id)
                self.sudo().update_registered_cropplan_for_waterconnections(
                    new_ids_parcel, self.id)
        else:
            super(WuaCropplan, self).write(vals)
        return True

    @api.multi
    def unlink(self):
        for record in self:
            if ((not self.env.user.has_group('base_wua.group_wua_user') and
               (not self.env['ir.values'].get_default(
                   'wua.configuration', 'wua_portal_user_can_edit')) or
               not self.agriculturalseason_id.is_the_active)):
                raise exceptions.UserError(_(
                    'You do not have permission to edit data.'))
            if record.agriculturalseason_id.is_the_active:
                old_ids_parcel = self.get_ids_parcel_from_enrolledsubparcels(
                    record.enrolledsubparcel_ids)
                self.sudo().update_cropplan_for_parcels(old_ids_parcel, 0)
                self.sudo().update_registered_cropplan_for_waterconnections(
                    old_ids_parcel, 0)
                self.sudo().update_cropplan_for_partner(
                    record.partner_id.id, 0)
        return super(WuaCropplan, self).unlink()

    def has_a_cropplan(self, partner_id):
        resp = False
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('is_the_active', '=', True)])
        if active_agriculturalseason:
            active_agriculturalseason = active_agriculturalseason[0]
            cropplan = self.env['wua.cropplan'].search(
                [('partner_id', '=', partner_id),
                 ('agriculturalseason_id', '=', active_agriculturalseason.id)])
            if cropplan:
                resp = True
        return resp

    def process_vals_enrolledsubparcel_ids(self, vals):
        accumulative_data = self.get_accumulative_data(vals)
        if not accumulative_data:
            return []
        parcel_with_incorrect_subparcels_area = \
            self.get_parcel_with_incorrect_subparcels_area(accumulative_data)
        if parcel_with_incorrect_subparcels_area:
            parcel = self.env['wua.parcel'].browse(
                parcel_with_incorrect_subparcels_area)
            warning_incorrect_subparcels_area_01 = \
                _('The sum of the areas of the subparcels of parcel ')
            warning_incorrect_subparcels_area_02 = \
                _(' is grather than the area of the parcel.')
            raise exceptions.UserError(warning_incorrect_subparcels_area_01 +
                                       parcel.name +
                                       warning_incorrect_subparcels_area_02)
        self.assign_order_to_enrolledsubparcels(vals, accumulative_data)
        return accumulative_data

    def assign_order_to_enrolledsubparcels(self, vals, accumulative_data):
        for parcel_data in accumulative_data:
            current_parcel_id = parcel_data['parcel_id']
            enrolledsubparcels = self.env['wua.enrolledsubparcel']
            last_order = 0
            max_enrolledsubparcel_id = 0
            # Loop #1: get the last order of the each group of
            # enrolled subparcels
            for enrolledsubparcel in vals:
                enrolledsubparcel_oper = enrolledsubparcel[0]
                enrolledsubparcel_id = enrolledsubparcel[1]
                enrolledsubparcel_vals = enrolledsubparcel[2]
                parcel_id = 0
                # Get the implied parcel_id.
                if enrolledsubparcel_oper == 0:
                    parcel_id = enrolledsubparcel_vals['parcel_id']
                if enrolledsubparcel_oper == 4:
                    notmodified_enrolledsubparcel = \
                        enrolledsubparcels.browse(enrolledsubparcel_id)
                    parcel_id = notmodified_enrolledsubparcel.parcel_id.id
                if enrolledsubparcel_oper == 1:
                    modified_enrolledsubparcel = enrolledsubparcels.browse(
                        enrolledsubparcel_id)
                    parcel_id = modified_enrolledsubparcel.parcel_id.id
                    if ('parcel_id' in enrolledsubparcel_vals and
                       enrolledsubparcel_vals['parcel_id'] != parcel_id):
                        parcel_id = enrolledsubparcel_vals['parcel_id']
                # Only process if the implied parcel_id is equal to
                # current_parcel_id
                if parcel_id != current_parcel_id:
                    continue
                if (enrolledsubparcel_oper == 1 or
                   enrolledsubparcel_oper == 4):
                    if enrolledsubparcel_id > max_enrolledsubparcel_id:
                        max_enrolledsubparcel_id = enrolledsubparcel_id
            if max_enrolledsubparcel_id > 0:
                last_enrolledsubparcel_of_current_parcel = \
                    enrolledsubparcels.browse(max_enrolledsubparcel_id)
                last_order = last_enrolledsubparcel_of_current_parcel.order
            # Loop #2: assign a order for each new enrolled subparcel.
            order = last_order + 1
            for enrolledsubparcel in vals:
                enrolledsubparcel_oper = enrolledsubparcel[0]
                enrolledsubparcel_vals = enrolledsubparcel[2]
                if (enrolledsubparcel_oper == 0 and
                   enrolledsubparcel_vals['parcel_id'] == current_parcel_id):
                    enrolledsubparcel_vals['order'] = order
                    order = order + 1

    # The result of get_accumulative_data method is a list of dictionaries.
    # Each key is a parcel code, and there are two values: the sum of areas
    # of their subparcels and the subparcel position of last subparcel.
    def get_accumulative_data(self, vals):
        resp = []
        enrolledsubparcels = self.env['wua.enrolledsubparcel']
        for enrolledsubparcel in vals:
            enrolledsubparcel_oper = enrolledsubparcel[0]
            enrolledsubparcel_id = enrolledsubparcel[1]
            enrolledsubparcel_vals = enrolledsubparcel[2]
            if enrolledsubparcel_oper in [0, 1, 4]:
                # New enrolled subparcel.
                if enrolledsubparcel_oper == 0:
                    parcel_id = enrolledsubparcel_vals['parcel_id']
                    area_official = enrolledsubparcel_vals['area_official']
                # Not-modified enrolled subparcel.
                if enrolledsubparcel_oper == 4:
                    notmodified_enrolledsubparcel = enrolledsubparcels.browse(
                        enrolledsubparcel_id)
                    parcel_id = notmodified_enrolledsubparcel.parcel_id.id
                    area_official = notmodified_enrolledsubparcel.area_official
                # Modified enrolled subparcel.
                if enrolledsubparcel_oper == 1:
                    modified_enrolledsubparcel = enrolledsubparcels.browse(
                        enrolledsubparcel_id)
                    parcel_id = modified_enrolledsubparcel.parcel_id.id
                    if ('parcel_id' in enrolledsubparcel_vals and
                       enrolledsubparcel_vals['parcel_id'] != parcel_id):
                        parcel_id = enrolledsubparcel_vals['parcel_id']
                        area_official = enrolledsubparcel_vals['area_official']
                    else:
                        if 'area_official' in enrolledsubparcel_vals:
                            area_official = \
                                enrolledsubparcel_vals['area_official']
                        else:
                            area_official = \
                                modified_enrolledsubparcel.area_official
                # Updating the parcels dictionary
                if not resp:
                    resp.append({
                        'parcel_id': parcel_id,
                        'area_official': area_official,
                        'number_of_enrolledsubparcels': 1,
                        })
                else:
                    current_parcel = filter(
                        lambda parcel: parcel['parcel_id'] == parcel_id, resp)
                    if current_parcel:
                        current_parcel = current_parcel[0]
                        current_parcel['area_official'] = \
                            current_parcel['area_official'] + area_official
                        current_parcel['number_of_enrolledsubparcels'] = \
                            current_parcel['number_of_enrolledsubparcels'] + 1
                    else:
                        resp.append({
                            'parcel_id': parcel_id,
                            'area_official': area_official,
                            'number_of_enrolledsubparcels': 1,
                            })
        return resp

    # Simillar to "get_accumulative_data", but directly from the
    # enrolledsubparcel_ids field (not from "vals").
    def get_accumulative_data_from_cropplan(self, cropplan):
        resp = []
        for enrolledsubparcel in cropplan.enrolledsubparcel_ids:
            parcel_id = enrolledsubparcel.parcel_id.id
            area_official = enrolledsubparcel.area_official
            if not resp:
                resp.append({
                    'parcel_id': parcel_id,
                    'area_official': area_official,
                    'number_of_enrolledsubparcels': 1,
                    })
            else:
                current_parcel = filter(
                    lambda parcel: parcel['parcel_id'] == parcel_id, resp)
                if current_parcel:
                    current_parcel = current_parcel[0]
                    current_parcel['area_official'] = \
                        current_parcel['area_official'] + area_official
                    current_parcel['number_of_enrolledsubparcels'] = \
                        current_parcel['number_of_enrolledsubparcels'] + 1
                else:
                    resp.append({
                        'parcel_id': parcel_id,
                        'area_official': area_official,
                        'number_of_enrolledsubparcels': 1,
                        })
        return resp

    def is_close(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def get_parcel_with_incorrect_subparcels_area(self, accumulative_data):
        resp = 0
        parcels = self.env['wua.parcel']
        for parcel_data in accumulative_data:
            parcel = parcels.browse(parcel_data['parcel_id'])
            area_official_of_parcel = parcel.area_official
            area_official_of_enrolledsubparcels = parcel_data['area_official']
            areas_are_equal = self.is_close(
                area_official_of_parcel, area_official_of_enrolledsubparcels,
                1e-09, 0.00011)
            if (not areas_are_equal and
               not area_official_of_enrolledsubparcels <
               area_official_of_parcel):
                resp = parcel_data['parcel_id']
                break
        return resp

    def all_enrolledparcels_with_correct_partner(self, partner_id,
                                                 accumulative_data):
        resp = True
        parcels = self.env['wua.parcel']
        for parcel_data in accumulative_data:
            partner_of_parcel_data = \
                parcels.browse(parcel_data['parcel_id']).partner_id
            if partner_of_parcel_data.id != partner_id:
                resp = False
                break
        return resp

    def update_census(self, cropplan_id, accumulative_data,
                      enrolledsubparcel_ids):
        parcels = self.env['wua.parcel']
        subparcels = self.env['wua.parcel.subparcel']
        enrolledsubparcels = self.env['wua.enrolledsubparcel']
        no_cultivation_subparcel_type = self.env.ref(
            'base_wua_crop_planning.subparceltype_00')
        for parcel_data in accumulative_data:
            parcel = parcels.browse(parcel_data['parcel_id'])
            area_official_of_parcel = parcel.area_official
            area_official_of_enrolledsubparcels = parcel_data['area_official']
            areas_are_equal = self.is_close(
                area_official_of_parcel, area_official_of_enrolledsubparcels,
                1e-09, 0.00011)
            if (not areas_are_equal and
               area_official_of_enrolledsubparcels <
               area_official_of_parcel):
                remaining_area = area_official_of_parcel - \
                    area_official_of_enrolledsubparcels
                enrolledsubparcel_ids_current_parcel = \
                    enrolledsubparcel_ids.filtered(
                        lambda x: x.parcel_id.id == parcel_data['parcel_id'])
                max_order = 0
                for enrolledsubparcel in enrolledsubparcel_ids_current_parcel:
                    if enrolledsubparcel.order > max_order:
                        max_order = enrolledsubparcel.order
                max_order = max_order + 1
                # Add enrolled subparcel with "no cultivation".
                enrolledsubparcels.create({
                    'cropplan_id': cropplan_id,
                    'parcel_id': parcel.id,
                    'order': max_order,
                    'area_official': remaining_area,
                    'area_perc': (remaining_area/parcel.area_official) * 100,
                    'subparceltype_id': no_cultivation_subparcel_type.id})
            # Renenerate subparcels in census.
            subparcels.search([('parcel_id', '=', parcel.id)]).unlink()
            enrolledsubparcels_to_add = enrolledsubparcels.search(
                [('cropplan_id', '=', cropplan_id),
                 ('parcel_id', '=', parcel.id)])
            for enrolledsubparcel in enrolledsubparcels_to_add:
                subparcels.create({
                    'subparcel_code': parcel.name + '-' +
                    str(enrolledsubparcel.order).
                    zfill(parcel.SIZE_SUBPARCEL_SUFFIX),
                    'parcel_id': parcel.id,
                    'pos': enrolledsubparcel.order,
                    'area_official': enrolledsubparcel.area_official,
                    'area_perc': enrolledsubparcel.area_perc,
                    'subparceltype_id': enrolledsubparcel.subparceltype_id.id,
                    'cultivation_id': enrolledsubparcel.cultivation_id.id,
                    'cultivationvariety_id':
                        enrolledsubparcel.cultivationvariety_id.id,
                    'irrigationsystem_id':
                        enrolledsubparcel.irrigationsystem_id.id,
                    'productionmethod_id':
                        enrolledsubparcel.productionmethod_id.id})

    def get_ids_parcel_from_enrolledsubparcels(self, enrolledsubparcel_ids):
        resp = []
        for enrolledsubparcel in enrolledsubparcel_ids:
            parcel_id = enrolledsubparcel.parcel_id.id
            if parcel_id not in resp:
                resp.append(parcel_id)
        return resp

    def get_ids_parcel_from_accumulative_data(self, accumulative_data):
        resp = []
        for parcel_data in accumulative_data:
            resp.append(parcel_data['parcel_id'])
        return resp

    def update_cropplan_for_parcels(self, ids_parcel, cropplan_id):
        # If cropplan_id is zero, then set with null the crop plan of parcels
        # "ids_parcel" and reset their subparcels (a only subparcel with
        # "no-cultivation"). Else, assign to parcels the crop plan.
        parcels = self.env['wua.parcel'].browse(ids_parcel)
        subparcels = self.env['wua.parcel.subparcel']
        no_cultivation_subparcel_type = self.env.ref(
            'base_wua_crop_planning.subparceltype_00')
        for parcel in parcels:
            if cropplan_id > 0:
                parcel.cropplan_id = cropplan_id
            else:
                subparcels.search([('parcel_id', '=', parcel.id)]).unlink()
                subparcels.create({
                    'subparcel_code': parcel.name + '-' +
                    '1'.zfill(parcel.SIZE_SUBPARCEL_SUFFIX),
                    'parcel_id': parcel.id,
                    'pos': 1,
                    'area_official': parcel.area_official,
                    'area_perc': 100,
                    'subparceltype_id': no_cultivation_subparcel_type.id})
                parcel.cropplan_id = None

    def update_registered_cropplan_for_waterconnections(
            self, ids_parcel, cropplan_id):
        # If cropplan_id is zero, then get the water connections of parcels
        # "ids_parcel" and set with "False" the "registered_cropplan" field
        # of these water connections (if there is not other parcels with crop
        # plan). Else, set with "True" the "registered_cropplan" field of
        # the water connections.
        parcels = self.env['wua.parcel'].browse(ids_parcel)
        for parcel in parcels:
            irrigationpointwcs = \
                self.env['wua.parcel.irrigationpointwc'].search(
                    [('parcel_id', '=', parcel.id)])
            for irrigationpointwc in irrigationpointwcs:
                waterconnection = irrigationpointwc.waterconnection_id
                if cropplan_id > 0:
                    if not waterconnection.registered_cropplan:
                        waterconnection.registered_cropplan = True
                else:
                    unregister_cropplan = True
                    for ipwc_of_wc in waterconnection.irrigationpointwc_ids:
                        if (ipwc_of_wc.parcel_id != parcel.id and
                           ipwc_of_wc.parcel_id.registered_cropplan):
                            unregister_cropplan = False
                            break
                    if unregister_cropplan:
                        waterconnection.registered_cropplan = False
                        if waterconnection.working:
                            waterconnection.working = False

    def update_cropplan_for_partner(self, partner_id, cropplan_id):
        # If croppan_id is zero, then set with null the crop plan of
        # partner "partner_id". Else, assign to partner the crop plan.
        partner = self.env['res.partner'].browse(partner_id)
        if cropplan_id > 0:
            partner.cropplan_id = cropplan_id
        else:
            partner.cropplan_id = None

    @api.multi
    def action_regenerate_census(self, go_to_partners=True):
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('is_the_active', '=', True)])
        if not active_agriculturalseasons:
            raise exceptions.UserError(_('There is no active agricultural '
                                         'season.'))
        # First: Reset all (virtual closing of agricultural season)
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)])
        if not partners:
            return True
        for partner in partners:
            partner.cropplan_id = None
        parcels = self.env['wua.parcel'].search([])
        ids_parcel = []
        for parcel in parcels:
            ids_parcel.append(parcel.id)
        self.update_cropplan_for_parcels(ids_parcel, 0)
        waterconnections = self.env['wua.waterconnection'].search([])
        for waterconnection in waterconnections:
            waterconnection.write({
                'registered_cropplan': False,
                'working': False})
        # Second: Update census from all crop plans.
        active_agriculturalseason = active_agriculturalseasons[0]
        cropplans = self.env['wua.cropplan'].search(
            [('agriculturalseason_id', '=', active_agriculturalseason.id)])
        for cropplan in cropplans:
            accumulative_data = \
                self.get_accumulative_data_from_cropplan(cropplan)
            if accumulative_data:
                self.update_census(cropplan.id, accumulative_data,
                                   cropplan.enrolledsubparcel_ids)
                new_ids_parcel = self.get_ids_parcel_from_accumulative_data(
                    accumulative_data)
                self.update_cropplan_for_parcels(new_ids_parcel, cropplan.id)
                self.update_registered_cropplan_for_waterconnections(
                    new_ids_parcel, cropplan.id)
                self.update_cropplan_for_partner(cropplan.partner_id.id,
                                                 cropplan.id)
        # Third: Go to res_partner tree view.
        if go_to_partners:
            condition = [('is_wua_partner', '=', True)]
            id_form_view = self.env.ref('base_wua.view_partner_form').id
            id_tree_view = self.env.ref('base_wua.view_partner_tree').id
            search_view = self.env.ref('base_wua.view_partner_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Partners'),
                'res_model': 'res.partner',
                'view_type': 'form',
                'view_mode': 'tree,form,kanban',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                'context': {'wua': '1', 'default_is_wua_partner': True}
                }
            return act_window
        else:
            return True

    @api.multi
    def validate_cropplan(self):
        self.ensure_one()
        self.state = 'validated'

    @api.multi
    def cancel_cropplan(self):
        self.ensure_one()
        self.state = 'draft'

    @api.multi
    def get_subparcels(self):
        self.ensure_one()
        subparcels_of_partner = self.env['wua.parcel.subparcel'].search(
            [('partner_id', '=', self.partner_id.id)])
        enrolledsubparcels = []
        for subparcel in subparcels_of_partner:
            enrolledsubparcel = {
                'parcel_id': subparcel.parcel_id.id,
                'area_official': subparcel.area_official,
                'area_perc': subparcel.area_perc,
                'cultivation_id': subparcel.cultivation_id.id,
                'cultivationvariety_id': subparcel.cultivationvariety_id.id,
                'irrigationsystem_id': subparcel.irrigationsystem_id.id,
                'productionmethod_id': subparcel.productionmethod_id.id,
            }
            enrolledsubparcels.append([0, False, enrolledsubparcel])
        if (enrolledsubparcels):
            self.write({
                'enrolledsubparcel_ids': enrolledsubparcels
            })

    def validate_cropplans(self, active_cropplans):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        cropplans = self.env['wua.cropplan'].browse(active_cropplans)
        for cropplan in cropplans:
            if cropplan.state == 'draft':
                cropplan.validate_cropplan()

    def cancel_cropplans(self, active_cropplans):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        cropplans = self.env['wua.cropplan'].browse(active_cropplans)
        for cropplan in cropplans:
            if cropplan.state == 'validated':
                cropplan.cancel_cropplan()


class WuaEnrolledsubparcel(models.Model):
    _name = 'wua.enrolledsubparcel'
    _description = 'Enrolled Subparcel'
    _order = 'name'

    MAX_SIZE_SUBPARCEL_CODE = 25
    MAX_SIZE_NAME = 22 + MAX_SIZE_SUBPARCEL_CODE
    SIZE_SUBPARCEL_SUFFIX = 2

    @api.model
    def default_get(self, fields):
        res = super(WuaEnrolledsubparcel, self).default_get(fields)
        cultivable_subparceltypes = self.env['wua.subparceltype'].search(
            [('is_cultivable', '=', True)], order='name')
        if len(cultivable_subparceltypes) > 0:
            res['subparceltype_id'] = cultivable_subparceltypes[0].id
        return res

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        required=True,
        index=True,
        ondelete='cascade')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_partner_id')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='restrict')

    order = fields.Integer(
        string='Order',
        required=True,
        default=0)

    subparcel_code = fields.Char(
        string='Subparcel Code',
        size=MAX_SIZE_SUBPARCEL_CODE,
        store=True,
        index=True,
        compute='_compute_subparcel_code')

    name = fields.Char(
        string='Enrolled Subparcel',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        required=True,
        default=0)

    overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue')

    area_perc = fields.Float(
        string='%',
        digits=(5, 2),
        default=0)

    profile = fields.Selection([
        ('O', 'Owner'),
        ('L', 'Lessee'),
        ('P', 'Payer'),
        ], string='Profile',
        store=True,
        compute='_compute_profile')

    subparceltype_id = fields.Many2one(
        string='Type',
        comodel_name='wua.subparceltype',
        required=True,
        index=True,
        ondelete='restrict')

    is_cultivable = fields.Boolean(
        string="Cultivable",
        store=True,
        compute='_compute_is_cultivable')

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        index=True,
        ondelete='restrict')

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        index=True,
        ondelete='restrict')

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
        index=True,
        ondelete='restrict')

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        index=True,
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        store=True,
        ondelete='restrict',
        compute='_compute_hydraulicsector_id')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Enrolled Subparcel.'),
        ('valid_area_official', 'CHECK (area_official >= 0)',
         'The area must be a value zero or positive.'),
        ('valid_area_perc', 'CHECK (area_perc >= 0 and area_perc <= 100)',
         'The area percentage must be a value from 0 to 100.'),
        ]

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.agriculturalseason_id.initial_date,
                '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.agriculturalseason_id.end_date,
                '%Y-%m-%d').strftime('%x')
            name = initial_date_str + ' - ' + end_date_str + ' ' + \
                '[' + record.subparcel_code + ']'
            result.append((record.id, name))
        return result

    @api.depends('cropplan_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            record.agriculturalseason_id = \
                record.cropplan_id.agriculturalseason_id

    @api.depends('cropplan_id')
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = \
                record.cropplan_id.partner_id

    @api.depends('parcel_id', 'order')
    def _compute_subparcel_code(self):
        for record in self:
            record.subparcel_code = record.parcel_id.name + '-' + \
                str(record.order).zfill(self.SIZE_SUBPARCEL_SUFFIX)

    @api.depends('agriculturalseason_id', 'subparcel_code')
    def _compute_name(self):
        for record in self:
            record.name = record.agriculturalseason_id.initial_date + '/' + \
                record.agriculturalseason_id.end_date + '/' + \
                record.subparcel_code

    @api.depends('parcel_id')
    def _compute_profile(self):
        for record in self:
            partnerlinks = self.env['wua.parcel.partnerlink'].search(
                [('parcel_id', '=', record.parcel_id.id)])
            for partnerlink in partnerlinks:
                if partnerlink.partner_id == record.partner_id:
                    record.profile = partnerlink.profile
                    break

    @api.depends('subparceltype_id')
    def _compute_is_cultivable(self):
        for record in self:
            record.is_cultivable = record.subparceltype_id.is_cultivable

    @api.multi
    def _compute_overdue(self):
        for record in self:
            overdue = False
            if (record.parcel_id):
                overdue = record.parcel_id.overdue
            record.overdue = overdue

    @api.depends('parcel_id', 'parcel_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            record.hydraulicsector_id = record.parcel_id.hydraulicsector_id

    @api.onchange('parcel_id')
    def _onchange_parcel_id(self):
        self.area_perc = 100
        self.area_official = self.parcel_id.area_official

    @api.onchange('area_perc')
    def _onchange_area_perc(self):
        self.area_official = round((self.parcel_id.area_official *
                                    self.area_perc) / 100, 4)

    @api.onchange('area_official')
    def _onchange_area_official(self):
        if self.parcel_id.area_official > 0:
            self.area_perc = (self.area_official *
                              100) / self.parcel_id.area_official

    @api.onchange('cultivation_id')
    def _onchange_cultivation_id(self):
        if self.cultivation_id.id:
            return {
                'domain': {'cultivationvariety_id':
                           [('cultivation_id', '=', self.cultivation_id.id)]}
            }

    @api.model
    def create(self, vals):
        if 'subparceltype_id' in vals:
            subparceltype_id = vals['subparceltype_id']
            if subparceltype_id:
                if not self.env['wua.subparceltype'].browse(
                   subparceltype_id).is_cultivable:
                    vals['cultivation_id'] = None
                    vals['cultivationvariety_id'] = None
                    vals['irrigationsystem_id'] = None
                    vals['productionmethod_id'] = None
        new_enrolledsubparcel = super(WuaEnrolledsubparcel, self).create(vals)
        return new_enrolledsubparcel

    @api.multi
    def write(self, vals):
        if 'subparceltype_id' in vals:
            subparceltype_id = vals['subparceltype_id']
            if subparceltype_id:
                if not self.env['wua.subparceltype'].browse(
                   subparceltype_id).is_cultivable:
                    vals['cultivation_id'] = None
                    vals['cultivationvariety_id'] = None
                    vals['irrigationsystem_id'] = None
                    vals['productionmethod_id'] = None
        super(WuaEnrolledsubparcel, self).write(vals)
        return True
