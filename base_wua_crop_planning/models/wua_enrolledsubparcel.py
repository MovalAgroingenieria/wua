# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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
        ondelete='restrict')

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
