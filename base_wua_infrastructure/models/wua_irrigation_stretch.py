# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WuaIrrigationStretch(models.Model):
    _name = 'wua.irrigation.stretch'
    _description = 'Irrigation Irrigation Stretch'
    _order = 'id'

    type = fields.Selection([
        ('pressure', 'Pressure'),
        ('gravity', 'Gravity'),
    ], string='Segment Type', required=True)

    name = fields.Char(
        string='Segment Identifier',
        required=True,
        unique=True,
    )

    length_meters = fields.Float(
        string='Length',
        digits=(32, 4),
    )

    roughness_coefficient = fields.Float(
        string='Roughness Coefficient',
        digits=(32, 4),
    )

    tag = fields.Char(
        string='Tag',
    )

    description = fields.Char(
        string='Description',
    )

    material = fields.Char(
        string='Material',
    )

    nominal_diameter = fields.Integer(
        string='Nominal Diameter',
    )

    pipe_specification = fields.Char(
        string='Pipe Specification',
    )

    pipe_section = fields.Char(
        string='Pipe Section',
    )

    manufacturer = fields.Char(
        string='Manufacturer',
    )

    brand = fields.Char(
        string='Brand',
    )

    model = fields.Char(
        string='Model',
    )

    technical_sheet = fields.Char(
        string='Technical Sheet',
    )

    installation_date = fields.Date(
        string='Installation Date',
    )

    observations = fields.Text(
        string='Observations',
    )

    notes = fields.Text(
        string='Notes',
    )

    incident_code = fields.Char(
        string='Incident Code',
    )

    nominal_pressure = fields.Char(
        string='Nominal Pressure',
    )

    external_diameter = fields.Float(
        string='External Diameter',
        digits=(32, 4),
    )

    photo_01 = fields.Binary(
        string='Photo 1',
    )

    photo_02 = fields.Binary(
        string='Photo 2',
    )

    photo_url = fields.Char(
        string='Photo URL',
    )

    channel_section_width = fields.Float(
        string='Channel Width',
        digits=(32, 4),
    )

    channel_section_height = fields.Float(
        string='Channel Height',
        digits=(32, 4),
    )

    is_channel_covered = fields.Boolean(
        string='Is Covered (Piped)',
        help='Indicates whether the gravity segment is enclosed (piped)',
    )

    channel_cross_section_area = fields.Float(
        string='Cross Section Area',
        digits=(32, 4),
        compute='_compute_channel_cross_section_area',
        store=True,
        readonly=True,
    )

    @api.depends('channel_section_width', 'channel_section_height')
    def _compute_channel_cross_section_area(self):
        for record in self:
            record.channel_cross_section_area = (
                record.channel_section_width * record.channel_section_height
                if record.channel_section_width and
                record.channel_section_height
                else 0.0
            )
