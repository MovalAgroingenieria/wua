# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WizardChangeParcelName(models.TransientModel):
    _inherit = 'wizard.change.parcel.name'
    _description = 'Dialog box to change the parcel name (code), ' + \
                   'with irrigation infrastructure'

    def set_another_parcel_name(self, parcel, new_parcel_name):
        for irrigationpointwc in parcel.irrigationpointwc_ids:
            irrigationpointwc.irrigationpointwc_code = \
                new_parcel_name + '-' + \
                irrigationpointwc.irrigationpointwc_code[
                    -parcel.__class__.SIZE_IRRIGATIONPOINT_SUFFIX:]
