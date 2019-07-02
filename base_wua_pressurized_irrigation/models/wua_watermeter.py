# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWatermeter(models.Model):
    _name = 'wua.watermeter'
    _description = 'Entity (water meter)'
    _order = 'name'

    # Size of field "name".
    MAX_SIZE_NAME = 30

    def _default_type(self):
        resp = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'default_watermeter_type')
        return resp

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('stored', 'Stored'),
        ('discarted', 'Discarted')],
        string='State',
        required=True,
        default='active')

    nominal_diameter = fields.Integer(
        string='Nominal Diameter',
        required=True,
        default=0)

    nominal_water_flow = fields.Float(
        string='Water Flow (m3/hour)',
        digits=(32, 2),
        required=True,
        default=0)

    pressure = fields.Float(
        string='Pressure (bar)',
        digits=(32, 2),
        required=True,
        default=0)

    type = fields.Selection([
        ('undefined', 'Undefined'),
        ('multistream', 'Multi-stream'),
        ('woltmann', 'Woltmann'),
        ('electromagnetic', 'Electromagnetic'),
        ('ultrasonic', 'Ultrasonic')],
        string='Type',
        required=True,
        default=_default_type)

    last_reading_time = fields.Datetime(
        string='Last Reading Time')

    last_reading_value = fields.Float(
        string='Last Reading Value',
        digits=(32, 4))

    waterconnection_ids = fields.One2many(
        string='Water Connections',
        comodel_name='wua.waterconnection',
        inverse_name='watermeter_id')

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_waterconnection_id',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_irrigationshed_id',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulicsector_id',
        ondelete='restrict')

    wcwm_ids = fields.One2many(
        string='Assigned Water Connections',
        comodel_name='wua.wc.wm',
        inverse_name='watermeter_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('valid_nominal_diameter',
         'CHECK (nominal_diameter >= 0)',
         'The nominal diameter can not be a negative value.'),
        ('valid_nominal_water_flow',
         'CHECK (nominal_water_flow >= 0)',
         'The nominal water flow can not be a negative value.'),
        ('valid_pressure',
         'CHECK (pressure >= 0)',
         'The pressure can not be a negative value.'),
        ]

    @api.depends('waterconnection_ids')
    def _compute_waterconnection_id(self):
        for record in self:
            waterconnection_id = None
            filtered_waterconnections = \
                self.env['wua.waterconnection'].search([
                    ('watermeter_id', '=', record.id)])
            if len(filtered_waterconnections) == 1:
                waterconnection_id = filtered_waterconnections[0].id
            record.waterconnection_id = waterconnection_id

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            irrigationshed_id = None
            if record.waterconnection_id:
                irrigationshed_id = \
                    record.waterconnection_id.irrigationshed_id
            record.irrigationshed_id = irrigationshed_id

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if record.waterconnection_id:
                hydraulicsector_id = \
                    record.waterconnection_id.hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.multi
    def action_see_readings(self):
        self.ensure_one()
        condition = [('watermeter_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_reading_view_form').id
        id_tree_view = self.env.ref('base_wua_pressurized_irrigation.'
                                    'wua_reading_one_watermeter_view_tree').id
        search_view = self.env.ref('base_wua_pressurized_irrigation.'
                                   'wua_reading_one_watermeter_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Readings'),
            'res_model': 'wua.reading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
