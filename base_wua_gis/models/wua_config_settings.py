# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    partner_gis_preview_in_form = fields.Boolean(
        string='GIS preview of partners in the form',
        default=False,
        help='If checked, then the GIS preview of the partner parcels will be '
             'placed in the form view; else, in a page of the notebook')

    parcel_gis_preview_in_form = fields.Boolean(
        string='GIS preview of parcels in the form',
        default=False,
        help='If checked, then the GIS preview of the parcel will be '
             'placed in the form view; else, in a page of the notebook')

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.configuration',
                           'partner_gis_preview_in_form',
                           self.partner_gis_preview_in_form)
        values.set_default('wua.configuration',
                           'parcel_gis_preview_in_form',
                           self.parcel_gis_preview_in_form)
