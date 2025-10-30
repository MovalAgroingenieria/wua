# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class MeasurementDeviceSensor(models.Model):
    _inherit = 'mdm.measurement.device.sensor'

    reservoir_id = fields.Many2one(
        string='Reservoir',
        comodel_name='wua.reservoir',
        ondelete="set null",
    )
