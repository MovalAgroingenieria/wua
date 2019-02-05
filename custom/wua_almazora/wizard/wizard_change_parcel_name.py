# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WizardChangeParcelName(models.TransientModel):
    _inherit = 'wizard.change.parcel.name'
    _description = 'Dialog box to change the parcel name (code), ' + \
                   'for Almassora'

    def set_another_parcel_name(self, parcel, new_parcel_name):
        super(WizardChangeParcelName, self).set_another_parcel_name(
            parcel, new_parcel_name)
        for subparcel in parcel.subparcel_ids:
            irrigationgate_id = subparcel.irrigationgate_id.id
            if irrigationgate_id:
                irrigationgate = self.env['wua.irrigationgate'].browse(
                    irrigationgate_id)
                if irrigationgate:
                    irrigationgate.name = new_parcel_name
            break  # Only a subparcel for each parcel
