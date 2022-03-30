# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaEnrolledsubparcel(models.Model):
    _inherit = 'wua.enrolledsubparcel'

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        related='parcel_id.irrigationditch_id')
