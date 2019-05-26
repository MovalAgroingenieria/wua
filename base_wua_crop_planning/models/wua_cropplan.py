# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WuaCropplan(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.cropplan'
    _description = 'Crop Plan'
    _order = 'name'

    # Size of field "name".
    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_NAME = 22 + MAX_SIZE_PARTNER_CODE

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

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Crop Plan.'),
        ]

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

    @api.model
    def create(self, vals):
        accumulative_data = []
        if vals['enrolledsubparcel_ids'] is not None:
            accumulative_data = self.process_vals_enrolledsubparcel_ids(
                vals['enrolledsubparcel_ids'])
        new_cropplan = super(WuaCropplan, self).create(vals)
        if accumulative_data:
            # Provisional
            # Update subparcels census...
            pass
        # print new_cropplan.enrolledsubparcel_ids[0].area_official
        return new_cropplan

    @api.multi
    def write(self, vals):
        accumulative_data = []
        if len(self) == 1:
            if 'enrolledsubparcel_ids' in vals:
                accumulative_data = self.process_vals_enrolledsubparcel_ids(
                    vals['enrolledsubparcel_ids'])
        super(WuaCropplan, self).write(vals)
        if accumulative_data:
            # Provisional
            # Update subparcels census...
            pass
        # print self.enrolledsubparcel_ids[0].area_official
        return True

    def process_vals_enrolledsubparcel_ids(self, vals):
        accumulative_data = self.get_accumulative_data(vals)
        # Provisional
        print accumulative_data
        return accumulative_data

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
                    order = 0
                # Not-modified enrolled subparcel.
                if enrolledsubparcel_oper == 4:
                    notmodified_enrolledsubparcel = enrolledsubparcels.browse(
                        enrolledsubparcel_id)
                    parcel_id = notmodified_enrolledsubparcel.parcel_id.id
                    area_official = notmodified_enrolledsubparcel.area_official
                    order = notmodified_enrolledsubparcel.order
                # Modified enrolled subparcel.
                if enrolledsubparcel_oper == 1:
                    modified_enrolledsubparcel = enrolledsubparcels.browse(
                        enrolledsubparcel_id)
                    parcel_id = modified_enrolledsubparcel.parcel_id.id
                    if ('parcel_id' in enrolledsubparcel_vals and
                       enrolledsubparcel_vals['parcel_id'] != parcel_id):
                        parcel_id = enrolledsubparcel_vals['parcel_id']
                        area_official = enrolledsubparcel_vals['area_official']
                        order = 0
                    else:
                        if 'area_official' in enrolledsubparcel_vals:
                            area_official = \
                                enrolledsubparcel_vals['area_official']
                        else:
                            area_official = \
                                modified_enrolledsubparcel.area_official
                        order = modified_enrolledsubparcel.order
                # Updating the parcels dictionary
                if not resp:
                    resp.append({
                        parcel_id: parcel_id,
                        area_official: area_official,
                        order: 1,
                    })
                else:
                    current_parcel = filter(
                        lambda parcel: parcel['parcel_id'] == parcel_id, resp)
                    if current_parcel:
                        current_parcel = current_parcel[0]
                        current_parcel['area_official'] = \
                            current_parcel['area_official'] + area_official
                        if current_parcel['order'] > order:
                            order = current_parcel['order']
                            current_parcel['order'] = order + 1
                    else:
                        resp.append({
                            parcel_id: parcel_id,
                            area_official: area_official,
                            order: 1,
                        })
                # Provisional
                print parcel_id
                print area_official
                print order
        return resp


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
