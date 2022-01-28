# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    import_from_intake_readings = fields.Boolean(
        string='Import from intake readings')

    import_from_waterpipe_readings = fields.Boolean(
        string='Import from water pipe readings')

    import_from_flowmeter = fields.Boolean(
        string='Import from flow meter')
