# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import datetime
import pytz


class WuaPhotovoltaicmeasurement(models.Model):
    _name = 'wua.photovoltaicmeasurement'
    _description = 'Entity (photovoltaicmeasurement)'
    _order = 'measurement_time desc'

    MAX_NAME_SIZE = 30

    photovoltaicplant_id = fields.Many2one(
        string='Photovoltaic Plant',
        comodel_name='wua.photovoltaicplant',
        index=True,
        required=True,
        ondelete="restrict",
    )

    measurement_time = fields.Datetime(
        string='Instant',
        required=True,
        index=True,
    )

    name = fields.Char(
        string='Measurement',
        size=MAX_NAME_SIZE,
        store=True,
        compute='_compute_name',
        index=True,
    )

    generated_power = fields.Float(
        string="Generated Power (kW)",
        digits=(32, 2),
        default=0.0,
        required=True,
        index=True,
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        compute="_compute_agriculturalseason_id",
        store=True,
        index=True,
        ondelete="set null"
    )

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        compute="_compute_of_active_agriculturalseason",
        store=True,
    )

    is_last_measurement = fields.Boolean(
        string="Last Measurement",
        compute="_compute_is_last_measurement",
    )

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing photovoltaic measurement.'),
        ('positive_generated_power',
         'CHECK (generated_power >= 0)',
         'Generated power cannot be a negative value.'),
    ]

    @api.depends('photovoltaicplant_id', 'measurement_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.photovoltaicplant_id and record.measurement_time:
                name = str(
                    record.photovoltaicplant_id.photovoltaicplant_code).\
                    zfill(6) + ' - ' + record.measurement_time
            record.name = name

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

    # Dont update on agriculturalseason_id.active_agroculturalseason
    # this will be do by the agriculturalseason_id on a SQL query
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
            if (record.measurement_time ==
                    record.photovoltaicplant_id.last_measurement_time):
                record.is_last_measurement = True
            else:
                record.is_last_measurement = False

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = ''
            if (record.photovoltaicplant_id.name and
                    record.photovoltaicplant_id.photovoltaicplant_code and
                    record.measurement_time):
                measurement_time = \
                    fields.Datetime.from_string(record.measurement_time)
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(measurement_time)
                    measurement_time = measurement_time + offset
                measurement_time_str = str(measurement_time)
                date_str = measurement_time_str[:10]
                hour_str = measurement_time_str[-8:]
                date_str_localized = self.env['wua.parcel'].\
                    transform_date_to_locale(date_str)
                measurement_time_formatted = \
                    date_str_localized + ' ' + hour_str
                name = record.photovoltaicplant_id.name + ' ' + \
                    '[' + str(record.photovoltaicplant_id.
                              photovoltaicplant_code) + '] - ' + \
                    measurement_time_formatted
            result.append((record.id, name))
        return result

    @api.multi
    def action_see_pumpgroups(self):
        self.ensure_one()
        condition = [('photovoltaicplant_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_infrastructure_pump.'
                                    'wua_pumpgroup_view_form').id
        id_tree_view = \
            self.env.ref('base_wua_infrastructure_pump.'
                         'wua_pumpgroup_view_tree').id
        search_view = self.env.ref('base_wua_infrastructure_pump.'
                                   'wua_pumpgroup_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Pumpgroups'),
            'res_model': 'wua.pumpgroup',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window

    def action_assign_agriculturalseason_to_photovoltaicmeasurements(self):
        measurement_title = self.env['wua.parcel'].get_value_from_translation(
            'base_wua_pressurized_irrigation_photovoltaic_monitoring',
            'Measurements'
        )
        if not measurement_title:
            measurement_title = _('Measurements')
        all_measurements = self.env['wua.photovoltaicmeasurement'].search([])
        if all_measurements:
            all_measurements._compute_agriculturalseason_id()
        return {
            'type': 'ir.actions.act_window',
            'name': measurement_title,
            'res_model': 'wua.photovoltaicmeasurement',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
        }
