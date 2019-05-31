# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    cropplan_id = fields.Many2one(
        string='Crop Plan',
        comodel_name='wua.cropplan',
        ondelete='set null',
        readonly=True)

    enrolledsubparcel_ids = fields.One2many(
        string='Enrolled Subparcels',
        comodel_name='wua.enrolledsubparcel',
        inverse_name='parcel_id')

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False,
        store=True,
        compute='_compute_registered_cropplan')

    can_be_watered = fields.Boolean(
        string='Can be watered',
        default=False,
        store=True,
        compute='_compute_can_be_watered')

    permanent = fields.Boolean(
        string='Permanent',
        default=False)

    @api.depends('cropplan_id')
    def _compute_registered_cropplan(self):
        for record in self:
            registered_cropplan = False
            if record.cropplan_id:
                registered_cropplan = True
            record.registered_cropplan = registered_cropplan

    @api.depends('enrolledsubparcel_ids',
                 'enrolledsubparcel_ids.is_cultivable')
    def _compute_can_be_watered(self):
        for record in self:
            can_be_watered = False
            cultivable_enrolledsubparcels = \
                record.enrolledsubparcel_ids.filtered(
                    lambda x: x.agriculturalseason_id.is_the_active and
                    x.is_cultivable)
            if cultivable_enrolledsubparcels:
                can_be_watered = True
            record.can_be_watered = can_be_watered

    @api.multi
    def name_get(self):
        result = []
        if self.env.context.get('in_combo', False):
            for record in self:
                parcel_code = record.name
                area_official_str = _('area:') + ' ' + \
                    '{:.4f}'.format(record.area_official)
                result.append((record.id, parcel_code + ' (' +
                               area_official_str + ')'))
        else:
            for record in self:
                result.append((record.id, record.name))
        return result
