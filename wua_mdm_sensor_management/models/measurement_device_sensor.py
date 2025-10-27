from odoo import models, fields, api, exceptions, _

class MdmMeasurementDeviceSensor(models.Model):
    _inherit = "mdm.measurement.device.sensor"

    requires_exclusivity = fields.Boolean(
        string="Requires exclusivity (y/n)",
        related="type_id.requires_exclusivity",
        store=True,
        help="Copied from the sensor type."
    )

    @api.constrains('requires_exclusivity', 'type_id', 'device_id')
    def _check_requires_exclusivity(self):
        for record in self:
            if not record.requires_exclusivity:
                continue
            # Search for other sensors for a device with the same type requiring exclusivity
            domain = [
                ('id', '!=', record.id),
                ('device_id', '=', record.device_id.id),
                ('type_id', '=', record.type_id.id),
                ('requires_exclusivity', '=', True),
            ]
            existing_exclusive = self.search(domain, limit=1)
            if existing_exclusive:
                raise exceptions.ValidationError(
                    _('A sensor of type "%s" already exists in device "%s", and only one is allowed.')
                    % (record.type_id.display_name, record.device_id.display_name)
                )
