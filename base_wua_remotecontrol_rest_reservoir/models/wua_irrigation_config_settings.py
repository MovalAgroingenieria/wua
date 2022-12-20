# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    # Function to be inherited and extended by every telecontrol
    # With super
    def import_from_reservoir_any(self):
        return False
