# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWatermeter(models.Model):
    _inherit = 'wua.watermeter'

    last_controlreading_time = fields.Datetime(
        string='Last Control-Reading Time')

    last_controlreading_value = fields.Float(
        string='Last Control-Reading Value',
        digits=(32, 4))
