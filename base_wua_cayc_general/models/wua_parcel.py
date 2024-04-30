# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    is_primary = fields.Boolean(
        string='Is primary',
        default=False,
    )

    wuabase_id = fields.Many2one(
        string='WUA Base',
        comodel_name='wua.wuabase',
        index=True,
    )

    @api.constrains('is_primary', 'parcel_class_ids')
    def check_primary_parcel_class(self):
        for record in self:
            if record.is_primary and len(record.parcel_class_ids) != 0:
                raise exceptions.ValidationError(
                    _('A primary parcel cannot have a class associated.'))
            elif not record.is_primary and len(record.parcel_class_ids) < 1:
                raise exceptions.ValidationError(
                    _('A che parcel must have at least one class associated.'))

    @api.constrains('is_primary', 'partnerlink_ids')
    def check_primary_partnerlinks(self):
        for record in self:
            if (len(record.partnerlink_ids) > 0):
                if record.is_primary and len(record.partnerlink_ids.filtered(
                        lambda x: not x.partner_id.is_primary)) > 0:
                    raise exceptions.ValidationError(
                        _('A primary parcel cannot have a non primary '
                          'partner.'))
                elif not record.is_primary and len(
                    record.partnerlink_ids.filtered(
                        lambda x: x.partner_id.is_primary)) > 0:
                    raise exceptions.ValidationError(
                        _('A CHE parcel cannot have a non CHE '
                          'partner.'))

    @api.multi
    def write(self, vals):
        super(WuaParcel, self).write(vals)
        if ('partner_id' in vals and vals['partner_id']):
            # This could be an ensure one, but use for massive assignments
            for record in self:
                if (not record.wuabase_id):
                    record.wuabase_id = record.partner_id.wuabase_id
        return True

    # Inherit method to ensure that parcels not primary have at least
    # one parcel class on creation
    def should_create_parcel_class_on_creation(self, parcel_vals):
        return super(WuaParcel, self).should_create_parcel_class_on_creation(
            parcel_vals) and ('is_primary' not in parcel_vals or
                              not parcel_vals['is_primary'])

    # Inherit and modify method, primary parcels don't have parcel classes
    def is_parcel_classes_area_correct(
            self, parcel_id, area_official, parcel_class_ids, parcel_vals):
        parcels = self.env['wua.parcel']
        parcel = parcels.browse(parcel_id)
        if (('is_primary' in parcel_vals and parcel_vals['is_primary']) or
                (parcel.is_primary and 'is_primary' not in parcel_vals)):
            return True
        else:
            return super(WuaParcel, self).is_parcel_classes_area_correct(
                parcel_id, area_official, parcel_class_ids, parcel_vals)


class WuaParcelClass(models.Model):
    _inherit = 'wua.parcel.class'

    wuabase_id = fields.Many2one(
        string='WUA Base',
        comodel_name='wua.wuabase',
        related='parcel_id.wuabase_id',
        store=True,
        index=True,
    )
