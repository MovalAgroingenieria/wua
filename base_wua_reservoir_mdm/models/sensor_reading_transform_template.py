# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class MdmSensorReadingTransformTemplate(models.Model):
    _inherit = 'mdm.sensor.reading.transform.template'

    def _create_wizard_from_template(self, template):
        """Create a transformation wizard from a template."""
        return self.env['mdm.sensor.reading.transform.wizard'].create({
            'template_id': template.id,
            'name': template.name,
            'use_all_sensors': template.use_all_sensors,
            'sensor_ids': [(6, 0, template.sensor_ids.ids)],
            'sensor_domain_filter': template.sensor_domain_filter,
            'target_model_id': template.target_model_id.id,
            'selection_mode': template.selection_mode,
            'date_from': template.date_from,
            'date_to': template.date_to,
            'reference_date': fields.Datetime.now(),
            'auto_date_from_last_record': (
                template.auto_date_from_last_record
            ),
            'target_date_field_id': (
                template.target_date_field_id.id
                if template.target_date_field_id else False
            ),
            'field_mapping_json': template.field_mapping_json,
            'domain_filter': template.domain_filter,
            'detect_negative_readings': template.detect_negative_readings,
            'negative_model_id': (
                template.negative_model_id.id
                if template.negative_model_id else False
            ),
            'reference_field': template.reference_field,
            'volume_field': template.volume_field,
            'date_field_for_last_reading': (
                template.date_field_for_last_reading
            ),
            'negative_field_mapping_json': (
                template.negative_field_mapping_json
            ),
        })

    @api.model
    def cron_transform_reservoir_readings(self):
        """Transform pressure sensor readings to reservoir readings."""
        # Get reservoir reading template
        reservoir_template = self.env.ref(
            'base_wua_reservoir_mdm.'
            'transform_template_sensor_to_reservoirreading',
            raise_if_not_found=False,
        )
        # Transform reservoir readings
        if reservoir_template:
            wizard = self._create_wizard_from_template(reservoir_template)
            wizard.action_transform()
