# -*- coding: utf-8 -*-
# 2022-2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from odoo import models, fields, api


class WuaElectricitypoint(models.Model):
    _name = 'wua.electricitypoint'
    _description = 'Electricity supply point'
    _order = 'code'
    _rec_name = 'name'

    code = fields.Integer(
        string='Code',
        required=True,
        index=True,
    )

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        size=100,
    )

    cups = fields.Char(
        string='CUPS',
        size=30,
        required=True,
        index=True,
    )

    powerline_ids = fields.One2many(
        string='Power Lines',
        comodel_name='wua.powerline',
        inverse_name='electricitypoint_id',
    )

    number_of_powerlines = fields.Integer(
        string='Number of power lines',
        compute='_compute_number_of_powerlines',
    )

    powerlinesupport_ids = fields.One2many(
        string='Power Line Supports',
        comodel_name='wua.powerlinesupport',
        inverse_name='electricitypoint_id',
    )

    number_of_powerlinesupports = fields.Integer(
        string='Number of power line supports',
        compute='_compute_number_of_powerlinesupports',
    )

    processingcentre_ids = fields.One2many(
        string='Processing Centres',
        comodel_name='wua.processingcentre',
        inverse_name='electricitypoint_id',
    )

    number_of_processingcentres = fields.Integer(
        string='Number of processing centres',
        compute='_compute_number_of_processingcentres',
    )

    notes = fields.Html(
        string='Notes',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'A electricity point with that name already exists.'),
        ]

    @api.depends('powerline_ids')
    def _compute_number_of_powerlines(self):
        for record in self:
            record.number_of_powerlines = len(record.powerline_ids)

    @api.depends('processingcentre_ids')
    def _compute_number_of_processingcentres(self):
        for record in self:
            record.number_of_processingcentres = len(
                record.processingcentre_ids)

    @api.depends('powerlinesupport_ids')
    def _compute_number_of_powerlinesupports(self):
        for record in self:
            record.number_of_powerlinesupports = len(
                record.powerlinesupport_ids)


    def action_show_powerlines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Power Lines',
            'res_model': 'wua.powerline',
            'view_mode': 'tree,form',
            'domain': [('electricitypoint_id', '=', self.id)],
            'context': {'default_electricitypoint_id': self.id},
        }

    def action_show_powerlinesupports(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Line Supports',
            'res_model': 'wua.powerlinesupport',
            'view_mode': 'tree,form',
            'domain': [('electricitypoint_id', '=', self.id)],
            'context': {'default_electricitypoint_id': self.id},
        }

    def action_show_processingcentres(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transform. Centers',
            'res_model': 'wua.processingcentre',
            'view_mode': 'tree,form',
            'domain': [('electricitypoint_id', '=', self.id)],
            'context': {'default_electricitypoint_id': self.id},
        }
