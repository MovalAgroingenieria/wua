# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WuaAgriculturalseason(models.Model):
    _name = 'wua.agriculturalseason'
    _description = 'Agricultural Seasons'
    _order = 'name'

    # Size of fields "name" and "description".
    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 75

    initial_date = fields.Date(
        string='Initial Date',
        default=lambda self: fields.datetime.now(),
        required=True)

    end_date = fields.Date(
        string='End Date',
        default=lambda self: fields.datetime.now() + timedelta(days=364),
        required=True)

    name = fields.Char(
        string='Agricultural Season',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    description = fields.Char(
        string='Description',
        required=True,
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    wateringperiod_ids = fields.One2many(
        string='Watering Periods',
        comodel_name='wua.wateringperiod',
        inverse_name='agriculturalseason_id')

    number_of_periods = fields.Integer(
        string='Number of periods',
        store=True,
        compute='_compute_number_of_periods')

    watering_ids = fields.One2many(
        string='Waterings',
        comodel_name='wua.watering',
        inverse_name='agriculturalseason_id')

    number_of_waterings = fields.Integer(
        string='Number of waterings',
        store=True,
        compute='_compute_number_of_waterings')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Agricultural Season.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('initial_date')
    def _compute_name(self):
        for record in self:
            record.name = record.initial_date

    @api.depends('wateringperiod_ids')
    def _compute_number_of_periods(self):
        for record in self:
            record.number_of_periods = \
                len(record.wateringperiod_ids)

    @api.depends('watering_ids')
    def _compute_number_of_waterings(self):
        for record in self:
            record.number_of_waterings = \
                len(record.watering_ids)

    @api.constrains('description')
    def _check_name(self):
        description_no_blanks = self.description.strip()
        if description_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value (description).'))

    @api.model
    def create(self, vals):
        self.refine_description(vals)
        return super(WuaAgriculturalseason, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'description' in vals:
            self.refine_description(vals)
        return super(WuaAgriculturalseason, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.end_date, '%Y-%m-%d').strftime('%x')
            if record.description != '':
                name = initial_date_str + ' - ' + end_date_str + ' ' + \
                    '(' + record.description + ')'
            else:
                name = name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def action_see_waterings(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_form').id
        id_tree_view = self.env.ref('base_wua_gravity_irrigation.'
                                    'wua_watering_view_tree').id
        search_view = self.env.ref('base_wua_gravity_irrigation.'
                                   'wua_watering_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Waterings'),
            'res_model': 'wua.watering',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            'context': {'search_default_watering_period': 1},
            }
        return act_window

    def refine_description(self, vals):
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})
