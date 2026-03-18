# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class MdmMeasurementDeviceSensorReading(models.Model):
    _inherit = 'mdm.measurement.device.sensor.reading'

    is_out_of_range = fields.Boolean(
        string='Out of range',
        store=True,
        index=True,
        compute='_compute_is_out_of_range',
        help='True if the reading value falls outside the effective '
             'min/max range defined for the sensor.',
    )
    range_status = fields.Selection(
        string='Range status',
        selection=[
            ('normal', 'Normal'),
            ('low', 'Below minimum'),
            ('high', 'Above maximum'),
            ('unchecked', 'Not checked'),
        ],
        store=True,
        index=True,
        compute='_compute_is_out_of_range',
        help='Validity status of the reading with respect to the sensor '
             'range: normal, below minimum, above maximum, or not checked '
             '(when range validation is disabled for the sensor).',
    )

    @api.multi
    @api.depends('value', 'sensor_id')
    def _compute_is_out_of_range(self):
        """
        Only recomputes automatically when a reading's value or sensor
        assignment changes. Changes to the sensor type range do NOT trigger
        auto-recompute here (that would cascade over millions of readings).
        Use action_recompute_readings_range_status on the sensor type instead.
        """
        for record in self:
            if not record.sensor_id.effective_has_validation:
                record.range_status = 'unchecked'
                record.is_out_of_range = False
            elif record.value < record.sensor_id.effective_min_value:
                record.range_status = 'low'
                record.is_out_of_range = True
            elif record.value > record.sensor_id.effective_max_value:
                record.range_status = 'high'
                record.is_out_of_range = True
            else:
                record.range_status = 'normal'
                record.is_out_of_range = False
