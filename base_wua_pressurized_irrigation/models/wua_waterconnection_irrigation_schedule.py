# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterconnectionIrrigationSchedule(models.Model):
    _name = 'wua.waterconnection.irrigation.schedule'
    _description = 'Entity (waterconnection irrigation schedule)'
    _order = 'name'

    # TODO Max Size Name:
    MAX_SIZE_NAME = 52

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        ondelete='cascade',
    )

    irrigation_start_day = fields.Selection(
        [
            ('00_monday', 'Monday'),
            ('01_tuesday', 'Tuesday'),
            ('02_wednesday', 'Wednesday'),
            ('03_thursday', 'Thursday'),
            ('04_friday', 'Friday'),
            ('05_saturday', 'Saturday'),
            ('06_sunday', 'Sunday'),
        ],
        string='Irrigation Start Day',
        required=True,
        default='00_monday',
    )

    irrigation_start_hour = fields.Float(
        string='Irrigation Start Hour',
        digits=(32, 2),
        required=True,
    )

    irrigation_end_hour = fields.Float(
        string='Irrigation End Hour',
        digits=(32, 2),
        required=True,
    )

    irrigation_duration = fields.Float(
        string='Irigation Duration',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    shift_number = fields.Integer(
        string='Shift Number',
        required=True,
        default=1,
    )

    max_irrigation_volume = fields.Float(
        string='Max Irrigation Volume (m³)',
        digits=(32, 2),
        default=0.0,
    )

    state = fields.Selection(
        [('00_inactive', 'Inactive'),
         ('01_active', 'Active'), ],
        string='State',
        required=True,
        default='01_active',
    )

    name = fields.Char(
        string='Schedule Data',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Irrigation Schedule.'),
        ]

    @api.depends('waterconnection_id', 'irrigation_start_day', 'shift_number')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.waterconnection_id and record.irrigation_start_day and \
                    record.shift_number:
                value = record.waterconnection_id.name + u'-' + \
                    record.irrigation_start_day + u'-' + str(
                        record.shift_number).zfill(2)
            record.name = value
