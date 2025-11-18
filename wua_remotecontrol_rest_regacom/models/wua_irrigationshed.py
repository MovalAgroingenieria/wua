# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'

    regacom_enabled = fields.Boolean(
        string='Regacom Telecontrol',
        default=False,
        help='Enable Regacom remote control integration for this '
             'irrigation shed',
    )

    regacom_dirum = fields.Integer(
        string='Regacom DirUM',
        help='Management unit directory identifier in Regacom database '
             '(HIRU_nDirUM / HIRUC_nDirUM)',
    )

    regacom_diriru = fields.Integer(
        string='Regacom DirIRU',
        help='Hydrant/device directory identifier in Regacom database '
             '(HIRU_nDirIRU / HIRUC_nDirIRU)',
    )
