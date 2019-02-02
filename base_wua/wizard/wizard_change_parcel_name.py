# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardChangeParcelName(models.TransientModel):
    _name = 'wizard.change.parcel.name'
    _description = 'Dialog box to change the parcel name (code)'

    SIZE_NAME = 20

    parcel_name = fields.Char(
        string='New parcel code',
        size=SIZE_NAME,
        help='The code of the link-to-partners, subparcels and other ' +
        'dependent entities will also be changed')

    @api.model
    def default_get(self, var_fields):
        return {'parcel_name': self.get_current_parcel_name()}

    @api.multi
    def set_parcel_name(self):
        self.ensure_one()
        if len(self.env.context['active_ids']) > 1:
            raise exceptions.UserError(_(
                'Operation not allowed for multiple records.'))
        current_parcel_name = self.get_current_parcel_name()
        new_parcel_name = ''
        parcel_name_ok = self.parcel_name
        if parcel_name_ok:
            new_parcel_name = self.parcel_name.strip()
            if new_parcel_name == '':
                parcel_name_ok = False
        if not parcel_name_ok:
            raise exceptions.ValidationError(_('Empty parcel code.'))
        parcels = self.env['wua.parcel']
        parcels_filtered = parcels.search([('name', '=', current_parcel_name)])
        if len(parcels_filtered) == 1:
            parcel = parcels_filtered[0]
            parcel.name = new_parcel_name
            for subparcel in parcel.subparcel_ids:
                subparcel.subparcel_code = new_parcel_name + '-' + \
                    subparcel.subparcel_code[
                        -parcel.__class__.SIZE_SUBPARCEL_SUFFIX:]
            for partnerlink in parcel.partnerlink_ids:
                partnerlink.partnerlink_code = new_parcel_name + '-' + \
                    partnerlink.partnerlink_code[
                        -parcel.__class__.SIZE_PARTNERLINK_SUFFIX:]
            self.set_another_parcel_name(parcel, new_parcel_name)

    def set_another_parcel_name(self, parcel, new_parcel_name):
        # This is a abstract method for inherited models (hook).
        pass

    def get_current_parcel_name(self):
        current_parcel_name = ''
        current_parcel_id = self.env.context['active_id']
        parcels = self.env['wua.parcel']
        parcels_filtered = parcels.search([('id', '=', current_parcel_id)])
        if len(parcels_filtered) == 1:
            current_parcel_name = parcels_filtered[0].name
        return current_parcel_name
