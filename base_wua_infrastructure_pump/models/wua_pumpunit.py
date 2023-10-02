# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPumpunit(models.Model):
    _name = 'wua.pumpunit'
    _description = 'Entity (pumpunit)'
    _order = 'pumpunit_number'

    pumpunit_number = fields.Integer(
        string='Pump N.',
        required=True,
        index=True,
    )

    pumpgroup_id = fields.Many2one(
        string='Pump Group',
        comodel_name='wua.pumpgroup',
        required=True,
        index=True,
        ondelete='restrict'
    )

    name = fields.Char(
        string='Pump Unit',
        size=15,
        store=True,
        compute='_compute_name',
    )

    pumpunit_alias = fields.Char(
        string='Alias',
        size=50,
        index=True,
    )

    pump_trademark = fields.Char(
        string='Pump Trademark',
        size=40,
        index=True,
    )

    pump_model = fields.Char(
        string='Pump Model',
        size=40,
        index=True,
    )

    engine_trademark = fields.Char(
        string='Engine Trademark',
        size=40,
    )

    engine_model = fields.Char(
        string='Engine Model',
        size=40,
    )

    rpm = fields.Integer(
        string='RPM',
        required=True,
        default=0,
    )

    photo_01 = fields.Binary(
        string='Photo 1',
        attachment=True)

    photo_02 = fields.Binary(
        string='Photo 2',
        attachment=True)

    typology = fields.Selection(
        [
            ('01_vcaldriedengine', 'Vertical Dried Engine'),
            ('02_vcal', 'Vertical'),
            ('03_wellpump', 'Well Pump'),
            ('04_htalsplitcamera', 'Horizontal Split Camera'),
            ('05_htalmonoblock', 'Horizontal Monoblock'),
        ],
        string='Typology',
        required=True,
        index=True,
        default='01_vcaldriedengine',
    )

    nominal_power = fields.Float(
        string='Nominal Power (kW)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    nominal_flow = fields.Float(
        string='Nominal Flow (m³/h)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    nominal_height = fields.Float(
        string='Nominal Height (mca)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    number_of_pumpunits = fields.Integer(
        string='Number of pump units of the pump group',
        compute='_compute_number_of_pumpunits',
        store=False,
    )

    start_and_regulation = fields.Html(
        string='Start and Regulation',
    )

    notes = fields.Html(
        string='Notes',
    )

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing pump unit.'),
        ('correct_pumpunit_number',
         'CHECK (pumpunit_number >= 1 AND '
         'pumpunit_number <= 999999)',
         'Invalid pumpunit number.'),
        ('positive_nominal_flow',
         'CHECK (nominal_flow >= 0)',
         'Nominal flow cannot be a negative value.'),
        ('positive_nominal_height',
         'CHECK (nominal_height >= 0)',
         'Nominal height cannot be a negative value.'),
        ('positive_rpm',
         'CHECK (rpm >= 0)',
         'RPM cannot be a negative value.'),
        ('positive_nominal_power',
         'CHECK (nominal_power >= 0)',
         'Nominal power cannot be a negative value.'),
        ]

    @api.onchange('pumpgroup_id')
    def _onchange_pumpgroup_id(self):
        pumpunit_number = 0
        if (self.pumpgroup_id):
            if (len(self.pumpgroup_id.pumpunit_ids) > 0):
                for pumpunit in self.pumpgroup_id.pumpunit_ids:
                    # Needed for not autocheck myself
                    if (pumpunit.id):
                        pumpunit_number = max(pumpunit_number,
                                              pumpunit.pumpunit_number)
        self.pumpunit_number = pumpunit_number + 1

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.pumpgroup_id:
                pump_label = _('pump')
                pump_alias_value = ''
                if (record.pumpunit_alias):
                    pump_alias_value = record.pumpunit_alias + ', '
                name = record.pumpgroup_id.name + ', ' + \
                    pump_label + u' nº ' + str(record.pumpunit_number) + \
                    ' (' + pump_alias_value + str(record.nominal_flow) + \
                    u' m³/h)'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.multi
    def _compute_number_of_pumpunits(self):
        for record in self:
            number_of_pumpunits = 0
            if record.pumpgroup_id:
                number_of_pumpunits = record.pumpgroup_id.number_of_pumpunits
            record.number_of_pumpunits = number_of_pumpunits

    @api.depends('pumpgroup_id', 'pumpgroup_id.pumpgroup_code',
                 'pumpunit_number')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.pumpgroup_id and record.pumpunit_number:
                name = str(record.pumpgroup_id.pumpgroup_code).zfill(6) + \
                    ' - ' + str(record.pumpunit_number).zfill(6)
            record.name = name
