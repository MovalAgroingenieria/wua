# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    last_reading_time = fields.Datetime(
        string='Last Reading Time')

    last_reading_value = fields.Float(
        string='Last Reading Value',
        digits=(32, 4))

    last_reading_instantflow = fields.Float(
        string='Last Reading Value',
        digits=(32, 4))

    flowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.flowreading',
        inverse_name='flowmeter_id')

    intakeconsumption_ids = fields.One2many(
        string='Intake Consumptions',
        comodel_name='wua.intakeconsumption',
        inverse_name='flowmeter_id')

    infm_ids = fields.One2many(
        string='Assigned Intakes',
        comodel_name='wua.in.fm',
        inverse_name='flowmeter_id')
