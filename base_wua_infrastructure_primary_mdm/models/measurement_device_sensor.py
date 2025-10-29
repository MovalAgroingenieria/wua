# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields


class MeasurementDeviceSensor(models.Model):
    _inherit = 'mdm.measurement.device.sensor'

    flowmeter_id = fields.Many2one(
        string='Flowmeter',
        comodel_name='wua.flowmeter',
        ondelete="set null",
    )
