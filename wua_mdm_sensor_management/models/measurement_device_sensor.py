from odoo import models, fields, api, exceptions, _


class MdmMeasurementDeviceSensor(models.Model):
    _inherit = 'mdm.measurement.device.sensor'

    requires_exclusivity = fields.Boolean(
        string='Requires exclusivity (y/n)',
        related='type_id.requires_exclusivity',
        store=True,
        help='Copied from the sensor type.',
    )
