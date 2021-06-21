# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, _


class WuaPumpgroupmeasurement(models.Model):
    _name = 'wua.pumpgroupmeasurement'
    _description = 'Entity (pumpgroupmeasurement)'
    _order = 'pumpgroup_code, measurement_time desc'

    pumpgroup_id = fields.Many2one(
        string="Pump Group",
        comodel_name="wua.pumpgroup",
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    measurement_time = fields.Datetime(
        string="Time",
        required=True,
        index=True)

    pumpgroup_code = fields.Integer(
        string='Code',
        store=True,
        compute='_compute_pumpgroup_code',
        index=True)

    name = fields.Char(
        string="Measurement",
        size=30,
        store=True,
        index=True,
        compute="_compute_name")

    instantaneous_flow = fields.Float(
        string="Instantaneous Flow (m³/h)",
        required=True,
        digits=(32, 2),
        help="Instantaneous flow in the pumping outlet pipe, in m³/h.")

    suction_pressure = fields.Float(
        string="Suction Presure (mwc)",
        required=True,
        digits=(32, 2),
        default=0,
        help="Suction pressure of the pumping, in mwc.")

    impulsion_pressure = fields.Float(
        string="Impulsion Pressure (mwc)",
        required=True,
        digits=(32, 2),
        help="Pumping impulse pressure, in mwc.")

    consumed_power = fields.Float(
        string="Consumed Power (kW)",
        required=True,
        digits=(32, 2),
        default=0,
        help="Consumed electrical power, in kW.")

    calculated_consumed_power = fields.Float(
        string="Consumed Power (kW)",
        compute="_compute_calculated_consumed_power")

    consumed_energy = fields.Float(
        string="Consumed Energy (kWh)",
        required=True,
        digits=(32, 2),
        default=0,
        help="Consumed electrical energy, in kWh.")

    agriculturalseason_id = fields.Many2one(
        string="Agricultural Season",
        comodel_name="wua.agriculturalseason",
        store=True,
        index=True,
        compute="_compute_agriculturalseason_id",
        ondelete='set null')

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    is_last_measurement = fields.Boolean(
        string="Last Measurement",
        compute="_compute_is_last_measurement")

    specific_consumption = fields.Float(
        string="Specific Consumption (kWh/m³)",
        digits=(32, 2),
        compute="_compute_specific_consumption",
        help="Ratio between consumed power and flow.")

    electrical_voltage = fields.Float(
        string="Electrical Voltage (V)",
        required=True,
        digits=(32, 2),
        default=0)

    amperage = fields.Float(
        string="Amperage (A)",
        required=True,
        digits=(32, 2),
        default=0)

    phi_cosine = fields.Float(
        string="Phi Cosine",
        required=True,
        digits=(32, 2),
        default=0)

    manometric_height = fields.Float(
        string="Manometric Height (mwc)",
        digits=(32, 2),
        store=True,
        compute="_compute_manometric_height")

    supplied_power = fields.Float(
        string="Supplied Power (kW)",
        digits=(32, 2),
        store=True,
        compute="_compute_supplied_power")

    energy_efficiency = fields.Float(
        string="Energy Efficiency (%)",
        digits=(32, 2),
        store=True,
        compute="_compute_energy_efficiency")

    energy_efficiency_rating = fields.Selection(
        [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")],
        string="Energy Efficiency Rating",
        store=True,
        compute="_compute_energy_efficiency_rating")

    energy_efficiency_rating_with_desc = fields.Char(
        string="Energy Efficiency Rating",
        compute="_compute_energy_efficiency_rating_with_desc",
        help="Pumping energy rating with descriptive clarification.")

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing measurement.'),
        ('valid_instantaneous_flow',
         'CHECK (instantaneous_flow >= 0)',
         'The instantaneous flow must be a value zero or positive.'),
        ('valid_impulsion_pressure',
         'CHECK (impulsion_pressure >= 0)',
         'The impulsion pressure must be a value zero or positive.'),
        ('valid_consumed_power',
         'CHECK (consumed_power >= 0)',
         'The consumed power must be a value zero or positive.'),
        ('valid_consumed_energy',
         'CHECK (consumed_energy >= 0)',
         'The consumed energy must be a value zero or positive.'),
        ('valid_amperage',
         'CHECK (amperage >= 0)',
         'The amperage must be a value zero or positive.'),
        ('valid_electrical_voltage',
         'CHECK (electrical_voltage >= 0)',
         'The electrical voltage must be a value zero or positive.'),
        ('valid_phi_cosine',
         'CHECK (phi_cosine >= -1 and phi_cosine <= 1)',
         'The phi_cosine must be between -1 and 1.'),
        ]

    @api.depends('pumpgroup_id', 'pumpgroup_id.pumpgroup_code')
    def _compute_pumpgroup_code(self):
        for record in self:
            pumpgroup_code = 0
            if record.pumpgroup_id:
                pumpgroup_code = record.pumpgroup_id.pumpgroup_code
            record.pumpgroup_code = pumpgroup_code

    @api.depends('pumpgroup_id', 'pumpgroup_id.pumpgroup_code',
                 'measurement_time')
    def _compute_name(self):
        for record in self:
            if record.pumpgroup_id and record.pumpgroup_id.pumpgroup_code \
                    and record.measurement_time:
                pumpgroup_code = \
                    str(record.pumpgroup_id.pumpgroup_code).zfill(6)
                record.name = pumpgroup_code + ' - ' + record.measurement_time

    @api.depends('consumed_power')
    def _compute_calculated_consumed_power(self):
        for record in self:
            record.calculated_consumed_power = record.consumed_power

    @api.depends('measurement_time')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.measurement_time:
                agriculturalseasons = self.env['wua.agriculturalseason'].\
                    search(
                    [('initial_date', '<=', record.measurement_time),
                     ('end_date', '>=', record.measurement_time)])
                if len(agriculturalseasons) == 1:
                    agriculturalseason_id = agriculturalseasons[0]
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id:
                of_active_agriculturalseason = record.agriculturalseason_id.\
                    active_agriculturalseason
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.multi
    def _compute_is_last_measurement(self):
        for record in self:
            if record.measurement_time == \
                    record.pumpgroup_id.last_measurement_time:
                record.is_last_measurement = True
            else:
                record.is_last_measurement = False

    @api.depends('consumed_power', 'instantaneous_flow')
    def _compute_specific_consumption(self):
        for record in self:
            specific_consumption = 0
            consumed_power = record.consumed_power
            instantaneous_flow = record.instantaneous_flow
            if instantaneous_flow > 0:
                specific_consumption = consumed_power / instantaneous_flow
            record.specific_consumption = specific_consumption

    @api.depends('impulsion_pressure', 'suction_pressure')
    def _compute_manometric_height(self):
        for record in self:
            # Check no negative value
            record.manometric_height = \
                max(record.impulsion_pressure - record.suction_pressure, 0.00)

    @api.depends('instantaneous_flow', 'manometric_height')
    def _compute_supplied_power(self):
        for record in self:
            record.supplied_power = 9.81 * record.manometric_height * \
                record.instantaneous_flow / 3600

    @api.depends('supplied_power', 'consumed_power')
    def _compute_energy_efficiency(self):
        for record in self:
            energy_efficiency = 0
            supplied_power = record.supplied_power
            consumed_power = record.consumed_power
            if consumed_power > 0:
                energy_efficiency = supplied_power / consumed_power
                if energy_efficiency > 1:
                    energy_efficiency = 1
                energy_efficiency = 100 * energy_efficiency
            record.energy_efficiency = energy_efficiency

    @api.depends('energy_efficiency')
    def _compute_energy_efficiency_rating(self):
        model_values = self.env['ir.values'].sudo()
        limit_energy_efficiency_d = model_values.get_default(
            'wua.infrastructure.configuration', 'limit_energy_efficiency_d')
        limit_energy_efficiency_c = model_values.get_default(
            'wua.infrastructure.configuration', 'limit_energy_efficiency_c')
        limit_energy_efficiency_b = model_values.get_default(
            'wua.infrastructure.configuration', 'limit_energy_efficiency_b')
        limit_energy_efficiency_a = model_values.get_default(
            'wua.infrastructure.configuration', 'limit_energy_efficiency_a')
        for record in self:
            energy_efficiency_rating = 'E'
            energy_efficiency = record.energy_efficiency
            if energy_efficiency > 0:
                if energy_efficiency > limit_energy_efficiency_a:
                    energy_efficiency_rating = 'A'
                else:
                    if energy_efficiency >= limit_energy_efficiency_b:
                        energy_efficiency_rating = 'B'
                    else:
                        if energy_efficiency >= limit_energy_efficiency_c:
                            energy_efficiency_rating = 'C'
                        else:
                            if energy_efficiency >= limit_energy_efficiency_d:
                                energy_efficiency_rating = 'D'
            record.energy_efficiency_rating = energy_efficiency_rating

    @api.multi
    def _compute_energy_efficiency_rating_with_desc(self):
        for record in self:
            energy_efficiency_rating_with_desc = _('E (unnaceptable)')
            if record.energy_efficiency_rating == 'D':
                energy_efficiency_rating_with_desc = _('D (acceptable)')
            if record.energy_efficiency_rating == 'C':
                energy_efficiency_rating_with_desc = _('C (normal)')
            if record.energy_efficiency_rating == 'B':
                energy_efficiency_rating_with_desc = _('B (good)')
            if record.energy_efficiency_rating == 'A':
                energy_efficiency_rating_with_desc = _('A (optimal)')
            record.energy_efficiency_rating_with_desc = \
                energy_efficiency_rating_with_desc

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.pumpgroup_id and record.measurement_time:
                if record.pumpgroup_id.pumpgroup_code > 0:
                    measurement_name = \
                        record.pumpgroup_id.name + ' [' + \
                        str(record.pumpgroup_id.pumpgroup_code) + ']'
                else:
                    measurement_name = record.name
                measurement_time = \
                    fields.Datetime.from_string(record.measurement_time)
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(measurement_time)
                    measurement_time = measurement_time + offset
                measurement_time_str = str(measurement_time)
                date_str = measurement_time_str[:10]
                hour_str = measurement_time_str[-8:]
                name = measurement_name + ' - ' + \
                    datetime.datetime.strptime(
                        date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
                result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        self._process_vals(vals)
        return super(WuaPumpgroupmeasurement, self).create(vals)

    @api.multi
    def write(self, vals):
        self._process_vals(vals)
        super(WuaPumpgroupmeasurement, self).write(vals)
        return True

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'instantaneous_flow' in fields:
            fields.remove('instantaneous_flow')
        if 'impulsion_pressure' in fields:
            fields.remove('impulsion_pressure')
        if 'suction_pressure' in fields:
            fields.remove('suction_pressure')
        if 'manometric_height' in fields:
            fields.remove('manometric_height')
        if 'supplied_power' in fields:
            fields.remove('supplied_power')
        if 'consumed_power' in fields:
            fields.remove('consumed_power')
        if 'energy_efficiency' in fields:
            fields.remove('energy_efficiency')
        return super(WuaPumpgroupmeasurement, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    def _process_vals(self, vals):
        model_values = self.env['ir.values'].sudo()
        threshold_pump_flow = 0
        threshold_pump_pressure = 0
        threshold_pump_power = 0
        threshold_pump_energy = 0
        threshold_pump_flow_in_values = model_values.get_default(
            'wua.infrastructure.configuration', 'threshold_pump_flow')
        threshold_pump_pressure_in_values = model_values.get_default(
            'wua.infrastructure.configuration', 'threshold_pump_pressure')
        threshold_pump_power_in_values = model_values.get_default(
            'wua.infrastructure.configuration', 'threshold_pump_power')
        threshold_pump_energy_in_values = model_values.get_default(
            'wua.infrastructure.configuration', 'threshold_pump_energy')
        if threshold_pump_flow_in_values:
            threshold_pump_flow = threshold_pump_flow_in_values
        if threshold_pump_pressure_in_values:
            threshold_pump_pressure = threshold_pump_pressure_in_values
        if threshold_pump_power_in_values:
            threshold_pump_power = threshold_pump_power_in_values
        if threshold_pump_energy_in_values:
            threshold_pump_energy = threshold_pump_energy_in_values
        if 'instantaneous_flow' in vals and \
                vals['instantaneous_flow'] < threshold_pump_flow:
            vals.update({'instantaneous_flow': 0})
        if 'suction_pressure' in vals:
            suction_pressure_abs_value = abs(vals['suction_pressure'])
            if suction_pressure_abs_value < threshold_pump_pressure:
                vals.update({'suction_pressure': 0})
        if 'impulsion_pressure' in vals and \
                vals['impulsion_pressure'] < threshold_pump_pressure:
            vals.update({'impulsion_pressure': 0})
        if 'consumed_power' in vals and \
                vals['consumed_power'] < threshold_pump_power:
            vals.update({'consumed_power': 0})
        if 'consumed_energy' in vals and \
                vals['consumed_energy'] < threshold_pump_energy:
            vals.update({'consumed_energy': 0})

    def action_assign_agseason_and_efrating_to_pumpgroupmeasurements(self):
        all_measurements = self.env['wua.pumpgroupmeasurement'].search([])
        if all_measurements:
            all_measurements._compute_agriculturalseason_id()
            all_measurements._compute_energy_efficiency_rating()
