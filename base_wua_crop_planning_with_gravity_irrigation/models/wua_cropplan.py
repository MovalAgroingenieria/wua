# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaEnrolledsubparcel(models.Model):
    _inherit = 'wua.enrolledsubparcel'

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute='_compute_irrigationditch_id')

    @api.depends('parcel_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            irrigationditch_id = None
            if (record.parcel_id):
                irrigationditch_id = record.parcel_id.irrigationditch_id
            record.irrigationditch_id = irrigationditch_id
