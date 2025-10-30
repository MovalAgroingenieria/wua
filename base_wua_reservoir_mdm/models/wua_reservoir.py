# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaReservoir(models.Model):
    _inherit = 'wua.reservoir'

    sensor_ids = fields.One2many(
        string='Sensors',
        comodel_name='mdm.measurement.device.sensor',
        inverse_name='reservoir_id',
    )
