# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class MeasurementDeviceSensorType(models.Model):
    _inherit = 'mdm.measurement.device.sensor.type'

    requires_exclusivity = fields.Boolean(
        string='Requires exclusivity (y/n)',
        default=False,
        help='If enabled, only one sensor of this type may coexist in the '
             'same parcel.',
    )
