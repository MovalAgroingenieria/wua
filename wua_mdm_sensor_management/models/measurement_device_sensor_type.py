# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MeasurementDeviceSensorType(models.Model):
    _inherit = 'mdm.measurement.device.sensor.type'

    requires_exclusivity = fields.Boolean(
        string='Requires exclusivity (y/n)',
        default=False,
        help='If enabled, only one sensor of this type may coexist in the '
             'same parcel.',
    )
    has_range_validation = fields.Boolean(
        string='Range validation',
        default=False,
        index=True,
        help='If enabled, readings of sensors of this type will be checked '
             'against the defined min/max values.',
    )
    min_value = fields.Float(
        string='Minimum value',
        digits=(32, 4),
        help='Lower bound for normal readings. Readings below this value '
             'will be flagged as out of range.',
    )
    max_value = fields.Float(
        string='Maximum value',
        digits=(32, 4),
        help='Upper bound for normal readings. Readings above this value '
             'will be flagged as out of range.',
    )

    @api.onchange('has_range_validation')
    def _onchange_has_range_validation(self):
        """Clear min/max values in the UI when validation is disabled."""
        if not self.has_range_validation:
            self.min_value = 0.0
            self.max_value = 0.0

    @api.multi
    def write(self, vals):
        range_fields_changed = bool(
            {'has_range_validation', 'min_value', 'max_value'} & set(vals)
        )
        disabling = 'has_range_validation' in vals and not vals['has_range_validation']
        if disabling:
            vals['min_value'] = 0.0
            vals['max_value'] = 0.0
        res = super(MeasurementDeviceSensorType, self).write(vals)
        if range_fields_changed:
            # After super(), all effective_* fields on sensors are already
            # recomputed (stored). action_recompute_readings_range_status reads
            # effective_has_validation / effective_min / effective_max from
            # the sensor, so it correctly sets 'unchecked' when disabled
            # and low/high/normal when enabled.
            for record in self:
                _logger.info(
                    'write: range fields changed on type %s (%s), '
                    'triggering reading recompute', record.id, record.name
                )
                record.action_recompute_readings_range_status()
        return res

    @api.multi
    def action_recompute_readings_range_status(self):
        """
        Batch-recompute is_out_of_range and range_status for all active
        readings whose sensor belongs to this sensor type.

        This method exists because auto-recomputation via @api.depends is
        intentionally disabled on the reading level (too expensive when a
        type has millions of readings). Call this after changing min_value,
        max_value or has_range_validation on the type.
        """
        self.ensure_one()
        Reading = self.env['mdm.measurement.device.sensor.reading']
        readings = Reading.search(
            [('sensor_id.type_id', '=', self.id)]
        )
        if not readings:
            _logger.info(
                'action_recompute_readings_range_status: no readings found '
                'for sensor type %s (%s)', self.id, self.name
            )
            return
        _logger.info(
            'action_recompute_readings_range_status: processing %d readings '
            'for sensor type %s (%s)', len(readings), self.id, self.name
        )
        ids_normal = []
        ids_low = []
        ids_high = []
        ids_unchecked = []
        sensor_cache = {}
        for record in readings:
            sid = record.sensor_id.id
            if sid not in sensor_cache:
                sensor_cache[sid] = {
                    'has_validation': record.sensor_id.effective_has_validation,
                    'min_value': record.sensor_id.effective_min_value,
                    'max_value': record.sensor_id.effective_max_value,
                }
            sc = sensor_cache[sid]
            if not sc['has_validation']:
                ids_unchecked.append(record.id)
            elif record.value < sc['min_value']:
                ids_low.append(record.id)
            elif record.value > sc['max_value']:
                ids_high.append(record.id)
            else:
                ids_normal.append(record.id)
        cr = self.env.cr
        if ids_normal:
            cr.execute(
                "UPDATE mdm_measurement_device_sensor_reading "
                "SET range_status = 'normal', is_out_of_range = false "
                "WHERE id = ANY(%s)",
                (ids_normal,)
            )
        if ids_low:
            cr.execute(
                "UPDATE mdm_measurement_device_sensor_reading "
                "SET range_status = 'low', is_out_of_range = true "
                "WHERE id = ANY(%s)",
                (ids_low,)
            )
        if ids_high:
            cr.execute(
                "UPDATE mdm_measurement_device_sensor_reading "
                "SET range_status = 'high', is_out_of_range = true "
                "WHERE id = ANY(%s)",
                (ids_high,)
            )
        if ids_unchecked:
            cr.execute(
                "UPDATE mdm_measurement_device_sensor_reading "
                "SET range_status = 'unchecked', is_out_of_range = false "
                "WHERE id = ANY(%s)",
                (ids_unchecked,)
            )
        readings.invalidate_cache(
            ['is_out_of_range', 'range_status'], readings.ids
        )
        _logger.info(
            'action_recompute_readings_range_status: done. '
            'normal=%d low=%d high=%d unchecked=%d',
            len(ids_normal), len(ids_low), len(ids_high), len(ids_unchecked)
        )
