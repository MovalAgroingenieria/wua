# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class MdmMeasurementDeviceSensor(models.Model):
    _inherit = 'mdm.measurement.device.sensor'

    requires_exclusivity = fields.Boolean(
        string='Requires exclusivity (y/n)',
        related='type_id.requires_exclusivity',
        store=True,
        help='Copied from the sensor type.',
    )
    has_range_validation = fields.Boolean(
        string='Range validation',
        default=False,
        help='If enabled, this sensor validates readings against a '
             'min/max range regardless of the sensor type setting.',
    )
    has_custom_range = fields.Boolean(
        string='Custom range',
        default=False,
        help='If enabled, this sensor uses its own min/max values instead '
             'of those defined at the sensor type level.',
    )
    custom_min_value = fields.Float(
        string='Custom minimum value',
        digits=(32, 4),
        help='Lower bound specific to this sensor. Only applies when '
             'custom range is enabled.',
    )
    custom_max_value = fields.Float(
        string='Custom maximum value',
        digits=(32, 4),
        help='Upper bound specific to this sensor. Only applies when '
             'custom range is enabled.',
    )
    effective_has_validation = fields.Boolean(
        string='Effective validation',
        store=True,
        compute='_compute_effective_range',
        readonly=True,
        help='Resolved validation flag: True if this sensor or its type '
             'has range validation enabled.',
    )
    effective_min_value = fields.Float(
        string='Effective minimum',
        digits=(32, 4),
        store=True,
        compute='_compute_effective_range',
        readonly=True,
        help='Resolved minimum value: custom range if enabled, otherwise '
             'the sensor type minimum.',
    )
    effective_max_value = fields.Float(
        string='Effective maximum',
        digits=(32, 4),
        store=True,
        compute='_compute_effective_range',
        readonly=True,
        help='Resolved maximum value: custom range if enabled, otherwise '
             'the sensor type maximum.',
    )

    @api.onchange('has_range_validation')
    def _onchange_has_range_validation(self):
        """Auto-enable custom range when sensor-level validation is activated."""
        if self.has_range_validation:
            self.has_custom_range = True

    @api.onchange('has_custom_range')
    def _onchange_has_custom_range(self):
        """Clear custom min/max in the UI when custom range is disabled."""
        if not self.has_custom_range:
            self.custom_min_value = 0.0
            self.custom_max_value = 0.0

    @api.multi
    def write(self, vals):
        sensor_range_fields = {
            'has_range_validation', 'has_custom_range',
            'custom_min_value', 'custom_max_value',
        }
        range_fields_changed = bool(sensor_range_fields & set(vals))
        res = super(MdmMeasurementDeviceSensor, self).write(vals)
        if range_fields_changed:
            for record in self:
                _logger.info(
                    'write: range fields changed on sensor %s (%s), '
                    'triggering reading recompute', record.id, record.name
                )
                record.action_recompute_sensor_readings_range_status()
        return res

    @api.multi
    def action_recompute_sensor_readings_range_status(self):
        """
        Batch-recompute is_out_of_range and range_status for all readings
        of this sensor. Reads the effective_* fields already stored on the
        sensor, so it handles both enabling and disabling correctly.
        """
        self.ensure_one()
        Reading = self.env['mdm.measurement.device.sensor.reading']
        readings = Reading.search([('sensor_id', '=', self.id)])
        if not readings:
            return
        _logger.info(
            'action_recompute_sensor_readings_range_status: processing %d '
            'readings for sensor %s (%s)',
            len(readings), self.id, self.name
        )
        ids_normal = []
        ids_low = []
        ids_high = []
        ids_unchecked = []
        has_validation = self.effective_has_validation
        min_value = self.effective_min_value
        max_value = self.effective_max_value
        for record in readings:
            if not has_validation:
                ids_unchecked.append(record.id)
            elif record.value < min_value:
                ids_low.append(record.id)
            elif record.value > max_value:
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
            'action_recompute_sensor_readings_range_status: done. '
            'normal=%d low=%d high=%d unchecked=%d',
            len(ids_normal), len(ids_low), len(ids_high), len(ids_unchecked)
        )

    @api.multi
    @api.depends(
        'has_range_validation',
        'has_custom_range',
        'custom_min_value',
        'custom_max_value',
        'type_id.has_range_validation',
        'type_id.min_value',
        'type_id.max_value',
    )
    def _compute_effective_range(self):
        for record in self:
            effective_has_validation = (
                record.has_range_validation
                or record.type_id.has_range_validation
            )
            if record.has_custom_range:
                effective_min_value = record.custom_min_value
                effective_max_value = record.custom_max_value
            else:
                effective_min_value = record.type_id.min_value
                effective_max_value = record.type_id.max_value
            record.effective_has_validation = effective_has_validation
            record.effective_min_value = effective_min_value
            record.effective_max_value = effective_max_value
