# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['wua.controlperiod'].search([])._compute_deviation()
    env['wua.agriculturalseason'].search([])._compute_deviation()
    env['wua.parcel.subparcel'].search([])._compute_deviation()
    env['wua.comparative.subparcel.presconsumption'].search([]).\
        _compute_deviation()
