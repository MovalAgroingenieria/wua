# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class MdmMeasurementDeviceSensor(models.Model):
    _inherit = 'mdm.measurement.device.sensor'

    requires_exclusivity = fields.Boolean(
        string='Requires exclusivity (y/n)',
        related='type_id.requires_exclusivity',
        store=True,
        help='Copied from the sensor type.',
    )
